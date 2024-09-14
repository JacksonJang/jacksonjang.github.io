---
layout:     post
title:      "[iOS] Tuist 사용하기 (1)"
subtitle:   "\"How to use Tuist? (1)\""
date:       2024-07-31 19:00:00
author:     "JacksonJang"
header-img: "assets/posts/post-bg_2024.jpg"
post_assets: "/assets/posts/2024-07-31"
catalog: true
tags:
    - iOS
    - Tuist
---
### Tuist 주소
[https://github.com/tuist/tuist](https://github.com/tuist/tuist)

## Tuist 란?
```
Tuist is a command line tool that leverages project generation to abstract intricacies of Xcode projects, and uses it as a foundation to help teams maintain and optimize their large modular projects.
```
Tuist는 추상적인 복잡한 Xcode의 프로젝트들을 생성하는 CLI 툴이며, 큰 모듈화된 프로젝트들을 최적화하며 팀의 유지보수 하는데 도움을 줍니다.

간단히 말하면 **Xcode 프로젝트를 관리하는 툴**입니다.

## Tuist의 필요성
협업을 하다보면 **Xcode 프로젝트(프로젝트명.xcodeproj)**가 git 충돌나게 되는데, 이러한 부분을 개선해 주는 게 `Tuist` 입니다

## 본격적으로 Tuist 사용하기
### 이제 더 이상 사용하지 않음
```sh
curl -Ls https://install.tuist.io | bash
```
예전에는 curl 을 통해서 설치 후 사용하였으나, 현재는 **mise**를 통해 사용하고 있습니다.
<br />

관련 주소 : [https://tuist.io/blog/2023/12/15/rtx-default/](https://tuist.io/blog/2023/
12/15/rtx-default/)
<br />

**관련 사진**
<img src="{{ page.post_assets }}/deprecated.png" style="height:200px" /> <br />

## mise 설치
```sh
curl https://mise.run | sh
```

## mise 설치 확인법
```sh
~/.local/bin/mise --version
```

<img src="{{ page.post_assets }}/setup_check.png" style="height:200px" /> 
지금까지 잘 따라오셨다면, 위에처럼 화면이 떴을겁니다.

```sh
echo 'export PATH="$HOME/.local/bin:$PATH"' >> "${ZDOTDIR-$HOME}/.zshrc"
```
이후에 `mise` 명령어를 편하게 사용하기 위해 위에처럼 설정해 주시고~


```sh
mise install tuist
```
mise 를 통해서 `tuist`를 설치하면 됩니다!


```sh
echo 'alias tuist="mise exec -- tuist"' >> "${ZDOTDIR-$HOME}/.zshrc"
```
이후에 `tuist` 명령어를 편하게 사용하기 위해 위에처럼 설정해 주시면 설치는 끝!


### command not found: tuist 혹은 mise 해결법
```sh
source ~/.zshrc
```

그럼 이제 본격적으로 프로젝트 설정을 진행해 볼까요?


## 프로젝트 설정
```sh
mkdir 폴더명
cd 폴더명
```

### Tuist init 방법
```sh
tuist init --platform ios
```
```
mkdir WorkList
cd WorkList
tuist init --platform ios
```
저 같은 경우에는 **WorkList** 라는 프로젝트 이름으로 진행하겠습니다.
<br />
위에처럼 진행했다면, 아래처럼 정상적으로 프로젝트가 생성된 것을 확인할 수 있습니다.
<img src="{{ page.post_assets }}/tuist_folder.png" style="height:200px" /> 

### Tuist 명령어들
```sh
tuist edit # Customize your project manifest
tuist generate # Generates Xcode project & workspace
tuist build # Builds your project
```
[Tuist 주소](#tuist-주소)에서 언급된 명령어입니다.

- `tuist edit` 는 프로젝트의 설정 파일을 편집할 수 있게 해줍니다.
- `tuist generate` 는 설정된 파일을 기반으로 **Derived**, **xcodeproj**, **xcworkspace** 등의 파일을 생성합니다.
- `tuist build` 는 Xcode 를 열지 않은 상태로 빌드합니다.