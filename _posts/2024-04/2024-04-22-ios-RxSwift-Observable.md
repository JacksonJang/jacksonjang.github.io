---
layout:     post
title:      "[iOS] RxSwift 사용하기(2) - Observable"
subtitle:   "\"Let's use RxSwift - Observable\""
date:       2024-04-22 19:00:00
author:     "JacksonJang"
header-img: "assets/posts/post-bg_2024.jpg"
post_assets: "/assets/posts/2024-04-22"
catalog: true
tags:
    - Swift
    - RxSwift
    - Observable
    - iOS
---
## Observable 이란?
`Observable`은 이벤트를 방출하는 **스트림**입니다.

구독자(Observer)들이 구독(Subscribe)을 하면 새로운 값이 방출될 때마다 알림을 받아서 이벤트를 처리할 수 있습니다.
<br />
각 이벤트는 다음과 같이 나뉘게 됩니다.
- `onNext`: Observable이나 Subject가 새로운 값을 방출할 때마다 호출합니다.
- `onError`: Observable이 에러를 방출하거나, 예외 상황이 발생했을 때 호출합니다.
- `onCompleted`: 정상적으로 모든 이벤트를 방출한 후 호출합니다.

## 예시코드
```swift
let observable = Observable.of("Hello", "RxSwift")
        
observable.subscribe(
        onNext:{ value in
                print("Next: ", value)
        }, onError: { error in
                print("Error: ", error)
        }, onCompleted: {
                print("Completed")
        }, onDisposed: {
                print("Disposed")
        }
)
.disposed(by: disposeBag)
```

### 결과값
```swift
Next:  Hello
Next:  RxSwift
Completed
Disposed
```

## Cold Observable vs Hot Observable
갑자기 웬 뜨겁고 차가운 것을 갖고 오는지 궁금하실 수 있습니다.
<br />
RxSwift 공식 문서의 [HotAndColdObservables.md](https://github.com/ReactiveX/RxSwift/blob/main/Documentation/HotAndColdObservables.md)를 살펴보면, 자세하게 나와있지만 제가 쉽게 풀어서 설명하겠습니다.

## Cold Observable
`Cold`는 말 그대로 차가운 것이기 때문에 **구독을 하지 않으면 절대 방출되지 않는다.**
<br />
구독자(Observer)가 구독(Subscribe)을 하게 되면 차가웠던 게 녹는 것처럼 방출됩니다.

간단한 예시로 `Observable.create`, `Observable.just`, `Observable.from` 등등을 의미합니다.

### Cold Observable 예시 코드
```swift
let observable = Observable<Int>.create { observer in
        observer.onNext(1)
        observer.onNext(2)
        observer.onNext(3)
        observer.onCompleted()
        return Disposables.create()
}

observable.subscribe { event in
        print("Cold Observer 1: \(event)")
}
.disposed(by: disposeBag)

observable.subscribe { event in
        print("Cold Observer 2: \(event)")
}
.disposed(by: disposeBag)
```

### 결과값
```swift
Cold Observer 1: next(1)
Cold Observer 1: next(2)
Cold Observer 1: next(3)
Cold Observer 1: completed
Cold Observer 2: next(1)
Cold Observer 2: next(2)
Cold Observer 2: next(3)
Cold Observer 2: completed
```

## Hot Observable
`Hot`은 말 그대로 뜨거운 것이기 때문에 **구독 따위 필요 없이 항상 방출합니다**
<br />
한마디로 구독자(Observer)의 구독(Subscribe)이 필요 없이 스스로가 알아서 불처럼 방출한다고 생각하시면 됩니다.

만약 구독 전에 onNext를 했더라면, 구독자는 onNext한 것에 대한 이벤트를 받을 수 없습니다.

### Hot Observable 예시 코드
```swift
let observable = PublishSubject<Int>()

observable.subscribe { event in
        print("Hot Observer 1: \(event)")
}
.disposed(by: disposeBag)

observable.onNext(1)
observable.onNext(2)

observable.subscribe { event in
        print("Hot Observer 2: \(event)")
}
.disposed(by: disposeBag)

observable.onNext(3)
observable.onCompleted()
```

### 결과값
```swift
Hot Observer 1: next(1)
Hot Observer 1: next(2)
Hot Observer 1: next(3)
Hot Observer 2: next(3)
Hot Observer 1: completed
Hot Observer 2: completed
```

## github 예시 코드
[https://github.com/JacksonJang/RxSwiftExample](https://github.com/JacksonJang/RxSwiftExample)