---
layout:     post
title:      "[iOS] RxSwift 사용하기(3) - Subject"
subtitle:   "\"Let's use RxSwift - Subject\""
date:       2024-04-23 19:00:00
author:     "JacksonJang"
header-img: "assets/posts/post-bg_2024.jpg"
post_assets: "/assets/posts/2024-04-23"
catalog: true
tags:
    - Swift
    - RxSwift
    - Subject
    - iOS
---

## Subject 란?
`Subject`는 이벤트를 받아서 구독자에게 전달할 수 있으며 직접 스트림을 생성할 수 있습니다.
<br />
한 마디로 구독자들은 Subject를 구독할 수 있으며, 특정 작업이나 동작이 발생 했을 때 Subject로 전달하고, 이를 구독한 구독자들(Observer들)에게 방출됩니다.

## Subject의 종류
- `PublishSubject` : 구독 후에 발생하는 이벤트만 방출합니다.(즉 초기 값은 없음)
구독 전에 이벤트를 전달해도 구독자는 구독을 하지 않았기 때문에 받을 수 없습니다.
```swift
 let subject = PublishSubject<String>()

subject.onNext("You can't see this message")

subject.subscribe(onNext: { response in
    print("PublishSubject: \(response)")
})
.disposed(by: disposeBag)

subject.onNext("PublishSubject response 1")
subject.onNext("PublishSubject response 2")

/*
PublishSubject: PublishSubject response 1
PublishSubject: PublishSubject response 2
*/
```

- `BehaviorSubject` : 초기 값을 가질 수 있으며 이벤트를 갖고 있다가 구독자가 구독하면 방출합니다.
```swift
let subject = BehaviorSubject(value: "BehaviorSubject Init")
        
subject.onNext("You can see this message")

subject.subscribe(onNext: { response in
    print("PublishSubject: \(response)")
})
.disposed(by: disposeBag)

subject.onNext("response 1")
subject.onNext("response 2")

/*
PublishSubject: You can see this message
PublishSubject: response 1
PublishSubject: response 2
*/
```

- `ReplaySubject` : 설정한 버퍼의 크기를 가지고 있으며, 구독자가 구독할 때 버퍼에 저장된 이벤트를 재생(Replay)할 수 있습니다.
<br />
만약 이벤트를 저장할 때 설정한 버퍼의 크기를 초과한다면, 이전에 저장된 버퍼는 삭제가 되고 가장 최근의 이벤트로 남습니다.

```swift
let subject = ReplaySubject<String>.create(bufferSize: 2)

subject.onNext("Event 1")
subject.onNext("Event 2")
subject.onNext("Event 3")

subject.subscribe(onNext: { event in
    print("ReplaySubject: \(event)")
})
.disposed(by: disposeBag)

/*
ReplaySubject: Event 2
ReplaySubject: Event 3
*/
```

- `AsyncSubject`: 스트림이 완료된 후 마지막 이벤트를 구독자에게 방출합니다.
<br />
**완료되기 전까지는 이벤트 방출이 안됩니다.**(완료된 시점에 딱 1번만 방출합니다.)

```swift
 let subject = AsyncSubject<String>()
        
subject.onNext("Event 1")

subject.subscribe(onNext: { response in
    print("ReplaySubject Ex1 : \(response)")
}).disposed(by: disposeBag)

subject.onNext("Event 2")
subject.onNext("Event 3")

subject.onCompleted()

/*
ReplaySubject Ex1 : Event 3
*/
```

위 코드에서 `Event 2`와 `Event 3`을 빼면 어떻게 될까? 궁금해서 해봤습니다.
```swift
 let subject = AsyncSubject<String>()
        
subject.onNext("Event 1")

subject.subscribe(onNext: { response in
    print("ReplaySubject Ex1 : \(response)")
}).disposed(by: disposeBag)

subject.onCompleted()

/*
ReplaySubject Ex1 : Event 1
*/
```
결과적으로 Event 1이 콘솔에 보이는 것으로 보아 AsyncSubject는 구독 전 데이터도 갖고 있는 것을 확인하실 수 있습니다.

## github 예시 코드
[https://github.com/JacksonJang/RxSwiftExample](https://github.com/JacksonJang/RxSwiftExample)