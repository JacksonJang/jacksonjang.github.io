---
layout:     post
title:      "[Linux] 서버 계정 추가 및 root 권한 설정하기 (초간단)"
subtitle:   "\"Linux : Adding Server Account and Set the authorization as root(simply)\""
date:       2024-05-04 19:00:00
author:     "JacksonJang"
post_assets: "/assets/posts/2024-05-04"
catalog: true
categories:
    - Linux
tags:
    - Linux
---

일반적으로 서버를 aws나 호스팅 업체를 통해 구축하게 되면 ubuntu(우분투 사용하면)거나 root 계정을 부여받게 됩니다.
<br />
그래서 오늘은 서버 관리자가 직접 계정을 생성해서 루트 권한을 부여하는 것까지 알아보겠습니다.

## 서버 계정 추가하기
```sh
adduser 사용자계정명
```
서버에 접속하고나서 위에처럼 간단한 명령어를 통해 사용자 계정을 추가할 수 있습니다.

위와 같이 만들고나서 해당 계정으로 접속하고 `sudo` 명령어를 사용하면 다음과 같은 에러 메시지를 볼 수 있습니다.
```sh
사용자계정명 is not in the sudoers file.  This incident will be reported.
```

이제 위 에러를 해결하기 위해 새로 만들어진 `사용자계정명`에 루트 권한을 부여하겠습니다.

## 서버 계정에 루트 권한 부여하기
우선, /etc/sudoers를 수정하기 위해 `root` 계정으로 로그인 하고나서 다음과 같은 명령어를 쳐줍니다.

```sh
sudo visudo
```

그러면 `root ALL=(ALL:ALL) ALL` 로 되어 있는 부분이 있는데, 그 밑에
<br />
`사용자계정명 ALL=(ALL:ALL) ALL` 을 적어주고 저장하면 끝납니다.

의외로 간단하죠?
