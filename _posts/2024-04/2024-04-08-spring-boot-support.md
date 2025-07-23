---
layout:     post
title:      "[Spring Boot] 스프링부트 2.x 이제 퇴물이다!"
subtitle:   "\"Spring Boot doesn't support 2.x\""
date:       2024-04-08 19:00:00
author:     "JacksonJang"
post_assets: "/assets/posts/2024-04-08"
catalog: true
categories:
    - Spring Boot
tags:
    - Java
    - Tomcat
    - Gradle
    - Spring Boot
    - Backend
---
> 스프링부트 2.x 이제 퇴물이다!

### 요약
다음과 같은 스펙을 사용하자
- JDK 17 이상
- Tomcat 10.x 이상
- Gradle 7.5 이상

## 시작
안녕하세요.
<br />
다소 제목이 자극적이게 느껴질 수도 있겠지만, 시대가 빠르게 변화하면서 스프링부트도 빠르게 변화하고 있습니다. 
<br />
보통 일반적인 경우로 스프링부트 2.7 버전을 많이 사용 했으며, 실제로 스프링부트 강의들도 보면 2.x 버전이 상당히 많습니다.(저 같은 경우엔 그랬습니다.)

## [start.spring.io](https://start.spring.io/)
<img width="600px" src="{{ page.post_assets }}/spring_io_create.png" />
프로젝트 생성을 해볼려고 하는데.. 어?
<br />
스프링부트 2.x 버전의 프로젝트를 더 이상 생성할 수 없더라고요..?
<br />
그래서 조금 더 찾아보니까
<p />
<img width="600px" src="{{ page.post_assets }}/spring_io_stackoverflow.png" />
[Stack Overflow](https://stackoverflow.com/questions/77538583/did-spring-initializr-stop-support-for-spring-boot-2-x)에서도 누군가가 질문을 했더라고요

StackOverflow로는 자세히 알 수 없어서 공식 홈페이지를 찾아보니
<br />
<img width="600px" src="{{ page.post_assets }}/spring_io_support.png" />
2023년 11월부터 지원 중단했었습니다.

## "그럼 앞으로 어떻게 해야될까?"
<img width="600px" src="{{ page.post_assets }}/springboot_youtube_java_17.png" />
[스프링부트 공식 유튜브 영상](https://youtu.be/HrRQExD3xow?t=1199)에서도 SpringBoot3는 JDK17이 필요하다고 언급됩니다.

**JDK17**로 변경해서 사용합시다.

## JDK17로 인해 톰캣도 변경이 필요하다
<img width="600px" src="{{ page.post_assets }}/apache-tomcat9.png" />
[[Tomcat 9.0 Document](https://tomcat.apache.org/tomcat-9.0-doc/index.html)]
이전 SpringBoot2는 Servlet 4.0을 지원하고 있어서 Tomcat9 버전까지는 지원이 가능했습니다.
```
Apache Tomcat version 9.0 implements the Servlet 4.0
```

<img width="600px" src="{{ page.post_assets }}/springboot_docs.png" />
[공식 홈페이지의 docs](https://docs.spring.io/spring-boot/docs/current/reference/htmlsingle/)에도 명시되어 있듯이 현재 SpringBoot3는 Servlet 5.0 이상을 지원하고 있으며, Tomcat 10.1을 지원한다고 명시되어 있습니다.
> Servlet 5.0은 **javax.*** 에서 **jakarta.servlet** 으로 변경된 버전입니다.

<br />
따라서 앞으로는 스프링부트3 프로젝트를 JDK17과 함께 만들어서 사용합시다!
<p />
관련된 링크도 첨부할게요
<br />
관련링크 : [https://spring.io/projects/spring-boot#support](https://spring.io/projects/spring-boot#support)
