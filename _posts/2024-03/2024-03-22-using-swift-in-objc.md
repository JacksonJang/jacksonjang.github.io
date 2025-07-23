---
layout:     post
title:      "[iOS] Objective-C, Swift 서로 사용하기"
subtitle:   " \"Using Swift and Objective-C each other\""
date:       2024-03-22 19:30:00
author:     "JacksonJang"
post_assets: "/assets/posts/2024-03-22"
catalog: true
categories:
    - iOS
tags:
    - iOS
    - Swift
    - Objective-C
---

실무에서 모든 프로젝트가 Swift 언어로 되어 있으면 얼마나 편했을까? 라는 생각이 들 때가 있다.
<br />
왜냐하면, 많은 곳에서 Objective-C를 사용하는 프로젝트가 있기 때문이다!
<br />
(Swift에 관심 없는 Objc 개발자도 있기 때문)

만약 Swift는 잘 다루고 Objective-C는 잘 다루지 못하고 이해만 가능한 상황이라면, Swift로 만들어서 Objective-C로 사용하면 된다! (제일 좋은건 둘다 잘 다루는 것이지만..)

## Xcode 프로젝트 설정
Swift에서 Objective-C를 사용하든, Objective-C에서 Swift를 사용하든 어찌 되었든 **Xcode 내에서 Bridging-Header 설정**을 해야 합니다.
<br />
다음과 같이 2가지 방법으로 설정 할 수 있습니다.
<br />
**개인적으로 저는 1번 방법을 추천합니다.**
1. Xcode 내에서 프로젝트에 직접 파일(Swift or Objective-C)을 생성하면 아래와 같은 화면이 나옵니다.
<br />
<img src="{{ page.post_assets }}/bridge-header.png">
<br />
여기서 **Create Bridging Header** 버튼을 클릭해 줍니다.
<br />
그러면 자동으로 헤더 생성과 설정이 이루어 집니다.
<br />
<br />
2. Xcode 프로젝트에 수동 설정
1번과 같이 헤더가 뜨지 않는다면 수동으로 설정해야 합니다.
<br />
아래와 같은 순서로 진행하시면 됩니다.
- 프로젝트 내에서 Header File로 생성 후 이름을 **프로젝트명-Bridging-Header** 으로 설정합니다.
- 그 후에 **Build Settings** 에서 Swift Compiler 를 검색해서 Objective-C Bridging Header에 생성된 Header File의 경로를 넣어주면 설정이 끝납니다.
<br />
<img src="{{ page.post_assets}}/Build-Settings.png">

## Objective-C 에서 Swift 실행
```none
#import "프로젝트명-Swift.h"
```
위와 같이 import를 먼저 해줘야 Swift를 사용할 수 있습니다.
<br />
그렇다면, **프로젝트명-Swift.h**는 갑자기 어디서 나왔을까?
사실 위에 있는 2번 사진을 자세히 보면 **Generated Header Name**을 보면 **프로젝트명-Swift.h** 으로 설정되어 있는 것을 볼 수 있다. 
> 따라서, 설정된 Generated Header Name 을 import 해서 사용하면 된다.

하지만, import 를 해도 여전히 Swift를 사용할 수 없을 것이다.
<br />
왜냐하면 아직 Swift에서 @objc를 설정해주지 않았기 때문이다!

따라서, 아래와 같이 사용할 곳에 @objc를 붙여주면 된다.
```swift
@objc class SwiftExample: NSObject {
    @objc func print() {
        Swift.print("SwiftExample 테스트")
    }
}
```

### 완성 예시
```none
#import "ViewController.h"
#import "ObjectiveCExample-Swift.h"

@interface ViewController ()

@end

@implementation ViewController

- (void)viewDidLoad {
    [super viewDidLoad];
    
    SwiftExample *example = [[SwiftExample alloc] init];
    [example print];
}

@end
```

## Swift 에서 Objective-C 실행
Objective-C 에서 Swift를 사용 했다면, 이번에는 반대로 해볼 예정이다.

Objective-C 를 사용하려면, 위에서 만든 [Briding Header](#xcode-프로젝트-설정)를 사용해야 한다.
<br />
다음과 같이 Header.h 안에 사용할 Objective-C 파일을 넣어주면 됩니다!
```none
#import "헤더파일.h"
```

### 예시
```none
#import "ViewController.h"
```

## 예시 GitHub
[https://github.com/JacksonJang/ObjectiveCExample](https://github.com/JacksonJang/ObjectiveCExample)
