---
categories:
- java
- debezium
date: 2024-09-26 17:57 +0800
id: cf8f5822-6b13-4a91-9d51-1fef31063013
layout: post
tags:
- java
- debezium
title: debezium mysql connector 加表出现 Error processing binlog event
---

### 现象

在用 debezium 抽 MySQL 数据库时，往 `table.include.list` 加表，并通过 `PUT` 请求更新配置，在对新表做 DML 变更时 connector 出现异常：

```
io.debezium.DebeziumException: Encountered change event for table x whose schema isn't known to this connector
```



### 原因

原因在于配置 connector 时，`snapshot.mode` 配置的是 `schema_only`，这种模式只会抽取并存储本次相关表的元信息，而对于未配置的表不做处理，当出现新表的 binlog 日志时，debezium 知道要解析它但却缺少对应表的元数据，就会抛出该异常。

可以通过修改 `snapshot.mode` 为 `initial` 防止这种问题的发生，但是如果表是在之后新建的，仍然会又可能出现。



### 修复方式

官方文档提供了一种解决方式：[Capturing data from tables not captured by the initial snapshot (no schema change)](https://debezium.io/documentation/reference/2.7/connectors/mysql.html#mysql-capturing-data-from-tables-not-captured-by-the-initial-snapshot-no-schema-change)，但略显繁琐，这里提供另外一种加表的方式：

1. 在 `table.include.list` 加上新增的表，如果已经加上且出现错误可以继续后面的步骤
2. 修改 `snapshot.mode` 为 `schema_only_recovery`
3. 删除或修改 `database.history.kafka.topic` 的名称
4. 更新 connector 配置

通过这种方式，当后面还需要再次加表时，可以直接修改 `database.history.kafka.topic` 的名称，再更新 connector 配置即可（步骤：1 -> 3 -> 4）



---

1. [apache kafka - Debezium MySQL connector error: Encountered change event for table whose schema isn't known to this connector - Stack Overflow](https://stackoverflow.com/questions/75518352/debezium-mysql-connector-error-encountered-change-event-for-table-whose-schema)
2. [A year and a half with Debezium: CDC With MySQL \| by Midhun Sukumaran \| Bigbasket](https://tech.bigbasket.com/a-year-and-a-half-with-debezium-f4f323b4909d)