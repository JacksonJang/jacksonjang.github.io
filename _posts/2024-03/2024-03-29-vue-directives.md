---
layout:     post
title:      "[Vue.js] Vue.js 기초(3) - 지시자"
subtitle:   " \"Vue.js Directives\""
date:       2024-03-29 18:00:00
author:     JacksonJang
post_assets: "/assets/posts/2024-03-29"
catalog: true
categories:
    - Vue.js
tags:
    - Frontend
    - Vue.js
---

[Vue.js의 문서](https://vuejs.org/api/built-in-directives.html)를 기반으로 작성했습니다.

## v-text
Element의 text를 업데이트 하는데 사용됩니다.

```html
<p v-text="msg"></p>
{% raw %}<p>{{ msg }}</p>{% endraw %}
```

## v-html
Element의 innerHTML 을 업데이트합니다.
<br />
> XSS 공격을 당할 수 있기 때문에 신뢰할 수 있는 컨텐츠에만 v-html을 사용하고, 사용자가 제공하는 컨텐츠에는 절대 사용하면 안됩니다.
```html
<div v-html="html"></div>
```

## v-show
엘리먼트의 표출 여부를 결정합니다.
```html
<div v-show="false"></div>
```

## v-if, v-else, v-else-if
엘리먼트 또는 템플릿을 조건부로 렌더링합니다.
```html
<div v-if="true">이건 보일거야</div>
<div v-else>이건 안보여</div>

<div v-if="type === 'A'">타입은 A 입니다.</div>
<div v-if="type === 'B'">타입은 B 입니다.</div>
```

## v-for
엘리먼트 또는 템플릿을 반복문으로 렌더링 가능합니다.
```html
<div v-for="item in items">
  {% raw %}<p>{{ item.text }}</p>{% endraw %}
</div>
<div v-for="(item, index) in items"></div>
<div v-for="(value, key) in object"></div>
<div v-for="(value, name, index) in object"></div>
```

## v-on
엘리먼트에 이벤트 리스너를 연결합니다.
```html
<!-- 메서드 핸들러 -->
<button v-on:click="doThis"></button>

<!-- 동적 이벤트 -->
<button v-on:[event]="doThis"></button>

<!-- 인라인 표현식 -->
<button v-on:click="doThat('hello', $event)"></button>

<!-- 단축 문법 -->
<button @click="doThis"></button>

<!-- 단축 문법 동적 이벤트 -->
<button @[event]="doThis"></button>

<!-- 전파 중지 -->
<button @click.stop="doThis"></button>

<!-- event.preventDefault() 작동 -->
<button @click.prevent="doThis"></button>

<!-- 표현식 없이 event.preventDefault()만 사용 -->
<form @submit.prevent></form>

<!-- 수식어 이어서 사용 -->
<button @click.stop.prevent="doThis"></button>

<!-- 키 별칭을 수식어로 사용 -->
<input @keyup.enter="onEnter" />

<!-- 클릭 이벤트 단 한 번만 트리거 -->
<button v-on:click.once="doThis"></button>

<!-- 객체 문법 -->
<button v-on="{ mousedown: doThis, mouseup: doThat }"></button>
```

## v-bind
하나 이상의 속성 또는 컴포넌트 prop을 표현식에 동적으로 바인딩합니다.

```html
<!-- 속성 바인딩 -->
<img v-bind:src="imageSrc" />

<!-- 동적인 속성명 -->
<button v-bind:[key]="value"></button>

<!-- 단축 문법 -->
<img :src="imageSrc" />

<!-- 같은 이름 생략 가능 (3.4+), 오른쪽과 같음 :src="src" -->
<img :src />

<!-- 단축 문법과 동적 속성명 -->
<button :[key]="value"></button>

<!-- 인라인으로 문자열 결합 -->
<img :src="'/path/to/images/' + fileName" />

<!-- class 바인딩 -->
<div :class="{ red: isRed }"></div>
<div :class="[classA, classB]"></div>
<div :class="[classA, { classB: isB, classC: isC }]"></div>

<!-- style 바인딩 -->
<div :style="{ fontSize: size + 'px' }"></div>
<div :style="[styleObjectA, styleObjectB]"></div>

<!-- 속성을 객체로 바인딩 -->
<div v-bind="{ id: someProp, 'other-attr': otherProp }"></div>

<!-- prop 바인딩. "prop"은 자식 컴포넌트에서 선언되어 있어야 함 -->
<MyComponent :prop="someThing" />

<!-- 자식 컴포넌트와 공유될 부모 props를 전달 -->
<MyComponent v-bind="$props" />

<!-- XLink -->
<svg><a :xlink:special="foo"></a></svg>
```

## v-model
사용자 입력을 받는 폼(form) 엘리먼트 또는 컴포넌트에 양방향 바인딩을 만듭니다.
<br />
핵심은 **양방향** 입니다.
```html
<input type="text" v-model="inputTest"/>
```

## v-slot
하위 컴포넌트에서 정의한 데이터를 상위 컴포넌트의 슬롯 컨텐츠에서 사용할 수 있도록 합니다

## v-pre
모든 자식 엘리먼트의 컴파일을 생략합니다.
```html
{% raw %}<span v-pre>{{ 이곳은 컴파일되지 않습니다. }}</span>{% endraw %}
```

## v-once
엘리먼트와 컴포넌트를 한번만 렌더링하고, 향후 업데이트를 생략합니다.

```html
{% raw %}<span v-once>절대 바뀌지 않음: {{msg}}</span>{% endraw %}
```

## v-cloak
준비될 때까지 컴파일되지 않은 템플릿을 숨기는 데 사용됩니다.
```html
<div v-cloak>
  test
</div>
```

## github 예시
[https://github.com/JacksonJang/Vue-js-directives.git](https://github.com/JacksonJang/Vue-js-directives.git)
