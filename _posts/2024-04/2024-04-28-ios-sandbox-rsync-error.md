---
layout:     post
title:      "[iOS] Sandbox:rsync.samba 에러 해결법"
subtitle:   "\"How to solve the error 'Sandbox:rsync.samba' \""
date:       2024-04-28 13:00:00
author:     "JacksonJang"

post_assets: "/assets/posts/2024-04-28"
catalog: true
categories:
    - iOS
tags:
    - Swift
    - RxSwift
    - Xcode15
    - iOS
---

## 에러 메시지
<img src="{{ page.post_assets }}/error.png">
> error: Sandbox: rsync.samba(5159) deny(1) file-write-create /Users/janghyowon/Library/Developer/Xcode/DerivedData

Xcode 15.0.1 기준으로 빌드하니까 위와 같은 에러가 발생했었습니다.
<br />
우선 에러를 해결하고 싶어하셔서 들어오셨을테니 해결법부터 말씀드리자면

<img src="{{ page.post_assets }}/Build_Settings.png">
**해결법** : Project TARGETS -> Build Settings -> ENABLE_USER_SCRIPT_SANDBOXING 검색 후 -> **YES** 를 **NO** 로 변경

그리고 다시 빌드!
<img src="{{ page.post_assets }}/Build_Success.png">
간단하죠?

## 관련링크
[Xcode 15 beta build issues](https://forums.developer.apple.com/forums/thread/731041)
