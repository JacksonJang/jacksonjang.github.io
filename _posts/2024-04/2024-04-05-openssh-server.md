---
layout:     post
title:      "[Linux] openssh-server 란?"
subtitle:   " \"What's the openssh-server?'\""
date:       2024-04-05 19:00:00
author:     "JacksonJang"
header-img: "assets/posts/post-bg_2024.jpg"
post_assets: "/assets/posts/2024-04-05"
catalog: true
tags:
    - Linux
    - Ubuntu
---
> Ubuntu 20 버전 기준으로 작성되었습니다.

요즘 회사 홈페이지 제작을 하면서 서버 세팅이 필요한 일이 생겼다. 그래서 오늘 회사에서 데스크톱을 이용해서 공용으로 사용할 서버 컴퓨터를 사용하기 위해 서버 구축을 진행하게 되었다. 

AWS나 NHN Cloud를 사용해도 되었지만, 내부 개발 사이트용으로만 사용할 것이라 이런 방식으로 진행했습니다.

우선 SSH 부터 간단히 알아보겠습니다.

## SSH 란?
`Secure Shell`의 약자로 네트워크 상에서 원격지 호스트 컴퓨터에 접속하기 위해 사용되는 인터넷 프로토콜 입니다. 기본 포트는 `22`로 사용하고 있습니다.

### SSH 접속 방법
```shell
ssh [원격 계정]@[원격지 ip] -p [포트번호]
```

### 접속 예시
```shell
ssh jacksonjang@127.0.0.1 -p 22
```

## Ubuntu에서 openssh-server 사용하기

### OpenSSH 란?
> Secure Shell Protocol을 이용하여 암호화된 통신 세션을 컴퓨터 네트워크에 제공하는 컴퓨터 프로그램의 모임입니다.

openssh-server를 설치하게 되면 다른 곳에서 ssh 프로토콜을 통해 원격지 컴퓨터에 접속할 수 있게 됩니다.

### openssh-server 설치하기
```shell
sudo apt update
sudo apt install openssh-server
```

위와 같이 apt update를 통해 패키지를 업데이트 해주고 나서, openssh-server를 설치합니다.

설치가 완료되면, SSH 서비스가 **자동으로 실행**됩니다.
그러면 이제 제대로 서비스가 실행 됐는지 확인이 필요한데..

### SSH 서비스 확인
```shell
sudo systemctl status ssh
```

위와 같은 명령어를 통해 실행 됐는지 확인할 수 있다!

그 외의 기능들도 나열하겠습니다.

### SSH 서비스 중지
```shell
sudo systemctl stop ssh
```

### SSH 서비스 비활성화
```shell
sudo systemctl disable ssh
```

> 중지는 말 그대로 중지되지만 재부팅 하게되면 다시 실행되고, 비활성화를 하면 완전히 비활성화돼서 사용도 못하고 재부팅 해도 다시 시작되지 않습니다.

### SSH 서비스 시작
```shell
sudo systemctl start ssh
```

### SSH 서비스 재시작
```shell
sudo systemctl restart ssh
```

