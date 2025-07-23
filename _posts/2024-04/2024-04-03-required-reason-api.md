---
layout:     post
title:      "[iOS] ITMS-91053: Missing api 해결법 (2024년 5월 1일부터 시행)"
subtitle:   " \"Describing use of required reason API\""
date:       2024-04-03 19:00:00
author:     "JacksonJang"
post_assets: "/assets/posts/2024-04-03"
catalog: true
categories:
    - iOS
tags:
    - iOS
    - Privacy
    - Manifest
---
> 매우 귀찮은 작업임이 분명하다

<img width="600px" src="{{ page.post_assets }}/mail.png" /> <br />
앱을 심사 받으려고 하니까, **ITMS-91053: Missing api declaration**의 장문 메일이 왔었습니다.

[애플의 문서 내용 중 일부](https://developer.apple.com/documentation/bundleresources/privacy_manifest_files/describing_use_of_required_reason_api)
```
If you upload an app to App Store Connect that uses required reason API without describing the reason in its privacy manifest file, Apple sends you an email reminding you to add the reason to the app’s privacy manifest. Starting May 1, 2024, apps that don’t describe their use of required reason API in their privacy manifest file aren’t accepted by App Store Connect.
```

간단히 요약하면 다음과 같습니다.

```
2024년 5월 1일부터 API를 사용하는 이유에 대해 개인정보 매니페스트 파일(Privacy Manifest file)에 설명해야 합니다. 설명하지 않으면 승인되지 않습니다.
```

개인정보 보호를 강화하기 위해 도입 되었으며, 개인정보와 관련된 [required reason API](https://developer.apple.com/documentation/bundleresources/privacy_manifest_files/describing_use_of_required_reason_api)가 있다면 추가해야 합니다.

따라서, **2024년 5월 1일 이후엔 PrivacyInfo.xcprivacy 파일을 사실상 필수적으로 추가해야 합니다.**

이제 어느 정도 필수로 **PrivacyInfo.xcprivacy**를 사용해야 한다는 것을 강조 드린 것 같으니 바로 시작하겠습니다.

## Reason API Scanner 사용하기
어느 무림 고수가 쉘 스크립트를 통해 자동으로 필수 사유 API 를 찾는 스크립트를 만들었습니다.
<br />
이것을 이용해서 간단하게 사용하고 있는 API Type들을 찾을 예정입니다.
<br />
밑에 설명하기에 앞서 이 프로그램으로 먼저 실행해서 돌리면서 차근차근 설명을 보시면 될 것 같습니다.
<br />
**생각보다 스캐너가 오래 걸림**

쉘 스크립트 주소 : [https://github.com/Wooder/ios_17_required_reason_api_scanner](https://github.com/Wooder/ios_17_required_reason_api_scanner)

## Reason API Scanner 간단한 사용 예시
1. [required_reason_api_text_scanner.sh](https://github.com/Wooder/ios_17_required_reason_api_scanner/blob/main/required_reason_api_text_scanner.sh)를 다운 받습니다.
2. 그 이후에 스캔하고자 하는 프로젝트의 루트 폴더에 넣습니다.(xcodeproj 가 있는 폴더)
3. 그리고 아래 명령어를 통해 스캔을 시작합니다.
```shell
sh required_reason_api_text_scanner.sh ./
```
<img src="{{ page.post_assets }}/scanner.png" /> <br />
위 과정을 진행하면 사진과 같이 스캔이 이루어 집니다.
<br />
그럼 이제 스캔하는 동안 자세한 설명을 봅시다!

## PrivacyInfo.xcprivacy 파일 생성하기
<img src="{{ page.post_assets }}/new_privacy.png" /> <br />
프로젝트의 새 파일 추가를 통해 **App Privacy**를 추가합니다.

반드시, 타겟 설정을 진행해 주셔야 합니다.

## [PrivacyInfo.xcprivacy 구성 요소](https://developer.apple.com/documentation/bundleresources/privacy_manifest_files)
- Privacy Tracking Enabled(NSPrivacyTracking) : 앱이나 써드파티 SDK가 추적을 위해 App Tracking Transparency 프레임워크를 사용하는지 여부입니다.
- Privacy Tracking Domains(NSPrivacyTrackingDomains) : SDK가 연결하는 인터넷 도메인의 목록입니다. NSPrivacyTracking 가 true(YES)로 설정 했을 때만 사용합니다.
- Privacy Nutrition Label Types(NSPrivacyCollectedDataTypes) : 앱이나 타사 SDK가 수집하는 데이터 유형을 설명하는 딕셔너리 배열로, 사용자가 자신의 데이터가 어떻게 사용되는지 이해할 수 있도록 합니다.
- Privacy Accessed API Types(NSPrivacyAccessedAPITypes) : 앱이나 타사 SDK가 접근하는 API 유형을 설명하는 딕셔너리 배열입니다.

> 앱이나 사용하는 타사 SDK가 OS, iPadOS, tvOS, visionOS, and watchOS 중 하나에서 작동한다면, NSPrivacyAccessedAPITypes 를 제공해야 합니다.

## API 의 타입에 대해서는 공식 문서에서..
내용이 너무 많기 때문에 간단히 사용하는 방법만 말씀 드렸습니다.
어떤 타입을 넣어야 할지 모르겠다면, 아까 [스캔 했던 것](#reason-api-scanner-간단한-사용-예시)을 살펴보면서 대입하면 됩니다.
[https://developer.apple.com/documentation/bundleresources/privacy_manifest_files/describing_use_of_required_reason_api](https://developer.apple.com/documentation/bundleresources/privacy_manifest_files/describing_use_of_required_reason_api)

밑에는 임시로 적용한 예시입니다. 참고용으로만 확인해 주세요!

## github 예시
[https://github.com/JacksonJang/PrivacyInfoExample.git](https://github.com/JacksonJang/PrivacyInfoExample.git)
