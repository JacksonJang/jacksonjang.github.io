---
layout:     post
title:      "[JavaScript] null vs undefined 차이 제대로 알기"
subtitle:   "[JavaScript] What's the diffence null and undefined?"
date:       2025-07-27 18:00:00
author:     JacksonJang
post_assets: "/assets/posts/2025-07-27"
catalog: true
categories:
    - JavaScript
tags:
    - JavaScript
    - null
    - undefined
---

# JavaScript 의 null, undefined 알아보기
## undefined 의미
`JavaScript`에서 `undefined`는 <b>변수를 선언하고 값을 할당하지 않은 상태</b>를 의미합니다.
```js
let x;
```
<br />

## null 의미
`null`은 `변수를 선언하고 빈 값을 할당한 상태`입니다.
```js
let x = null;
```
<br />

## 위 차이에 대해 구분하는 테스트하기(typeof 사용)
`JavaScript`에서는 `typeof` 라는 연산자가 있습니다.
<br />
이 연산자를 이용해서 타입들에 대해 볼 수 있는데 아래와 같이 Console 창에서 바로 확인 가능합니다.
<br />
<img src="{{ page.post_assets }}/typeof.png">

```js
typeof null         // 'object'
typeof undefined    // 'undefined'
typeof 1            // 'number'
typeof test         // 'string'
```

여기서 왜 `null` 이 `object` 타입인지 궁금하신 분들이 계실겁니다.
<br />
`null`이 `object` 타입인 것은 <b>자바스크립트의 초창기 설계 실수(버그)</b> 때문에 `typeof` 연산자를 썼을 때 결과가 다르게 나오게 된 것입니다.
<br />
<br />
그럼 수정하면 되지 않나요? 라고 생각하실 수 있습니다. (저 또한 그랬죠)
<br />
<br />
당시 자바스크립트는 값을 내부적으로 태그(타입 태그)와 함께 저장했는데, 
<br />null의 태그가 0으로 설정되었고, 객체의 태그 또한 0으로 시작하는 비트 패턴을 사용했기 때문에 `typeof null`을 하면 `object`가 반환되게 된 거예요.
<br />
<br />
이 `typeof null`의 결과 값을 바꾸게 되면 기존 웹사이트의 수많은 코드가 깨져서 사이드 이펙트를 불러올 수 있어서 변경하지 못하고 있습니다ㅎㅎ;(웃픈 사실)
<br />
<br />

### javascript 원시타입
하지만 `null`과 `undefined` 타입에 관련된 내용은 [ECMAScript 참고자료](https://tc39.es/ecma262/#sec-ecmascript-overview) 링크를 통해서 확인할 수 있었습니다.
<br />
<br />

위 [참고자료](https://tc39.es/ecma262/#sec-ecmascript-overview)의 내용 중 이에 대해 언급하는 내용으로 다음과 같이 작성되어 있습니다.
```
A primitive value is a member of one of the following built-in types: Undefined, Null, Boolean, Number, BigInt, String, and Symbol.
```
<br />

해석하자면,
<br />
<b>원시타입(Primitive type) 값은 다음과 같은 내장 타입 중 하나에 속하는 값이다: Undefined, Null, Boolean, Number, BigInt, String, and Symbol.</b>
<br />
<br />

여기서 우리는 `null`과 `undefined`는 `Primitive type` 이라는 것을 알 수 있죠.
<br />

## 동등 비교(==) vs 일치 비교(===) 연산자 차이
`null`와 `undefined`는 `값이 없음`을 나타냅니다.
<br />
따라서, `null == undefined` 를 하게 되면 `true`의 값을 얻게되죠.
<br />
<br />
그런데 `null === undefined` 의 경우에는 다릅니다.
<br />
위에서 살펴보았듯이 `null`은 `object`타입이고, `undefined`는 `undefined` 타입이라는 것을 `typeof`을 통해 알게 되었었죠.
<br />
<br />
그러므로 결과는 당연히 `null === undefined` 는 `false`의 값을 얻게됩니다.
<br />

```js
null == undefined   // true
null === undefined   // false
```
<br />

## JSON.stringify 사용
### 객체일 때
```js
const data = { name: undefined, age: null };
```
`name` 과 `age` 를 가진 객체 `data` 가 있다고 가정하겠습니다.
<br />
위의 결과를 출력하면
```js
console.log(JSON.stringify(data)); // {"age":null}
```
`undefined` 로 지정된 `name` 이 사라진 것을 볼 수 있습니다.
<br />
<br />
왜 그런걸까요?
<br />
<br />

### JSON 표준 문서
JSON 형식에서는 <b>`undefined`라는 값이 존재하지 않고 있다</b>는 것입니다.
<br />
위 내용에 대해서는 [JSON 표준 ECMA-404 문서](https://ecma-international.org/wp-content/uploads/ECMA-404.pdf)에서 확인 가능합니다.
<br />
<br />
하지만, 이 또한 친절한 잭슨씨가 내용을 갖고 왔습니다^^
<br />
<img src="{{ page.post_assets }}/JSON_Standard.png">
위 내용을 확인해 보면, JSON 의 표준은 다음과 같이 표시된 것을 볼 수 있습니다.
- 객체(Obejct)
- 배열(Array)
- 숫자(Number)
- 문자열(String)
- `true`, `false`
- `null`


### 하지만, 배열일 때는 undefined가 포함됩니다! 단...
위 [JSON 표준 문서](#json-표준-문서)에서 알아 봤듯이 JSON은 `undefined`를 허용하고 있지 않습니다.
<br />
그렇지만, 배열에 포함된 undefined 요소를 생략하면 순서가 깨지므로 
<br />
JSON으로 변환 시 `undefined` -> `null` 로 변환하는 것이죠.
<br />
<br />
다음은 관련된 예시입니다.
```js
const arr = [1, undefined, 3];
const json = JSON.stringify(arr);   // "[1,null,3]"
const parsed = JSON.parse(json);    // [1, null, 3]
console.log(arr[1]);                // undefined
console.log(arr.length);            // 3
```


## 결론
`null`과 `undefined`의 차이는 <b>값을 명시적으로 할당했는지 여부</b>에 따라 구분된다는 점을 [null의 의미](#null-의미) 와 [undefined 의미](#undefined-의미)에서 살펴보았습니다.
<br />
<br />
또한 `undefined`, `null`이 [원시타입](#javascript-원시타입)에 속하지만, `typeof null`의 결과가 `object`로 출력되는 것은 자바스크립트 초기 설계상의 실수라는 점도 확인했습니다.
<br />
<br />
그리고 [동등 비교(==) vs 일치 비교(===) 연산자](#동등-비교-vs-일치-비교-연산자-차이)를 통한 차이로 `null`, `undefined`의 값과 타입 비교 차이를 이해했으며,
[JSON.stringify 사용](#jsonstringify-사용) 예시를 통해 `객체`와 `배열`에서 각각 어떻게 처리되는지도 알아보았습니다.

이 글이 이해에 도움이 되었길 바랍니다.
<br />
감사합니다!
