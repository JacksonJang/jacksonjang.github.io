---
layout:     post
title:      "Spring @Transactional 사용 시 주의사항"
subtitle:   "Spring @Transactional Pitfalls"
date:       2026-02-18 12:00:00
author:     JacksonJang
post_assets: "/assets/posts/2026-02-18"
catalog: true
categories:
    - Spring Boot
tags:
    - Spring
    - Transactional
---

## @Transactional이란?
`@Transactional`은 Spring에서 트랜잭션을 선언적으로 관리할 수 있게 해주는 어노테이션입니다.
클래스 또는 메서드에 붙이게 되면 해당 범위 내에서 실행되는 DB 작업들이 하나의 트랜잭션으로 묶이게 됩니다.

```java
@Transactional
public void addData(String data) {
    repository.save(data);
}
```
위 코드에선 예외가 발생하면 롤백이 진행됩니다.
단, Checked Exception 이면 롤백이 안됩니다.

Checked Exception 문제를 포함한 다양한 문제에 대해 알아보겠습니다.


## @Transactional 사용 시 주의사항

| # | 주의사항 | 원인 | 해결 |
|---|---------|------|------|
| [1](#1-private-메서드에서는-transactional-무시됨) | **private** 메서드 무시됨 | 프록시가 오버라이드 불가 | public 사용 |
| [2](#2-final-클래스메서드에-transactional-무시됨) | **final** 클래스/메서드 무시됨 | 프록시가 상속/오버라이드 불가 | final 제거 |
| [3](#3-self-invocation-내부-호출-시-transactional-무시됨) | **Self-Invocation** 무시됨 | 내부 호출은 프록시 안 거침 | 별도 서비스 분리 |
| [4](#4-checked-exception은-롤백되지-않음) | **Checked Exception** 롤백 안 됨 | 기본 롤백 대상 아님 | rollbackFor 지정 |
| [5](#5-try-catch로-예외를-삼키면-롤백-안-됨) | **try-catch**로 삼키면 롤백 안 됨 | 스프링이 예외 감지 못 함 | throw로 다시 던지기 |
| [6](#8-timeout-미설정-시-무한-대기-위험) | **timeout 미설정** | 무한 대기로 장애 유발 | timeout 명시적 설정 |


### 1. private 메서드에서는 @Transactional 무시됨
Spring의 `@Transactional`은 **프록시 패턴**으로 동작하며,
인터페이스 유무에 따라 **JDK Dynamic Proxy** 또는 **CGLIB(Code Generator Library) 프록시**를 사용합니다.
(Spring Boot 2.0+ **기본값은 CGLIB**)

> **CGLIB란?**
> 클래스의 바이트 코드를 조작하여 프록시 객체를 생성해 주는 라이브러리입니다.
> 인터페이스 없이도 구체 클래스를 상속받아 프록시를 만들 수 있습니다.

프록시 객체가 타겟 객체를 감싸서 메서드 호출을 가로채고 트랜잭션 로직을 주입하는데 `private` 메서드는 Java의 접근 제어 특성상 상속 시 오버라이드가 불가능하므로 프록시가 해당 메서드를 가로챌 수 없습니다.

```java
@Service
public class OrderService {

    // 불가능 : private 안됨
    @Transactional
    private void processOrderPrivate(Long orderId) {
        // ...
    }

    // 불가능 : static 메서드는 프록시가 가로챌 수 없음
    @Transactional
    public static void processOrderStatic(Long orderId) {
        // ...
    }

    // 가능 : Spring 6 이후로 protected 가능하지만 권장하지 않음
    @Transactional
    protected void processOrderProtected(Long orderId) {
        // ...
    }

    // 가능 : Spring 6 이후로 package-private 가능하지만 권장하지 않음
    @Transactional
    void processOrderDefault(Long orderId) {
        // ...
    }

    // 가능 : public 으로 사용 권장
    @Transactional
    public void processOrderPublic(Long orderId) {
        // ...
    }
}
```

```
The @Transactional annotation is typically used on methods with public visibility.
As of 6.0, protected or package-visible methods can also be made transactional for
class-based proxies by default. Note that transactional methods in interface-based
proxies must always be public and defined in the proxied interface.
For both kinds of proxies, only external method calls coming in through the proxy are intercepted.
```
[Spring 공식 문서](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/annotations.html)에 따르면 Spring 6부터 클래스 기반 프록시(CGLIB)를 사용하는 경우 `protected`, `package-private` 메서드에도 트랜잭션 적용이 가능합니다.

#### Spring 구현 코드 확인

##### CglibAopProxy.doValidateClass()
`CglibAopProxy.doValidateClass()` 메서드에서 프록시 가능 여부를 검증합니다.

```java
for (Method method : methods) {
    int mod = method.getModifiers();
    // static이거나 private이면 검증 대상에서 제외
    if (!Modifier.isStatic(mod) && !Modifier.isPrivate(mod)) {
        if (Modifier.isFinal(mod)) {
            if (logger.isWarnEnabled() && Modifier.isPublic(mod)) {
                if (implementsInterface(method, ifcs)) {
                    logger.warn("Unable to proxy interface-implementing method [" + method + "] because " +
                            "it is marked as final, consider using interface-based JDK proxies instead.");
                }
                else {
                    logger.warn("Public final method [" + method + "] cannot get proxied via CGLIB, " +
                            "consider removing the final marker or using interface-based JDK proxies.");
                }
            }
        }
    }
}
```

##### AopUtils.selectInvocableMethod()
`AopUtils.selectInvocableMethod()` 메서드에서는 private 메서드가 프록시에서 호출될 경우 `IllegalStateException` 예외를 던집니다.

```java
Method methodToUse = MethodIntrospector.selectInvocableMethod(method, targetType);
// private 메서드는 프록시에서 호출 불가능
if (Modifier.isPrivate(methodToUse.getModifiers()) && 
    !Modifier.isStatic(methodToUse.getModifiers()) &&
    SpringProxy.class.isAssignableFrom(targetType)) {
    throw new IllegalStateException(String.format(
            "Need to invoke method '%s' found on proxy for target class '%s' but cannot " +
            "be delegated to target bean. Switch its visibility to package or protected.",
            method.getName(), method.getDeclaringClass().getSimpleName()));
}
```

### 2. final 클래스/메서드에 @Transactional 무시됨
`final` 클래스는 상속이 불가능하고, `final` 메서드는 오버라이드가 불가능하므로 프록시 생성이 실패합니다.

```java
// 불가 : 클래스 final
@Service
public final class PaymentService {

    @Transactional
    public void pay(Long orderId) {
        // ...
    }
}

// 불가 : 메서드 final
@Service
public class PaymentService {

    @Transactional
    public final void pay(Long orderId) {
        // ...
    }
}
```

#### Spring 구현 코드 확인

##### final 클래스인 경우
`CGLIB`의`Enhancer`가 프록시 클래스를 생성할 때, 부모 클래스가 `final`이면 `IllegalArgumentException` 예외를 발생시킵니다.

```java
// Enhancer.java
@Override
public void generateClass(ClassVisitor v) throws Exception {
    Class sc = (superclass == null) ? Object.class : superclass;

    // 클래스 타입이 final 이면 예외 발생
    if (TypeUtils.isFinal(sc.getModifiers())) {
        throw new IllegalArgumentException("Cannot subclass final class " + sc.getName());
    }
    // ...
}
```

이 예외는 `CglibAopProxy.buildProxy()`에서 `AopConfigException`으로 감싸져 던져집니다.

```java
// CglibAopProxy.java
private Object buildProxy(@Nullable ClassLoader classLoader, boolean classOnly) {
    // ...
    catch (CodeGenerationException | IllegalArgumentException ex) {
        throw new AopConfigException("Could not generate CGLIB subclass of " + this.advised.getTargetClass() +
                ": Common causes of this problem include using a final class or a non-visible class",
                ex);
    }
}
```

##### final 메서드인 경우
`Enhancer.getMethods()`에서 `final` 메서드를 프록시 대상에서 제외합니다.
`final` 메서드는 오버라이드가 불가능하므로 프록시가 가로챌 수 없어, `@Transactional`이 조용히 무시됩니다.

```java
// Enhancer.java
private static void getMethods(Class superclass, Class[] interfaces, List methods, List interfaceMethods, Set forcePublic) {
    // ...
    CollectionUtils.filter(methods, new RejectModifierPredicate(Constants.ACC_STATIC));
    CollectionUtils.filter(methods, new VisibilityPredicate(superclass, true));
    CollectionUtils.filter(methods, new DuplicatesPredicate());
    CollectionUtils.filter(methods, new RejectModifierPredicate(Constants.ACC_FINAL));
}
```

### 3. Self-Invocation (내부 호출) 시 @Transactional 무시됨
`@Transactional`은 **Spring AOP 프록시**를 통해 동작하기 때문에
같은 클래스 내부에서 메서드를 호출하면 프록시를 거치지 않아 트랜잭션이 적용되지 않습니다.

#### 문제 코드
```java
@Service
public class OrderService {

    public void createOrder(OrderRequest request) {
        // 내부 호출 -> 프록시를 거치지 않음!
        saveOrder(request);
    }

    @Transactional
    public void saveOrder(OrderRequest request) {
        orderRepository.save(request.toEntity());
    }
}
```
`createOrder()`에서 `saveOrder()`를 호출해도 **트랜잭션이 적용되지 않습니다.**
왜냐하면 내부 호출은 `this.saveOrder()`로 실행되기 때문에 프록시 객체를 거치지 않기 때문입니다.

#### 왜 프록시를 거쳐야 하는가?
Spring은 `@Transactional`이 붙은 빈을 프록시 객체로 감싸서 관리합니다.
외부에서 호출하면 **프록시 -> 트랜잭션 시작 -> 실제 메서드 실행 -> 커밋/롤백** 순서로 동작하지만,
같은 클래스 내부에서 호출하면 프록시를 우회하여 직접 메서드가 실행됩니다.

```
[외부 호출] // 트랜잭션 적용됨 
Controller -> Proxy(OrderService) -> saveOrder() 

[내부 호출] // 트랜잭션 미적용
createOrder() -> this.saveOrder()
```

#### 해결 방법
클래스를 분리하여 외부 호출로 변경합니다.

```java
@Service
@RequiredArgsConstructor
public class OrderService {

    private final OrderInternalService orderInternalService;

    public void createOrder(OrderRequest request) {
        orderInternalService.saveOrder(request);
    }
}

@Service
public class OrderInternalService {

    @Transactional
    public void saveOrder(OrderRequest request) {
        orderRepository.save(request.toEntity());
    }
}
```


### 4. Checked Exception은 롤백되지 않음
Spring의 `@Transactional`은 기본적으로 **Unchecked Exception** (`RuntimeException`, `Error`)만 롤백합니다.
`Checked Exception`이 발생하면 트랜잭션이 커밋됩니다.

Spring 내부 코드에서도 `Unchecked Exception`에 대한 분기 처리를 확인할 수 있습니다.
```java
// DefaultTransactionAttribute.java
public boolean rollbackOn(Throwable ex) {
    return (ex instanceof RuntimeException || ex instanceof Error);
}

// TransactionAspectSupport.java
protected void completeTransactionAfterThrowing(
    @Nullable TransactionInfo txInfo,
    InvocationCallback invocation, Throwable ex) {
        if (txInfo.transactionAttribute != null && 
            // 여기서 rollbackOn 부분에서 분기 처리
            txInfo.transactionAttribute.rollbackOn(ex)) {
                invocation.onRollback(ex, txInfo.getTransactionStatus());
                try {
                    txInfo.getTransactionManager().rollback(txInfo.getTransactionStatus());
                }
                catch (TransactionSystemException ex2) {
                    logger.error("Application exception overridden by rollback exception", ex);
                    ex2.initApplicationException(ex);
                    throw ex2;
                }
                catch (RuntimeException | Error ex2) {
                    logger.error("Application exception overridden by rollback exception", ex);
                    throw ex2;
                }
        }
}
```

Spring `@Transactional`이 `Checked Exception`에서 커밋하는 이유는
Java 설계 철학상 `Checked Exception`은 복구 가능한 예외로 간주되기 때문입니다.
"복구할 수 있으니 롤백까지는 필요 없다"는 판단이지만 `@Transactional(rollbackFor = Exception.class)`처럼 `Checked Exception`에서도 롤백되도록 명시하는 게 좋습니다.

#### 문제 코드
```java
@Service
public class FileService {

    // IOException(Checked Exception) 발생 시 롤백되지 않음
    @Transactional
    public void saveWithFile(Data data) throws IOException {
        dataRepository.save(data);
        fileManager.upload(data.getFile()); // IOException 발생 가능
    }
}
```

#### 해결 방법
`rollbackFor`를 지정하면 안전하게 해결할 수 있습니다.

```java
@Transactional(rollbackFor = Exception.class)
public void saveWithFile(Data data) throws IOException {
    dataRepository.save(data);
    fileManager.upload(data.getFile());
}
```

### 5. try-catch로 예외를 삼키면 롤백 안 됨
`try-catch`로 작성하고나서 `catch` 문에 `throw` 를 하지 않으면
스프링이 예외를 감지하지 못해 트랜잭션이 정상 커밋됩니다.

왜냐하면 프록시는 메서드 내부 구현을 들여다보지 않습니다.
메서드 경계에서 예외가 전파되었는지 여부만으로 커밋/롤백을 판단하기 때문에 `throw`를 하지 않으면 프록시에게는 구분할 방법이 없는 것입니다.

```java
@Service
public class OrderService {

    // 예외를 삼켜서 롤백되지 않음
    @Transactional
    public void placeOrder(Order order) {
        try {
            orderRepository.save(order);
            paymentService.pay(order); // 예외 발생
        } catch (Exception e) {
            log.error("주문 실패", e);
            // 예외를 삼킴 -> 롤백 안 됨
        }
    }
}
```

#### 해결 방법
catch 문에서 예외를 삼키지 않고 던져주면 해결됩니다.
```java
@Transactional
public void placeOrder(Order order) {
    try {
        orderRepository.save(order);
        paymentService.pay(order);
    } catch (Exception e) {
        log.error("주문 실패", e);
        throw e; // 예외를 다시 던져서 롤백 유도
    }
}
```

### 6. timeout 미설정 시 무한 대기 위험
`@Transactional`의 기본 timeout은 데이터베이스 또는 트랜잭션 매니저의 기본값을 따릅니다.
명시적으로 설정하지 않으면 데드락이나 느린 쿼리로 인해 무한 대기 상태에 빠질 수 있습니다.

```java
@Service
public class ReportService {

    // timeout 미설정 -> 무한 대기 가능
    @Transactional
    public Report generateReport(Long reportId) {
        // 대량 데이터 처리 시 장시간 소요될 수 있음
        return reportRepository.generateComplexReport(reportId);
    }
}
```

#### 해결 방법
timeout 명시적 설정하면 됩니다.
제일 좋은 방법은 [전역 timeout 설정](#전역-timeout-설정)으로 해결하면 됩니다.
```java
@Transactional(timeout = 30)
public Report generateReport(Long reportId) {
    return reportRepository.generateComplexReport(reportId);
}
```

#### timeout 발생 시 동작
timeout이 초과되면 `TransactionTimedOutException`이 발생하고 트랜잭션은 롤백됩니다.

```java
@Service
public class BatchService {

    @Transactional(timeout = 60)
    public void processBatch(List<Data> dataList) {
        for (Data data : dataList) {
            // 60초 초과 시 TransactionTimedOutException 발생
            dataRepository.process(data);
        }
    }
}
```

#### 전역 timeout 설정
개별 메서드마다 설정하기 번거로운 경우, 전역으로 기본 timeout을 설정할 수 있습니다.

```yaml
# application.yml
spring:
  transaction:
    default-timeout: 30  # 단위: 초
```

```java
// 또는 Java Config로 설정
@Configuration
public class TransactionConfig {

    @Bean
    public PlatformTransactionManager transactionManager(DataSource dataSource) {
        DataSourceTransactionManager tm = new DataSourceTransactionManager(dataSource);
        tm.setDefaultTimeout(30); // 단위: 초
        return tm;
    }
}
```