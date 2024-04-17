---
layout:     post
title:      "[Linux] sudo: /usr/bin/sudo must be owned by uid 0 and have the setuid bit set 에러 해결법"
subtitle:   " \"How to solve sudo: /usr/bin/sudo must be owned by uid 0 and have the setuid bit set?\""
date:       2024-04-06 12:00:00
author:     "JacksonJang"
header-img: "assets/posts/post-bg_2024.jpg"
post_assets: "/assets/posts/2024-04-06"
catalog: true
tags:
    - Linux
---
> Ubuntu 20 버전을 사용하고 있습니다.

난 오늘 실수로 sudo chmod 777 /usr/bin/ 을 통해 sudo 권한을 강제로 바꿔버려서 제목과 같은 에러를 겪어 버렸습니다..
매우매우 치명적인 실수라 처음부터 다시 설치할까 싶었지만, 이 에러를 해결할 수 있을까 라는 생각이 들어서 직접 해결해
보기로 했습니다.

방법을 찾아보니 Ubuntu 설치가 가능한 부팅 USB가 필요했었습니다.
다행히 설치할 때 포함된 Ubuntu USB가 있어서 굳이 따로 준비하진 않았습니다.

## Ubuntu USB 부팅 시작(설치화면 접근)
Ubuntu USB 부팅을 시작하면 "GNU GRUB" 화면에서 ubuntu, ubuntu(safe graphics), OEM install 등이 뜨게 되는데, ubuntu를 클릭해서 설치 화면으로 진입합니다.

## Ubuntu 설치화면에서 디스크 확인 먼저
여기서는 Ubuntu 설치에 대한 화면을 볼 수 있습니다.
만약 Ubuntu Desktop 이라면, Ctrl + Alt + T 를 통해 터미널에 접근이 가능합니다.

그럼 **ubuntu@ubuntu:** 상태의 터미널 창을 통해 시스템 마운트의 구성을 확인하실 수 있습니다.

### df 사용
```
df -h
```

### /etc/mtab 확인
```
cat /etc/mtab
```

## /mnt 폴더에 마운트
```
sudo mount /dev/sda2 /mnt
```
제 경우에는 **/dev/sda2 폴더에 Ubuntu 설치가 되어 있어서 /mnt 폴더에 마운트합니다.

## sudo 권한 변경하기
```
sudo chmod 4755 /mnt/usr/bin/sudo
```
위 명령어를 통해 권한을 올바르게 설정합니다.
**4755** 권한 설정은 보안상 중요한 실행 파일에 자주 사용되는데, 특정 명령어를 루트 권한 또는 다른 사용자의 권한으로 실행할 수 있게 하기 위함입니다.