---
layout:     post
title:      "[iOS] RxSwift 사용하기(5) - Schedulers"
subtitle:   "\"Let's use RxSwift - Schedulers\""
date:       2024-04-26 19:00:00
author:     "JacksonJang"
header-img: "assets/posts/post-bg_2024.jpg"
post_assets: "/assets/posts/2024-04-26"
catalog: true
tags:
    - Swift
    - RxSwift
    - Schedulers
    - iOS
---

## Scheduler
`Scheduler`는 특정 코드를 실행할 때 사용할 스레드 또는 큐를 결정하는 역할을 합니다.
<br />
RxSwift에서 Scheduler를 사용함으로서 동시성을 쉽게 처리할 수 있습니다.

## MainScheduler
메인 쓰레드에서의 실행을 보장합니다.(UI 업데이트 사용에 적절해요)

## ConcurrentDispatchQueueScheduler
동시성 실행을 허용합니다.
<br />
즉, 병렬로 여러 작업들을 동시에 처리할 수 있습니다.

## SerialDispatchQueueScheduler
백그라운드에서 순서대로 직렬로 실행하도록 설계되어 있습니다.
<br />
즉, 병렬이 아닌 직렬이기 때문에 하나의 작업이 완료될 때까지 다음 작업이 시작되지 않으므로 작업 순서가 중요할 때 사용됩니다.

`SerialDispatchQueueScheduler`는 `백그라운드` 쓰레드이기 때문에 메인 쓰레드와 같이 사용해도 상관 없습니다.

## OperationQueueScheduler
`NSOperationQueue` 기반으로 작업을 스케줄링합니다. 

`NSOperationQueue`는 작업을 큐에 추가하고 우선순위를 설정하며 병렬 또는 직렬로 실행할 수 있게 하는 API입니다. 

## 참고링크
[Managing Concurrency in RxSwift with Schedulers](https://medium.com/@mumensh/managing-concurrency-in-rxswift-with-schedulers-6874ee2dff96)