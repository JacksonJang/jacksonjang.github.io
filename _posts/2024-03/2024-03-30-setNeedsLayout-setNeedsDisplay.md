---
layout:     post
title:      "[iOS] setNeedsLayout()와 setNeedsDisplay()의 차이"
subtitle:   " \"setNeedsLayout() vs setNeedsDisplay()\""
date:       2024-03-30 03:00:00
author:     "JacksonJang"
header-img: "assets/posts/post-bg_2024.jpg"
post_assets: "/assets/posts/2024-03-30"
catalog: true
tags:
    - iOS
    - Swift
---

## [setNeedsLayout()](https://developer.apple.com/documentation/uikit/uiview/1622601-setneedslayout)
```none
Invalidates the current layout of the receiver and triggers a layout update during the next update cycle.
```
위의 말은 번역하자면, 현재 레이아웃을 무효화하고 다음 업데이트 사이클에 레이아웃을 업데이트 한다는 것을 의미합니다.

setNeedsLayout()은 직접적으로 레이아웃을 변경하지는 않지만, 레이아웃을 변경해야 한다는 신호를 보내고, 실제 레이아웃 변경은 시스템이 layoutSubviews()를 호출할 때 이루어집니다.

## [setNeedsDisplay()](https://developer.apple.com/documentation/uikit/uiview/1622437-setneedsdisplay)
```none
You can use this method or the setNeedsDisplay(_:) to notify the system that your view’s contents need to be redrawn. This method makes a note of the request and returns immediately. The view is not actually redrawn until the next drawing cycle, at which point all invalidated views are updated.
```
위의 말을 요약하면, setNeedsDisplay(_:)를 사용하면, 시스템한테 뷰의 컨텐츠를 다시 그리는 것을 알립니다.

이 메소드를 사용하여 다시 그려야 할 영역의 CGRect을 지정할 수 있습니다.

## github 예제
[https://github.com/JacksonJang/setNeedsLayoutAndsetNeedsDisplay.git](https://github.com/JacksonJang/setNeedsLayoutAndsetNeedsDisplay.git)