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

```swift
Observable.just("Hello, RxSwift")
    .observe(on: MainScheduler.instance)
    .subscribe(onNext: { value in
        print("MainScheduler : ", value)
    })
    .disposed(by: disposeBag)
```

## ConcurrentDispatchQueueScheduler
동시성 실행을 허용합니다.
<br />
즉, 병렬로 여러 작업들을 동시에 처리할 수 있습니다.

```swift
Observable.from([1, 2, 3, 4, 5])
    .observe(on: ConcurrentDispatchQueueScheduler(qos: .background))
    .map { $0 * 2 }
    .subscribe(onNext: { value in
        print("ConcurrentDispatchQueueScheduler : ", value)
    })
    .disposed(by: disposeBag)
```

## SerialDispatchQueueScheduler
백그라운드에서 순서대로 직렬로 실행하도록 설계되어 있습니다.
<br />
즉, 병렬이 아닌 직렬이기 때문에 하나의 작업이 완료될 때까지 다음 작업이 시작되지 않으므로 작업 순서가 중요할 때 사용됩니다.

`SerialDispatchQueueScheduler`는 `백그라운드` 쓰레드이기 때문에 메인 쓰레드와 같이 사용해도 상관 없습니다.

```swift
Observable.of("Task 1", "Task 2", "Task 3")
    .observe(on: SerialDispatchQueueScheduler(qos: .default))
    .subscribe(onNext: { value in
        print("SerialDispatchQueueScheduler : ", value)
    })
    .disposed(by: disposeBag)
```

## OperationQueueScheduler
~~`NSOperationQueue` 기반으로 작업을 스케줄링합니다.~~
`OperationQueue` 기반으로 작업을 스케줄링합니다. 

`OperationQueue`는 작업을 큐에 추가하고 우선순위를 설정하며 병렬 또는 직렬로 실행할 수 있게 하는 API입니다. 

```
let operationQueue = OperationQueue()

Observable.of("Operation 1", "Operation 2", "Operation 3")
    .observe(on: OperationQueueScheduler(operationQueue: operationQueue))
    .subscribe(onNext: { value in
        print("OperationQueueScheduler : ", value)
    })
    .disposed(by: disposeBag)
```

## 참고링크
[Managing Concurrency in RxSwift with Schedulers](https://medium.com/@mumensh/managing-concurrency-in-rxswift-with-schedulers-6874ee2dff96)

## github 예제
[https://github.com/JacksonJang/RxSwiftScheduler](https://github.com/JacksonJang/RxSwiftScheduler)