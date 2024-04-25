---
layout:     post
title:      "[iOS] RxSwift 사용하기(4) - Operators"
subtitle:   "\"Let's use RxSwift - Operators\""
date:       2024-04-25 19:00:00
author:     "JacksonJang"
header-img: "assets/posts/post-bg_2024.jpg"
post_assets: "/assets/posts/2024-04-25"
catalog: true
tags:
    - Swift
    - RxSwift
    - Operators
    - iOS
---

## Operator 사용하기
[RxMarbles](https://rxmarbles.com/) 사이트에서 Rx Observables에 대한 학습용 다이어그램을 제공하고 있습니다.
<br />
직접 코딩하기 귀찮거나 간단히 확인하고 싶을 땐 위 사이트를 통해 확인하는 게 좋습니다!
<br />
다만, 2021년 10월 27일 기준으로 수정된 내용이 없으므로 일부 메서드들은 없을 수 있습니다.(예: amb)

RxSwift에서 대중적으로 많이 사용되는 것들에 대해 알아보았으니 천천히 즐기면서 보시면 됩니다. :)

# Combining 관련

## merge()
`merge`는 여러 Observable의 데이터를 상관없이 합칩니다.
<br />즉, 데이터가 도착하는 순서대로 합쳐지므로 서로 다른 Observable의 데이터가 방출됩니다.

```swift
let subject1 = PublishSubject<String>()
let subject2 = PublishSubject<String>()

let observables = Observable.of(subject1, subject2)

observables.merge()
    .subscribe(onNext: {
        print("merge : \($0)")
    })
    .disposed(by: disposeBag)

subject1.onNext("subject1")
subject2.onNext("subject2")
subject1.onNext("subject1-1")
subject2.onNext("subject2-1")
subject1.onNext("subject1-2")
subject2.onNext("subject2-2")

/*
merge : subject1
merge : subject2
merge : subject1-1
merge : subject2-1
merge : subject1-2
merge : subject2-2
*/
```

## concat()
`concat`은 여러 Observable의 데이터를 Observable 기준으로 합칩니다.
<br />
즉, 하나의 Observable이 완료될 때까지 기다리고 다음 Observable이 방출됩니다.

```swift
 let subject1 = PublishSubject<String>()
let subject2 = PublishSubject<String>()

subject1.concat(subject2)
    .subscribe(onNext: {
        print("concat response : \($0)")
    })
    .disposed(by: disposeBag)

subject1.onNext("subject1")
subject2.onNext("subject2")
subject1.onNext("subject1-1")
subject2.onNext("subject2-1")
subject1.onNext("subject1-2")

subject1.onCompleted()
subject2.onNext("subject2-2")

/*
concat response : subject1
concat response : subject1-1
concat response : subject1-2
concat response : subject2-2
*/
```

## combineLatest()
`combineLatest` 연산자는 두 개 이상의 Observable을 합치고, 데이터가 들어올 때마다 결합된 값을 방출해서 보여줍니다.
<br />
Observable은 최대 8개만 결합할 수 있습니다.
<br />
간단히 요약하면 A, B Observable 중 하나의 Observable이 방출하면 다른 Observable의 마지막 데이터를 가져와서 같이 방출됩니다.

```swift
let subject1 = PublishSubject<String>()
let subject2 = PublishSubject<String>()

Observable.combineLatest(subject1, subject2) { value1, value2 in
    return "\(value1) + \(value2)"
}.subscribe(onNext: {
    print("combineLatest : \($0)")
})
.disposed(by: disposeBag)

subject1.onNext("subject1")
subject2.onNext("subject2")
subject1.onNext("subject1-1")
subject2.onNext("subject2-1")
subject1.onNext("subject1-2")
subject1.onNext("subject1-3")
subject2.onNext("subject2-2")

/*
combineLatest : subject1 + subject2
combineLatest : subject1-1 + subject2
combineLatest : subject1-1 + subject2-1
combineLatest : subject1-2 + subject2-1
combineLatest : subject1-3 + subject2-1
combineLatest : subject1-3 + subject2-2
*/
```

## zip()
`zip` 연산자는 두 개 이상의 Observable을 합치고, 데이터가 들어올 때마다 다른 하나의 Observable이 들어왔는지 확인하고 들어왔을 때 방출합니다.
<br />
`combineLatest`랑 비슷하지만 `zip`은 **기다리는 것**에서 차이가 난다고 볼 수 있습니다.
`combineLatest`과 마찬가지로 최대 8개의 Observable만 결합할 수 있습니다.

```swift
let subject1 = PublishSubject<String>()
let subject2 = PublishSubject<String>()

Observable.zip(subject1, subject2) { value1, value2 in
        return "\(value1) - \(value2)"
    }
    .subscribe(onNext: {
        print("zip : \($0)")
    })
    .disposed(by: disposeBag)

subject1.onNext("subject1")
subject2.onNext("subject2")
subject1.onNext("subject1-1")
subject2.onNext("subject2-1")
subject1.onNext("subject1-2")

/*
zip : subject1 - subject2
zip : subject1-1 - subject2-1
*/
```

## amb()
`amb`는 동시에 방출할 수 있게 허용합니다. 
<br />
하지만 `amb`는 한 개의 Observable이 방출하자마자 연결된 또 다른 Observable은 전부 삭제되고 무시하게 됩니다.

```swift
let subject1 = PublishSubject<String>()
let subject2 = PublishSubject<String>()

subject1.amb(subject2)
    .subscribe(onNext: {
        print("amb response : \($0)")
    })
    .disposed(by: disposeBag)

subject1.onNext("amb subject1")
subject2.onNext("amb subject2")
subject1.onNext("amb subject1")
subject2.onNext("amb subject2")

/*
amb response : amb subject1
amb response : amb subject1
*/
```
만약 위 코드에서 아래와 같이 바꾼다면 결과값이 바뀌게 됩니다.
```swift
subject2.onNext("amb subject2")
subject1.onNext("amb subject1")
subject2.onNext("amb subject2")

/*
amb response : amb subject2
amb response : amb subject2
*/
```

## github 예시 코드
[https://github.com/JacksonJang/RxSwiftExample](https://github.com/JacksonJang/RxSwiftExample)

## 참고자료
[THE 5 MOST IMPORTANT COMBINING OPERATORS IN RXSWIFT](https://andreaslydemann.com/the-5-most-important-combining-operators-in-rxswift/)