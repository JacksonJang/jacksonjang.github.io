---
layout:     post
title:      "[SQL] 프로시저 란?"
subtitle:   " \"What's the procedure?\""
date:       2024-04-04 19:00:00
author:     "JacksonJang"
header-img: "assets/posts/post-bg_2024.jpg"
post_assets: "/assets/posts/2024-04-04"
catalog: true
tags:
    - SQL
    - MySQL
    - Procedure
---
> MySQL 8 버전 기준으로 작성되었습니다.

## Procedure 란?
> 어떤 업무를 수행하기 위한 절차를 의미한다.

위에처럼 요약할 수 있지만 설명이 부진하다고 생각해서 추가적으로 설명하겠습니다.
<br />
데이터베이스에서 **실행할 수 있는 하나 이상의 SQL 문**을 모아 놓은 것이며, 복잡한 작업을 하나의 블록으로 캡슐화한 것을 의미합니다.
<p />
즉, 프로세스를 **절차적**으로 기술해 놓은 것을 의미합니다.

## Procedure 문법
```sql
CREATE
    [DEFINER = user]
    PROCEDURE [IF NOT EXISTS] sp_name ([proc_parameter[,...]])
    [characteristic ...] routine_body
```
```
proc_parameter:
    [ IN | OUT | INOUT ] param_name type

characteristic: {
    COMMENT 'string'
  | LANGUAGE SQL  | [NOT] DETERMINISTIC
  | { CONTAINS SQL | NO SQL | READS SQL DATA | MODIFIES SQL DATA }
  | SQL SECURITY { DEFINER | INVOKER }
}

routine_body:
    SQL routine
```

## Procedure 사용하기
한번 위의 문법을 바탕으로해서 가장 기본적인 반복문을 통해 데이터를 삽입하는 작업을 하겠습니다.
```sql
CREATE PROCEDURE insertTestTitleAndNumber()
BEGIN
    DECLARE i INT DEFAULT 1;
    WHILE i <= 100000 DO
        INSERT INTO test_table (title, number)
        VALUES (CONCAT('제목 : ', i), i);
        SET i = i + 1;
    END WHILE;

END
```

## 참고링크
- [https://dev.mysql.com/doc/refman/8.3/en/create-procedure.html](https://dev.mysql.com/doc/refman/8.3/en/create-procedure.html)