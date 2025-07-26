---
layout:     post
title:      "[React.js] 알면 유용한 Hooks"
subtitle:   "\"React.js, useful to know Hooks\""
date:       2024-04-27 19:00:00
author:     JacksonJang
post_assets: "/assets/posts/2024-04-27"
catalog: true
categories:
    - React.js
tags:
    - Frontend
    - React.js
---
## React Hook
React Hook은 React 16.8 버전에서 도입된 새로운 기능입니다.
관련 링크 : https://ko.legacy.reactjs.org/blog/2019/02/06/react-v16.8.0.html

React Hook은 함수형 컴포넌트에서 클래스 컴포넌트의 여러 기능들을 사용할 수 있게해서 상태관리나 생명주기 관리 등을 사용 가능하게 해주었습니다.

```js
import React from 'react';

// 함수형 컴포넌트 예시 코드입니다.
function HelloWorld(props) {
  return <h1>Hello, {props.name}</h1>;
}

export default HelloWorld;
```

그렇다면 이제부터 React Hooks의 종류에 대해 알아보겠습니다.

## useState
상태값과 상태값을 갱신하는 함수를 제공하는 훅이다.

```js
// 선언 방법
const [상태값, 상태값을 갱신하는 함수] = useState(초기값)

// 예시코드
const [state, setState] = useState("");
```

- **useState**를 const로 선언합니다.
> const로 선언하는 이유는 상태 값과 setter의 함수가 변경되지 않는 불변성을 유지해야 하기 때문입니다.

- **useState**의 상태값이 변경될 때마다 다시 렌더링을 진행합니다.

## useEffect
컴포넌트가 렌더링 될 때마다 사이드 이펙트(Side Effect)를 실행할 수 있도록 하는 훅입니다.

이전에는 `componentDidMount()`, `componentDidUpdate()`, `componentWillUnmount()` 방식이 결합된 형태가 `useEffect` 라고 볼 수 있습니다.

> 참고 : 컴포넌트 렌더링 프로세스에 방해가 되지 않도록 설계된 것으로 **사이드 이펙트**는 렌더링 이후에 비동기로 호출됩니다.


```js
// 선언 방법
useEffect(sideEffect, 의존성)
```
만약 의존성 배열을 비워두면, 컴포넌트가 마운트된 후 한 번만 실행합니다.

아래는 간단한 예시와 설명입니다.
```js
const [data1, setData1] = useState("");

// 마운트된 후 한 번만 실행
useEffect( () => console.log("mount"), [] );

// 의존성 배열에 data1 전달, data1의 값이 바뀌면 호출
useEffect( () => console.log("data1 update"), [ data1 ] );

// 의존성 배열에 여러개의 useState도 넣을 수 있습니다.
// data1, data2, data3 중 1개라도 수정되면 호출
useEffect( () => console.log("data1, data2, data3 update"), [ data1, data2, data3 ] );

// 의존성 배열이 없는 경우,  렌더링이 될 때마다 호출
useEffect( () => console.log("any update") );

// data1이 업데이트 되거나, unmount 될 때 호출
useEffect( () => () => console.log("data1 update or unmount"), [ data1 ] );

// unmount 될 때 호출
useEffect( () => () => console.log("unmount"), [] );
```

> 참고 : unmount는 "컴포넌트가 DOM에서 제거될 때" 를 의미합니다.
> 참고 : **의존성 배열**이 비어 있으면, 처음 랜더링될 때만 실행되고 이후에는 재실행되지 않습니다.

## useContext
함수형 컴포넌트에서 Context 를 편하게 사용할 수 있도록 도와주는 훅입니다.

그렇다면 Context에 대해 알아볼 필요가 있습니다.

### Context API
Context API를 사용하면 컴포넌트 트리의 모든 레벨에 걸쳐 props를 직접 전달하지 않고도 데이터를 공유할 수 있습니다. Provider와 함께 사용됩니다.

### Provider
React 컴포넌트 트리에서 값을 제공하는 역할을 합니다. `Provider`의 `value` prop를 통해 하위 컴포넌트에 데이터를 전달할 수 있습니다. 이를 통해 [props 드릴링](https://jacksonjang.github.io/2024/04/16/react-props/)을 해결할 수 있습니다.

```js
// 선언 방법
const value = useContext(SomeContext)
```

아래는 간단한 예시입니다.
App.js
```js
const theme = "white";

<ThemeContext.Provider value={theme}>
  <TestSample />
</ThemeContext.Provider>
```

TestSample.js
```js
import React, { useContext } from "react";
import ThemeContext from "./TestContext";

const TestSample = () => {
  const theme = useContext(ThemeContext);
  const style = {
      width: '24px',
      height: '24px',
      background: theme
  };
    return <div style={style}></div>
};

export default TestSample;
```

TestContext.js
```js
import { createContext } from "react";

const TestContext = createContext();

export default TestContext;
```

위에처럼 구성하게 되면 useContext를 이용해서 상위 컴포넌트로 부터 Context 데이터를 받아와서 사용할 수 있습니다.

## useReducer
상태 로직을 관리하는 훅입니다. <br />
`useState`은 단순한 상태를 관리하는 훅이라면, `useReducer`는 복잡한 상태 로직과 다양한 상태에 대한 업데이트 케이스를 관리하기 위해 액션을 통한 상태 업데이트 방식을 사용하는 훅입니다.

```js
// 선언 방법
const [state, dispatch] = useReducer(reducer, initialArg, init?)
```
- Parameter 설명
1. `reducer`는 상태(state)와 액션(action)을 인자로 받아서 액션에 따른 상태를 반환하는 함수입니다.
2. `initialArg`는 모든 타입의 값이 들어갈 수 있으며 reducer에서 사용하게 될 데이터를 설정합니다.
3. `init?`은 초기 상태에 대해 추가적으로 설정할 부분이 있다면 설정합니다. 만약 사용하지 않는다면, initialArg가 초기 상태 설정 값이 됩니다.

아래는 간단한 예시입니다.
```js
const [state, dispatch] = useReducer(reducer, { count: 0 })

function reducer(state, action) {
  switch (action.type) {
    case "add":
      return {
        count: state.count + 1
      };
    case "minus":
      return {
        count: state.count - 1
      };
    case "reset":
      return {
        count: 0
      };
  }
}

// html 영역
<div>
  Count: { state.count }
  <input type="button" value="더하기" onClick={ () => dispatch({ type: 'add' }) }/>
  <input type="button" value="빼기" onClick={ () => dispatch({ type: 'minus' }) }/>
  <input type="button" value="리셋" onClick={ () => dispatch({ type: 'reset' }) }/>
</div>
```

## useMemo
re-render 사이에서 **계산된 결과 값**을 메모이제이션(Memoization)해서 사용할 수 있는 훅입니다.

```js
// 선언 방법
const cachedValue = useMemo(calculateValue, dependencies)
```
- Parameter 설명
1. `calculateValue` 는 캐싱을 원하는 계산된 값을 리턴하는 함수를 넣어주면 됩니다. `dependencies`에서 마지막 렌더링 때 변경된 게 없으면 같은 값을 리턴해 옵니다.
2. `dependencies` 는 **의존성 배열**을 넣으면 됩니다.

```js
const [memoA, setMemoA] = useState(1);
const [memoB, setMemoB] = useState(2);

function calcMemo(a, b) {
  console.log("using calcMemo function")
  return a * b;
}

// html 영역
<input type="button" value="useMemo 사용" onClick={() => setMemoA(memoA )}/>
```

## useCallback
re-render 사이에서 **함수 정의**를 메모이제이션(Memoization)해서 사용할 수 있는 훅입니다.

```js
const [callBackA, setCallBackA] = useState(1);
const [callBackB, setCallBackB] = useState(2);

const onChangeCallBackValue = useCallback( e => {
  setCallBackA(e.target.value);
}, []);

// html 영역
<input type="text" value={callBackA} onChange={onChangeCallBackValue} />
```

## useRef
re-render 되어도 참조된 값으로 현재 값을 유지할 수 있는 훅입니다.
<br />
값 변경은 `useRef`의 `current` 속성을 이용해서 변경할 수 있습니다.
<br />
참고로 **값을 변경해도 re-render가 되지 않습니다.**

```js
// useRef 사용
const countRef = useRef(5);

const onClickCountRef = useCallback( e => {
  countRef.current += 1;
  console.log(countRef)
}, []);

// html 영역
countRef: {countRef.current}
<input type="button" value="useRef 숫자 + 1 증가" onClick={onClickCountRef}/>
```
위 코드에서 `countRef`의 속성 값이 증가하고 있지만(**console.log**로 확인 가능), UI 렌더링이 없기 때문에 보여지지 않는 모습을 확인 할 수 있습니다

## 참고 자료
- [React.js 공식 홈페이지 문서](https://react.dev/reference/react)
- [useEffect 관련 StackOverFlow](https://stackoverflow.com/questions/55020041/react-hooks-useeffect-cleanup-for-only-componentwillunmount)
- [useEffect 문서](https://legacy.reactjs.org/docs/hooks-effect.html)
- [[React]Hook: useContext](https://jaylee-log.tistory.com/55)
- [리액트의 Hooks 완벽 정복하기](https://velog.io/@velopert/react-hooks)
- [useReducer를 어떻게, 그리고 언제 사용할까?](https://eun-jee.com/post/front-end/react/04-useReducer/)
