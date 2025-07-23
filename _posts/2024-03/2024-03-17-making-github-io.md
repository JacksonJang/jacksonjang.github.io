---
layout:     post
title:      "github.io 사이트 만들기(With. Jekyll)"
subtitle:   " \"Making a github.io site\""
date:       2024-03-17 17:00:00
author:     "JacksonJang"
post_assets: "/assets/posts/2024-03-17"
catalog: true
categories:
    - Etc
tags:
    - github.io
    - git
    - Jekyll
---

> 지킬 테마를 이용하면 만들기 쉬워요!

### 준비물
- git 에 대한 지식

### Jekyll Theme 1줄 요약
정적 사이트의 디자인이나 레이아웃을 템플릿화 시킨 테마입니다. <br />
밑에는 다양한 지킬 테마를 볼 수 있는 사이트들 입니다.
- [http://jekyllthemes.org/](http://jekyllthemes.org/)
- [https://github.com/topics/jekyll-theme](https://github.com/topics/jekyll-theme)

위에서 원하시는 테마를 선택하고 다운 받으시거나, github에서 fork 하셔도 됩니다!

### github.io 저장소 생성
1. github 사이트 접속 후 로그인합니다. 
<br />
(링크 : https://github.com/)
<br />
<img src="{{ page.post_assets }}/github.png">
<br />
<br />

2. Repositories를 누르고, New를 눌러줍니다.
<img src="{{ page.post_assets }}/github-repository.png">
<br />
<br />

3. Repository name을 "깃헙계정명.github.io" 로 설정합니다.
<br />
예시 : 내 계정 아이디가 test1234 라면, test1234.github.io 로 설정하면 됩니다.
<br />
<img src="{{ page.post_assets }}/github-create-new-repository.png">
<br />
<br />

4. 생성된 github 주소를 Clone 하고, 다운받은 지킬 테마를 해당 폴더에 넣어줍니다.
<br />
<br />

5. git 의 푸시를 통해 깃허브에 올려주면 해당 Repository의 Actions에서 확인할 수 있습니다.
<br />
<img src="{{ page.post_assets }}/github-actions.png">
<br />
<br />

### 끝
