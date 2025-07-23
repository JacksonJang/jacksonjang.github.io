---
layout:     post
title:      "[React.js] props 란?"
subtitle:   "\"React.js props\""
date:       2024-04-16 19:00:00
author:     "JacksonJang"
post_assets: "/assets/posts/2024-04-16"
catalog: true
categories:
    - React.js
tags:
    - Frontend
    - React.js
---
`props`는 **properties**의 줄임말로, 부모 컴포넌트에서 자식 컴포넌트로 데이터를 전달할 때 사용합니다.
각 컴포넌트는 받은 `props`를 사용하여 렌더링하거나 다른 자식 컴포넌트에게 전달할 수 있습니다.

## Props Drilling
한 컴포넌트에서 시작하여 여러 단계의 중첩된 컴포넌트를 거쳐 props를 전달하는 과정

## Props Drilling 현상의 문제점
- 유지보수 비용 증가
- 코드의 복잡성 증가
- 컴포넌트 의존성 증가

`Props Drilling` 현상을 해결하기 위해서는 다음과 같은 방법으로 해결할 수 있습니다.
- Context API 사용: [React 16 이상](https://ko.legacy.reactjs.org/blog/2019/02/06/react-v16.8.0.html)부터 사용 가능한 기본 내장 API
- 상태 관리 라이브러리 사용 : Redux, MobX 등
- 컴포넌트 구조 수정 : 불필요한 props 전달 사용 안하기
