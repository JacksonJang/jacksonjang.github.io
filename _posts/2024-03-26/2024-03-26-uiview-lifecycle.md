---
layout:     post
title:      "[iOS] UIView 라이프사이클"
subtitle:   " \"UIView LifeCycle\""
date:       2024-03-26 20:00:00
author:     "JacksonJang"
header-img: "assets/posts/post-bg_2024.jpg"
post_assets: "/assets/posts/2024-03-26"
catalog: true
tags:
    - iOS
    - Swift
    - UIView
---

## UIKit에 정의된 UIView 살펴보기

```swift
@available(iOS 2.0, *)
@MainActor open class UIView : UIResponder, NSCoding, UIAppearance, UIAppearanceContainer, UIDynamicItem, UITraitEnvironment, UICoordinateSpace, UIFocusItem, UIFocusItemContainer, CALayerDelegate {

    public init(frame: CGRect)

    public init?(coder: NSCoder)

    open func willMove(toSuperview newSuperview: UIView?)

    open func didMoveToSuperview()

    open func willMove(toWindow newWindow: UIWindow?)

    open func didMoveToWindow()

    open func layoutSubviews()

    open func draw(_ rect: CGRect)
```
이전 [UIViewController 라이프사이클](https://jacksonjang.github.io/2024/03/23/uiviewcontroller-lifecycle/)에서도 봤었던 `@MainActor`는 Swift 5.5에서 나온 개념으로 **메인 쓰레드에서 실행되도록 보장하는 역할** 이라고 보시면 됩니다.

이제 하나씩 자세히 살펴 보겠습니다.

## init
```swift
public init(frame: CGRect)

public init?(coder: NSCoder)
```
`init?(coder: NSCoder)`는 스토리보드를 통해 생성할 때 호출됩니다.
<br />
`init(frame: CGRect)` 는 코드 베이스로 생성할 때 호출됩니다.

## [willMove(toSuperview:)](https://developer.apple.com/documentation/uikit/uiview/1622629-willmove)
```swift
open func willMove(toSuperview newSuperview: UIView?)
```
뷰가 뷰 계층에 추가되기 전에 호출됩니다.
만약 `newSuperview`가 `nil`이라면, 뷰가 뷰 계층에서 제거되는 것을 의미한다고 보시면 됩니다.


## [didMoveToSuperview()](https://developer.apple.com/documentation/uikit/uiview/1622433-didmovetosuperview)
```swift
open func didMoveToSuperview()
```
뷰가 뷰 계층에 추가된 후에 호출됩니다.

## [willMove(toWindow:)](https://developer.apple.com/documentation/uikit/uiview/1622563-willmove)
```swift
open func willMove(toWindow newWindow: UIWindow?)
```
뷰가 윈도우에 추가되기 전에 호출됩니다. [willMove(toSuperview:)](#willmovetosuperview)와 마찬가지로 `newWindow`가 `nil`이라면, 뷰가 윈도우에서 제거되는 것을 의미한다고 보시면 됩니다.

## [didMoveToWindow()](https://developer.apple.com/documentation/uikit/uiview/1622527-didmovetowindow)
```swift
open func willMove(toWindow newWindow: UIWindow?)
```
뷰가 윈도우에 추가된 후 호출됩니다.

## [layoutSubviews()](https://developer.apple.com/documentation/uikit/uiview/1622482-layoutsubviews)
```swift
open func layoutSubviews()
```
뷰의 서브뷰들의 레이아웃에 대한 처리가 완료 되었을 때 호출됩니다.
<p />
그리고 1번만 호출하는게 아니라 뷰의 크기가 변경될 때마다 호출됩니다.

## [draw(_:)](https://developer.apple.com/documentation/uikit/uiview/1622529-draw)
```swift
open func draw(_ rect: CGRect)
```
뷰가 추가되어 화면에 추가되어 좌표 설정이 되면 호출됩니다.
<br />
추가적으로, `setNeedsDisplay()` 메서드가 호출될 때 자동으로 draw 메서드가 호출됩니다.
<p />
**CGRect가 .zero라면 호출되지 않습니다.**

## Test 코드 예시
```swift
import UIKit

class ViewController: UIViewController {
    
    override func viewDidLoad() {
        super.viewDidLoad()
        
        let view = CustomView(frame: CGRect(x: 0, y: 0, width: 100, height: 100))
        self.view.addSubview(view)
    }
}

class CustomView: UIView {
    override init(frame: CGRect) {
        super.init(frame: frame)
        print("init(frame: CGRect)")
    }
    
    override func willMove(toSuperview newSuperview: UIView?) {
        super.willMove(toSuperview: newSuperview)
        
        print("willMove(toSuperview newSuperview: UIView?)")
    }
    
    override func didMoveToSuperview() {
        super.didMoveToSuperview()
        print("didMoveToSuperview()")
    }
    
    override func willMove(toWindow newWindow: UIWindow?) {
        super.willMove(toWindow: newWindow)
        print("willMove(toWindow newWindow: UIWindow?)")
    }
    
    override func didMoveToWindow() {
        super.didMoveToWindow()
        print("didMoveToWindow()")
    }
    
    override func layoutSubviews() {
        super.layoutSubviews()
        print("layoutSubviews()")
    }
    
    override func draw(_ rect: CGRect) {
        super.draw(rect)
        print("draw(_ rect: CGRect)")
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
}
```

## Test 결과 콘솔
```swift
init(frame: CGRect)
willMove(toSuperview newSuperview: UIView?)
didMoveToSuperview()
willMove(toWindow newWindow: UIWindow?)
didMoveToWindow()
layoutSubviews()
layoutSubviews()
draw(_ rect: CGRect)
```