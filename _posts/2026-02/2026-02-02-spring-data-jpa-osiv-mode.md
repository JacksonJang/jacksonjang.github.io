---
layout:     post
title:      "Spring Data JPA - OSIV(Open Session In View) 정리(+논란 포함)"
subtitle:   "Spring Data JPA - OSIV(Open Session In View)"
date:       2026-02-02 19:00:00
author:     JacksonJang
post_assets: "/assets/posts/2026-02-02"
catalog: true
categories:
    - Spring Boot
tags:
    - Spring Boot
    - JPA
    - OSIV
---

# OSIV 활성화 시 나타나는 메시지
```
spring.jpa.open-in-view is enabled by default.
Therefore, database queries may be performed during view rendering.
Explicitly configure spring.jpa.open-in-view to disable this warning
```
로그에 보이는 메시지는 `Spring Boot`의 `OSIV(Open Session In View)` 설정이 기본적으로 활성화되어 있음을 알려줍니다.
이 설정 값이 왜 중요하고, 개발자들 사이에서 논란이 있었는지 자세히 알아보겠습니다.

# OSIV 모드란?
`OSIV`는 영속성 컨텍스트를 **HTTP 응답이 완전히 전송될 때까지** 유지하는 기능입니다.

- OEIV(Open EntityManager In View) : JPA
- OSIV(Open Session In View) : Hibernate

View 렌더링(JSP/Thymeleaf)이 완료될 때까지 `EntityManager`를 열어두고, 
렌더링이 완료되면 `EntityManager`를 닫습니다.
<img src="{{ page.post_assets }}/open-entity-manager-in-view-filter.png">

추가적으로, `OSIV` 가 활성화 되어 있으면 영속성 컨텍스트가 유지되므로 
지연 로딩을 사용할 수 있어서 개발 편의성이 향상되고,
View 에서도 사용할 수 있습니다.

이렇게 `OSIV`의 설정은 `spring.jpa.open-in-view` 속성 값을 `true` 혹은 `false`를 통해 설정 가능합니다.


# spring.jpa.open-in-view 기본값 논란
<img src="{{ page.post_assets }}/issue-1-kr.png">
이슈 링크: [https://github.com/spring-projects/spring-boot/issues/7107](https://github.com/spring-projects/spring-boot/issues/7107)
2016년 10월, Spring Boot 커뮤니티에서 `@vpavic`님의 "OSIV 활성화는 안티패턴이다"라는 주장을 시작으로 논쟁이 시작되었습니다.
`@vpavic`님은 `OpenEntityManagerInViewInterceptor`를 기본적으로 활성화하는 것이 문제이며 opt-in 방식으로 전환하거나 최소한 문서화를 강화해야 한다고 주장했습니다.
`@odrotbohm`님(Spring Data 리드)은 `OSIV`를 왜 안티패턴으로 봐야 하는지에 대한 명확한 근거를 요구했으며 단순히 "널리 알려진 안티패턴"이라는 주장만으로는 기본 설정을 변경할 수 없다는 입장을 보였습니다.
`@s4gh`님은 Spring Boot의 핵심 철학인 "그냥 실행할 수 있는(just run)" 애플리케이션 구축과 상충된다는 점을 지적하며, 기본 설정 변경이 기존 애플리케이션에 미칠 영향(LazyInitializationException 발생 등)을 우려했습니다.

> Spring Boot makes it easy to create stand-alone, production-grade Spring based Applications that you can "just run".


# 결국..
<img src="{{ page.post_assets }}/issue-end.png">
<br />
논쟁이 길어지면서 이슈는 종료되었고, 최종적으로 `@aahlenst`님의 제안대로 [경고 메시지를 출력](#osiv-활성화-시-나타나는-메시지)하는 방향으로 결정되었습니다.

# OSIV를 false 로 변경되면 어떻게 되길래?
`OSIV` 모드를 `false`로 설정하면 영속성 컨텍스트(Persistence Context)의 생명주기가 트랜잭션 범위 내로 제한됩니다.

# 지연 로딩 문제의 사전 탐지 가능
`OSIV`가 비활성화되면 `@Transactional` 범위를 벗어난 영역(Controller, View)에서 지연 로딩을 시도할 경우 즉시 `LazyInitializationException`이 발생합니다.

이는 언뜻 불편해 보이지만, 실제로는 **개발 단계에서 N+1 쿼리 문제를 조기에 발견**할 수 있습니다.
`OSIV`가 활성화된 상태에서는 이러한 문제가 숨겨져 있다가 실제 프로덕션 환경의 대용량 트래픽에서 성능 저하로 나타나게 됩니다.
```java
// OSIV = false 일 때
@Transactional
public Order findOrder(Long id) {
    return orderRepository.findById(id); // Order만 조회
}

public OrderResponse getOrder(Long id) {
    Order order = orderService.findOrder(id);
    // LazyInitializationException 발생!
    // 개발 단계에서 즉시 문제를 인지하고 수정 가능
    order.getOrderItems().size(); 
}
```

이를 해결하기 위해 이전에 작성한 [JPA N+1 문제 해결하기](/posts/spring-jpa-n+1) 포스팅을 참고하시면 됩니다.


# 커넥션 풀 고갈 방지
`OSIV`가 활성화(`true`)된 경우 HTTP 요청이 시작되면 데이터베이스 커넥션을 획득하고 응답이 완료될 때까지 보유합니다. 이후에 데이터베이스 작업이 끝난 후에도 View 렌더링, JSON 직렬화 등의 긴 시간 동안 커넥션을 점유하게 돼서 문제가 발생하는데..

`OSIV`를 비활성화(`false`)하면 트랜잭션이 종료되는 즉시 커넥션이 반환되어서 **커넥션 풀의 회전율이 향상**됩니다.

그래서 `OSIV = false` 설정은 초기 개발 비용(명시적 Fetch 전략 수립)을 요구하지만, **프로덕션 환경의 안정성과 성능을 위한 필수적인 선택**이라고 봅니다.