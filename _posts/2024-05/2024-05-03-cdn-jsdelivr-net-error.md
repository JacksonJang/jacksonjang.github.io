---
layout:     post
title:      "[Frontend] cdn.jsdelivr.net SSL 에러 사태"
subtitle:   "\"Error : cdn.jsdelivr.net SSL\""
date:       2024-05-03 17:30:00
author:     "JacksonJang"
post_assets: "/assets/posts/2024-05-03"
catalog: true
categories:
    - Javascript
tags:
    - Frontend
    - Javascript
    - jsdelivr
---

## 에러 확인
2024년 5월 2일 오전 10시(추정시간)에 발생한 의문의 접속 장애로 인해 고객사 측에서 문의가 왔었다.

<img src="{{ page.post_assets }}/hls-js-error.png" /> <br />
그래서 에러에 대한 부분 확인해 보니 `hls.js@latest` 에서 에러가 발생하고 있었다(?)

<img src="{{ page.post_assets }}/privacy.png" /> <br />
해당 cdn 주소([https://cdn.jsdelivr.net/npm/hls.js@latest](https://cdn.jsdelivr.net/npm/hls.js@latest ))에 접속해 보니
<br />
`Your connection is not private` 에러가 발생하고 있었고, 해당 에러는 SSL 인증과 관련된 에러였다.

<img src="{{ page.post_assets }}/jsdelivr.png" /> <br />
혹시 몰라서 [https://www.jsdelivr.com/](https://www.jsdelivr.com/) 사이트에 접속해서 모든 cdn을 확인하였으나, 모두 접속이 안되었다.

이러한 에러가 인터넷 문제 때문인지 특정 지역만 그런건지 몰라서 해당 부분을 더 자세히 찾아보니...(우리만 겪은게 아니였다!)

## github issue
[https://github.com/jsdelivr/jsdelivr/issues/18565](https://github.com/jsdelivr/jsdelivr/issues/18565)에서 해당 내용을 자세히 확인할 수 있었다.

<img src="{{ page.post_assets }}/github.png" /> <br />
`tienipia`라는 한국인 분께서 제일 먼저 이슈를 제기해 주셨고, 여러 나라에서도 해당 이슈를 같이 경험했었다.

<img src="{{ page.post_assets }}/github2.png" /> <br />
결국 `cdn.jsdelivr.net`으로 되어있는 주소를 `fastly.jsdelivr.net` 로 변경하고 나서야 해당 에러는 해결되었다!
