---
layout:     post
title:      "[Vue.js] Vue.js 기초(4) - watch, nextTick"
subtitle:   " \"Vue.js watch, nextTick\""
date:       2024-03-31 19:00:00
author:     "JacksonJang"
header-img: "assets/posts/post-bg_2024.jpg"
post_assets: "/assets/posts/2024-03-31"
catalog: true
tags:
    - Frontend
    - Vue.js
---

## watch
> 데이터의 변화를 감지하고, 그에 반응하여 특정 로직을 실행할 때 사용됩니다.

newValue는 변경되는 값, oldValue는 변경전 값이 호출됩니다.

## $nextTick
`$nextTick`은 데이터 변경에 따른 DOM의 업데이트가 완료된 바로 그 시점에 원하는 코드를 안전하게 실행할 수 있습니다.

## 예시 코드
```js
new Vue({
  data() {
    return {
      message: ''
    }
  },
  watch: {
    message(newValue, oldValue) {
      this.$nextTick(() => {
        console.log('DOM 업데이트 완료 후 작업');
        console.log('oldValue : ', oldValue);
        console.log('newValue : ', newValue);
      });
    }
  }
});
```