---
layout:     post
title:      "[Javascript] var, let, const 차이점"
subtitle:   "\"What different var, let and const?\""
date:       2024-04-10 19:00:00
author:     "JacksonJang"
header-img: "assets/posts/post-bg_2024.jpg"
post_assets: "/assets/posts/2024-04-10"
catalog: true
tags:
    - Javascript
    - Frontend
---

## var
ES5(2009)까지는 `var`는 변수 선언하는 유일한 방법이었습니다.
<br />
과거에는 절대적으로 사용하고 있었으며 호이스팅 때문에 예기치 않은 버그를 유발하곤 했었습니다.
<br />
그래서 ES6(ES2015) 이후부터는 `let`, `const` 더 많이 사용합니다.(굳이 `var`를 사용할 이유가 없어졌기 때문에)

**특징**
- 사용 가능한 범위 : 전역 혹은 함수
- 호이스팅 : 호이스팅 과정에서 자동으로 `undefined`로 초기화 됩니다.
- 재선언 가능

> 인터프리터가 변수와 함수의 메모리 공간을 선언 전에 미리 할당하는 것을 의미.
**한마디로 초기화만 진행**

`예시`
```js
// 전역 범위
var hello = "hello";

function test() {
  // 함수 범위
  var world = "world";
}

console.log(hello) // hello
console.log(world) // error : world is not defined

// 함수 내 호이스팅
function example() {
  if (true) {
    var x = 10;
    console.log(x); // 10
  }
  console.log(x); // 10
}

example();

// 재선언 가능
var test = ""
var test = "t"
console.log(test) // t
```

## TDZ(Temporal Dead Zone) 여부
`TDZ` : 변수가 선언된 위치부터 초기화 또는 할당이 이루어지는 위치까지의 구간을 의미

`var`와 `let`, `const`의 차이가 있다면, `TDZ`에 의해 제약을 받는다는 것입니다. 
<br />
`let`과 `const`로 선언된 변수는 TDZ 구간에서는 아직 초기화되지 않은 상태입니다.

제약을 받는 것을 통해 `ReferenceError`를 발생시키고, 이를 통해 개발자는 실수한 부분을 쉽게 찾고 개발에 집중할 수있습니다.

## let
ES6(ES2015) 이후부터는 `var`보다 `let` 를 많이 사용하고 있습니다.
<br />
왜냐하면 var는 위에서 말씀드렸던 것 처럼 호이스팅을 잘 활용하면 함수 내부 어디서든 변수를 사용할 수 있는 장점이 있지만, 자칫 잘못 사용하면 예기치 않은 버그의 원인이 되기도 합니다.

**따라서, 가급적이면 `var` 보다는 `let` 사용을 권장드립니다.**

**특징**
- 사용 가능한 범위 : 중괄호 안에 있는 것은 모두 블록 범위
- 호이스팅 : 선언은 호이스팅되지만, 초기화는 호이스팅되지 않습니다.
- 재선언 불가능

`예시`
```js
// 전역 범위
let hello = "hello";

function test() {
  // 함수 범위
  let world = "world";
}

console.log(hello) // hello
console.log(world) // error : world is not defined

// 함수 내 호이스팅
function example() {
  if (true) {
    let x = 10;
    console.log(x); // 10
  }
  console.log(x); // x is not defined
}

example();

// 재선언 불가능
let test = ""
let test = "t" // Identifier 'test' has already been declared
console.log(test)
```

## const
`let`과 유사한 점이 많이 존재하지만, `const`에서는 업데이트와 재선언이 모두 안됩니다.

**특징**
- 사용 가능한 범위 : 중괄호 안에 있는 것은 모두 블록 범위
- 호이스팅 : 선언은 호이스팅되지만, 초기화는 호이스팅되지 않습니다.
- 업데이트, 재선언 불가능

**즉, 1번 선언하면 객체는 절대 변경되지 않습니다.**

여기서 주의해야 할 사항은 절대 변경되지 않는 것은 `객체`이고, `속성`은 변경이 가능합니다.
<br />
이게 무슨 뜻이냐면, 아래와 같이 `user`가 존재한다고 가정하겠습니다.
```js
// user 객체 선언
const user = {
  name: "jacksonjang",
  age: 29 
}
```

```js
// 객체는 변경 불가능
user = {
  name: "changeName",
  age: 10 
}
```
위와 같은 코드로 변경하려고 하면 불가능 합니다.

```js
// 객체의 속성은 변경 가능
user.age = 19;
```

`예시 전체`

```js

// user 객체 선언
const user = {
  name: "jacksonjang",
  age: 29 
}

// 객체는 변경 불가능
user = {
  name: "changeName",
  age: 10 
}

// 객체의 속성은 변경 가능
user.age = 19;

// 객체의 속성은 변경 가능
user.age = 19;
```