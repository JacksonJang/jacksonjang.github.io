---
layout:     post
title:      "[CS] 네이티브앱 vs 하이브리드앱 vs 웹앱"
subtitle:   "\"Difference between Native app, Hybrid app, Web app\""
date:       2024-04-20 19:00:00
author:     JacksonJang
post_assets: "/assets/posts/2024-04-20"
catalog: true
categories:
    - CS
tags:
    - CS
    - Android
    - iOS
    - Frontend
---
네이티브앱, 하이브리드앱, 웹앱에 대한 개념을 구체적으로 설명하기 위해 포스팅 했습니다.

## 네이티브앱(Native App)
`Android`는 주로 `Java`와 `Kotlin` 언어로 개발되며, `iOS`는 `Objective-C`와 `Swift`를 사용하여 개발된 특정 플랫폼용 운영체제입니다.

다른 방식(하이브리드, 웹)에 비해 성능이 뛰어난 편이며 UI 만드는 것에 있어서도 자유롭습니다. 디바이스의 하드웨어적인 기능들 또한 자유롭게 사용이 가능합니다.

하지만 단점도 분명합니다.
<br />
각 플랫폼마다 별도의 앱을 개발해야 하고 개발 비용과 시간이 맣이 들어갑니다.
<br />
앱을 수정해야 한다면 웹이 아니라서 앱 심사를 거쳐야 하는 단점이 있습니다.

## 웹앱 (Web App)
반면 웹앱은 HTML, CSS, JavaScript 등으로 만들어진 `웹`을 의미합니다. 즉, 별도의 앱을 설치하지 않고 인터넷 브라우저 기반으로 이용할 수 있습니다. 반응형 웹을 만들어 놓으면 운영체제에 상관없이 보여질 수 있어서 네이티브 앱에 비해 비용과 시간이 적은 편입니다.

웹앱도 단점이 있습니다.
<br />
인터넷 연결이 반드시 필요하며 네이티브에서 사용하는 디바이스의 기능 사용에 대해 한계가 분명히 존재합니다.
<br />
또한 운영체제를 신경 쓰지 않아도 되는 단점이 있는 반면 `브라우저`별로 신경 써야 할 수도 있습니다. 예를 들어.. 크롬, 사파리, 파이어폭스 등..

## 하이브리드앱 (Hybrid App)
단순하게 생각하면 `네이티브앱` + `웹앱`의 결합이 `하이브리드앱` 이라고 생각할 수 있습니다.

왜냐하면 네이티브앱처럼 앱을 설치 했으므로 디바이스의 기능을 사용할 수 있을 뿐 아니라 웹으로 만들었기 때문에 `크로스 플랫폼`으로 만들 수 있습니다.
<br />
즉, 한 번의 개발을 통해 Android, iOS 앱을 만들 수 있다는 장점이 있습니다.

하이브리드 앱도 2가지 방식으로 나뉘게 됩니다.
<br />
1. 네이티브앱 안에 단순히 링크를 삽입한 경우
2. React Native, Flutter를 사용하는 경우

수정사항이 생겼을 때, 다음과 같은 차이가 있습니다.
<br />
1번의 경우에는 단순히 연결된 웹을 수정하면 바로 앱에 적용이 되지만,
<br />
2번의 경우에는 네이티브 앱과 똑같이 앱 심사가 필요합니다.

단점으로는 네이티브 앱에 비해 성능이 낮고, 디바이스의 기능을 사용하려면 웹과 호환하는 기능을 수동으로 설정해줘야 하기 때문에 결국 네이티브 언어 학습이 필요하게 됩니다. 안드로이드 같은 경우에는 뒤로가기 버튼에 대한 예외처리도 해줘야 하고.. 해줄 것이 많습니다.

## 결론
제가 실무에서 겪은 기준으로 말씀드리겠습니다.

사실 단정 지을 수 있는 건 없습니다. 프로젝트마다 매 번 다르기 때문이죠..
<br />
규모가 큰 앱을 만든다면 `네이티브 앱`을 규모가 작은 앱이라면 `하이브리드 앱`을 추천해 드립니다.

## 참고자료
- [앱의 종류 : 네이티브 앱 vs 웹 앱 vs 하이브리드 앱](https://blog.hectodata.co.kr/app_kinds)
