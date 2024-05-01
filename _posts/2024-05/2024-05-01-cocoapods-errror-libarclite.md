---
layout:     post
title:      "[iOS] SDK does not contain 'libarclite' at the path 에러"
subtitle:   "\"Error : SDK does not contain 'libarclite' at the path' \""
date:       2024-05-01 19:00:00
author:     "JacksonJang"
header-img: "assets/posts/post-bg_2024.jpg"
post_assets: "/assets/posts/2024-05-01"
catalog: true
tags:
    - Xcode
    - iOS
    - Cocoapods
---

## 에러
코코아 팟을 이용해서 Podfile에 라이브러리를 추가하고 프로젝트를 실행 했을 때 다음과 같은 에러가 뜰 때 해결법을 공유하겠습니다!

```swift
clang: error: SDK does not contain 'libarclite' at the path '/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/lib/arc/libarclite_iphoneos.a'; try increasing the minimum deployment target
```

## 해결법
Podfile 최하단에 추가하고 `pod install`을 다시 하시면 됩니다.

```swift
post_install do |installer|
  installer.pods_project.targets.each do |target|
    target.build_configurations.each do |config|
      config.build_settings['IPHONEOS_DEPLOYMENT_TARGET'] = '14.0'
    end
  end
end
```

## 예시
```swift
# Uncomment the next line to define a global platform for your project
platform :ios, '14.0'

target 'TestProject' do
  # Comment the next line if you don't want to use dynamic frameworks
  use_frameworks!

  # Pods for TestProject
  pod 'RxSwift'
  pod 'SnapKit'
  pod 'FSCalendar'

end

post_install do |installer|
  installer.pods_project.targets.each do |target|
    target.build_configurations.each do |config|
      config.build_settings['IPHONEOS_DEPLOYMENT_TARGET'] = '14.0'
    end
  end
end
```