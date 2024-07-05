---
layout:     post
title:      "[iOS] Localization 사용해서 글로벌 앱 만들기"
subtitle:   " \"Using Localization to make a global app\""
date:       2024-04-02 19:00:00
author:     "JacksonJang"
header-img: "assets/posts/post-bg_2024.jpg"
post_assets: "/assets/posts/2024-04-02"
catalog: true
tags:
    - iOS
    - Swift
    - Localization
---
> Xcode 15 이상에서는 문자열 카탈로그가 문자열을 현지화하는 데 권장되는 방법입니다.
> ([애플 문서 내용 중 일부](https://developer.apple.com/localization/))

Localization 기능은 글로벌 앱을 만들기 위해서 필수적으로 존재해야 하는 중요한 기능입니다.

오늘은 Xcode 15 이상에서 사용할 수 있는 stringsdict 와 이전부터 전통적으로 사용해왔던 strings의 사용법에 대해 알아보겠습니다.

<img src="{{ page.post_assets }}/a-2.png" />
Xcode 15가 출시되면서 구분되어 생성할 수 있게 바뀌었습니다.

<img style="width:200px;" src="{{ page.post_assets }}/a-1.png" />

이제부터 strngdict, strings를 사용해서 글로벌 앱을 만들어 보겠습니다.

## 시작 전 TIP : 사용하는 언어 변경해서 디버깅하기
<img src="{{ page.post_assets }}/common-1.png" /> <br />
상단의 "Edit Scheme"을 클릭해서, 스키마 설정 화면으로 이동합니다.

<img src="{{ page.post_assets }}/common-2.png" /> <br />
**Run** -> **Options** -> **App Language** 를 통해 내가 사용하는 언어에 대해 설정이 가능합니다.

> Localizable.strings 와 Localizable.stringdict 는 중복해서 사용할 수 없습니다. <br />
> 한마디로 **같은 이름의 Localizable**을 사용할 수 없습니다.

# [stringdict (Xcode 15 이상)](https://developer.apple.com/documentation/xcode/localizing-and-varying-text-with-a-string-catalog)

애플 공식 문서에서도 설명이 잘 되어 있어서 공식 문서의 내용의 일부분을 가져와서 보여드리겠습니다.

<img src="{{ page.post_assets }}/localize-1.png" /> <br />
이전에는 Strings File을 이용했었지만 **(Legacy)** 가 붙은 것처럼 이제는 **String Catalog** 를 사용하는 것을 권장합니다.

아무튼 **String Catalog**를 "Localizable" 이름으로 새로 생성합니다.

## 언어 추가
<img src="{{ page.post_assets }}/localize-2.png" /> <br />

그럼 위와 같이 English와 같은 언어가 생성됩니다.
<br />
**+ 버튼**을 통해 새로운 언어 추가가 가능합니다.
저는 한국인이니 Korean을 추가하겠습니다.
<p />
[Xcode 15이전](#strings-xcode-15-이전)을 보면, Project 탭에서 Info 탭을 선택해서 + 버튼을 눌러서 지원할 언어를 수동으로 추가해야 했지만, 이제는 자동으로 추가됩니다.

## 간단한 예시
```swift
Xcode15 and later
```
위에 **Xcode15 and later** 가 Localization의 Key 라고 가정하겠습니다.

<img src="{{ page.post_assets }}/localize-3.png" /> <br />
그럼 위와 같이 설정할 수 있습니다.

<p />
간단히 설명하자면 다음과 같습니다.(**참고로 Key는 다른 이름으로 설정해도 됩니다.**)
<br />
- Key : Xcode15 and later
- en : Xcode15 and later
- ko : Xcode15 이후

```swift
String(localized: String.LocalizationValue("Xcode15 and later"))
```
그럼 Key 값이 **Xcode15 and later** 이니까, 언어가 영어라면 "Xcode15 and later", 한국어라면 "Xcode15 이후"로 보여지게 됩니다.

## Int 값과 함께 사용하기
```swift
%lld
```
위와 같은 형식을 통해 간단한 예시를 보겠습니다.

Key 값이 **%lld Test**이고, ko 를 **%lld 테스트**로 설정 했다고 가정하겠습니다.

그럼 아래와 같은 코드를 입력하면 다음과 같은 결과 값을 얻을 수 있습니다.
```swift
String(localized: String.LocalizationValue("\(123) Test"))
// 결과값 : 123 테스트"
```

그치만, 저 같은 경우는 String 형태로 해도 되지 않을까? 해서 아래와 같이 테스트 해봤는데... 결과는 안됐었다
```swift
String(localized: String.LocalizationValue("123 Test"))
// 결과값 : 123 Test
// 참고로 결과값은 Key 값이 그대로 보여진 것이다. 제대로 되었다면, 한글이 보여져야함
```

<img src="{{ page.post_assets }}/localize-4.png" /> <br />
> 아래와 같은 코드(NSLocalizedString)를 이용해서 컴파일 후 실행하게 되면 자동으로 Catalog에 입력이 됩니다.
> 따라서, 이전에 NSLocalizedString를 사용했었다면 하나의 카탈로그에서 관리할 수 있다.
>
> NSLocalizedString("Xcode before code", comment: "이것은 코드에서 사용하는 방법입니다.")

# strings (Xcode 15 이전)
## lproj 생성
<img src="{{ page.post_assets }}/legacy-1.png" />
**Project** 탭에서 **Info** 탭을 선택해서 **Localizations** 에서 + 버튼을 눌러서 지원할 언어를 추가합니다.

<img style="width:500px;" src="{{ page.post_assets }}/legacy-2.png" />
저 같은 경우에는 Korean을 선택했습니다.

<img src="{{ page.post_assets }}/legacy-3.png" />
Korean 을 누르면 위와 같이 적용할 파일을 눌러줍니다.

<img src="{{ page.post_assets }}/legacy-4.png" />
그러면 Proejct 루트 폴더에 선택한 언어의 lproj가 생성됩니다.

<img src="{{ page.post_assets }}/legacy-5.png" />
생성된 것을 확인하면, **Localizations** 에서 **Set Default** 를 클릭해서 사용하는 언어로 기본 설정합니다.

## 스토리보드 Localization 설정
<img style="width:300px;" src="{{ page.post_assets }}/legacy-6.png" />
스토리보드를 클릭하면 **Localization** 영역이 보이는데, 여기서 생성된 **Korean**과 **English**를 눌러줍니다.

<img src="{{ page.post_assets }}/legacy-7.png" />
그럼 위와 같이 Main.storyboard 안에 Korean과 English가 생긴 것을 확인하실 수 있습니다.

## Localization 설정하기(Storyboard 편)
> 나중에 관리하기 힘들어서 권장하지 않는 방법입니다.
UILabel(Xcode15 before)의 Object-id 를 먼저 확인해야 합니다.

<img style="width:300px;" src="{{ page.post_assets }}/legacy-8.png" />
**RJf-Dt-NCI** 인 것을 확인 했으니, Main 스토리보드 안에 있는 Main (Korean), Main (English) 파일을 각각 수정합니다.

### Main (Korean)
```none
"RJf-Dt-NCI.text" = "Xcode15 이전";
```
### Main (English)
```none
"RJf-Dt-NCI.text" = "Xcode15 before";
```

## In-Code Localization 설정
<img src="{{ page.post_assets }}/legacy-9.png" />
**Strings File(Legacy)**를 클릭해서 "Localizable"이라는 이름으로 생성합니다.

<img style="width:300px;" src="{{ page.post_assets }}/legacy-10.png" />
**Localize..**를 클릭합니다.

<img style="width:300px;" src="{{ page.post_assets }}/legacy-11.png" />
사용할 언어에 대해 설정합니다.

<img style="width:300px;" src="{{ page.post_assets }}/legacy-12.png" />
Korean, English 둘 다 선택합니다.

그 이후에, Localizable을 보면 Storyboard와 같이 Korean과 English로 나뉘어져 있는 것을 볼 수 있습니다.

[스토리 보드 방식](#main-korean)과 동일하게 입력해 주고(단, object-id가 필요 없음), NSLocalizedString 를 이용해서 텍스트 내용을 가져오면 됩니다.

### Main (Korean)
```none
"Xcode before code" = "Xcode 이전(코드)";
```
### Main (English)
```none
"Xcode before code" = "Xcode before(Code)";
```

### NSLocalizedString 예시
```swift
NSLocalizedString("Xcode before code", comment: "이것은 코드에서 사용하는 방법입니다.")
```

만약, Localizable.strings 의 파일 이름을 변경 했다면, 아래와 같이 사용 가능합니다.
> Localizable 을 Localizable_legacy 로 변경했다.

```swift
NSLocalizedString("Xcode before code", tableName: "Localizable_legacy", comment: "이것은 코드에서 사용하는 방법입니다.")
```

## github 예시
[https://github.com/JacksonJang/ios-localization.git](https://github.com/JacksonJang/ios-localization.git)