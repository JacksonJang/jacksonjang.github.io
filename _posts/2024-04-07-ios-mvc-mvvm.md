---
layout:     post
title:      "[CS] MVC vs MVVM 패턴"
subtitle:   " \"What difference between MVC and MVVM\""
date:       2024-04-07 14:00:00
author:     "JacksonJang"
header-img: "assets/posts/post-bg_2024.jpg"
post_assets: "/assets/posts/2024-04-07"
catalog: true
tags:
    - CS
    - iOS
    - Swift
    - Architecture
---
> iOS 기준으로 Swift 언어를 사용해서 간단히 설명하겠습니다.

## 개요
제가 개발을 시작했었을 때, 처음 배웠던 아키텍처 패턴으로 MVC를 배웠었습니다.
<br />
아키텍처 패턴 중에서 제일 유명한 패턴으로 소프트웨어 개발에서 사용되고 있습니다.
<br />
하지만, 모바일 OS에서는 MVC를 대신해서 MVVM이 대중적으로 자리를 잡았습니다.

그렇지만 우리가 이러한 패턴에 대해 왜 알아야 하고 굳이 써야 되나? 싶을 수도 있겠지만, 이런 것들이 사용되는 이유 또한 **개발의 편의성**을 위해서라는 것을 기억해야 합니다.

이제부터 하나씩 알아가보겠습니다.

## MVC
> 모델(Model), 뷰(View), 컨트롤러(Controller)

**모델(Model)**
~~~
데이터와 비즈니스 로직을 관리하는 역할을 합니다.
~~~
```swift
struct User {
    var name: String
    var age: Int
}
```

**뷰(View)**
~~~
사용자 인터페이스(UI) 요소를 담당하는 역할을 합니다.
~~~
```swift
class UserView: UIView {
    func showUser(name: String, age: Int) {
        print("이름: \(name), 나이: \(age)")
    }
}
```

**컨트롤러(Controller)**
~~~
사용자의 입력을 받아 모델을 업데이트하고 뷰를 갱신하는 역할을 합니다.
~~~
```swift
class ViewController: UIViewController {
    var user: User?
    var userView = UserView()

    override func viewDidLoad() {
        super.viewDidLoad()
        
        updateUser(name: "장효원", age: 29)
    }
    
    func updateUser(name: String, age: Int) {
        self.user = User(name: name, age: age)
        guard let user = user else {
            return
        }
        userView.showUser(name: user.name, age: user.age)
    }
}
```

## MVVM
> 모델(Model), 뷰(View), 뷰모델(ViewModel)

**모델(Model)**
~~~
데이터와 비즈니스 로직을 관리하는 역할을 합니다. API 통신하는 부분을 모델에 넣어도 괜찮지만, 모델이 무거워질 수 있으니 가급적이면 ViewModel에서 사용하는 게 좋습니다.
~~~
```swift
struct User {
    var name: String
    var age: Int
}
```

**뷰(View)**
~~~
MVVM에서의 View는 ViewModel로 부터 Model의 데이터를 받아와서 화면에 보여주는 역할을 합니다.
~~~
```swift
class ViewController: UIViewController {
    private lazy var viewModel = UserViewModel(viewController: self)

    override func viewDidLoad() {
        super.viewDidLoad()
        
        viewModel.updateUser(name: "장효원", age: 29)
    }
    
    public func showUser() {
        viewModel.showUser()
    }
}
```

**뷰모델(ViewModel)**
~~~
뷰와 모델 사이의 중재자 역할을 합니다. API 통신하는 부분을 여기서 처리하는 것을 권장합니다.
View에서 발생하는 이벤트를 감지하고, 해당 이벤트에 맞는 비즈니스 로직을 수행합니다.
또한 View에 표시할 데이터를 가공하여 제공하는 역할을 합니다.
~~~
```swift
class UserViewModel {
    private var user: User? {
        didSet {
            updateView()
        }
    }
    
    weak var viewController: ViewController?

    init(viewController: ViewController?) {
        self.viewController = viewController
    }

    func updateUser(name: String, age: Int) {
        user = User(name: name, age: age)
    }
    
    func showUser() {
        guard let user = user else {
            return
        }
        print("이름: \(user.name), 나이: \(user.age)")
    }

    private func updateView() {
        viewController?.showUser()
    }
}

```
<br />
아키텍처 패턴은 코드의 구조를 결정하고, 각 구성 요소 간의 상호작용 방식을 정의하기 때문에 프로젝트의 요구 사항과 팀의 작업 방식에 따라 알맞은 아키텍처 패턴을 선택하는 것이 중요합니다.

## 프로젝트의 요구 사항 예시
1. UI와 사용자의 인터렉션이 복잡하다면
-> **MVVM** 패턴을 사용하는 것이 효과적입니다. 왜냐하면 UI 업데이트가 자동으로 이루어지고, UI와 비즈니스 로직을 완전 분리할 수 있어서 유지보수에 좋습니다.

2. 프로젝트 규모가 크고 확장성이 클 때
-> **MVVM** 패턴을 사용하는 것이 효과적입니다. 왜냐하면, UI 컴포넌트를 독립적으로 개발할 수 있게 만들어주기 때문에 확장성과 유지보수에 좋습니다.

3. 소규모 및 빠른 개발을 원할 때
-> **MVC** 패턴이 적합합니다. 단순하면서 빠른 개발이 가능하지만, 단점으로는 유지보수가 힘듭니다.. 정말..ㅎㅎ

## github 예시