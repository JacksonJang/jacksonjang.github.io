---
layout:     post
title:      "[iOS] AVFoundation을 이용해서 바코드 인식 앱 만들기"
subtitle:   " \"Using AVFoundation to make app to detect a barcode\""
date:       2024-03-24 14:00:00
author:     "JacksonJang"
post_assets: "/assets/posts/2024-03-24"
catalog: true
categories:
    - iOS
tags:
    - iOS
    - Swift
    - AVFoundation
    - Barcode
---

## AVFoundation 이란?
> 멀티미디어(카메라, 오디오 재생 및 레코드, 이미지 생성 등)를 처리하기 위한 프레임워크 입니다.

## 만들게 될 바코드 앱 원리
비디오 촬영 기능을 통해 디바이스의 화면에 출력 시키고, 카메라를 통해 바코드를 입력 받아서 바코드의 값을 꺼내쓸 예정입니다.

## 사용되는 클래스 설명
- AVCaptureVideoPreviewLayer : 카메라에서 캡처한 비디오를 실시간으로 보여줄 때 사용, AVCaptureSession 과 함께 사용될 예정입니다.

- AVCaptureSession : 오디오와 비디오 캡처 작업을 관리하는 핵심 클래스, 입력(카메라, 마이크 등)으로부터 데이터를 받아 출력(비디오 등)으로 데이터를 전송하는 역할을 합니다. 해당 클래스로 카메라를 제어할 예정입니다.

- AVCaptureDevice : 디바이스의 장치에서 사용할 기능(예: 비디오, 오디오)를 설정합니다.

- AVCaptureDeviceInput : AVCaptureDevice로 부터 입력 데이터를 받아서 AVCaptureSession으로 전달하는 데 사용되는 클래스입니다.

- AVCaptureMetadataOutput : 캡처된 데이터에서 메타데이터를 추출하는데 사용하는 클래스, 이 객체는 AVCaptureSession에 추가해서 메타데이터가 감지되는 이벤트가 있다.

- AVMetadataObject : 캡처된 미디어에서 메타데이터를(예: 바코드)를 나타내는 객체, 메타데이터의 타입, 위치 등에 대한 정보가 포함되어 있습니다. AVCaptureMetadataOutput 에서 메타데이터를 받아옵니다.

- AVMetadataMachineReadableCodeObject : 메타데이터를 통해 가져온 바코드 정보

- AVCaptureMetadataOutputObjectsDelegate : AVCaptureMetadataOutput 객체가 메타데이터를 객체를 감지했을 때 응답을 제공합니다.

## info.plist 필수!
> AVCaptureDeviceInput 를 사용하면, 아래 권한이 필요해요.
```swift
Privacy - Camera Usage Description
```
따라서, info.plist에서 위 권한 설정을 추가해야만 사용 가능합니다.

# 바코드 구현 시작!

## Status 추가
비디오의 감지 여부를 위해 Status 를 추가합니다.
```swift
enum BarcodeViewStatus {
    case success(code: String)
    case error
}
```

## 완료 처리를 위한 delegate 추가
```swift
protocol BarcodeViewDelegate: AnyObject {
    func complete(status: BarcodeViewStatus)
}
```

## BarcodeView 만들기

### 사용할 메타 데이터 설정
```swift
private let metatdataObjectTypes: [AVMetadataObject.ObjectType] = [.upce, .code39, .code39Mod43, .code93, .code128, .ean8, .ean13, .aztec, .pdf417, .itf14, .dataMatrix, .interleaved2of5, .qr]
```

### 각 필요한 속성 추가
```swift
private var session: AVCaptureSession = AVCaptureSession()
private var videoDevice: AVCaptureDevice? = AVCaptureDevice.default(for: .video)

private lazy var videoPreviewLayer: AVCaptureVideoPreviewLayer = {
    let videoPreviewLayer = AVCaptureVideoPreviewLayer(session: session)
    
    videoPreviewLayer.videoGravity = AVLayerVideoGravity.resizeAspectFill
    
    return videoPreviewLayer
}()

private lazy var captureMetadataOutput: AVCaptureMetadataOutput = {
    let captureMetadataOutput = AVCaptureMetadataOutput()
    
    return captureMetadataOutput
}()
```

### 카메라의 PreviewLayer 크기를 맞추어 줘야 합니다.
따라서, 사용할 UIViewController의 viewDidLayoutSubviews 에 추가해줍시다!
```swift
/**
    Barcode 내에 있는 함수
*/
public func updateUI() {
    videoPreviewLayer.frame = self.frame
}

// MARK: UIViewController 내에서 추가
override func viewDidLayoutSubviews() {
    super.viewDidLayoutSubviews()
    
    barcodeView.updateUI()
}
```

### 아까 선언 해줬던 속성들에 대한 처리

```swift
private func setupCapture() {
    guard let videoDevice = videoDevice,
            let captureDeviceInput = try? AVCaptureDeviceInput(device: videoDevice) 
    else {
        return
    }
    
    // 디바이스 사용할 수 있는지 확인 후 추가
    if self.session.canAddInput(captureDeviceInput) {
        self.session.addInput(captureDeviceInput)
    }
    
    // 메타데이터 사용 가능한지 확인 후 추가
    if self.session.canAddOutput(captureMetadataOutput) {
        self.session.addOutput(captureMetadataOutput)
        
        captureMetadataOutput.metadataObjectTypes = metatdataObjectTypes
        captureMetadataOutput.setMetadataObjectsDelegate(self, queue: DispatchQueue.main)
    }
}
```

### AVCaptureMetadataOutputObjectsDelegate를 이용해서 감지하기
```swift
extension BarcodeView: AVCaptureMetadataOutputObjectsDelegate {
    func metadataOutput(_ output: AVCaptureMetadataOutput, didOutput metadataObjects: [AVMetadataObject], from connection: AVCaptureConnection) {
        
        // 감지 했기 때문에 정지
        stop()
        
        guard let metadata = metadataObjects.first(where: { $0 is AVMetadataMachineReadableCodeObject }) as? AVMetadataMachineReadableCodeObject,
              let code = metadata.stringValue
        else {
            self.delegate?.complete(status: .error)
            return
        }
        
        self.delegate?.complete(status: .success(code: code))
    }
}
```

## github 예시 코드
[https://github.com/JacksonJang/BarcodeExample](https://github.com/JacksonJang/BarcodeExample)
