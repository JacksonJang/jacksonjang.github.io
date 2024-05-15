---
layout:     post
title:      "[iOS] Core Data 사용하기 (1)"
subtitle:   "\"Let's use Core Data in iOS - 1\""
date:       2024-05-15 15:00:00
author:     "JacksonJang"
header-img: "assets/posts/post-bg_2024.jpg"
post_assets: "/assets/posts/2024-05-15"
catalog: true
tags:
    - iOS
    - CoreData
---

CoreData를 사용할 일이 있어서 공부할 겸 포스팅하게 되었습니다.

## Core Data 프로젝트 생성
<img src="{{ page.post_assets }}/01-project.png" /> <br />
프로젝트를 생성할 떄, 위와 같이 Storage에 `Core Data`를 체크해서 생성해주면 됩니다.
<br />
저는 우선 **CoreDataExample**이라는 이름으로 프로젝트 생성을 진행하겠습니다.

그러면 아래와 같이 정상적으로 생성된 것을 확인할 수 있습니다.
### 프로젝트 구조
<img src="{{ page.post_assets }}/02-project.png" /> <br />

그리고 AppDelegate안에 NSPersistentContainer타입의 `persistentContainer` 변수와 `saveContext()` 함수명이 생성된 것을 확인할 수 있습니다.

SceneDelegate에도 추가되어 있는 것을 확인할 수 있습니다.
```swift
func sceneDidEnterBackground(_ scene: UIScene) {
    // Called as the scene transitions from the foreground to the background.
    // Use this method to save data, release shared resources, and store enough scene-specific state information
    // to restore the scene back to its current state.

    // Save changes in the application's managed object context when the application transitions to the background.
    (UIApplication.shared.delegate as? AppDelegate)?.saveContext()
}
```
위와 같이 백그라운드에 진입 했을 때 `saveContext()`를 통해 저장하는 이유는 데이터의 무결성을 보장하기 위함입니다.

### 만약 이미 생성된 프로젝트라면?
이미 위와 같이 `Core Data` 프로젝트를 생성 했을 때와 동일하게 생성하면 됩니다.

순서대로 말씀드리자면,
<br />
**File** -> **New** -> **File** 을 통해 `Data Model`을 선택해서 **xcdatamodeld** 확장자의 모델을 추가합니다.

이 파일은 [프로젝트 구조](#프로젝트-구조)에서 보았던, 맨 아래에 해당하는 파일입니다. 여기서 실질적인 Core Data 와 관련된 모델에 대한 작업을 진행합니다.

<img src="{{ page.post_assets }}/03-coredata.png" /> <br />
03-coredata.png

## 본격적으로 사용해 보자!
`People`이라는 모델을 생성해서 name과 age를 추가하는 간단한 모델 생성을 진행하곘습니다.
<br />
**xcdatamodeld** 확장자로 생성된 CoreDataExample을 클릭해서 보면 다음과 같은 화면을 볼 수 있습니다.
<img src="{{ page.post_assets }}/04-coredata.png" style="height:400px" /> <br />
그럼 위와 같이 **Add Entity**를 클릭하면

<img src="{{ page.post_assets }}/05-entity.png" /> <br />
 `Entities`안에 새로운 `Entity`가 생성된 것을 확인하실 수 있습니다.

 `Entity` 이름을 `People`로 변경해 주고, Attributes 안에 `name`, `age`를 각각 생성합니다.

### 완성된 People 모델
<img src="{{ page.post_assets }}/06-people-model.png" /> <br />

## Core Data 의 모델 생성
`People` 모델을 생성하기 전에 `People`을 클릭해서 **inspector**를 보면 `Codegen`에 **Class Definition**으로 설정되어 있는 것을 확인할 수 있습니다.

`Codegen`은 다음과 같이 3가지로 분류되어 있습니다.
- Manual/None
- Class Definition
- Category/Extension

이제 하나씩 알아보겠습니다.

### Manual/None
Xcode가 자동으로 Entity에 대해 생성하지 않고, 직접 수동으로 관리합니다.

<img src="{{ page.post_assets }}/07-editor.png" /> <br />
그래서 **Editor** -> **Create NSManagedObject SubClass...**를 통해 CoreData의 모델을 수동으로 생성해야 합니다.

### Class Definition
Entity를 생성하면 기본적으로 설정되는 옵션으로 Xcode에서 자동으로 Entity에 대한 클래스 파일을 생성합니다. 따로 수정이 불가능해서 DerivedData 폴더에 저장됩니다.

### Category/Extension
Xcode로 Build 할 때 class의 extension을 생성합니다. 이 class의 extension은 Entity에 대한 접근자를 포함시킵니다. 따로 수정이 불가능해서 DerivedData 폴더에 저장됩니다.

## Class Definition vs Category/Extension
`Class Definition`와 `Category/Extension`는 공통적으로 Xcode에서 자동으로 관리해 주는 공통점이 있습니다.

`Class Definition`는 자동으로 관리해줘서 간편하지만 구체적인 수정을 할 수 없습니다. 그래서 `Class Definition`으로 설정하고 빌드 했을 때, 별도의 추가 작업을 해주지 않아도 정상적으로 실행됩니다.

각각에 대한 파일 생성되는 폴더는 **DerivedData** 폴더에서 확인 가능합니다.

<img src="{{ page.post_assets }}/08-class.png" /> <br />
그럼 위와 같이 3개의 파일이 생성됩니다.

- CoreDataExample+CoreDataModel.swift
- People+CoreDataClass.swift
- People+CoreDataProperties.swift

### Class Definition 의 파일 내용
```swift
// CoreDataExample+CoreDataModel.swift
import Foundation
import CoreData

// People+CoreDataClass.swift
import Foundation
import CoreData

@objc(People)
public class People: NSManagedObject {

}

// People+CoreDataProperties.swift
import Foundation
import CoreData

extension People {

    @nonobjc public class func fetchRequest() -> NSFetchRequest<People> {
        return NSFetchRequest<People>(entityName: "People")
    }

    @NSManaged public var age: Int16
    @NSManaged public var name: String?

}

extension People : Identifiable {

}
```

`Category/Extension`는 [모델 생성](#완성된-people-모델)에서 작성한 `NSManagedObject` 타입의 클래스가 직접 선언되어야 합니다.
<br />
왜냐하면 class의 extension만 생성하기 때문에 아래처럼 선언해 주어야 정상적으로 실행 가능합니다.

빌드하면 다음과 같은 파일들이 생성되는 것을 확인할 수 있습니다.
<img src="{{ page.post_assets }}/09-extension.png" /> <br />
그럼 위와 같이 3개의 파일이 생성됩니다.

- CoreDataExample+CoreDataModel.swift
- People+CoreDataProperties.swift

혹시 눈치 채셨나요? [Class Definition](#class-definition-의-파일-내용)에서 확인한 것 중에서 **People+CoreDataClass.swift**가 빠진 것을 볼 수 있습니다.

즉, `Category/Extension`에서는 클래스에 대한 관리는 직접 가능하다는 것을 눈치챌 수 있습니다. 파일 내용 또한 동일하지만, `People`에 대한 클래스가 없어서 직접 선언해줘야 합니다.

### Category/Extension 의 파일 내용
```swift
// CoreDataExample+CoreDataModel.swift
import Foundation
import CoreData

// People+CoreDataProperties.swift
import Foundation
import CoreData

extension People {

    @nonobjc public class func fetchRequest() -> NSFetchRequest<People> {
        return NSFetchRequest<People>(entityName: "People")
    }

    @NSManaged public var age: Int16
    @NSManaged public var name: String?

}

extension People : Identifiable {

}
```

## Manual/None 사용
제 경우에는 `Codegen`에 대해서 제대로 공부하지않고, `Class Definition`를 사용하면서 수동으로 `Manual/None` 방식으로 사용하려다가 오류가 발생 했었는데, 저와 같은 오류를 겪지 않길 바라며.. 오류 대처법도 적겠습니다.

<img src="{{ page.post_assets }}/10-manual-error.png" style="height:400px" /> <br />
`Class Definition`으로 설정하고 [Manual/None 모델 생성](#manualnone)하는 방법을 생성하면 위와 같이 정상적으로 생성된 것처럼 보이지만.. 다음과 같은 에러를 마주하실 것 입니다.

<img src="{{ page.post_assets }}/10-manual-error2.png" /> <br />

```sh
Multiple commands produce '/Users/janghyowon/Library/Developer/Xcode/DerivedData/CoreDataExample-gomiinkmygqdemfldcgbicpitgrc/Build/Intermediates.noindex/CoreDataExample.build/Debug-iphonesimulator/CoreDataExample.build/Objects-normal/arm64/People+CoreDataClass.swiftconstvalues'
```

왜냐하면, 위에서 언급한 [Manual/None 모델 생성](#manualnone)은 `수동`이고, **Class Definition**은 `자동`이기 때문에 당연히 발생할 수 밖에 없는 오류입니다.

따라서, 각자의 Codegen 옵션에 대한 선택에 따라 관리해줘야 합니다.

`People` Entity의 Codegen 옵션을 `Manual/None`으로 설정하고 `Clean` -> `Build`를 진행하면 에러가 사라진 모습을 볼 수 있습니다.

[Manual/None 모델 생성](#manualnone)에 대한 설명이 부실하게 느껴질 수 있어서 생성하는 방법도 간단히 올리겠습니다.

**Editor** -> **Create NSManagedObject SubClass...**를 통해 클릭했다면 다음과 같은 화면을 마주칠 수 있습니다.
<img src="{{ page.post_assets }}/11-manual.png" style="height:400px" /> <br />
Next를 누르시고..(추가를 원하는 Core Data)

<img src="{{ page.post_assets }}/12-select-model.png" style="height:400px" /> <br />
Next를 누르시면..(추가를 원하는 Entity 설정)

<img src="{{ page.post_assets }}/13-model-location.png" style="height:400px" /> <br />
위와 같이 추가할 경로에 추가할 수 있습니다.


<img src="{{ page.post_assets }}/14-build-complete.png" style="height:400px" /> <br />
그러면 위와 같이 빌드 성공을 할 수 있습니다!


~~금방 끝날 것 같았는데 꽤 길어졌네요ㅠ~~