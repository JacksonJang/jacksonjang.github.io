---
layout:     post
title:      "[iOS] layoutIfNeeded() 알아보기"
subtitle:   " \"Learn about layoutIfNeeded()\""
date:       2024-03-31 13:00:00
author:     "JacksonJang"
header-img: "assets/posts/post-bg_2024.jpg"
post_assets: "/assets/posts/2024-03-31"
catalog: true
tags:
    - iOS
    - Swift
---

## [layoutIfNeeded()](https://developer.apple.com/documentation/uikit/uiview/1622507-layoutifneeded)
```none
Lays out the subviews immediately, if layout updates are pending.
```
해석하자면, 레이아웃 업데이트가 대기중이라면, 서브뷰를 즉시 배치합니다.

layoutIfNeeded()는 시스템이 자동으로 레이아웃을 업데이트하는 다음 주기를 기다리지 않고, 호출된 시점에 레이아웃을 갱신하도록 합니다. 
그래서 **즉시 조정**해야 할 때 유용하게 사용할 수 있습니다.

> 기본적으로 iOS 레이아웃 시스템은 비동기적으로 작동하여, 
> 레이아웃을 변경하더라도 업데이트는 다음 렌더링에서 일괄적으로 처리됩니다.

## setNeedsLayout, setNeedsDisplay 알아보기
[https://jacksonjang.github.io/2024/03/31/setNeedsLayout-setNeedsDisplay/](https://jacksonjang.github.io/2024/03/31/setNeedsLayout-setNeedsDisplay/)