---
layout:     post
title:      "[iOS] UIImagePickerController vs PHPickerViewController"
subtitle:   "\"iOS UIImagePickerController vs PHPickerViewController\""
date:       2024-05-09 19:00:00
author:     "JacksonJang"
header-img: "assets/posts/post-bg_2024.jpg"
post_assets: "/assets/posts/2024-05-09"
catalog: true
tags:
    - iOS
    - UIImagePickerController
    - PHPickerViewController
---

오늘은 카메라와 앨범 기능을 사용하기 위해 `UIImagePickerController`와 `PHPickerViewController`에 대해 알아보겠습니다.

## UIImagePickerController 사용하기

우선 `UIImagePickerController`를 사용하기 위해서 `info.plist`에 권한에 대한 설명을 함께 추가해야 합니다.
<br />
단, iOS 14미만이라면 **NSPhotoLibraryUsageDescription** 를 추가해야 합니다.(iOS 14이상은 추가할 필요가 없습니다.)

### info.plist
- **NSCameraUsageDescription** : 카메라 접근 권한에 대한 설명
- **NSPhotoLibraryUsageDescription** : 앨범 접근 권한에 대한 설명

밑에는 간단한 예시입니다.

```xml
<key>NSCameraUsageDescription</key>
<string>앱에서 음식 사진을 촬영하기 위해서 카메라 접근이 필요합니다.</string>
<key>NSPhotoLibraryUsageDescription</key>
<string>앱에서 음식 사진을 선택하기 위해 앨범 접근이 필요합니다.</string>
```

## UIImagePickerController는 camera만 사용하자!
왜? 라는 생각이 들 수도 있지만, 사실 이전부터 계속 애플에선 deprecated 상태로 알려왔습니다.

```swift
@available(iOS, introduced: 2, deprecated: 100000, message: "Will be removed in a future release, use PHPicker.")
case photoLibrary = 0

case camera = 1

@available(iOS, introduced: 2, deprecated: 100000, message: "Will be removed in a future release, use PHPicker.")
case savedPhotosAlbum = 2
```

> Will be removed in a future release, use PHPicker.
위 내용은 미래의 배포 버전에서 삭제될 예정이니 `PHPicker`를 사용하라고 말하고 있습니다.

그래서 우리는 `PHPicker`를 사용해야 합니다.

그래도 여전히 카메라는 `UIImagePickerController`를 사용해야 하니 예시를 보여드리겠습니다.

```swift
class ViewController: UIViewController {
    let imagePicker = UIImagePickerController()
    
    @IBOutlet weak var imageView: UIImageView!
    
    override func viewDidLoad() {
        super.viewDidLoad()
        
        imagePicker.delegate = self
    }

    @IBAction func openCamera(_ sender: Any) {
        // 카메라 사용 가능한지 여부 체크
        if UIImagePickerController.isSourceTypeAvailable(.camera) {
            // 카메라 타입 설정
            imagePicker.sourceType = .camera
            present(imagePicker, animated: true, completion: nil)
        } else {
            print("카메라 사용 불가")
        }
    }
}
```

위와 같이 설정 했다면, 아래처럼 `UIImagePickerControllerDelegate`, `UINavigationControllerDelegate` 같이 설정해줘야 합니다.

```swift
extension ViewController: UIImagePickerControllerDelegate, UINavigationControllerDelegate {
    // 사진 선택 완료 했을 때
    func imagePickerController(_ picker: UIImagePickerController, didFinishPickingMediaWithInfo info: [UIImagePickerController.InfoKey : Any]) {
        if let image = info[.originalImage] as? UIImage {
            DispatchQueue.main.async {
                self.imageView.image = image
            }
        }
        picker.dismiss(animated: true, completion: nil)
    }

    // 취소를 클릭 했을 때
    func imagePickerControllerDidCancel(_ picker: UIImagePickerController) {
        picker.dismiss(animated: true, completion: nil)
    }
}
```

자 그럼 이제 `PHPicker`에 대해 알아봅시다!

## PHPickerViewController 사용하기

우선 `PhotosUI` 를 import 해줘야 사용 가능합니다.
```swift
import PhotosUI
```

`PhotosUI`는 구체적으로 PHPicker에 대해 설정할 수 있는 `PHPickerConfiguration`를 제공하고 있습니다.

`PHPickerConfiguration`의 유용한 속성을 통해 다음과 같은 기능을 설정할 수 있습니다.
- **selectionLimit** : 선택할 이미지의 개수
- **filter** : 필터링 할 타입 선택(images, videos, livePhotos 등등)

그 이후에 `PHPickerViewController` 를 사용할 때, 생성자의 파라미터 값으로 사용하면 됩니다.
```swift
 var config = PHPickerConfiguration(photoLibrary: .shared())
// 선택할 이미지의 개수
config.selectionLimit = 1
// 이미지만 선택
config.filter = .images
```

그리고 `PHPickerViewController` 도 `UIImagePickerController`처럼 delegate을 위임해줘야 이후에 처리가 가능합니다.

아래는 간단한 예시입니다.
```swift
class ViewController: UIViewController {
    @IBOutlet weak var imageView: UIImageView!
    
    override func viewDidLoad() {
        super.viewDidLoad()

    }
    
    @IBAction func openAlbum(_ sender: Any) {
        var config = PHPickerConfiguration(photoLibrary: .shared())
        // 선택할 이미지의 개수
        config.selectionLimit = 1
        // 이미지만 선택
        config.filter = .images

        let picker = PHPickerViewController(configuration: config)
        picker.delegate = self
        present(picker, animated: true, completion: nil)
    }
}

extension ViewController: PHPickerViewControllerDelegate {
    func picker(_ picker: PHPickerViewController, didFinishPicking results: [PHPickerResult]) {
        picker.dismiss(animated: true, completion: nil)
        
        let itemProvider = results.first?.itemProvider
        if let itemProvider = itemProvider, itemProvider.canLoadObject(ofClass: UIImage.self) {
            itemProvider.loadObject(ofClass: UIImage.self) { [weak self] image, error in
                DispatchQueue.main.async {
                    if let image = image as? UIImage {
                        self?.imageView.image = image
                    }
                }
            }
        }
    }
}
```

## github 예시코드
- [https://github.com/JacksonJang/ImagePickerExample](https://github.com/JacksonJang/ImagePickerExample)
