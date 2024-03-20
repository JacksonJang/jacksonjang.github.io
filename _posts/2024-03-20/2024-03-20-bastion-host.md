---
layout:     post
title:      "[CS] 배스천 호스트 란?"
subtitle:   " \"What's a Bastion Host?\""
date:       2024-03-20 19:00:00
author:     "JacksonJang"
header-img: "assets/posts/post-bg_2024.jpg"
post_assets: "/assets/posts/2024-03-20"
catalog: true
tags:
    - CS
    - BastionHost
    - Server
---

> 요약 : 배스천 호스트(Bastion Host)란 침입 차단 소프트웨어가 설치되어 내부와 외부 네트워크 사이에서 일종의 게이트 역할을 수행하는 호스트입니다.

## Bastion 본래 뜻
<img style="margin:0;" src="{{ page.post_assets }}/bastion-english.png">
<br />
출처 : 네이버
<br />
Bastion은 수호자, 보루, 요새와 같은 뜻을 가지고 있습니다. 이는 네트워크에서도 비슷한 역할을 수행합니다.
<br />

> [!TIP]
> 각 나라별로 다음과 같이 발음됩니다! <br />
> 미국에서는 "배스천('bæstʃ(ə)n)" <br />
> 영국에서는 "배스티언(ˈbæstiən)"

## 그렇다면 Bastion Host 는 먼데?
Bastion Host는 **외부에서 내부 네트워크에 접근할 수 있는 유일한 방법** 이라고 생각하면 됩니다. 보안성이 높은 인프라와 외부 인터넷을 연결하는 중계 서버로 작동하며, 모든 인바운드 트래픽은 Bastion Host를 통과해야 내부 네트워크로 들어갈 수 있습니다.

따라서, 외부 네트워크에서 공격을 받아 패스워드를 탈취 당해도 내부 네트워크엔 접근할 수 없습니다.

## 주요 특징
- 접근 제어 : 내부와 외부 네트워크 사이에 있는 중계서버에서 제어합니다. 
  <br />
  특정 IP 주소에서만 접근할 수 있도록 설정 할 수 있습니다. (방화벽 기능)
- 감사 및 로깅 : 모든 접근시도에 대한 로깅은 보안 위협을 탐지합니다.

## 권장사항
권장되는 내용으로는 **Bastion Host 에 접근할 특정 IP 만 명시적으로 접근을 허용**하고, **SSH 포트는 22가 아닌 다른 포트를 사용**할 것이며, **로그인 시 Two Factor 인증**을 통해 보안을 강화하는 것이 권장되고 있습니다.

## 참고 링크
- [https://harris91.vercel.app/bastion-host]("https://harris91.vercel.app/bastion-host")
- [https://blog.naver.com/pentamkt/221034903499]("https://blog.naver.com/pentamkt/221034903499")
- [https://velog.io/@makeitcloud/%EB%9E%80-Bastion-host-%EB%9E%80]("https://velog.io/@makeitcloud/%EB%9E%80-Bastion-host-%EB%9E%80")
- [https://www.lesstif.com/ws/%EB%B2%A0%EC%8A%A4%EC%B2%9C-%ED%98%B8%EC%8A%A4%ED%8A%B8-43843897.html]("https://www.lesstif.com/ws/%EB%B2%A0%EC%8A%A4%EC%B2%9C-%ED%98%B8%EC%8A%A4%ED%8A%B8-43843897.html")

## 끝