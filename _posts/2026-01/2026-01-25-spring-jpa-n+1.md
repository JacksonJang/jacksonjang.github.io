---
layout:     post
title:      "JPA N+1 문제 해결하기"
subtitle:   "Resolving JPA N+1 Problem"
date:       2026-01-25 20:00:00
author:     JacksonJang
post_assets: "/assets/posts/2026-01-25"
catalog: true
categories:
    - Spring Boot
tags:
    - Spring Boot
    - JPA
---

## N+1 문제란?
`N+1 문제`는 데이터를 `1건 조회`했을 때, 연관된 데이터를 가져오기 위해 `N번의 쿼리가 추가로 실행되는 현상`입니다.


## N+1 문제 발생 예시
`팀(Team)`이 10개 있다고 가정하고

`팀(Team) 목록을 조회`한 뒤, 각 팀의 `멤버(Member)를 조회`하면

총 **11번(1+10(N))의 쿼리가 발생**합니다.

### 왜 11번의 쿼리가 발생하게 되는가?
```java
@Entity
public class Team {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String name;

    @OneToMany(mappedBy = "team", fetch = FetchType.LAZY)
    private List<Member> members = new ArrayList<>();
}

@Entity
public class Member {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String name;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "team_id")
    private Team team;
}
```
이렇게 `팀(Team)` 과 `멤버(Member)`가 연관 관계를 가지고 있다고 하겠습니다.


### N+1 발생 코드
```java
public void findAllTeamsWithNPlusOneProblem() {
    System.out.println("N+1 시작");
    List<Team> teams = teamRepository.findAll();
    System.out.println("팀 조회 끝");

    for (Team team : teams) {
        // 각 팀의 멤버 조회 쿼리 발생 (N번)
        team.getMembers().size();
    }
}
```

#### 로그 확인
```sql
-- 팀 전체 조회 (1번)
select t1_0.id, t1_0.name from team t1_0;

-- 각 팀의 멤버 조회 (N번)
select m1_0.team_id,m1_0.id,m1_0.name from member m1_0 where m1_0.team_id=1;
...
select m1_0.team_id,m1_0.id,m1_0.name from member m1_0 where m1_0.team_id=10;
```
지금처럼 `LAZY` 로딩이라도 `연관 데이터에 접근하는 순간` 쿼리가 발생합니다.


## 해결 방법

### Fetch Join
JPQL에서 `JOIN FETCH`를 사용하여 연관된 엔티티를 한 번에 조회합니다.

```java
public interface TeamRepository extends JpaRepository<Team, Long> {

    @Query("SELECT t FROM Team t JOIN FETCH t.members")
    List<Team> findAllWithMembers();
}
```

#### 로그 확인
```sql
select
        t1_0.id,
        m1_0.team_id,
        m1_0.id,
        m1_0.name,
        t1_0.name 
    from
        team t1_0 
    join
        member m1_0 
            on t1_0.id=m1_0.team_id
```
한 번에 조회하지만, 페이징이랑 같이쓰면 상당히 위험합니다.


### Fetch Join을 페이징하면 왜 위험한가?
```java
// Fetch Join + 페이징
@Query("SELECT t FROM Team t JOIN FETCH t.members")
Page<Team> findAllWithMembersByFetchJoinAndPaging(Pageable pageable);
```
**실제 데이터**
- `Team` 1,000개
- 각 `Team`당 `Member` 50명

**원하는 결과**
`Team` 10개 조회 (`Member` 포함해서 약 500 rows)

#### 테스트 시작!
```java
// 1개 요청
PageRequest pageRequest = PageRequest.of(0, 1);

Page<Team> teams = teamRepository.findAllWithMembersByFetchJoinAndPaging(pageRequest);

System.out.println(">>> 조회된 팀 수: " + teams.getContent().size());
System.out.println(">>> 전체 팀 수: " + teams.getTotalElements());
```

```
HHH90003004: firstResult/maxResults specified with 
collection fetch; applying in memory
```
테스트를 실행하게 되면 이런 메시지를 얻을 수 있습니다.
<br />
위 뜻을 해석하면, 페이징(LIMIT/OFFSET)을 요청했지만
- LIMIT : setFirstResult()
- OFFSET : setMaxResults()

Collection 에 fetch join을 같이 썼으니 `DB에서 페이징 못하고 메모리에서 처리`한다.
<br />
즉, 메모리에서 처리한다는 건 일단 `전부 다 조회한다`는 뜻입니다.

#### 로그 확인
```sql
select
        count(t1_0.id) 
    from
        team t1_0 
    join
        member m1_0 
            on t1_0.id=m1_0.team_id
```
여기서 **반드시 기억할 것**은 `Fetch Join + 페이징` 사용 금지


### @EntityGraph
어노테이션 기반으로 Fetch Join과 동일한 작업이 가능합니다.

```java
public interface TeamRepository extends JpaRepository<Team, Long> {

    @EntityGraph(attributePaths = {"members"})
    @Query("SELECT t FROM Team t")
    List<Team> findAllWithMembersByEntityGraph();
}
```


### @BatchSize
`@BatchSize`를 사용하면 N번의 쿼리를 IN 쿼리로 묶어서 실행합니다.

```java
@Entity
public class Team {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String name;

    @BatchSize(size = 100)
    @OneToMany(mappedBy = "team", fetch = FetchType.LAZY)
    private List<Member> members = new ArrayList<>();
}
```

또는 `application.properties`에서 전역 설정:
```properties
spring.jpa.properties.hibernate.default_batch_fetch_size=100
```

단, `@BatchSize`의 `size`는 너무 크면 IN 절이 길어져서 DB 성능에 영향을 줄 수 있습니다. 

#### 로그 확인
```sql
select
        m1_0.team_id,
        m1_0.id,
        m1_0.name 
    from
        member_batch m1_0 
    where
        m1_0.team_id in (1, 2, 3, 4, 5, ...);
```


### N + 1 해결 방법 요약
- **단건 조회 + 연관 데이터 필요:** Fetch Join 또는 @EntityGraph
- **목록 조회 + 페이징 필요:** @BatchSize (전역 설정 추천)
- **대량 데이터 조회:** @BatchSize + 적절한 size 조정