---
layout:     post
title:      "[iOS] TestFlight 수출 규정 준수 정보"
subtitle:   "\"iOS Export Compliance Information\""
date:       2024-05-07 15:00:00
author:     "JacksonJang"
header-img: "assets/posts/post-bg_2024.jpg"
post_assets: "/assets/posts/2024-05-07"
catalog: true
tags:
    - Swift
    - iOS
    - TestFlight
---

## TestFlight에 올리면 귀찮은 일
<img src="{{ page.post_assets }}/export_compliance.png" style="height:400px" /> <br />
TestFlight를 올리면 위와 같이 **수출 규정 준수 정보**(Export Compliance Information)이 뜬다.
<br />
이 경우에는 TestFlight에서 맨 아래를 누르고 **Save**를 클릭하면 됩니다.

<h1>
하지만..!
</h1>

## 깔끔한 해결 방법
**Project** -> **TARGETS** -> **Info** 로 접근해서 다음과 같이 바꿔주면 됩니다!

<img src="{{ page.post_assets }}/info.png" /> <br />

```swift
<key>ITSAppUsesNonExemptEncryption</key> <No>
```

혹은

직접 **App Uses Non-Exempt Encryption** 를 입력하시고, **NO**를 입력하시면 됩니다!
