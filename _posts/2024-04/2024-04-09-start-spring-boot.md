---
layout:     post
title:      "[Spring Boot] 스프링부트 프로젝트 생성 "
subtitle:   "\"Create Spring Boot Project\""
date:       2024-04-09 19:00:00
author:     "JacksonJang"
header-img: "assets/posts/post-bg_2024.jpg"
post_assets: "/assets/posts/2024-04-09"
catalog: true
tags:
    - Java
    - Spring Boot
    - Backend
---

## [start.spring.io](https://start.spring.io/)에서 프로젝트 생성
<img width="600px" src="{{ page.post_assets }}/spring_io_create.png" />
- Project : 사용할 빌드 자동화 도구
- Language : 사용할 언어
- Spring Boot : 스프링부트 버전
- Group : 일반적으로 프로젝트의 도메인 이름을 거꾸로 써서 사용
```
예시 : jacksonjang.io 라면, io.jacksonjang
```
- Artifact : 빌드 시 생성되는 아티팩트명
```
예시 : example 이라면, example.jar
```
- Name : 프로젝트의 이름
- Description : 프로젝트 설명
- Package name : 패키지 이름
- Packaging : 패키지의 타입(Jar, War)
```
외부 톰캣을 사용할 예정이라면, War 설정
```
- Java : 자바 버전 설정

추가적으로 Dependencies에서 외부 라이브러리나 프레임워크의 설정을 원하시면 추가합니다.

위의 입력 사항을 입력 및 선택 후 GENERATE 을 클릭하면 zip 파일 형태로 프로젝트 생성된 것을 확인하실 수 있습니다.