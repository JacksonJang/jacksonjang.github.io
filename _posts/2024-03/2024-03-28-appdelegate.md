---
layout:     post
title:      "[iOS] AppDelegate 란?"
subtitle:   " \"What's the AppDelegate?\""
date:       2024-03-28 05:00:00
author:     JacksonJang
post_assets: "/assets/posts/2024-03-28"
catalog: true
categories:
    - iOS
tags:
    - iOS
    - Swift
---

## AppDelegate 역할
`AppDelegate`는 단어 그대로 `App` + `Delegate`로 앱이 해야할 일을 대신 구현한다는 의미이며, 앱의 시작부터 종료까지 다양한 라이프 사이클을 관리하고 있습니다.

그럼 프로젝트를 생성하면 기본적으로 생성되는 메서드들을 하나씩 알아보겠습니다.

## [application(_:didFinishLaunchingWithOptions:)](https://developer.apple.com/documentation/uikit/uiapplicationdelegate/1622921-application)
```
Tells the delegate that the launch process is almost done and the app is almost ready to run.
```
앱이 거의 시작되기 직전에 호출됩니다. 파이어베이스나 앱의 기본 설정들을 설정할 때, 이곳에서 설정해 주면 됩니다.
<br />
```swift
func application(_ application: UIApplication,
didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?)
-> Bool {
    return true
}

```
return 값은 앱의 실행 준비가 마무리되었다는 값인데, true로 고정해서 사용하는 걸 권장합니다. false로 해도 앱은 종료되진 않지만, 예외적으로 앱이 실행되지 않았음을 처리하는 것은 따로 UI로 보여주는 등 예외 처리를 해주는 게 좋습니다.

## [application(_:configurationForConnecting:options:)](https://developer.apple.com/documentation/uikit/uiapplicationdelegate/3197905-application)
scene이 생성되는 것을 관리하는 데 사용됩니다. iOS 13.0 이상부터 생긴 메서드로 `UIApplicationDelegate`에 정의되어 있습니다.

주로, iPadOS와 macOS에서 여러 창을 관리할 때 사용됩니다.

```swift
func application(_ application: UIApplication, 
configurationForConnecting connectingSceneSession: UISceneSession, 
options: UIScene.ConnectionOptions) 
-> UISceneConfiguration {
    return UISceneConfiguration(name: "Default Configuration", sessionRole: connectingSceneSession.role)
}
```

위 코드에서 `Default Configuration`는 어디서 설정 되는지 알아보았는데, 이건 info.plist에서 설정할 수 있습니다.
<br />
<img src="{{ page.post_assets }}/AppDelegate-config.png">


## [application(_:didDiscardSceneSessions:)](https://developer.apple.com/documentation/uikit/uiapplicationdelegate/3197906-application)
scene이 폐기되는 것을 관리하는 데 사용됩니다. iOS 13.0 이상부터 생긴 메서드로 `UIApplicationDelegate`에 정의되어 있습니다.

```swift
func application(_ application: UIApplication, 
didDiscardSceneSessions sceneSessions: Set<UISceneSession>) { }
```
