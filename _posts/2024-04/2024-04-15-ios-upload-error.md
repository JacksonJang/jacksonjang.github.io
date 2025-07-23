---
layout:     post
title:      "[iOS] App Store connect access for is required. add an account in accounts settings 에러 해결"
subtitle:   "\"Solve App Store connect access for is required. add an account in accounts settings\""
date:       2024-04-15 19:00:00
author:     "JacksonJang"
post_assets: "/assets/posts/2024-04-15"
catalog: true
categories:
    - iOS
tags:
    - iOS
---

<img width="300px" src="{{ page.post_assets }}/error.png" />
```swift
App Store connect access for is required. add an account in accounts settings
```
앱을 배포하려다가 에러를 발견해서 해결법을 알아보니... 간단했었다.

해결법 : `Xcode` **재시작(restart)**

위 해결법으로도 되지 않는다면 Xcode에 연결된 계정을 삭제 했다가 다시 시도하면 될 것 같다.
<br />
저는 Xcode 재시작으로 해결됐습니다!
