---
layout:     post
title:      "[iOS] try increasing the minimum deployment target 에러 해결법"
subtitle:   "\"How to solve the error 'try increasing the minimum deployment target' \""
date:       2024-05-05 15:00:00
author:     JacksonJang
post_assets: "/assets/posts/2024-05-05"
catalog: true
categories:
    - iOS
tags:
    - Swift
    - Xcode15
    - iOS
---

`FSCalendar`의 예시 파일을 실행하니 아래와 같은 에러를 마주하게 되었습니다.

## 에러 메시지
```
SDK does not contain 'libarclite' at the path '/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/lib/arc/libarclite_iphonesimulator.a'; try increasing the minimum deployment target
```

에러 메시지에서는 minimum deployment target 버전을 높히라고 말하고 있다!

### 에러난 Xcode 내 설정 화면
<img src="{{ page.post_assets }}/general.png" /> <br />
위와 같이 8.0으로 설정되어 있는데 12.0 이상으로 바꾸면 된다!

## 근데 왜 12 이상인가..?
사실 이 부분은 Xcode 15가 출시되면서 iOS 12 미만의 버전들은 전부 deprecated 이 되었습니다.
<br />
한마디로 앞으로 Xcode 15이상부터 **iOS 12**이상만 지원합니다.

<img src="{{ page.post_assets }}/xcode15.png" /> <br />
```
Xcode 15 includes SDKs for iOS 17, iPadOS 17, tvOS 17, watchOS 10, and macOS Sonoma. The Xcode 15 release supports on-device debugging in iOS 12 and later, tvOS 12 and later, and watchOS 4 and later. Xcode 15 requires a Mac running macOS Ventura 13.5 or later.
```
[Xcode 15 Release](https://developer.apple.com/documentation/xcode-release-notes/xcode-15-release-notes)에서도 나와 있듯이 
**The Xcode 15 release supports on-device debugging in iOS 12** 로 iOS 12 이상을 지원한다는 것을 확인할 수 있습니다.

다른 분들께서도 도움이 되셨으면 좋겠습니다!
