---
layout:     post
title:      "@Transactional 전파 타입(Propagation) 정리"
subtitle:   "Spring @Transactional Propagation Types"
date:       2026-02-11 19:00:00
author:     JacksonJang
post_assets: "/assets/posts/2026-02-11"
catalog: true
categories:
    - Spring Boot
tags:
    - Spring Boot
    - Transaction
---

## 전파 타입(Propagation) 요약

| 전파 타입 | 기존 트랜잭션 있음 | 기존 트랜잭션 없음 |
|---|---|---|
| **REQUIRED** | 기존 트랜잭션 참여 | 새 트랜잭션 생성 |
| **REQUIRES_NEW** | 기존 중단 + 새 트랜잭션 생성 | 새 트랜잭션 생성 |
| **SUPPORTS** | 기존 트랜잭션 참여 | 트랜잭션 없이 실행 |
| **NOT_SUPPORTED** | 기존 중단 + 트랜잭션 없이 실행 | 트랜잭션 없이 실행 |
| **MANDATORY** | 기존 트랜잭션 참여 | 예외 발생 |
| **NEVER** | 예외 발생 | 트랜잭션 없이 실행 |
| **NESTED** | Savepoint 생성 (중첩) | 새 트랜잭션 생성 |

## @Transactional 전파(Propagation)란?
`@Transactional`의 `전파(Propagation)`는 **트랜잭션이 이미 존재할 때, 새로운 트랜잭션을 어떻게 처리할지** 결정하는 설정입니다.

예를 들어, `A 메서드`에서 `B 메서드`를 호출할 때 A의 트랜잭션을 그대로 사용할지 아니면 B에서 새로운 트랜잭션을 생성할지를 정할 수 있습니다.

```java
@Transactional
public void methodA() {
    // A의 트랜잭션이 존재하는 상태
    methodB();
}

@Transactional(propagation = Propagation.???)
public void methodB() {
    // 전파 타입에 따라 트랜잭션 동작이 달라진다
}
```

## 왜 전파 타입을 알아야 하는가?
기본적으로 `@Transactional`의 전파 타입은 `REQUIRED`입니다.
```java
/**
 * The transaction propagation type.
 * <p>Defaults to {@link Propagation#REQUIRED}.
 * @see org.springframework.transaction.interceptor.TransactionAttribute#getPropagationBehavior()
 */
Propagation propagation() default Propagation.REQUIRED;
```
대부분의 경우 기본값(`REQUIRED`)으로 충분하지만
아래와 같은 상황에서는 전파 타입을 변경해야 합니다.

- **로그 기록** : 비즈니스 로직이 실패해도 로그는 반드시 저장해야 할 때
- **외부 API 호출** : 외부 API 호출 결과를 별도로 관리해야 할 때
- **읽기 전용 작업** : 트랜잭션 없이 조회만 해야 할 때


## 전파 타입 종류

### REQUIRED (기본값)
**기존 트랜잭션이 있으면 참여하고, 없으면 새로 생성합니다.**

가장 많이 사용되는 기본 전파 타입입니다.
```java
@Transactional(propagation = Propagation.REQUIRED)
public void createOrder(OrderRequest request) {
    orderRepository.save(request.toEntity());
}
```

동작 방식:
- 기존 트랜잭션 **있음** → 기존 트랜잭션에 참여
- 기존 트랜잭션 **없음** → 새 트랜잭션 생성

**주의할 점:** 기존 트랜잭션에 참여한 경우, 내부 메서드에서 예외가 발생하면 **전체 트랜잭션이 롤백**됩니다.


### REQUIRES_NEW
**항상 새로운 트랜잭션을 생성하고, 기존 트랜잭션은 일시 중단합니다.**

```java
@Transactional(propagation = Propagation.REQUIRES_NEW)
public void saveLog(String message) {
    logRepository.save(new Log(message));
}
```

동작 방식:
- 기존 트랜잭션 **있음** → 기존 트랜잭션 일시 중단 + 새 트랜잭션 생성
- 기존 트랜잭션 **없음** → 새 트랜잭션 생성

```java
@Transactional
public void processOrder(OrderRequest request) {
    orderRepository.save(request.toEntity()); // 주문 저장

    logService.saveLog("주문 생성"); // 별도 트랜잭션으로 실행

    // 여기서 예외 발생해도 로그는 이미 커밋됨
    validateOrder(request);
}
```

즉, `REQUIRES_NEW`는 기존 트랜잭션과 **완전히 독립적**이기 때문에 내부 트랜잭션의 커밋/롤백이 외부 트랜잭션에 영향을 주지 않습니다.


### SUPPORTS
**기존 트랜잭션이 있으면 참여하고, 없으면 트랜잭션 없이 실행합니다.**

```java
@Transactional(propagation = Propagation.SUPPORTS)
public List<Order> getOrders() {
    return orderRepository.findAll();
}
```

동작 방식:
- 기존 트랜잭션 **있음** → 기존 트랜잭션에 참여
- 기존 트랜잭션 **없음** → 트랜잭션 없이 실행


### NOT_SUPPORTED
**트랜잭션 없이 실행하고, 기존 트랜잭션이 있으면 일시 중단합니다.**

```java
@Transactional(propagation = Propagation.NOT_SUPPORTED)
public void sendNotification(String userId) {
    // 트랜잭션 없이 실행
    notificationClient.send(userId, "알림 메시지");
}
```

동작 방식:
- 기존 트랜잭션 **있음** → 기존 트랜잭션 일시 중단 + 트랜잭션 없이 실행
- 기존 트랜잭션 **없음** → 트랜잭션 없이 실행

외부 시스템 호출처럼 트랜잭션이 필요 없는 작업에 활용할 수 있습니다.


### MANDATORY
**반드시 기존 트랜잭션이 있어야 하고, 없으면 예외가 발생합니다.**

```java
@Transactional(propagation = Propagation.MANDATORY)
public void deductStock(Long productId, int quantity) {
    Product product = productRepository.findById(productId)
            .orElseThrow();
    product.deductStock(quantity);
}
```

동작 방식:
- 기존 트랜잭션 **있음** → 기존 트랜잭션에 참여
- 기존 트랜잭션 **없음** → `IllegalTransactionStateException` 발생

```java
// 트랜잭션 없이 호출하면 예외 발생!
deductStock(1L, 10); // IllegalTransactionStateException
```

**항상 트랜잭션 내에서만 호출되어야 하는 메서드**에 사용하면, 실수로 트랜잭션 없이 호출하는 상황을 방지할 수 있습니다.


### NEVER
**트랜잭션이 있으면 예외가 발생합니다. 트랜잭션 없이만 실행 가능합니다.**

```java
@Transactional(propagation = Propagation.NEVER)
public String checkHealthStatus() {
    return "OK";
}
```

동작 방식:
- 기존 트랜잭션 **있음** → `IllegalTransactionStateException` 발생
- 기존 트랜잭션 **없음** → 트랜잭션 없이 실행

`MANDATORY`와 정반대 개념입니다.


### NESTED
**기존 트랜잭션 내에서 중첩 트랜잭션(Savepoint)을 생성합니다.**

```java
@Transactional(propagation = Propagation.NESTED)
public void addBonusPoint(Long userId, int point) {
    pointRepository.save(new Point(userId, point));
}
```

동작 방식:
- 기존 트랜잭션 **있음** → Savepoint를 생성하고 중첩 트랜잭션 실행
- 기존 트랜잭션 **없음** → 새 트랜잭션 생성 (`REQUIRED`와 동일)

```java
@Transactional
public void processPayment(PaymentRequest request) {
    paymentRepository.save(request.toEntity()); // 결제 저장

    try {
        pointService.addBonusPoint(request.getUserId(), 100); // 중첩 트랜잭션
    } catch (Exception e) {
        // 포인트 적립 실패해도 결제는 유지됨
        // Savepoint까지만 롤백
    }
}
```

`REQUIRES_NEW`와의 차이점:
- `REQUIRES_NEW` : 완전히 독립된 트랜잭션 → 외부 트랜잭션이 롤백되어도 내부 트랜잭션은 유지
- `NESTED` : 부모 트랜잭션에 종속 → **부모가 롤백되면 중첩 트랜잭션도 롤백**

> **주의:** `NESTED`는 JDBC Savepoint를 사용하기 때문에 JPA에서는 지원이 제한적입니다. `JpaTransactionManager`는 JDBC Savepoint를 지원하지만, JTA 환경에서는 사용할 수 없습니다.

## 주의할 점
### 같은 클래스 내부 호출 시 전파가 적용되지 않는다
`@Transactional`은 **프록시 기반**으로 동작하기 때문에, 같은 클래스 내부에서 호출하면 프록시를 거치지 않아 전파 설정이 무시됩니다.

```java
@Service
public class OrderService {

    @Transactional
    public void processOrder(OrderRequest request) {
        orderRepository.save(request.toEntity());
        saveLog("주문 생성"); // 내부 호출 -> 프록시 미적용!
    }

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void saveLog(String message) {
        // REQUIRES_NEW가 적용되지 않음
        // processOrder의 트랜잭션에 그대로 참여
        logRepository.save(new Log(message));
    }
}
```

### 해결 방법
별도의 클래스로 분리해서 호출하면 프록시가 정상적으로 동작합니다.
```java
@Service
@RequiredArgsConstructor
public class OrderService {

    private final LogService logService;

    @Transactional
    public void processOrder(OrderRequest request) {
        orderRepository.save(request.toEntity());
        logService.saveLog("주문 생성"); // 외부 클래스 호출 -> 프록시 적용!
    }
}

@Service
public class LogService {

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void saveLog(String message) {
        logRepository.save(new Log(message));
    }
}
```
