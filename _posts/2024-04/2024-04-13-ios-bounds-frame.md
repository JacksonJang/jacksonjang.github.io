---
layout:     post
title:      "[iOS] Bounds 와 Frame 의 차이점"
subtitle:   "\"What's the difference between Bounds and Frame\""
date:       2024-04-13 19:00:00
author:     JacksonJang
post_assets: "/assets/posts/2024-04-13"
catalog: true
categories:
    - iOS
tags:
    - iOS
    - Swift
---
> 요약 : bounds는 자기 자신 기준, frame은 상위(부모)뷰 기준

## Bounds 와 Frame 의 차이점
<br>

# Apple Developer Documnet
## [Frame](https://developer.apple.com/documentation/uikit/uiview/1622621-frame)
>The frame rectangle, which describes the view’s location and size in its superview’s coordinate system.

## [Bounds](https://developer.apple.com/documentation/uikit/uiview/1622580-bounds)
>The bounds rectangle, which describes the view’s location and size in its own coordinate system.

<br>

# 설명
**frame**
~~~
상위뷰(부모 뷰) 의 좌표 시스템안에서 뷰의 위치와 크기를 나타낸다.
~~~

**bounds**
~~~
자기 자신의 좌표 시스템 안에서 뷰의 위치와 크기를 나타낸다.
~~~
