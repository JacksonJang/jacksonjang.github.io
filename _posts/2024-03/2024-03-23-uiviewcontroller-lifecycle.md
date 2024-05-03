---
layout:     post
title:      "[iOS] UIViewController 라이프사이클"
subtitle:   " \"UIViewController LifeCycle\""
date:       2024-03-23 15:00:00
author:     "JacksonJang"
header-img: "assets/posts/post-bg_2024.jpg"
post_assets: "/assets/posts/2024-03-23"
catalog: true
tags:
    - iOS
    - Swift
---
iOS 개발에서 중요한 것은 문법도 중요하지만, 그 전에 애플리케이션이 어떻게 동작하고 관리되는지 알아야 효율적인 앱을 만들 수 있다고 생각해서 정리했습니다.

## UIKit에 정의된 UIViewController 살펴보기

```swift
@available(iOS 2.0, *)
@MainActor open class UIViewController : UIResponder, NSCoding, UIAppearanceContainer, UITraitEnvironment, UIContentContainer, UIFocusEnvironment {

    public init(nibName nibNameOrNil: String?, bundle nibBundleOrNil: Bundle?)

    public init?(coder: NSCoder)

    open func loadView()

    open func viewDidLoad()

    open func viewWillAppear(_ animated: Bool)

    open func viewDidAppear(_ animated: Bool)

    open func viewWillDisappear(_ animated: Bool)

    open func viewDidDisappear(_ animated: Bool)
```
위에처럼 정의되어 있는 모습을 확인할 수 있습니다.
예전에는 `@MainActor`는 Swift 5.5에서 나온 개념으로 **메인 쓰레드에서 실행되도록 보장하는 역할** 이라고 보시면 됩니다.

이제 하나씩 자세히 살펴 보겠습니다.

## init
```swift
// nib file 을 통해 인스턴스를 생성할 때 사용
public init(nibName nibNameOrNil: String?, bundle nibBundleOrNil: Bundle?)

// 스토리보드를 통해 인스턴스를 생성할 때 사용
public init?(coder: NSCoder)
```

## [loadView](https://developer.apple.com/documentation/uikit/uiviewcontroller/1621454-loadview)
```swift
// 뷰 컨트롤러의 view를 메모리에 올립니다.
open func loadView()
```
위 과정에서 @IBOutlet, @IBAction 등이 생성되고 view 객체들과 자동으로 연결됩니다.

> 만약, 스토리보드와 xib으로 직접 만들어서 사용할 시(즉, Interface Builder를 이용할 시), 절대 loadView 메서드를 override 하면 안됩니다.

[애플 공식 문서 내용]
```none
If you use Interface Builder to create your views and initialize the view controller,
you must not override this method.
```

## [viewDidLoad](https://developer.apple.com/documentation/uikit/uiviewcontroller/1621495-viewdidload)
```swift
open func viewDidLoad()
```
viewDidLoad는 UIViewController의 view가 메모리에 올라가면 호출됩니다.
위에서 이미 loadView를 통해 view가 올라가졌으니 viewDidLoad로 왔겠죠??

위에서 설명한 메서드(init, loadView, viewDidLoad)들은 최초 1번만 호출됩니다.

## [viewWillAppear](https://developer.apple.com/documentation/uikit/uiviewcontroller/1621510-viewwillappear/)
```swift
open func viewWillAppear(_ animated: Bool)
```
화면에 보이기 직전에 호출됩니다.
<br />
그치만, 너무 오래 걸리는 작업을 여기에 넣게되면 버벅거리는걸 느끼게 될 수 있어서 가급적이면 viewDidLoad에서 처리하는게 좋아요.
<p />
여러번 호출할 수 있는 메서드이기 때문에 최초 한번만 실행해야 하는 로직이 있다면, 피해주셔야 합니다.

## [viewDidAppear](https://developer.apple.com/documentation/uikit/uiviewcontroller/1621423-viewdidappear)
```swift
open func viewDidAppear(_ animated: Bool)
```
화면에 완전히 나타난 후 호출됩니다.
<p />
여러번 호출할 수 있는 메서드이기 때문에 최초 한번만 실행해야 하는 로직이 있다면, 피해주셔야 합니다.

## [viewWillDisappear](https://developer.apple.com/documentation/uikit/uiviewcontroller/1621485-viewwilldisappear)
```swift
open func viewWillDisappear(_ animated: Bool)
```
뷰가 제거되기 직전에 호출됩니다.
<p />
여러번 호출할 수 있는 메서드이기 때문에 최초 한번만 실행해야 하는 로직이 있다면, 피해주셔야 합니다.

## [viewDidDisappear](https://developer.apple.com/documentation/uikit/uiviewcontroller/1621477-viewdiddisappear)
```swift
open func viewDidDisappear(_ animated: Bool)
````
뷰가 뷰 계층에서 완전히 사라진 후 호출됩니다.
<p />
여러번 호출할 수 있는 메서드이기 때문에 최초 한번만 실행해야 하는 로직이 있다면, 피해주셔야 합니다.

## 참고 링크
- [https://bicycleforthemind.tistory.com/33](https://bicycleforthemind.tistory.com/33)