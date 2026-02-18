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

Spring은 내부적으로 **AOP 프록시**를 사용하여 트랜잭션을 관리하고 있는데
이 프록시 기반 동작 방식 때문에 몇 가지 주의사항이 존재합니다.


## @Transactional 사용 시 주의사항

| # | 주의사항 | 원인 | 해결 |
|---|---------|------|------|
| 1 | **private** 메서드 무시됨 | 프록시가 오버라이드 불가 | public 사용 |
| 2 | **final** 클래스/메서드 무시됨 | 프록시가 상속/오버라이드 불가 | final 제거 |
| 3 | **Self-Invocation** 무시됨 | 내부 호출은 프록시 안 거침 | 별도 서비스 분리 |
| 4 | **Checked Exception** 롤백 안 됨 | 기본 롤백 대상 아님 | rollbackFor 지정 |
| 5 | **try-catch**로 삼키면 롤백 안 됨 | 스프링이 예외 감지 못 함 | throw로 다시 던지기 |
| 6 | **멀티스레드** 전파 안 됨 | ThreadLocal에 트랜잭션 저장 | 동기 처리 또는 별도 설계 |
| 7 | **@Async** 메서드 전파 안 됨 | 비동기는 별도 스레드 | 명시적 트랜잭션 생성 |
| 8 | **timeout 미설정** | 무한 대기로 장애 유발 | timeout 명시적 설정 |


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
`Enhancer`가 프록시 클래스를 생성할 때, 부모 클래스가 `final`이면 `IllegalArgumentException` 예외를 발생시킵니다.

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
같은 클래스 내에서 메서드를 호출하면, 프록시를 거치지 않고 `this`로 직접 호출되기 때문에 트랜잭션이 적용되지 않습니다.

```java
@Service
public class UserService {

    public void register(User user) {
        // this.saveUser()로 호출되므로 프록시를 거치지 않음
        saveUser(user);
    }

    @Transactional
    public void saveUser(User user) {
        userRepository.save(user);
    }
}
```

#### 해결: 별도 서비스로 분리
```java
@Service
@RequiredArgsConstructor
public class UserService {

    private final UserPersistenceService persistenceService;

    public void register(User user) {
        persistenceService.saveUser(user);
    }
}

@Service
@RequiredArgsConstructor
public class UserPersistenceService {

    private final UserRepository userRepository;

    @Transactional
    public void saveUser(User user) {
        userRepository.save(user);
    }
}
```


### 4. Checked Exception은 롤백되지 않음
Spring의 `@Transactional`은 기본적으로 **Unchecked Exception** (`RuntimeException`, `Error`)만 롤백합니다.
`Checked Exception`이 발생하면 트랜잭션이 커밋됩니다.

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

#### 해결: rollbackFor 지정
```java
@Transactional(rollbackFor = Exception.class)
public void saveWithFile(Data data) throws IOException {
    dataRepository.save(data);
    fileManager.upload(data.getFile());
}
```


### 5. try-catch로 예외를 삼키면 롤백 안 됨
예외를 `try-catch`로 잡아서 처리하면, 스프링이 예외를 감지하지 못해 트랜잭션이 정상 커밋됩니다.

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

#### 해결: 예외를 다시 던지기
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


### 6. 멀티스레드 환경에서 트랜잭션 전파 안 됨
Spring의 트랜잭션 컨텍스트는 `ThreadLocal`에 저장됩니다.
새로운 스레드에서는 부모 스레드의 트랜잭션을 공유하지 않으므로, 별도의 트랜잭션으로 동작합니다.

```java
@Service
public class NotificationService {

    @Transactional
    public void sendNotifications(List<User> users) {
        // 새로운 스레드에서 실행되므로 부모 트랜잭션과 무관
        users.parallelStream().forEach(user -> {
            notificationRepository.save(new Notification(user));
        });
    }
}
```

#### 해결: 동기 처리
```java
@Transactional
public void sendNotifications(List<User> users) {
    users.forEach(user -> {
        notificationRepository.save(new Notification(user));
    });
}
```

비동기 처리가 반드시 필요한 경우, 각 스레드에서 별도의 `@Transactional` 메서드를 호출하도록 설계해야 합니다.


### 7. @Async 메서드에서 트랜잭션 전파 안 됨
`@Async`가 붙은 메서드는 별도의 스레드에서 실행되므로, 호출한 메서드의 트랜잭션이 전파되지 않습니다.
6번(멀티스레드)과 원리는 같지만, `@Async`는 Spring에서 자주 사용되므로 별도로 주의가 필요합니다.

```java
@Service
public class EmailService {

    // 호출자의 트랜잭션이 전파되지 않음
    @Async
    public void sendEmail(User user) {
        // 별도 스레드에서 실행 -> 트랜잭션 없음
        emailLogRepository.save(new EmailLog(user));
    }
}
```

#### 해결: @Async 메서드 내에서 명시적으로 트랜잭션 선언
```java
@Async
@Transactional
public void sendEmail(User user) {
    emailLogRepository.save(new EmailLog(user));
}
```

#### 주의: @Async + @Transactional 조합 시 Self-Invocation
`@Async`와 `@Transactional` 모두 프록시 기반이므로, 같은 클래스 내부에서 호출하면 둘 다 동작하지 않습니다.

```java
@Service
public class OrderService {

    @Transactional
    public void placeOrder(Order order) {
        orderRepository.save(order);
        // Self-Invocation으로 @Async, @Transactional 모두 무시됨
        sendOrderConfirmation(order);
    }

    @Async
    @Transactional
    public void sendOrderConfirmation(Order order) {
        // ...
    }
}
```

#### 해결: 별도 서비스로 분리
```java
@Service
@RequiredArgsConstructor
public class OrderService {

    private final OrderNotificationService notificationService;

    @Transactional
    public void placeOrder(Order order) {
        orderRepository.save(order);
        notificationService.sendOrderConfirmation(order);
    }
}

@Service
public class OrderNotificationService {

    @Async
    @Transactional
    public void sendOrderConfirmation(Order order) {
        // 프록시를 통해 호출되므로 @Async, @Transactional 모두 정상 동작
    }
}
```


### 8. timeout 미설정 시 무한 대기 위험
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

#### 해결: timeout 명시적 설정 (단위: 초)
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


## 정리
`@Transactional`은 Spring의 **AOP 프록시** 기반으로 동작하기 때문에, 프록시의 한계를 이해하고 사용해야 합니다.

| # | 핵심 포인트 |
|---|-----------|
| 1 | 프록시가 개입할 수 있도록 **public** 메서드에 적용 |
| 2 | **final** 키워드 사용 지양 |
| 3 | 내부 호출(Self-Invocation) 대신 **별도 서비스 분리** |
| 4 | Checked Exception도 롤백하려면 **rollbackFor** 지정 |
| 5 | 예외를 삼키지 말고 **다시 던지기** |
| 6 | 멀티스레드 환경에서는 트랜잭션 전파가 안 되므로 **별도 설계** 필요 |
| 7 | @Async 메서드는 **별도 트랜잭션** 필요하며, Self-Invocation 주의 |
| 8 | **timeout**을 명시적으로 설정하여 무한 대기 방지 |