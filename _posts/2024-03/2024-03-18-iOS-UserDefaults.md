---
layout:     post
title:      "[iOS] UserDefaults 사용하기"
subtitle:   " \"Using UserDefaults\""
date:       2024-03-18 19:09:00
author:     JacksonJang
post_assets: "/assets/posts/2024-03-18"
catalog: true
categories:
    - iOS
tags:
    - iOS
    - Swift
    - UserDefaults
---

> UserDefaults에 대해 자세히 알아보자!

UserDefaults는 실무에서도 자주 사용하는 저장 방식이라 필수적으로 알아야 할 기본적인 내용이라 정리할 기회가 생겨서 정리하게 되었습니다.

## Apple에서 설명하는 UserDefaults
[https://developer.apple.com/documentation/foundation/userdefaults](https://developer.apple.com/documentation/foundation/userdefaults)
<br />
<img src="{{ page.post_assets }}/UserDefaults.png">
<br />
영어를 해석하면 다음과 같다.
```
사용자의 기본 설정 데이터베이스에 대한 인터페이스로,
여러분의 앱을 실행할 때마다
키-값 쌍을 지속적으로 저장합니다.
```

## UserDefaults 에 대한 기타 지식?
하지만, 간단하게 저장되는 만큼 보안도 취약하다는 이야기도 있습니다. 왜냐하면, UserDefaults는 plist 파일 형태로 앱 내의 Sandbox 내에 저장됩니다. 따라서, 중요한 내용들은 Security 프레임워크를 이용해서 저장합시다!

이외에도 Realm, Core Data, SQLite 등 다양한 저장 방식이 있지만, 오늘은 UserDefaults에 대해서만 알아보겠습니다.

## UserDefaults Apple Document

### UserDefaults set
[https://developer.apple.com/documentation/foundation/userdefaults/1414067-set](https://developer.apple.com/documentation/foundation/userdefaults/1414067-set)
<br />
<img src="{{ page.post_assets }}/UserDefaults-set.png">

### UserDefaults get
[https://developer.apple.com/documentation/foundation/userdefaults/1410095-object](https://developer.apple.com/documentation/foundation/userdefaults/1410095-object)
<br />
<img src="{{ page.post_assets }}/UserDefaults-get.png">

## UserDefaults 사용하기

예전에 iOS 8 전에는 ~~UserDefaults.standard.synchronize()~~ 을 사용해줘야 했지만, 현재는 자동으로 호출하지 않아도 자동으로 저장되도록 관리해줍니다.

따라서, 다음과 같이 사용하면 끝이에요~
```swift
// 저장
UserDefaults.standard.set("값", forKey: "키")
// 조회
UserDefaults.standard.object(forKey: "키")
```

### 끝
