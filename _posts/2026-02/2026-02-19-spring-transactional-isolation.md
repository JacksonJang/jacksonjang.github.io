---
layout:     post
title:      "@Transactional 격리 수준(Isolation Level) 정리"
subtitle:   "Spring @Transactional Isolation Levels"
date:       2026-02-19 20:00:00
author:     JacksonJang
post_assets: "/assets/posts/2026-02-19"
catalog: true
categories:
    - Spring Boot
tags:
    - Spring Boot
    - Transactional
---

## 격리 수준(Isolation Level) 요약

| 격리 수준 | Dirty Read | Non-Repeatable Read | Phantom Read | 성능 |
|---|---|---|---|---|
| **READ_UNCOMMITTED** | O | O | O | 가장 빠름 |
| **READ_COMMITTED** | X | O | O | 빠름 |
| **REPEATABLE_READ** | X | X | O | 보통 |
| **SRIALIZABLEE** | X | X | X | 가장 느림 |

> O = 발생 가능, X = 방지됨

## 격리 수준(Isolation Level)이란?
`격리 수준(Isolation Level)`은 동시에 여러 트랜잭션이 실행될 때 **각 트랜잭션이 다른 트랜잭션의 변경 사항을 어느 정도까지 볼 수 있는지**를 결정하는 규칙입니다.

쉽게 말하면
> 다른 사람이 아직 끝내지 않은 작업 내용을 내가 볼 수 있게 할까?
> 아니면 완전히 끝난 결과만 보게 할까?

이걸 정하는 기준이라고 보면 됩니다.

트랜잭션의 **ACID** 원칙 중 **I(Isolation)**에 해당하며
격리 수준이 높을수록 데이터 정합성은 보장되지만 동시 처리 성능은 떨어집니다.


## 왜 격리 수준을 알아야 하는가?
기본적으로 `@Transactional`의 격리 수준은 `DEFAULT`입니다.
```java
/**
 * The transaction isolation level.
 * <p>Defaults to {@link Isolation#DEFAULT}.
 * <p>Exclusively designed for use with {@link Propagation#REQUIRED} or
 * {@link Propagation#REQUIRES_NEW} since it only applies to newly started
 * transactions. Consider switching the "validateExistingTransactions" flag to
 * "true" on your transaction manager if you'd like isolation level declarations
 * to get rejected when participating in an existing transaction with a different
 * isolation level.
 * @see org.springframework.transaction.interceptor.TransactionAttribute#getIsolationLevel()
 * @see org.springframework.transaction.support.AbstractPlatformTransactionManager#setValidateExistingTransaction
 */
Isolation isolation() default Isolation.DEFAULT;
```
`DEFAULT`는 데이터베이스의 기본 격리 수준을 따르는데 대부분의 데이터베이스는 아래와 같습니다.
- **MySQL(InnoDB)** : `REPEATABLE_READ`
- **PostgreSQL** : `READ_COMMITTED`
- **Oracle** : `READ_COMMITTED`

`REPEATABLE_READ`, `READ_COMMITTED` 는 [격리 수준 설정](#격리-수준-설정)에서 자세히 설명할 예정입니다.

DB마다 기본값이 다르기 때문에 동일한 코드라도 **사용하는 DB에 따라 동작이 달라질 수 있습니다.**
격리 수준을 이해하면 3가지의 동시성 문제를 예방할 수 있습니다.

- **Dirty Read** : 커밋되지 않은 데이터를 읽는 문제
- **Non-Repeatable Read** : 같은 조회를 두 번 했을 때 결과가 다른 문제
- **Phantom Read** : 같은 조건으로 조회했을 때 행의 수가 달라지는 문제

## 동시성 문제 3가지

### Dirty Read (더티 리드)
**커밋되지 않은** 다른 트랜잭션의 변경 사항을 읽는 현상입니다.

```
[트랜잭션 A]                         [트랜잭션 B]
                                    UPDATE product SET price = 5000
                                    WHERE id = 1; (아직 커밋 안 함)
SELECT price FROM product
WHERE id = 1;
-> 5000 읽음 (커밋 안 된 데이터!)
                                    ROLLBACK; (롤백!)
-> 5000은 존재하지 않는 데이터였음
```
트랜잭션 B가 롤백하면 트랜잭션 A가 읽은 5000은 실제로 존재하지 않는 데이터가 됩니다.

### Non-Repeatable Read (반복 불가능한 읽기)
같은 행을 두 번 읽었을 때 **다른 트랜잭션의 커밋으로 인해** 값이 달라지는 현상입니다.

```
[트랜잭션 A]                         [트랜잭션 B]
SELECT price FROM product
WHERE id = 1;
-> 10000 읽음
                                    UPDATE product SET price = 5000
                                    WHERE id = 1;
                                    COMMIT;
SELECT price FROM product
WHERE id = 1;
-> 5000 읽음 (같은 트랜잭션 내에서 값이 변경됨!)
```

### Phantom Read (팬텀 리드)
같은 조건으로 조회했을 때 **다른 트랜잭션의 INSERT/DELETE로 인해** 행의 수가 달라지는 현상입니다.

```
[트랜잭션 A]                         [트랜잭션 B]
SELECT * FROM product
WHERE price > 5000;
-> 3건 조회
                                    INSERT INTO product (name, price)
                                    VALUES ('새상품', 8000);
                                    COMMIT;
SELECT * FROM product
WHERE price > 5000;
-> 4건 조회 (유령처럼 행이 추가됨!)
```

## MVCC란?
`MVCC(Multi-Version Concurrency Control)`는 데이터를 읽을 때 **Lock을 사용하지 않고** 동시성을 제어하는 기술입니다.

일반적으로 Lock 기반 동시성 제어는 하나의 트랜잭션이 데이터를 읽는 동안 다른 트랜잭션이 해당 데이터를 수정하지 못하게 막습니다.
하지만 이 방식은 읽기와 쓰기가 서로를 차단(Block)하기 때문에 성능이 떨어집니다.

MVCC는 이 문제를 해결하기 위해 **데이터를 변경할 때 이전 버전을 별도로 보관**하는 방식을 사용합니다.

```
[트랜잭션 A - 읽기]                    [트랜잭션 B - 쓰기]

트랜잭션 시작 (스냅샷 생성)
                                     UPDATE product SET price = 5000
                                     WHERE id = 1;
SELECT price FROM product
WHERE id = 1;
-> 10000 읽음 (스냅샷 기준!)
                                     COMMIT;
SELECT price FROM product
WHERE id = 1;
-> 10000 읽음 (여전히 스냅샷 기준!)
```

위 예시에서 트랜잭션 B가 가격을 5000으로 변경하고 커밋해도,
트랜잭션 A는 **자신이 시작한 시점의 스냅샷(이전 버전)**을 읽기 때문에 항상 10000을 반환합니다.

이렇게 MVCC 덕분에 **읽기 작업은 쓰기를 차단하지 않고**, **쓰기 작업도 읽기를 차단하지 않아** 동시 처리 성능이 크게 향상됩니다.

> MySQL(InnoDB), PostgreSQL, Oracle 등 대부분의 RDBMS가 MVCC를 지원합니다.

## 격리 수준 설정

### DEFAULT
데이터베이스의 기본 격리 수준을 사용합니다.
Spring에서 별도로 격리 수준을 지정하지 않으면 이 값이 사용됩니다.

```java
@Transactional // isolation = Isolation.DEFAULT (생략 가능)
public Product getProduct(Long id) {
    return productRepository.findById(id).orElseThrow();
}
```

### READ_UNCOMMITTED
가장 낮은 격리 수준으로, **커밋되지 않은 데이터도 읽을 수 있습니다.**
Dirty Read, Non-Repeatable Read, Phantom Read 모두 발생할 수 있습니다.

```java
@Transactional(isolation = Isolation.READ_UNCOMMITTED)
public int getProductPrice(Long productId) {
    return productRepository.findById(productId)
            .orElseThrow()
            .getPrice();
}
```

정합성보다 **성능이 중요한 경우**에 사용합니다.
- 대략적인 통계 조회 (정확하지 않아도 되는 경우)
- 실시간 모니터링 대시보드

> **주의:** 실무에서는 데이터 정합성 문제가 크기 때문에 거의 사용하지 않습니다.

### READ_COMMITTED
**커밋된 데이터만 읽을 수 있습니다.** Dirty Read를 방지합니다.
대부분의 RDBMS(PostgreSQL, Oracle)의 기본 격리 수준입니다.

```java
@Transactional(isolation = Isolation.READ_COMMITTED)
public void transferMoney(Long fromId, Long toId, int amount) {
    Account from = accountRepository.findById(fromId).orElseThrow();
    Account to = accountRepository.findById(toId).orElseThrow();

    from.withdraw(amount);
    to.deposit(amount);
}
```

커밋된 데이터만 읽으므로 Dirty Read는 발생하지 않지만,
같은 트랜잭션 내에서 같은 데이터를 두 번 읽으면 값이 달라질 수 있습니다(Non-Repeatable Read).

### REPEATABLE_READ
트랜잭션이 시작된 시점의 데이터를 기준으로 **일관된 읽기를 보장**합니다.
같은 행을 여러 번 읽어도 항상 같은 값이 반환됩니다.

MySQL(InnoDB)의 기본 격리 수준입니다.

```java
@Transactional(isolation = Isolation.REPEATABLE_READ)
public void generateReport(Long productId) {
    // 첫 번째 조회
    Product product = productRepository.findById(productId).orElseThrow();
    int priceFirst = product.getPrice();

    // 중간에 다른 트랜잭션이 가격을 변경해도
    // 두 번째 조회 결과는 동일
    product = productRepository.findById(productId).orElseThrow();
    int priceSecond = product.getPrice();

    // priceFirst == priceSecond 보장
}
```

Dirty Read와 Non-Repeatable Read를 방지하지만, **SQL 표준 스펙상** Phantom Read는 발생할 수 있습니다.

#### MySQL InnoDB는 Phantom Read도 방지한다
MySQL InnoDB는 `REPEATABLE_READ`에서도 **MVCC + Next-Key Lock** 덕분에 Phantom Read가 **사실상 방지**됩니다.

**MVCC에 의한 방지 (일반 SELECT)**

일반 `SELECT`(Non-Locking Read)는 [MVCC](#mvcc란)의 **스냅샷 읽기** 덕분에 Phantom Read가 발생하지 않습니다.
트랜잭션이 시작된 시점의 스냅샷을 기준으로 읽기 때문에, 다른 트랜잭션이 INSERT/DELETE를 해도 보이지 않습니다.

```
[트랜잭션 A]                         [트랜잭션 B]
SELECT * FROM product
WHERE price > 5000;
-> 3건 조회 (스냅샷 생성)
                                    INSERT INTO product (name, price)
                                    VALUES ('새상품', 8000);
                                    COMMIT;
SELECT * FROM product
WHERE price > 5000;
-> 3건 조회 (스냅샷 기준이므로 동일!)
```

**Next-Key Lock에 의한 방지 (SELECT ... FOR UPDATE)**

`SELECT ... FOR UPDATE` 같은 Locking Read는 스냅샷이 아니라 **최신 데이터**를 읽으므로 MVCC만으로는 Phantom Read를 방지할 수 없습니다.
이때 InnoDB는 **Next-Key Lock(Record Lock + Gap Lock)**으로 해당 범위에 새로운 행이 삽입되는 것 자체를 막습니다.

```
Next-Key Lock = Record Lock + Gap Lock

Record Lock : 실제 존재하는 행(레코드)을 잠금
Gap Lock    : 행과 행 사이의 빈 공간(Gap)을 잠금 -> INSERT 차단
```

```
[트랜잭션 A]                         [트랜잭션 B]
SELECT * FROM product
WHERE price > 5000 FOR UPDATE;
-> 3건 조회 + price > 5000 범위에 Gap Lock 설정
                                    INSERT INTO product (name, price)
                                    VALUES ('새상품', 8000);
                                    -> Gap Lock에 의해 대기(Block)!
COMMIT;
                                    -> 이제 INSERT 실행됨
```

> **정리:** MySQL InnoDB의 `REPEATABLE_READ`는 SQL 표준보다 강력합니다.
> 일반 SELECT는 **MVCC 스냅샷**으로, Locking Read는 **Next-Key Lock**으로 Phantom Read를 방지합니다.
> 따라서 InnoDB 환경에서는 대부분의 경우 `SERIALIZABLE`까지 올릴 필요 없이 `REPEATABLE_READ`로 충분합니다.

### SERIALIZABLE
가장 높은 격리 수준으로, 트랜잭션을 **순차적으로 실행하는 것과 같은 효과**를 보장합니다.
모든 동시성 문제(Dirty Read, Non-Repeatable Read, Phantom Read)를 방지합니다.

```java
@Transactional(isolation = Isolation.SERIALIZABLE)
public void reserveSeat(Long seatId, Long userId) {
    Seat seat = seatRepository.findById(seatId).orElseThrow();

    if (seat.isAvailable()) {
        seat.reserve(userId);
    } else {
        throw new AlreadyReservedException("이미 예약된 좌석입니다.");
    }
}
```

가장 안전하지만 **성능 저하가 심합니다.**
- 동시 접근 시 대기(Lock Wait) 또는 실패 가능
- 데드락 발생 확률 높음
- 처리량(Throughput) 감소

> **주의:** 정합성이 매우 중요한 경우(좌석 예약, 재고 관리)에 사용하되, 성능 영향을 반드시 고려해야 합니다.

## 격리 수준 적용 시 주의사항

### 1. Propagation과의 관계
`isolation` 속성은 **새로운 트랜잭션이 생성될 때만** 적용됩니다.
기존 트랜잭션에 참여하는 경우(`REQUIRED`로 기존 트랜잭션에 합류)에는 격리 수준 설정이 무시됩니다.

```java
@Transactional(isolation = Isolation.READ_COMMITTED)
public void outerMethod() {
    // READ_COMMITTED로 트랜잭션 시작
    innerService.innerMethod();
}

// 기존 트랜잭션에 참여하므로 SERIALIZABLE 설정이 무시됨!
@Transactional(isolation = Isolation.SERIALIZABLE)
public void innerMethod() {
    // 실제로는 outerMethod의 READ_COMMITTED가 적용됨
}
```

독립적인 격리 수준을 적용하려면 `REQUIRES_NEW`와 함께 사용해야 합니다.
```java
@Transactional(
    propagation = Propagation.REQUIRES_NEW,
    isolation = Isolation.SERIALIZABLE
)
public void innerMethod() {
    // 새 트랜잭션으로 SERIALIZABLE 적용됨
}
```

### 2. DB별 지원 범위가 다름
모든 DB가 모든 격리 수준을 지원하는 것은 아닙니다.

| DB | READ_UNCOMMITTED | READ_COMMITTED | REPEATABLE_READ | SERIALIZABLE |
|---|---|---|---|---|
| **MySQL** | O | O | O (기본) | O |
| **PostgreSQL** | X (READ_COMMITTED로 처리) | O (기본) | O | O |
| **Oracle** | X | O (기본) | X | O |

지원하지 않는 격리 수준을 설정하면 DB에 따라 무시되거나 예외가 발생할 수 있으므로,
사용하는 DB의 지원 범위를 확인해야 합니다.

### 3. 격리 수준이 높을수록 Lock이 증가
격리 수준이 높으면 데이터 정합성은 보장되지만 그만큼 Lock이 많아져
**데드락(Deadlock)** 발생 확률이 높아지고 **동시 처리 성능이 저하**됩니다.

```java
// 데드락 위험이 높은 패턴
@Transactional(isolation = Isolation.SERIALIZABLE)
public void transferBetweenAccounts(Long fromId, Long toId, int amount) {
    Account from = accountRepository.findById(fromId).orElseThrow(); // Lock 획득
    Account to = accountRepository.findById(toId).orElseThrow();     // Lock 획득

    from.withdraw(amount);
    to.deposit(amount);
    // 두 트랜잭션이 서로 반대 순서로 Lock을 잡으면 데드락 발생!
}
```

## 실무에서의 권장 사항
대부분의 경우 DB 기본 격리 수준(`DEFAULT`)으로 충분합니다.

| 상황 | 권장 격리 수준 |
|---|---|
| 일반적인 CRUD | `DEFAULT` (DB 기본값) |
| 정확한 통계/집계 필요 | `REPEATABLE_READ` |
| 동시성 제어가 중요한 경우 (좌석 예약 등) | `SERIALIZABLE` 또는 비관적 락 |
| 대략적인 조회 (정합성 불필요) | `READ_UNCOMMITTED` |

> **팁:** 격리 수준을 높이는 것보다 **비관적 락(Pessimistic Lock)** 또는 **낙관적 락(Optimistic Lock)**을 활용하는 것이 성능과 정합성 모두를 잡을 수 있는 경우가 많습니다.
