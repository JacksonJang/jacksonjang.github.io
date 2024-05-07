---
layout:     post
title:      "[iOS] UIDatePicker 사용하기"
subtitle:   "\"Use UIDatePicker\""
date:       2024-05-06 15:00:00
author:     "JacksonJang"
header-img: "assets/posts/post-bg_2024.jpg"
post_assets: "/assets/posts/2024-05-06"
catalog: true
tags:
    - Swift
    - iOS
    - UIDatePicker
---

`UIDatePicker`를 사용할 일이 있어서 블로그엔 포스팅한 적이 없어서 내용 정리 해봤습니다!

## UIDatePickerStyle
```swift
@available(iOS 13.4, *)
public enum UIDatePickerStyle : Int, @unchecked Sendable {

    
    /// Automatically pick the best style available for the current platform & mode.
    case automatic = 0

    /// Use the wheels (UIPickerView) style. Editing occurs inline.
    case wheels = 1

    /// Use a compact style for the date picker. Editing occurs in an overlay.
    case compact = 2

    /// Use a style for the date picker that allows editing in place.
    @available(iOS 14.0, *)
    case inline = 3
}
```
`UIDatePcikerStyle`은 IOS 13.4부터 사용이 가능하며, 3가지의 종류(`wheels`, `compact`, `inline`(iOS 14이상), automatic은 자동이라 예외)로 나뉩니다.

## 사용법
```swift
let datePicker = UIDatePicker()
datePicker.datePickerMode = .date
datePicker.preferredDatePickerStyle = .wheels
```

`UIDatePickerStyle`은 `preferredDatePickerStyle`를 통해 설정 가능합니다.

날짜에 대한 형식(`datePickerMode`)을 변경하려면 아래 모드를 참조해서 설정하시면 됩니다.
```swift
public enum Mode : Int, @unchecked Sendable {
    case time = 0

    case date = 1

    case dateAndTime = 2

    case countDownTimer = 3
}
```

## wheels
<img src="{{ page.post_assets }}/wheels.png" style="height:400px" /> <br />

## compact
<img src="{{ page.post_assets }}/compact.png" style="height:400px" /> <br />

## inline
<img src="{{ page.post_assets }}/inline.png" style="height:400px" /> <br />

## github 예제
- [https://github.com/JacksonJang/UIDatePickerExample.git](https://github.com/JacksonJang/UIDatePickerExample.git)