---
layout:     post
title:      "[iOS] RxSwift 사용하기(1)"
subtitle:   "\"Let's use RxSwift\""
date:       2024-04-21 19:00:00
author:     "JacksonJang"
header-img: "assets/posts/post-bg_2024.jpg"
post_assets: "/assets/posts/2024-04-21"
catalog: true
tags:
    - Swift
    - RxSwift
    - iOS
---
## RxSwift 란?
> RxSwift is as compositional as the asynchronous work it drives. The core unit is RxSwift itself, while other dependencies can be added for UI Work, testing, and more.

[RxSwift](https://github.com/ReactiveX/RxSwift)는 비동기 작업을 지원하는 만큼 구성 요소를 쉽게 조합할 수 있습니다. 핵심 단위는 RxSwift 자체이며,  UI 작업, 테스팅, 다른 기능을 위해서 는 추가적인 의존성을 사용할 수 있습니다.

### RxSwift 구성 요소
아래와 같이 각 구성 요소는 서로 의존성을 갖고 있습니다.
┌──────────────┐    ┌──────────────┐
│   RxCocoa    ├────▶   RxRelay    │
└───────┬──────┘    └──────┬───────┘
        │                  │        
┌───────▼──────────────────▼───────┐
│             RxSwift              │
└───────▲──────────────────▲───────┘
        │                  │        
┌───────┴──────┐    ┌──────┴───────┐
│    RxTest    │    │  RxBlocking  │
└──────────────┘    └──────────────┘

- RxSwift: 핵심 부분으로 ReactiveX에 의해 정의된 Rx표준을 제공하며 다른 의존성이 없습니다.
- RxCocoa: Cocoa-specific 기능을 제공합니다. RxSwift와 RxRelay에 의존합니다.
- RxRelay: PublishRelay, BehaviorRelay, ReplayRelay와 같은 3가지 간단한 래퍼(Wrapper)를 제공합니다. RxSwift에 의존합니다.
- RxTest: Rx 기반 시스템의 테스트 기능을 제공합니다. RxSwift에 의존합니다.
- RxBlocking: 비동기 코드를 블록 기반으로 테스트할 수 있는 기능을 제공합니다. RxSwift에 의존합니다.

