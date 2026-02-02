---
layout:     post
title:      "Database Replication 사용하기(with MySQL)"
subtitle:   "Using Database Replication with MySQL"
date:       2025-08-09 13:00:00
author:     JacksonJang
post_assets: "/assets/posts/2025-08-09"
catalog: true
categories:
    - DevOps
tags:
    - DevOps
    - MySQL
---

고객사의 대규모 서비스를 도입하게 되어, 관련 내용을 정리하게 되었습니다.

## Database Replication 이란?
사용자가 많은 서비스에서는 하나의 DB로 모든 요청을 처리하기 어려울 수 있습니다. 그래서 이를 해결하기 위해 고안된 기술이 `Database Replication`입니다.

`Database`를 `Replication`(복제)해서 DB Read/Write 역할을 나눠서 성능과 안정성을 증가시키고, 일반적으로 Source/Replica 구조를 사용하며 다음과 같은 역할을 수행합니다.

- Source(혹은 Master) : Write(INSERT, UPDATE, DELETE)
- Replica(혹은 Slave) : Read(SELECT)

*참고 : MySQL 8.0 이후로 `Master/Slave` -> `Source/Replica` 로 변경되었습니다.
그렇지만, 설명의 편의성을 위해 `Master/Slave`로 설명하겠습니다.

## 테스트 진행
앞으로 진행할 테스트는 `docker-compose.yml` 을 사용하여 DB 구축 후 MySQL 명령어를 통해 계정 생성을 진행하고나서 `Master`와 `Slave`를 연결하여 최종적으로 `Master`에서 데이터 작성 후 `Slave`에 정상적으로 복제 되었는지 확인하는 과정이 되겠습니다.

### docker-compose.yml 작성
```yml
version: "3.9"
services:
  mysql-master:
    image: mysql:8.0
    container_name: mysql-master
    command: >
      --server-id=1
      --log-bin=mysql-bin
      --gtid-mode=ON
      --enforce-gtid-consistency=ON
      --binlog-format=ROW
      --default-authentication-plugin=mysql_native_password
    environment:
      MYSQL_ROOT_PASSWORD: rootpass
      TZ: Asia/Seoul
    ports: ["3307:3306"]
    volumes:
      - master-data:/var/lib/mysql

  mysql-replica:
    image: mysql:8.0
    container_name: mysql-replica
    command: >
      --server-id=2
      --log-bin=mysql-bin
      --gtid-mode=ON
      --enforce-gtid-consistency=ON
      --binlog-format=ROW
      --read-only=ON
      --default-authentication-plugin=mysql_native_password
    environment:
      MYSQL_ROOT_PASSWORD: rootpass
      TZ: Asia/Seoul
    ports: ["3308:3306"]
    volumes:
      - replica-data:/var/lib/mysql

volumes:
  master-data:
  replica-data:
```

`docker-compose.yml`을 복사해서 파일 생성 후 `docker-compse up -d` 후에 아래 명령어를 통해 복제 전용 계정을 마스터에 생성합니다.
-> 이렇게 복제 전용 계정을 생성하는 이유는 `REPLICATION SLAVE` 와 `REPLICATION CLIENT`의 권한만 필요하기 때문에 전용 계정을 생성하는 게 좋습니다.

### 복제 전용 계정 생성(Master DB에서 진행)
```sh
docker exec -it mysql-master mysql -uroot -prootpass -e "
  CREATE USER IF NOT EXISTS 'repl'@'%' IDENTIFIED BY 'replica_pass';
  GRANT REPLICATION SLAVE, REPLICATION CLIENT ON *.* TO 'repl'@'%';
  FLUSH PRIVILEGES;
"
```

### Master 바이너리 로그 위치 확인
```sh
docker exec -it mysql-master mysql -uroot -prootpass -e "SHOW MASTER STATUS\G"
```
<img src="{{ page.post_assets }}/master-status.png">
여기에서 `File`과 `Position`의 값은 나중에 쓸 예정이니 메모해야 합니다.

```
File: mysql-bin.000004
Position: 2273
```

### Replication 시작!
반대편에 속한 `Slave(Replica)`에서 연결시켜줍니다.

> ⚠️ **주의:** `Master` 와 `Slave(Replica)`의 테이블 구조와 데이터가 동일해야 합니다.

```sh
docker exec -it mysql-replica mysql -uroot -prootpass -e "
  STOP REPLICA; RESET REPLICA ALL;
  CHANGE REPLICATION SOURCE TO
    SOURCE_HOST = 'mysql-master',
    SOURCE_PORT = 3306,
    SOURCE_USER = 'repl',
    SOURCE_PASSWORD = 'replica_pass',
    SOURCE_LOG_FILE = 'mysql-bin.000004',
    SOURCE_LOG_POS  = 2273;
  START REPLICA;
"
```
`SOURCE_LOG_FILE` = `File`
`SOURCE_LOG_POS` = `Position`

이 때, [Master 바이너리](#master-바이너리-로그-위치-확인)에서 기록했었던 `File`과 `Position` 을 작성하면 됩니다.

### 복제가 정상적으로 됐는지 확인법
```sh
docker exec -it mysql-replica mysql -uroot -prootpass -e "SHOW REPLICA STATUS\G" | sed -n '1,120p'
```
`Replica_IO_Running`, `Replica_SQL_Running` 가 `YES`
`Seconds_Behind_Source` 가 0이면 됩니다.
(NULL 이면 실패)

### 테스트 시작~
```sql
CREATE TABLE IF NOT EXISTS t(id INT PRIMARY KEY, v VARCHAR(50))
```
위 명령어를 `Master`에서 실행시켜서 자동으로 `Slave(Replica)`에 생성된 것을 확인했습니다^^
<img src="{{ page.post_assets }}/check-replication.png">

~~신기하네요~~

그렇다면, 반대로 `Slave`에서 테이블을 생성하려고 한다면?

<img src="{{ page.post_assets }}/replica-create.png">

사진처럼 정상적으로 테이블이 생성되고 `Master`에서는 생성되지 않은 모습을 볼 수 있습니다.
그런데 앞서 우리는 [Database Replication 이란?](#database-replication-이란) 섹션에서 `Slave`는 `Read`의 역할만 한다는 것을 확인했습니다.

그럼 `read_only`가 `ON` 상태가 아닐까요?

### read_only 체크 명령어
```sh
docker exec -it mysql-replica mysql -uroot -prootpass -e "SHOW VARIABLES LIKE 'read_only';
```
<img src="{{ page.post_assets }}/read-only-check.png">

확인한 결과 이미 `read_only`가 `ON` 상태로 된 것을 확인할 수 있습니다.
그렇다면, 왜 이런 현상이 발생할까요?

정답은 `super-read-only` 값을 설정하지 않아서 그렇습니다.

### super-read-only 설정
```sh
docker exec -it mysql-replica mysql -uroot -prootpass -e "SET GLOBAL super_read_only=ON;"
```
위에처럼 설정하고 `Slave(Replica)`에서 테이블 생성하면?

<img src="{{ page.post_assets }}/super-read-only.png">

이제는 `Slave`에서 생성이 안되는 것을 확인할 수 있습니다.
<br/>
<br/>