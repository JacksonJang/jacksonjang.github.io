---
layout:     post
title:      "Spring Boot와 함께 Database Replication 사용하기"
subtitle:   "Using Database Replication with Spring Boot"
date:       2025-08-17 13:00:00
author:     JacksonJang
post_assets: "/assets/posts/2025-08-17"
catalog: true
categories:
    - Spring Boot
tags:
    - Spring Boot
---

앞서 정리한 [Database Replication 사용하기(with MySQL)](/posts/database-replication/) 글에서 살펴본 것처럼,
<br />
Spring Boot 환경에서도 동일하게 적용할 수 있습니다.

`Master/Source`와 `Slave/Replica`의 명칭 관련해서는 설명의 편의를 위해 `Master`와 `Replica`를 사용하겠습니다.
(MySQL 8.0 이후로 `Master/Slave` -> `Source/Replica` 로 변경되었습니다.)


## @Transactional을 이용해서 사용하기
`Spring Boot`에서는 `@Transactional` 을 통해 `Master`로 보낼지, `Replica`로 보낼지 정할 수 있습니다.

`Spring Boot`에서는 기본적으로 DB(DataSource)에 연결할지 결정하는 기능은 내장되어 있지 않기 때문에 <br />
`readOnly = false`가 `Master DataSource`로 <br />
`readOnly = true`가 `Replica DataSource`로 연결되는 설정이 필요합니다.

그럴려면 `AbstractRoutingDataSource` 를 상속 받아서 사용할 수 있게 해줘야 합니다.

## AbstractRoutingDataSource 란?
`AbstractRoutingDataSource`는 `getConnection()`(DB 연결이 필요한 순간) 시점에 <br />
`determineCurrentLookupKey()`로 현재 트랜잭션 컨텍스트(예: readOnly)에서 라우팅 키를 결정하고, <br />
그 키에 매핑된 DataSource로 위임하는 추상 클래스입니다.<br /><br />
이 메커니즘을 통해 Write는 `Master`로, 읽기는 `Replica` 로 보낼 수 있습니다.


## 테스트 진행
### RoutingDataSource 생성
```java
public enum RoutingKey {
  MASTER, REPLICA
}

public class RoutingDataSource extends AbstractRoutingDataSource {

  @Override
  protected Object determineCurrentLookupKey() {
    boolean readOnly = TransactionSynchronizationManager.isCurrentTransactionReadOnly();
    return readOnly ? RoutingKey.REPLICA : RoutingKey.MASTER;
  }
}
```
`TransactionSynchronizationManager`를 통해 트랜잭션의 ReadOnly 여부를 확인해서 `Master` 혹은 `Replica`로 보낼지 설정합니다.


### DataSourceProps 생성
```java
@Setter
@Getter
public class DataSourceProps {
  private String driverClassName;
  private String jdbcUrl;
  private String username;
  private String password;
  private String poolName;
  private Integer maximumPoolSize;
  private Integer minimumIdle;
}

@ConfigurationProperties(prefix = "app.datasource.master")
@Getter
@Setter
public class MasterDataSourceProps extends DataSourceProps { }

@ConfigurationProperties(prefix = "app.datasource.replica")
@Getter
@Setter
public class ReplicaDataSourceProps extends DataSourceProps{ }
```
공통 DataSource 설정을 위해 `DataSourceProps` 선언하고, 이를 상속 받아서 <br />
`MasterDataSourceProps` 와 `ReplicaDataSourceProps`을 선언합니다.


### DataSourceConfig 설정
```java
@Configuration
@EnableConfigurationProperties({ MasterDataSourceProps.class, ReplicaDataSourceProps.class })
public class DataSourceConfig {

  @Bean
  public HikariDataSource masterDataSource(MasterDataSourceProps p) {
    HikariDataSource ds = new HikariDataSource();
    ds.setDriverClassName(p.getDriverClassName());
    ds.setJdbcUrl(p.getJdbcUrl());
    ds.setUsername(p.getUsername());
    ds.setPassword(p.getPassword());
    return ds;
  }


  @Bean
  public HikariDataSource replicaDataSource(ReplicaDataSourceProps p) {
    HikariDataSource ds = new HikariDataSource();
    ds.setDriverClassName(p.getDriverClassName());
    ds.setJdbcUrl(p.getJdbcUrl());
    ds.setUsername(p.getUsername());
    ds.setPassword(p.getPassword());
    return ds;
  }


  @Bean
  public DataSource routingDataSource(HikariDataSource masterDataSource,
                                      HikariDataSource replicaDataSource) {
    RoutingDataSource rds = new RoutingDataSource();

    Map<Object, Object> targets = new HashMap<>();
    targets.put(RoutingKey.MASTER, masterDataSource);
    targets.put(RoutingKey.REPLICA, replicaDataSource);

    rds.setTargetDataSources(targets);
    rds.setDefaultTargetDataSource(masterDataSource);
    rds.afterPropertiesSet();
    return rds;
  }


  @Primary
  @Bean
  public DataSource dataSource(DataSource routingDataSource) {
    return new LazyConnectionDataSourceProxy(routingDataSource);
  }
}
```
`RoutingDataSource`이랑 `DataSourceConfig` 설정을 끝냈다면, <br />
`application.properties` 설정도 진행합니다.


### application.properties
```yaml
# JPA 설정
spring.jpa.open-in-view=false
spring.jpa.hibernate.ddl-auto=update
spring.jpa.properties.hibernate.format_sql=true
logging.level.org.hibernate.SQL=debug

# Master DataSource
app.datasource.master.driver-class-name=com.mysql.cj.jdbc.Driver
app.datasource.master.jdbc-url=jdbc:mysql://localhost:3307/testdb?useSSL=false&characterEncoding=utf8&serverTimezone=Asia/Seoul
app.datasource.master.username=root
app.datasource.master.password=rootpass
app.datasource.master.pool-name=MasterPool
app.datasource.master.maximum-pool-size=10
app.datasource.master.minimum-idle=1

# Replica DataSource
app.datasource.replica.driver-class-name=com.mysql.cj.jdbc.Driver
app.datasource.replica.jdbc-url=jdbc:mysql://localhost:3308/testdb?useSSL=false&characterEncoding=utf8&serverTimezone=Asia/Seoul
app.datasource.replica.username=root
app.datasource.replica.password=rootpass
app.datasource.replica.pool-name=ReplicaPool
app.datasource.replica.maximum-pool-size=10
app.datasource.replica.minimum-idle=1
```

위에처럼 설정을 끝내고 실행하면 다음과 같은 결과를 `Console` 창에서 확인할 수 있습니다.
```sh
Database JDBC URL [Connecting through datasource 'org.springframework.jdbc.datasource.LazyConnectionDataSourceProxy@13803a94']
Database driver: undefined/unknown
Database version: 8.0.43
Autocommit mode: undefined/unknown
Isolation level: undefined/unknown
Minimum pool size: undefined/unknown
Maximum pool size: undefined/unknown
```
이렇게 `undefined/unknown`로 나오는 현상은 `LazyConnectionDataSourceProxy`를 사용했기 때문에 <br />
부팅 시점에는 하이버네이트가 프록시만 보게 되고, `getConnection()`이 호출되기 전까지 실제 커넥션이 생성되지 않기 때문입니다.

자, 이제 설정이 끝났으니 실제 서비스로 사용을 시작할게요.

## 서비스 사용
```java
@Service
@RequiredArgsConstructor
public class UserService {
  private final UserRepository userRepository;

  // WRITE -> MASTER
  @Transactional
  public void insert(String name) {
    UserEntity user = new UserEntity();
    user.setName(name);
    userRepository.save(user);
  }

  // READ -> REPLICA
  @Transactional(readOnly = true)
  public String find(String name) {
    return userRepository.findByName(name).getName();
  }
}
```
위에처럼 `@Transactional` 을 사용할 때, `readOnly`를 통해 `MASTER`, `REPLICA`로 보낼 수 있습니다.