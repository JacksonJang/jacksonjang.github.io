---
layout:     post
title:      "[iOS] Keychain으로 저장해보자! (with. Security)"
subtitle:   " \"Let's save it with Keychain! (with. Security)\""
date:       2024-03-19 19:30:00
author:     "JacksonJang"
post_assets: "/assets/posts/2024-03-19"
catalog: true
categories:
    - iOS
tags:
    - iOS
    - Swift
    - Security
    - Keychain
---

> Keychain에 대해서 이해하는 것이 중요!

## Keychain 정의
Keychain은 비밀번호나 인증 토큰과 같은 민감한 정보를 안전하게 저장할 수 있게 도와주는 Security 프레임워크의 기능입니다.
<br />
Apple Document : [https://developer.apple.com/documentation/security/keychain_services](https://developer.apple.com/documentation/security/keychain_services/)

> 참고로 Keychain은 앱을 삭제해도 유지되는 값이므로, 앱 설계를 하실 때 매우 신중하게 선택해서 진행해 주셔야 합니다.

## Keychain 저장
1. 저장할 데이터 설정을 합니다.
- kSecClass 는 다양한 종류가 있지만, 여기서는 일반적인 비밀번호 항목인 kSecClassGenericPassword 로 가정해서 사용하겠습니다.
- kSecAttrAccount : 저장할 계정 및 아이디
- kSecValueData : 비밀번호
```swift
let query: [String: Any] = [
    kSecClass as String: kSecClassGenericPassword,
    kSecAttrAccount as String: account,
    kSecValueData as String: password
]
```

2. 이전 데이터 삭제
- 중복 저장을 피하기 위해서 이전에 똑같은 데이터를 삭제합니다.(안해도 상관 없지만, 중복 저장되면 골치 아파서 무조건 해야됨)
```swift
SecItemDelete(query as CFDictionary)
```

3. 데이터 저장
- 여기서 실제 Keychain 저장을 합니다.
SecItemAdd(query as CFDictionary, nil)

## Keychain 조회
1. 조회할 데이터 설정을 합니다.
- kSecClass : 아까 저장할 때 설정했던 kSecClassGenericPassword 를 입력해 줍시다.
- kSecAttrAccount : 저장할 계정 및 아이디
- kSecMatchLimit : 검색 쿼리가 반환할 결과의 수를 제한하는 데 사용 되는데, 우리는 한 건에 대해서만 받아올 예정이니 kSecMatchLimitOne 를 사용해 줍시다.
(다른 속성도 많은데 kSecMatchLimitAll 도 쓸 수 있습니다.)
- kSecReturnData : Data로 반환 받을지 설정
```swift
let query: [String: Any] = [
    kSecClass as String: kSecClassGenericPassword,
    kSecAttrAccount as String: account.data(using: .utf8)!,
    kSecMatchLimit as String: kSecMatchLimitOne,
    kSecReturnData as String: true
]
```

2. 받아올 변수 선언
```swift
var item: CFTypeRef?
```

3. 데이터 조회
```swift
let status = SecItemCopyMatching(query as CFDictionary, &item)
```

## Keychain 저장 및 조회 예시
이론보다는 역시 실습이 최고겠죠?

저 같은 경우에는 Storyboard 예시가 아닌, code based 로 간단한 예시를 만들었습니다.
따라서, 직접 사용하게 되실 때 적절히 입맛에 맞게 사용하시면 될 것 같습니다.

```swift
// 키체인을 이용한 저장
@objc func addToKeychain() {
    guard let accountText = self.accountTextField.text,
        let passwordText = self.passwordTextField.text
    else {
        return
    }
    let account = accountText.data(using: .utf8)!
    let password = passwordText.data(using: .utf8)!
    let query: [String: Any] = [
        kSecClass as String: kSecClassGenericPassword,
        kSecAttrAccount as String: account,
        kSecValueData as String: password
    ]

    // 이전 항목 삭제
    SecItemDelete(query as CFDictionary)

    // 새 항목 추가
    let status = SecItemAdd(query as CFDictionary, nil)
    if status != errSecSuccess {
        if let errorMessage = SecCopyErrorMessageString(status, nil) {
            print("Add to keychain failed: \(errorMessage)")
        }
    }
}

// 키체인을 이용한 조회
@objc func getFromKeychain(){
    guard let accountText = self.accountTextField.text else {
        return
    }
    let query: [String: Any] = [
        kSecClass as String: kSecClassGenericPassword,
        kSecAttrAccount as String: accountText.data(using: .utf8)!,
        kSecMatchLimit as String: kSecMatchLimitOne,
        kSecReturnData as String: true
    ]

    var item: CFTypeRef?
    let status = SecItemCopyMatching(query as CFDictionary, &item)
    if status == errSecSuccess, 
    let data = item as? Data, 
    let password = String(data: data, encoding: .utf8) {
        self.resultLabel.text = password
    } else {
        if let errorMessage = SecCopyErrorMessageString(status, nil) {
            print("키체인 조회 시: \(errorMessage)")
        }
        self.resultLabel.text = ""
    }
}
```

## github 예시 주소
[https://github.com/JacksonJang/KeychainExample](https://github.com/JacksonJang/KeychainExample)
