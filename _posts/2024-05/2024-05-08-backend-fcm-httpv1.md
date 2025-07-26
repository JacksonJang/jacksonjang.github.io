---
layout:     post
title:      "[Backend] 2024년 6월 FCM HTTP v1 삭제 관련(FCM 삭제)"
subtitle:   "\"About FCM will be removed June 2024\""
date:       2024-05-08 19:00:00
author:     JacksonJang
post_assets: "/assets/posts/2024-05-08"
catalog: true
categories:
    - Etc
tags:
    - Backend
    - Firebase
    - FCM
---

## 중요
<img src="{{ page.post_assets }}/fcm_migration.png" style="height:400px" /> <br />
> Sending messages (including upstream messages) with those APIs was deprecated on June 20, 2023, and will be removed in June 2024.
위 내용을 해석하면 "해당 API를 사용한 메시지 전송(업스트림 메시지 포함)은 2023년 6월 20일에 지원 중단되었으며, 2024년 6월에 삭제될 예정입니다.

즉, **2024년 6월**부터 사용 불가능합니다. 

기존에 사용중이라면 아래 링크를 통해 바꿔야 합니다!
[https://firebase.google.com/docs/cloud-messaging/migrate-v1](https://firebase.google.com/docs/cloud-messaging/migrate-v1)

## 하지만 한국어 문서엔 없다!!
<img src="{{ page.post_assets }}/fcm_migration_kr.png" style="height:400px" /> <br />
왜지...??

[한국어로 된 FCM 마이그레이션 문서](https://firebase.google.com/docs/cloud-messaging/migrate-v1?hl=ko)

## AWS SNS 내용 
<img src="{{ page.post_assets }}/fcm_aws.png" style="height:400px" /> <br />
[https://aws.amazon.com/ko/about-aws/whats-new/2024/01/amazon-sns-fcm-http-v1-api-mobile-notifications/](https://aws.amazon.com/ko/about-aws/whats-new/2024/01/amazon-sns-fcm-http-v1-api-mobile-notifications/)
<br />
AWS SNS에 의하면, **2024년 6월 1일부터 Google은 기존 FCM v1 API를 통해 모바일 푸시 알림을 전송하는 기능을 제거한다는 계획입니다.** 라는 말이 있으니 안전하게 6월 1일 전에 교체하는 것이 좋아보입니다.
