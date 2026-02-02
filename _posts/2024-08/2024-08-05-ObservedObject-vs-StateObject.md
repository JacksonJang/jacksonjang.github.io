---
layout:     post
title:      "[SwiftUI] @ObservedObject vs @StateObject"
subtitle:   "\"@ObservedObject vs @StateObject\""
date:       2024-08-05 19:00:00
author:     JacksonJang
post_assets: "/assets/posts/2024-08-05"
catalog: true
categories:
    - iOS
tags:
    - iOS
    - SwiftUI
---

## 핵심 정리
- 공통점 : 객체의 상태 변화를 감지하고 뷰를 업데이트하는 데 사용되는 속성 래퍼입니다.
- `@StateObject`는 부모 뷰가 직접 객체를 소유하고 관리합니다.
- `@ObservedObject`는 부모 뷰에서 객체를 **관찰**하고 업데이트를 반영합니다.


## ObservableObject 란?
`@StateObject` 와 `@ObservedObject`에 대해 알기 전에 우선적으로 `ObservableObject` 라는 프로토콜에 대해 이해할 필요가 있습니다.

```
@available(iOS 13.0, macOS 10.15, tvOS 13.0, watchOS 6.0, *)
public protocol ObservableObject : AnyObject {

    /// The type of publisher that emits before the object has changed.
    associatedtype ObjectWillChangePublisher : Publisher = ObservableObjectPublisher where Self.ObjectWillChangePublisher.Failure == Never

    /// A publisher that emits before the object has changed.
    var objectWillChange: Self.ObjectWillChangePublisher { get }
}
```
ObservableObject 는 AnyObject를 상속받은 프로토콜 입니다.
주로 `상태 관리`, `데이터 바인딩` 역할을 하는 `Publisher`를 포함한 객체입니다.
그리고 여기서 `상태 관리`, `데이터 바인딩` 에 대한 관리는 `@StateObject`, `@ObservedObject`를 사용해서 가능합니다.

예시를 진행하기 위해 간단한 모델을 생성하곘습니다

```swift
struct CustomModel: Identifiable {
    let id: String
    let name: String
    let age: Int
}
```

## @StateObject
부모 뷰에서 해당 객체를 소유하고 관리합니다.
즉, 뷰가 생성될 때 객체도 생성되며, 뷰가 사라질 때 객체도 같이 소멸되며 부모 뷰의 생명주기와 함께 유지됩니다.

### @StateObject 예시코드

```swift
// 뷰 모델
class ContentViewModel: ObservableObject {
    @Published var items: [CustomModel] = [
        CustomModel(id: UUID().uuidString, name: "JANG", age: 23),
        CustomModel(id: UUID().uuidString, name: "HYO", age: 29)
    ]
    
    func add() {
        items.append(CustomModel(id: UUID().uuidString, name: "ADD", age: Int.random(in: 0...100)))
    }
}

struct ContentView: View {
    @StateObject private var viewModel = ContentViewModel()
    
    var body: some View {
        VStack {
            Text("Total length : \(viewModel.items.count)")
            Button("ADD") {
                viewModel.add()
            }
        }
        .padding()
    }
}
```

## @ObservedObject
부모 뷰에서 전달된 ObservableObject를 자식 뷰에서 감지할 때 사용합니다.
부모 뷰에서 자식 뷰에게 @StateObject를 전달하면, 자식 뷰에서는 @ObservedObject를 이용해서 참조하게 됩니다.

### @ObservedObject 예시코드

```swift
// 뷰 모델
class ContentViewModel: ObservableObject {
    @Published var items: [CustomModel] = [
        CustomModel(id: UUID().uuidString, name: "JANG", age: 23),
        CustomModel(id: UUID().uuidString, name: "HYO", age: 29)
    ]
    
    func add() {
        items.append(CustomModel(id: UUID().uuidString, name: "ADD", age: Int.random(in: 0...100)))
    }
}

struct ContentView: View {
    @StateObject private var viewModel = ContentViewModel()
    
    var body: some View {
        VStack {
            Text("Total length : \(viewModel.items.count)")
            ChildView(viewModel: viewModel)
            Button("ADD") {
                viewModel.add()
            }
        }
        .padding()
    }
}

struct ChildView: View {
    @ObservedObject var viewModel: ContentViewModel
    
    var body: some View {
        List(viewModel.items) { item in
            Text("Name : \(item.name), Age : \(item.age)")
        }
    }
}

#Preview {
    ChildView(viewModel: ContentViewModel())
}
```

## github 예시 파일
[https://github.com/JacksonJang/ObservedVsState](https://github.com/JacksonJang/ObservedVsState)
