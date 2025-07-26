---
layout:     post
title:      "[iOS] 바텀시트 만들어보기(with. UIPanGestureRecognizer)"
subtitle:   "\"iOS Make BottomSheet(with.UIPanGestureRecognizer)\""
date:       2024-05-11 15:00:00
author:     JacksonJang
post_assets: "/assets/posts/2024-05-11"
catalog: true
categories:
    - iOS
tags:
    - iOS
    - UIPanGestureRecognizer
    - BottomSheet
---

<img src="{{ page.post_assets }}/bottomSheet.gif" style="height:400px" /> <br />
오늘은 `UIPanGestureRecognizer`를 사용해서 바텀 시트를 만들어 보면서 `UIPanGestureRecognizer`에 대해 알아보겠습니다.

## UIPanGestureRecognizer 란?
> A continuous gesture recognizer that interprets panning gestures.

[UIPanGestureRecognizer](https://developer.apple.com/documentation/uikit/uipangesturerecognizer)는 연속적인 제스처 인식기로 그리는 제스처를 해석합니다.

`UIPanGestureRecognizer`에 대해 추가적으로 더 설명하자면, **사용자의 손가락이 화면에 닿는 순간부터 움직임을 추적하기 시작하여, 움직임이 종료될 때까지의 전 과정을 감지합니다.**

우리는 **움직임을 추적**하는 메커니즘을 이용해서 바텀 시트를 제작할 예정입니다.

## UIPanGestureRecognizer 사용 예시
```swift
let panGesture = UIPanGestureRecognizer(target: self, action: #selector(handlePan))
self.view.addGestureRecognizer(panGesture)
```
위 코드는 간단한 예시 코드로 `self.view`(현재 뷰)에 panGesture가 동작할 때마다 handlePan 메서드에 움직임을 보내는 역할을 합니다. 따라서, handlePan 메서드에서 `self.view`에 대한 움직임을 추적할 수 있다고 보시면 됩니다. 즉, handlePan 메서드는 `콜백 함수`인 격이죠.

## 구성요소들
```swift
@available(iOS 3.2, *)
@MainActor open class UIPanGestureRecognizer : UIGestureRecognizer {
    open var minimumNumberOfTouches: Int // default is 1. the minimum number of touches required to match
    open var maximumNumberOfTouches: Int // default is UINT_MAX. the maximum number of touches that can be down

    open func translation(in view: UIView?) -> CGPoint // translation in the coordinate system of the specified view

    open func setTranslation(_ translation: CGPoint, in view: UIView?)
    
    open func velocity(in view: UIView?) -> CGPoint // velocity of the pan in points/second in the coordinate system of the specified view
    
    @available(iOS 13.4, *)
    open var allowedScrollTypesMask: UIScrollTypeMask
}
```
각 속성과 메서드에 대해 설명하자면 다음과 같습니다.
- minimumNumberOfTouches : 제스처 인식을 위해 필요한 터치 수 (기본 값: 1)
- maximumNumberOfTouches : 제스처 인식할 수 있는 최대 터치 수 (기본 값: UINT_MAX)
- translation(in view: UIView?) : 매개 변수에 있는 뷰의 좌표 시스템의 시작 지점에서부터 현재 위치까지의 거리를 x, y좌표 표시
- setTranslation(_ translation: CGPoint, in view: UIView?) : 제스처의 위치를 수동으로 설정할 때 사용
- velocity(in view: UIView?) : 뷰의 제스처 속도를 x와 y 로 반환
- allowedScrollTypesMask: 스크롤 뷰와 같은 특정 유형의 스크롤에 대해 제스처 인식기가 어떻게 반응할지 설정

오늘 만들어 볼 바텀시트는 `translation`, `velocity` 메서드를 이용해서 만들 예정입니다.

## 기본 UI 설정
바텀 시트는 총 3단계로 만들 예정입니다.

- 1단계 : 숨김처리
- 2단계 : 높이 400
- 3단계 : 높이 700

```swift
var state: Int = 1
```
단계 설정은 단순하게 Int 타입의 state 변수를 선언하겠습니다

```swift
let dimView: UIView = {
    let view = UIView()
    
    view.translatesAutoresizingMaskIntoConstraints = false
    view.backgroundColor = UIColor.black.withAlphaComponent(0.4)
    
    return view
}()

let bottomSheetView: UIView = {
    let view = UIView()
    
    view.translatesAutoresizingMaskIntoConstraints = false
    view.backgroundColor = .white
    
    return view
}()
```
그 이후로는 보여지게 될 뷰를 설정합니다.

이제 높이를 조정할 수 있는 `NSLayoutConstraint`가 필요하겠죠?
```swift
var bottomHeightConstraint: NSLayoutConstraint? = nil
```

이러면 UI에서 처리할 부분에 대한 준비는 끝났습니다.

## 본격적으로 translation과 velocity를 사용해 보자
`UIPanGestureRecognizer`로부터 발생하는 제스처 이벤트를 처리하는 콜백 함수인 `handlePan` 메서드를 만들고, `adjustSheetPosition` 메서드를 통해 상태값 변경과 동시에 높이에 대한 조정을 하는 메서드를 만들어서 `animateBottomSheet`와 `hideBottomSheet`를 통해 직접적인 UI 변경을 진행하겠습니다.

```swift
@objc private func handlePan(_ sender: UIPanGestureRecognizer) {
    guard let bottomHeightConstraint = self.bottomHeightConstraint else { return }
    
    let translation = sender.translation(in: view)
    let velocity = sender.velocity(in: view)
    let newHeight = min(max(0, bottomHeightConstraint.constant - translation.y), 700)

    sender.setTranslation(.zero, in: view)

    switch sender.state {
    case .began, .changed:
        bottomHeightConstraint.constant = newHeight
    case .ended, .cancelled:
        adjustSheetPosition(withVelocity: velocity.y, currentHeight: newHeight)
    default:
        break
    }

    view.layoutIfNeeded()
}

 private func adjustSheetPosition(withVelocity velocity: CGFloat, currentHeight: CGFloat) {
    if velocity > 500 {
        state = max(0, state - 1)
    } else if velocity < -500 {
        state = min(2, state + 1)
    }
    
    switch state {
    case 0:
        hideBottomSheet()
    case 1:
        animateBottomSheet(to: 400)
    case 2:
        animateBottomSheet(to: 700)
    default:
        break
    }
}

private func animateBottomSheet(to height: CGFloat) {
    UIView.animate(withDuration: 0.3, animations: {
        self.bottomHeightConstraint?.constant = height
        self.view.layoutIfNeeded()
    })
}

private func hideBottomSheet() {
    UIView.animate(withDuration: 0.3, animations: {
        self.bottomHeightConstraint?.constant = 0
        self.view.layoutIfNeeded()
    }) { _ in
        self.bottomSheetView.removeFromSuperview()
        self.dimView.removeFromSuperview()
    }
}
```
위 코드에서 `sender.setTranslation(.zero, in: view)`를 사용하는 이유가 궁금하실 수도 있는데, 해당 뷰에서 움직임을 계속해서 추적하게 되면 변화량이 누적됩니다. 따라서, 제스처가 길어지면 길어질 수록 변화량은 점점 더 커지기 때문에 초기화를 해줘야 정확한 측정이 가능합니다.

## github 예시 코드
- [https://github.com/JacksonJang/BottomSheetExample](https://github.com/JacksonJang/BottomSheetExample)
