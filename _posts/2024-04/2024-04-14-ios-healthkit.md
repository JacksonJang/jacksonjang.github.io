---
layout:     post
title:      "[iOS] HealthKit을 사용해 보자!"
subtitle:   "\"Let's use HealthKit in Swift\""
date:       2024-04-14 19:00:00
author:     JacksonJang
post_assets: "/assets/posts/2024-04-14"
catalog: true
categories:
    - iOS
tags:
    - iOS
    - Swift
    - HealthKit
---

요즘 코로나19 팬데믹 시대가 끝을 보이면서 다시 건강과 관련된 피트니스 앱을 통해 마이데이터 앱들이 많이 출시되고 있습니다. 그래서 HealthKit도 점차 많이 사용되고 있어서 HealthKit 프레임워크도 알아보겠다는 마음으로 포스팅 시작합니다.

## 프로젝트 설정
### HealthKit 추가
<img width="600px" src="{{ page.post_assets }}/add-HealthKit.png" />
<br />
**Project Targets -> Signing & Capabilities -> Plus 버튼 클릭 -> HealthKit 선택**

### info.plist 추가
HealthKit을 사용하려면 info.plist에 권한 문구를 추가해야 합니다.
Key : **NSHealthUpdateUsageDescription**
<br />
Value : **문구**
<br />
(예시 : 건강 정보 업데이트 때문에 앱에 대한 권한 요청을 합니다.)

Key : **NSHealthShareUsageDescription**
<br />
Value : **문구**
<br />
(예시 : 건강 정보 공유 때문에 앱에 대한 권한을 요청합니다.)

만약 추가하지 않으면 아래와 같은 에러가 나타납니다.
```swift
*** Terminating app due to uncaught exception 'NSInvalidArgumentException', reason: 'NSHealthUpdateUsageDescription must be set in the app's Info.plist in order to request write authorization for the following types: HKQuantityTypeIdentifierBodyMass'
```
```swift
*** Terminating app due to uncaught exception 'NSInvalidArgumentException', reason: 'NSHealthShareUsageDescription must be set in the app's Info.plist in order to request read authorization for the following types: HKQuantityTypeIdentifierStepCount, HKQuantityTypeIdentifierBodyMass'
```

## 이제 직접 사용해 보자!

### import 우선
당연히 HealthKit을 사용하려면, import를 해야겠죠?
```swift
import HealthKit
```

### 건강 정보 사용 가능한지 확인
```swift
guard HKHealthStore.isHealthDataAvailable() else { return }
```

### HealthKit의 기능 사용하기
```swift
let healthStore = HKHealthStore()
```
제일 먼저 `HKHealthStore`에 대해 알아야 합니다.
<br />
`HKHealthStore`는 건강 데이터를 읽거나 쓸 수 있게 도와주는 클래스이며, 사용하기 전에 권한 요청을 해야 사용 가능합니다.

그렇다면, 권한 설정을 어떻게 하는지 알아보겠습니다.

### HealthKit 사용을 위한 권한 요청
```swift
open func requestAuthorization(toShare typesToShare: Set<HKSampleType>?, read typesToRead: Set<HKObjectType>?, completion: @escaping (Bool, Error?) -> Void)
```
위 코드는 `HKHealthStore`의 내부에 있는 권한 요청 메서드로 `Set<HKSampleType>?` 와 `Set<HKObjectType>?`를 받아서 성공 여부를 나타내는 completion과 함께 사용됩니다.

그렇다면, `HKSampleType`이랑 `HKObjectType`에 대해 알아야겠죠?

### HKSampleType
`HKObjectType`의 서브클래스로, 건강 데이터의 일부분을 시간 기반으로 기록합니다.
```swift
open class HKSampleType : HKObjectType, @unchecked Sendable {}
```

### HKObjectType
`HKObjectType`는 모든 건강 데이터 타입의 베이스 클래스로 최상위 개념으로 생각하시면 됩니다.
```swift
open class HKObjectType : NSObject, NSSecureCoding, NSCopying, @unchecked Sendable {}
```

### HKQuantityType를 예시로 사용하기
`HKQuantityType` : 걸음 수, 칼로리 소모량, 혈당 수치 등 건강 및 피트니스 데이터를 관리하는 데 사용되는 타입입니다.
```swift
open class func quantityType(forIdentifier identifier: HKQuantityTypeIdentifier) -> HKQuantityType?
```
과거에는 HKObjectType의 quantityType 메서드를 사용 했었는데, deprecated이 될 예정이라 아래와 같은 코드로 타입을 지정해서 사용해야 합니다.
```swift
HKQuantityType(.stepCount)
```

### 권한 요청 코드
위 과정들을 모두 통해서 만든 예시입니다.
```swift
// 권한 요청
func requestPermissions(completion: @escaping (Bool) -> Void) {
    guard HKHealthStore.isHealthDataAvailable() else { return }

    let readTypes = Set([
        HKQuantityType(.stepCount)
    ])

    let writeTypes = Set<HKSampleType>()

    healthStore.requestAuthorization(toShare: writeTypes, read: readTypes) { bool, error in
        completion(bool)
    }
}
```

### 전체 걸음 수를 측정해 보자!
```swift
`HKHealthStore`를 이용해서 execute를 통해 전체 걸음 수를 측정해 보겠습니다.

먼저 `HKSampleQuery`의 `init` 부분을 상세히 보겠습니다.
/**
     @method        initWithSampleType:predicate:limit:sortDescriptors:resultsHandler:
     @abstract      Returns a query that will retrieve HKSamples matching the given predicate.
     
     @param         sampleType      샘플 타입
     @param         predicate       조건식
     @param         limit           리턴되는 샘플의 최대 숫자(HKObjectQueryNoLimit 사용하면 제한 없음)
     @param         sortDescriptors 정렬 Descriptors
     @param         resultsHandler  excuting 되면 반환되는 핸들러
     */
    public init(sampleType: HKSampleType, predicate: NSPredicate?, limit: Int, sortDescriptors: [NSSortDescriptor]?, resultsHandler: @escaping (HKSampleQuery, [HKSample]?, Error?) -> Void)
```
위를 보면 **샘플 타입**이 존재합니다.
<br />
**샘플 타입**은 아까 위에서 봤던 [HKQuantityType](#hkquantitytype를-예시로-사용하기)부분을 사용하면 됩니다.

조건식은 따로 지정 안하므로 `nil`로 지정하고, limit은 `HKObjectQueryNoLimit`를 추가해서 제한없이 가져오게 설정해서 `HKSampleQuery`를 만들겠습니다.

아래는 간단한 예시입니다.

```swift
// 걸음 수
func readStepCount(completion: @escaping (Double) -> Void) {
    let stepType = HKQuantityType(.stepCount)
    
    let query = HKSampleQuery(sampleType: stepType, predicate: nil, limit: HKObjectQueryNoLimit, sortDescriptors: nil) { _, samples, _ in
        guard let samples = samples as? [HKQuantitySample] else {
            completion(0)
            return
        }

        // 전체 걸음 수
        let totalSteps = samples.reduce(0.0) { $0 + $1.quantity.doubleValue(for: HKUnit.count()) }
        DispatchQueue.main.async {
            completion(totalSteps)
        }
    }

    // excute를 통해 쿼리 실행
    healthStore.execute(query)
}
```

## github 예제
[https://github.com/JacksonJang/HealthKitExample.git](https://github.com/JacksonJang/HealthKitExample.git)
