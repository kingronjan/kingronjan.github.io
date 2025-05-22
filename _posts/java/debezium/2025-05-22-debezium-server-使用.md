---
categories:
- java
- debezium
date: 2025-05-22 16:41 +0800
id: c591f958-3ab3-42ba-86d3-03c98c98f20f
layout: post
tags:
- java
- debezium
title: debezium server 使用
---

### 前言

debezium server 很早就推出来了，但是网上看到使用的分享资料很少，可能其作为独立模式部署并不具备 kafka connect 的健壮性，与分布式的 kafka connect 对比，它缺少：

- 通过 rest api 创建、启动、修改、删除
- 故障转移
- 资源动态伸缩
- 更多特性，可参考：[The debezium trio: Comparing kafka connect, Server, and Engin run times](https://blog.sequinstream.com/the-debezium-trio-comparing-kafka-connect-server-and-engine-run-times/)

因此使用场景比较少，但是在某些情况下使用仍然很有用，比如：

- 少量或无需长期维护的数据同步任务
- 单台机器运行，不希望使用集群模式，也不想依赖其他组件
- 使用集群的 connector 发生故障，希望查看详细的日志，但是调整日志级别的风险太大，希望能单独起一个日志级别较低的 debezium 进程方便观察

考虑到这些，我尝试使用 Debezium Server，主要用的 2.3 版本，并用 MySQL 数据库作为位点存储，同样也是将数据写入到 kafka，本文是使用的记录。

主要参考资料：

- [Debezium Server](https://debezium.io/documentation/reference/2.7/operations/debezium-server.html) 
- [Debezium 2.3.0.Final Released（jdbc offset 使用介绍）](https://debezium.io/blog/2023/06/21/debezium-2-3-final-released/)
- [kafka connect 文档](https://kafka.apache.org/documentation/#connect_configs)



### 下载 debezium-server 
地址：[Debezium Server distribution](https://repo1.maven.org/maven2/io/debezium/debezium-server-dist/2.7.4.Final/debezium-server-dist-2.7.4.Final.tar.gz)，下载后解压到 debezium-server 目录，内容如下：

```
debezium-server/
|-- CHANGELOG.md
|-- conf
|-- CONTRIBUTE.md
|-- COPYRIGHT.txt
|-- debezium-server-2.7.4.Final-runner.jar
|-- lib
|-- LICENSE-3rd-PARTIES.txt
|-- LICENSE.txt
|-- README.md
`-- run.sh
```



### 编译 debezium-storage-jdbc

由于通过官网下载的 debezium server 包并没有包含 debezium-storage-jdbc（使用 jdbc 数据库作为 offset 存储介质的依赖包），要想使用还需要额外编译并放到 `debezium-server/lib` 目录下。

可以新建 maven 项目，并将下面的依赖配置放到 pom.xml 文件中：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>org.example</groupId>
    <artifactId>debezium-jdbc-compiler</artifactId>
    <version>1.0-SNAPSHOT</version>

    <properties>
        <maven.compiler.source>11</maven.compiler.source>
        <maven.compiler.target>11</maven.compiler.target>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    </properties>

    <dependencies>
        <dependency>
            <groupId>io.debezium</groupId>
            <artifactId>debezium-storage-jdbc</artifactId>
            <version>2.3.0.Final</version>
        </dependency>
    </dependencies>

    <!-- 用于将 debzium-storage-jdbc 打包到 lib 目录下 -->
    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-dependency-plugin</artifactId>
                <version>3.5.0</version>
                <executions>
                    <execution>
                        <id>copy-debezium-storage-jdbc</id>
                        <phase>package</phase>
                        <goals>
                            <goal>copy</goal>
                        </goals>
                        <configuration>
                            <artifactItems>
                                <artifactItem>
                                    <groupId>io.debezium</groupId>
                                    <artifactId>debezium-storage-jdbc</artifactId>
                                    <version>2.3.0.Final</version>
                                    <outputDirectory>${project.build.directory}/lib</outputDirectory>
                                </artifactItem>
                            </artifactItems>
                        </configuration>
                    </execution>
                </executions>
            </plugin>
        </plugins>
    </build>
</project>
```

编译后将 `lib` 目录下的 `debezium-storage-jdbc-2.3.0.Final.jar` 放到`debezium-server/lib` 目录下即可。

### 配置 debezium

配置文件路径为 `debezium-server/conf/application.properties`，不支持指定。

配置内容如下：
```properties
debezium.source.connector.class=io.debezium.connector.mysql.MySqlConnector
debezium.source.transforms.Reroute.type=io.debezium.transforms.ByLogicalTableRouter
debezium.source.tasks.max=1

# database history by jdbc
debezium.source.schema.history.internal=io.debezium.storage.jdbc.history.JdbcSchemaHistory
debezium.source.schema.history.internal.jdbc.url=jdbc:mysql://<host>:<port>/offset_db
debezium.source.schema.history.internal.jdbc.user=dbuser
debezium.source.schema.history.internal.jdbc.password=dbpasswd
debezium.source.schema.history.internal.jdbc.schema.history.table.name=debezium_schema_history
debezium.source.schema.history.skip.unparseable.ddl=true
debezium.source.schema.history.store.only.captured.tables.ddl=true

debezium.source.transforms=Reroute
debezium.source.database.server.name=TEST_DBZ_SERVER
debezium.source.transforms.Reroute.topic.regex=.*
debezium.source.database.port=<dbport>
debezium.source.include.schema.changes=false
debezium.source.topic.prefix=TEST_DBZ_SERVER
debezium.source.transforms.Reroute.topic.replacement=TEST_DBZ_SERVER
debezium.source.decimal.handling.mode=string
# 不同于 kafka connect，这里需要自行指定
# 需要保证该数字对于每个 dbz 进程是唯一的，且与现有的 mysql client 不冲突
debezium.source.database.server.id=10
debezium.source.database.hostname=<dbhost>
debezium.source.database.user=dbuser
debezium.source.database.password=dbpasswd
debezium.source.database.include.list=test
debezium.source.table.include.list=test.test_table
debezium.source.dateConverters.format.timestamp.zone=UTC+8
debezium.source.snapshot.mode=schema_only
debezium.source.snapshot.locking.mode=none

# offset 配置
debezium.source.offset.storage=io.debezium.storage.jdbc.offset.JdbcOffsetBackingStore
debezium.source.offset.storage.jdbc.url=jdbc:mysql://<host>:<port>/offset_db
debezium.source.offset.storage.jdbc.user=dbuser
debezium.source.offset.storage.jdbc.password=dbpasswd
debezium.source.offset.storage.jdbc.offset_table_name=debezium_offset_storage

# 目标端配置，这里使用 kafka
debezium.sink.type=kafka
debezium.sink.kafka.producer.bootstrap.servers=<kafka_bootstrap_server>
debezium.sink.kafka.producer.key.serializer=org.apache.kafka.common.serialization.StringSerializer
debezium.sink.kafka.producer.value.serializer=org.apache.kafka.common.serialization.StringSerializer

debezium.format.value=json
debezium.format.key=json

# 日志格式默认为 json 格式，为了方便观察，这里去掉 json 格式输出
quarkus.log.console.json=false

# for debug only
#quarkus.log.level=DEBUG
#quarkus.log.category."io.debezium".level=DEBUG
```

其中 `debezium.source.schema.history.internal.jdbc.schema.history.table.name` 对应的配置内容 `debezium_schema_history` 需要手动创建，如果让 dbz 自动创建会报如下错误：

```
io.debezium.relational.history.SchemaHistoryException: Unable to create history table jdbc:mysql://<host>:<port>/offset_db: Error initializing Database history storage
...
Caused by: java.sql.SQLSyntaxErrorException: Column length too big for column 'history_data' (max = 16383); use BLOB or TEXT instead
```

手动创建的 SQL 如下（参考 debezium 2.3 源码）：
```sql
CREATE TABLE offset_db.debezium_schema_history (
    id varchar(36) not null ,
    history_data text,
    history_data_seq integer,
    record_insert_ts timestamp not null ,
    record_insert_seq integer not null 
)
```

需要确保 `debezium.source.schema.history.internal.jdbc.user` 对 `debezium.source.schema.history.internal.jdbc.schema.history.table.name`
表，以及 `debezium.source.offset.storage.jdbc.user` 对 `debezium.source.offset.storage.jdbc.offset_table_name` 表有增删改查权限，以及在数据库建表的权限（适用于自动建表）。

### 启动

执行 `debezium-server/run.sh` 文件即可。

### 验证位点抽取及断点续传
等待 debezium 启动后可以通过先停止 debezium 进程，往数据库写入数据，再次启动 debezium，如果 debezium 能抽到停止期间的数据，则说明断点续传成功。

首先确保 debezium 初始化已完成，可通过查看位点表和 schema.history 表是否有数据来判断：


schema.history 表：
```sql
mysql> select * from offset_db.debezium_schema_history limit 1\G
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  field               value
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  id                  52da3f13-a5cd-49be-a316-9a3d2f4957ec
  history_data        {"source":{"server":"TEST_DBZ_SERVER"},"position":{"ts_sec":1747719237,"file":"mysql-bin.000288","pos":630760754,"gtids":"1e965d87-b82d-11ef-b154-fa163e84cdd2:1-130514996","snapshot":true},"ts_ms":1747719238663,"databaseName":"","ddl":"SET character_set_server=utf8mb4, collation_server=utf8mb4_bin","tableChanges":[]}
  history_data_seq    0
  record_insert_ts    2025-05-20 13:41:06
  record_insert_seq   1
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

1 rows retrieved in 62.21 ms, (execution: 62.07 ms, fetching: 0.14 ms).
```

位点表：
```sql
mysql> select * from offset_db.debezium_offset_storage limit 1\G
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  field               value
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  id                  33239129-e1ce-48d6-b205-2dd645418c2a
  offset_key          ["kafka",{"server":"TEST_DBZ_SERVER"}]
  offset_val          {"transaction_id":null,"ts_sec":1747719980,"file":"mysql-bin.000288","pos":632468840,"gtids":"1e965d87-b82d-11ef-b154-fa163e84cdd2:1-130515650","row":1,"server_id":6013787,"event":3}
  record_insert_ts    2025-05-20 13:46:21
  record_insert_seq   3
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

1 rows retrieved in 64.5 ms, (execution: 64.37 ms, fetching: 0.13 ms).
```

停止 debezium 后，并触发数据变更：

```
mysql> insert into test.test_table values (1231234, 'name', 1, now(), now());
completed in 68.78 ms.
mysql> update test.test_table set name = 'name_111' where id = 1231234;
1 rows affected in 70.06 ms.
mysql> delete from test.test_table where id = 1231234;
1 rows affected in 69.78 ms.
```

再次启动 debezium，并查看 kafka 数据，变更数据有被正常抽取到 kafka：
```shell
$ consume TEST_DBZ_SERVER | jq '.payload'

{
  "before": null,
  "after": {
    "id": 1231234,
    "name": "name",
    "value": 1,
    "created_at": "2025-05-20T06:00:30Z",
    "updated_at": "2025-05-20T06:00:30Z"
  },
  "source": {
    "version": "2.3.7.Final",
    "connector": "mysql",
    "name": "TEST_DBZ_SERVER",
    "ts_ms": 1747720830000,
    "snapshot": "false",
    "db": "test",
    "sequence": null,
    "table": "test_table",
    "server_id": 6013787,
    "gtid": "1e965d87-b82d-11ef-b154-fa163e84cdd2:130515739",
    "file": "mysql-bin.000288",
    "pos": 632614586,
    "row": 0,
    "thread": 2385215,
    "query": null
  },
  "op": "c",
  "ts_ms": 1747720905549,
  "transaction": null
}
{
  "before": {
    "id": 1231234,
    "name": "name",
    "value": 1,
    "created_at": "2025-05-20T06:00:30Z",
    "updated_at": "2025-05-20T06:00:30Z"
  },
  "after": {
    "id": 1231234,
    "name": "name_111",
    "value": 1,
    "created_at": "2025-05-20T06:00:30Z",
    "updated_at": "2025-05-20T06:00:30Z"
  },
  "source": {
    "version": "2.3.7.Final",
    "connector": "mysql",
    "name": "TEST_DBZ_SERVER",
    "ts_ms": 1747720857000,
    "snapshot": "false",
    "db": "test",
    "sequence": null,
    "table": "test_table",
    "server_id": 6013787,
    "gtid": "1e965d87-b82d-11ef-b154-fa163e84cdd2:130515747",
    "file": "mysql-bin.000288",
    "pos": 632626015,
    "row": 0,
    "thread": 2385215,
    "query": null
  },
  "op": "u",
  "ts_ms": 1747720905560,
  "transaction": null
}
{
  "before": {
    "id": 1231234,
    "name": "name_111",
    "value": 1,
    "created_at": "2025-05-20T06:00:30Z",
    "updated_at": "2025-05-20T06:00:30Z"
  },
  "after": null,
  "source": {
    "version": "2.3.7.Final",
    "connector": "mysql",
    "name": "TEST_DBZ_SERVER",
    "ts_ms": 1747720868000,
    "snapshot": "false",
    "db": "test",
    "sequence": null,
    "table": "test_table",
    "server_id": 6013787,
    "gtid": "1e965d87-b82d-11ef-b154-fa163e84cdd2:130515748",
    "file": "mysql-bin.000288",
    "pos": 632626428,
    "row": 0,
    "thread": 2385215,
    "query": null
  },
  "op": "d",
  "ts_ms": 1747720905562,
  "transaction": null
}

```