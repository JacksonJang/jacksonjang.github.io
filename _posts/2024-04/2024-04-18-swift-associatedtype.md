---
layout:     post
title:      "[Swift] 연관 타입(associatedtype) 란?"
subtitle:   "\"What's the associatedtype?\""
date:       2024-04-18 19:00:00
author:     "JacksonJang"
header-img: "assets/posts/post-bg_2024.jpg"
post_assets: "/assets/posts/2024-04-18"
catalog: true
tags:
    - Swift
---
Swift 5.6 버전에서 `associatedtype` 이라는 연관타입이 생겼습니다.
[https://www.hackingwithswift.com/example-code/language/what-is-a-protocol-associated-type](https://www.hackingwithswift.com/example-code/language/what-is-a-protocol-associated-type)

```swift
 In essence, they mark holes in protocols that must be filled by whatever types conform to those protocols.
```
위 문장은 `Hacking with Swift`에 명시되어 있는 문장을 가져온 것으로 해석하면 다음과 같습니다.
> 본질적으로, 타입들은 프로토콜이 지정한 영역(associatedtype)을 준수하면서 채워 넣어야 합니다.

associatedtype을 사용하면 어떤 타입이든 원하는 타입으로 사용하기 때문에 `타입 안전성`, `재사용성` 등의 장점이 있습니다.

## 사용법
이제부터 Hacking with Swift에 나와있는 예시와 함께 설명 드리겠습니다.

```swift
protocol ItemStoring {
    associatedtype DataType

    var items: [DataType] { get set}
    mutating func add(item: DataType)
}
```
위에서 associatedtype으로 설정되어 있는 `DataType` 은 개발자가 직접 설정하는 것입니다.
<br />
저 타입명은 아무렇게나 지정해도 상관없기 때문에 `HyowonType` 이런식으로도 설정할 수 있습니다.

```swift
extension ItemStoring {
    mutating func add(item: DataType) {
        items.append(item)
    }
}
```
프로토콜의 구체적인 함수 구현은 extension을 통해서만 가능하니까 위에처럼 구현되었네요.

```swift
struct NameDatabase: ItemStoring {
    var items = [String]()
}
```
이제 ItemStoring 을 채택받은 NameDatabase 모델을 생성했습니다.
<br />아까 위에서 선언한 **associatedtype** `DataType`을 기억하시나요?
<br />`DataType`이 여기서 `String` 타입이 됩니다.

<p>
확실히 이렇게 사용하게 되니까 나중에 재사용할 때에도 편하겠죠? 혹은 공통적으로 사용하는 부분이 있다면 더더욱 좋고요!
</p>

```swift
var names = NameDatabase()
names.add(item: "hyowon")
names.add(item: "jackson")

names.items.forEach{ print($0) }
```
위 코드를 통해 데이터를 넣어주고 print를 하면?!

```swift
// 결과값
hyowon
jackson
```
위와 같이 정상적으로 처리된 결과 값을 얻을 수 있습니다.

## github 예시
[https://github.com/JacksonJang/associatedtypeExample](https://github.com/JacksonJang/associatedtypeExample)