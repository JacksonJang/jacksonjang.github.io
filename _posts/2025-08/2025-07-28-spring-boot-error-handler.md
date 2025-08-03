---
layout:     post
title:      "[Spring Boot] 에러를 효과적으로 처리하는 2가지 방법(@ExceptionHandler, @ControllerAdvice 사용)"
subtitle:   "Handle errors efficiently using @ExceptionHandler and @ControllerAdvice"
date:       2025-08-03 14:00:00
author:     JacksonJang
post_assets: "/assets/posts/2025-08-03"
catalog: true
categories:
    - Spring Boot
tags:
    - Spring Boot
    - ControllerAdvice
---

# 왜 필요해요?
프로젝트를 진행하다 보면 에러 응답 포맷을 변경해야 하는 상황이 생길 수 있습니다. 예를 들어, 고객 요구사항 변경, 공통 응답 규격 개편, 코드 리팩터링 등..

이때 모든 컨트롤러에 동일한 보일러플레이트 코드가 존재해서 수정할 때 유지보수 비용이 커집니다.
<br />
<br />

# try-catch 문
```java
@RestController
public class TryCatchController {

  @GetMapping("/tryCatch")
  public String tryCatch() {
    try {
      throw new IllegalArgumentException("IllegalArgument 에러");
    } catch (Exception e) {
      return "에러가 발생했습니다. : " + e.getMessage();
    }
  }

  @GetMapping("/tryCatch2")
  public String tryCatch2() {
    try {
      throw new RuntimeException("Runtime 에러");
    } catch (Exception e) {
      return "에러가 발생했습니다. : " + e.getMessage();
    }
  }

}
```
위와 같이 공통적인 에러를 처리할 때 각 메서드마다 `try-catch` 구문을 작성하는 방식은 실제로 간단하지만, 프로젝트의 규모가 커질수록 유지보수가 어려워지는 예시를 보여주고 있습니다.
<br />

그렇다면, `@ExceptionHandler` 와 `@ControllerAdvice` 를 같이 사용하면 어떻게 될까요?
<br />
<br />

# @ExceptionHandler + @ControllerAdvice 사용
```java
@ControllerAdvice
public class ErrorHandler {
  @ExceptionHandler(Exception.class)
  public String handleException(Exception e) {
    return "에러가 발생했습니다. : " + e.getMessage();
  }
}
```
`Exception` 에러 처리를 공통적으로 한번 묶어서 사용하니 이전보다 깔끔해 졌습니다.

이제 `@ExcpetionHandler` 와 `@ControllerAdvice` 가 무엇이고, 어떤 역할을 하는지 각각 알아보겠습니다.
<br />
<br />

# @ExceptionHandler 란?
`Spring MVC`에서 `컨트롤러 메서드`에서 발생한 예외를 처리하기 위해 사용하는 어노테이션입니다.
<br />
선언한 컨트롤러에서만 발생하는 예외에 대해 처리한다고 보시면 됩니다.

### @ExceptionHandler 예시코드
```java
@GetMapping("/exceptionHandler")
  public String exceptionHandler() {
    throw new IllegalArgumentException("IllegalArgument 에러");
  }

  @ExceptionHandler(IllegalArgumentException.class)
  public String handleIllegalArgument(IllegalArgumentException e) {
    return "에러 발생: " + e.getMessage();
  }
```
<br />
<br />

# @ControllerAdvice 란?
`Spring MVC`에서 `모든 컨트롤러`에 전역적으로 적용할 수 있는 기능을 제공하는 어노테이션입니다.

에러 처리 외에도 데이터 바인딩, 전역 모델 속성도 추가할 수 있지만
<br />
`에러 처리`외 나머지 기능은 다른 글을 통해 소개할게요.
<br />
<br />

### @ControllerAdvice 예시코드
```java
@ControllerAdvice
public class ErrorHandler {
  @ExceptionHandler(Exception.class)
  public String handleException(Exception e) {
    return "ControllerAdvice 에러가 발생했습니다. : " + e.getMessage();
  }
}
```
위 코드는 [@ExceptionHandler + @ControllerAdvice 사용](#exceptionhandler--controlleradvice-사용)에서 보셨던 코드와 동일합니다.
<br />
<br />

# 에러 처리 순서에 대해 주의하세요!
`@ExceptionHandler`와 `@ControllerAdvice`를 사용할 때, 주의할 내용이 있습니다.

```java
@RestController
public class ExceptionHandlerController {

  @GetMapping("/exceptionHandler")
  public String exceptionHandler() {
    try {
      throw new IllegalArgumentException("IllegalArgument 에러");
    } catch (Exception e) {
      return "여기서 동작해요";
    }
  }

  @ExceptionHandler(IllegalArgumentException.class)
  public String handleIllegalArgument(IllegalArgumentException e) {
    return "여기서 동작하지 않아요";
  }
}
```
위에 처럼 `try-catch`를 같이 쓰게 된다면 어떻게 될까요?

아무리 `@ExceptionHandler`, `@ControllerAdvice` 를 사용한다고 해도 컨트롤러 메서드 안에 `try-catch` 를 사용한다면 `try-catch`가 우선적으로 적용됩니다.

# @RestControllerAdvice 란?
`@ControllerAdvice` 외 `@RestControllerAdvice` 도 있습니다.
`@RestControllerAdvice`는 단순하게 `@ControllerAdvice` 와 `@ResponseBody` 를 합친 어노테이션입니다.

```java
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
@Documented
@ControllerAdvice
@ResponseBody
public @interface RestControllerAdvice
```

개인적으로 실무에서는 `@RestControllerAdvice`를 주로 사용하고 있어요.
<br />
<br />

# 예외 처리하는 우선순위 요약
우선순위가 높은 순서대로 나열했습니다.
<br />
1. 메서드 내부의 [try-catch](#try-catch-문)
2. [`@ExceptionHandler`(컨트롤러 내부 정의)](#exceptionhandler-란)
3. [`@ControllerAdvice`](#controlleradvice-란) or [`@RestControllerAdvice`](#restcontrolleradvice-란)


# @Order 사용으로 순서 정하기
만약, 아래처럼 2개의 `@ControllerAdvice`가 존재하면 어떻게 될까요?
```java
@ControllerAdvice
public class ErrorHandler {
  @ExceptionHandler(Exception.class)
  public String handleException(Exception e) {
    return "ControllerAdvice 에러가 발생했습니다. : " + e.getMessage();
  }
}

@ControllerAdvice
public class ErrorHandler2 {
  @ExceptionHandler(Exception.class)
  public String handleException(Exception e) {
    return "ControllerAdvice2 에러가 발생했습니다. : " + e.getMessage();
  }
}
```

`@Order`를 사용하면 여러 개의 `@ControllerAdvice`, `@RestControllerAdvice`가 존재할 때 순서를 정할 수 있습니다.
<br />
([`예외 처리하는 우선순위 요약`](#예외-처리하는-우선순위-요약)에 해당하는 1, 2번은 불가능)

`@Order` 의 설명을 보면, `Lower values have higher priority.` 로 되어 있습니다.
<br />
즉, `작은 값은 큰 우선순위를 갖는다.`라고 해석할 수 있으며,
<br />
아래처럼 `ErrorHandler`를 1순위로 줄 수 있습니다.

```java
@ControllerAdvice
@Order(1)
public class ErrorHandler {
  @ExceptionHandler(Exception.class)
  public String handleException(Exception e) {
    return "ControllerAdvice 에러가 발생했습니다. : " + e.getMessage();
  }
}
```

# github 예시 주소
