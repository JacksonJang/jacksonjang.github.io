---
layout:     post
title:      "[iOS] SceneDelegate 란?"
subtitle:   " \"What's the SceneDelegate?\""
date:       2024-04-01 19:00:00
author:     JacksonJang
post_assets: "/assets/posts/2024-04-01"
catalog: true
categories:
    - iOS
tags:
    - iOS
    - Swift
---

## iOS 12에서의 AppDelegate
기존 iOS 12에서는 아래와 같이 AppDelegate에서 Process Lifecycle과 UI Lifecycle을 모두 담당 했습니다. 즉, 앱의 시작부터 종료까지 모든 생명주기를 담당 했는데... iOS 13에서는 AppDelegate도 분업이라는 것을 하기 시작합니다.
<br />
<img src="{{ page.post_assets }}/iOS12.png" />

## AppDelegate에 대한 설명
[https://jacksonjang.github.io/2024/03/29/appdelegate-lifecycle/](https://jacksonjang.github.io/2024/03/29/appdelegate-lifecycle/)

## iOS 13에서 화성처럼 등장한 SceneDelegate
<img src="{{ page.post_assets }}/iOS13.png" />
<br />
iOS 13에서 `SceneDelegate` 라는 친구가 등장했습니다.
<p />
이 친구는 AppDelegate에서 관리 했었던 UI Lifecycle 역할을 뺏어와서 하나의 앱에서 여러 개의 UI 인스턴스(window)를 동시에 사용할 수 있게 되었습니다.

UI Lifecycle을 SceneDelegate에서 관리하니 당연히 포그라운드( `sceneWillEnterForeground(_:)`)와 백그라운드(`sceneDidEnterBackground(_:)`)를 SceneDelegate에서 담당하겠죠?

## [scene(_:willConnectTo:options:)](https://developer.apple.com/documentation/uikit/uiscenedelegate/3197914-scene)
Scene이 생성되고 초기 UI 설정이 필요할 때 호출됩니다.

```swift
func scene(_ scene: UIScene, willConnectTo session: UISceneSession, options connectionOptions: UIScene.ConnectionOptions) {
    // Use this method to optionally configure and attach the UIWindow `window` to the provided UIWindowScene `scene`.
    // If using a storyboard, the `window` property will automatically be initialized and attached to the scene.
    // This delegate does not imply the connecting scene or session are new (see `application:configurationForConnectingSceneSession` instead).
    guard let _ = (scene as? UIWindowScene) else { return }
}
```

처음 프로젝트를 생성하고, SceneDelegate으로 진입해서 보면 위와 같이 되어 있는 것을 확인할 수 있습니다. 만약 Storyboard 로 처음 뷰를 시작하는게 아니라면, 위에서 다음과 같은 방법으로 새로운 윈도우를 통해 실행시킬 수 있습니다.

```swift
func scene(_ scene: UIScene, willConnectTo session: UISceneSession, options connectionOptions: UIScene.ConnectionOptions) {
    guard let windowScene = (scene as? UIWindowScene) else { return }
    self.window = UIWindow(windowScene: windowScene)
    self.window?.rootViewController = ViewController()
    self.window?.makeKeyAndVisible()
}
```

## [sceneWillEnterForeground(_:)](https://developer.apple.com/documentation/uikit/uiscenedelegate/3197918-scenewillenterforeground)
해당 메서드는 포그라운드 상태로 진입 했을 때 호출됩니다.


## [sceneDidEnterBackground(_:)](https://developer.apple.com/documentation/uikit/uiscenedelegate/3197917-scenedidenterbackground)
해당 메서드는 백그라운드 상태로 진입 했을 때 호출됩니다.

## 그 이외의 메서드들
나머지 메서드들은 간단한 설명만 하고 넘어가겠습니다.

### sceneDidBecomeActive(_:)
Scene이 활성 상태가 되었을 때 호출합니다.

### sceneWillResignActive(_:)
Scene이 활성 상태가 아닐 때 호출됩니다.

### sceneDidDisconnect(_:)
Scene이 해제될 때 호출됩니다.
