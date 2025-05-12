---
categories:
- database
- mysql
- django
date: 2025-05-12 16:15 +0800
id: da2976e1-4903-4f33-80b9-5b3c3b965966
layout: post
tags:
- database
- mysql
title: Strict SQL Mode 对 INSERT 的影响
---

### 从 django 迁移说起

有次我需要为开发的 django 项目某张表增加一个字段，大概定义如下：

```python
class Article(models.Model):
    
    # 新增字段
    expired = models.IntegerField(null=True, default=0)
```

验证没有问题之后就使用 `migrate` 将变更应用到数据库了，后来测试告诉我说他验证之前版本（还没有我新增的字段）时遇到 MySQL 报错：`(1364, Field 'exprired' doesn't have a default value)`。这就很奇怪，我已经知道 django 不会将默认值保存到 MySQL，而是自己维护，但是这个字段是可以为空的（`null=True`），没道理还会报错。



### 字段为 NULL 写入还会报错

通过 `sqlmigrate` 命令我将 django 实际执行的 DDL 拿出来看了下，大概为：

```sql
alter table article add column expired int default 0 null;
alter table article alter column expired drop default;
```

看着也没有问题，后来我带着疑问询问了一位世外高人的意见：

Q：

> 我为一张 MySQL 表加字段，语句为 alter table t add column c smallint default 0 null, 之后再通过 alter table t alter column c drop default value 移除该字段的默认值，此时往表里写入数据时 MySQL 报错：field c doesn't have a default value

A：

> 好的，这个问题的原因和解决方案如下：
>
> **原因分析：**
>
> 1. 你首先执行了 `alter table t add column c smallint default 0 null`。这时，字段 `c` 的定义是：允许为 `NULL`，并且有一个默认值 `0`。
> 2. 接着你执行了 `alter table t alter column c drop default value`。这条语句**只移除了字段 `c` 的默认值 `0`**，但 **没有改变** 字段 `c` 允许为 `NULL` 的属性。
> 3. 此时，字段 `c` 的定义变成了：允许为 `NULL`，但**没有默认值**。
> 4. 当你往表 `t` 里写入数据时，如果你执行的 `INSERT` 语句**没有显式地为字段 `c` 指定一个值**（无论是具体数值还是 `NULL`），并且你的 MySQL 服务器启用了 **严格 SQL 模式 (Strict SQL Mode)**（这是现代 MySQL 版本的默认设置），MySQL 就会报错 `Field 'c' doesn't have a default value`。
>
> **为什么在允许 NULL 的情况下还会报错？**
>
> 在严格 SQL 模式下，当你插入一行数据，并且没有为一个**没有定义默认值**的列提供值时（即使该列允许 `NULL`），MySQL **不会** 自动帮你插入 `NULL`。它要求你**显式地**提供一个值。你得到的错误信息虽然说的是“没有默认值”，但其更深层的原因是在严格模式下，省略一个没有默认值的列是禁止的，它不知道该插入什么。
>
> **解决方案：**
>
> 你有几种方法来解决这个问题：
>
> 1. **在 INSERT 语句中显式为字段 `c` 提供值：**
>
>    - 如果你想插入 `0`，可以写成 `INSERT INTO t (..., c, ...) VALUES (..., 0, ...)`。
>    - 如果你想插入 `NULL`，可以写成 `INSERT INTO t (..., c, ...) VALUES (..., NULL, ...)`。
>    - 或者，如果你想插入 `NULL` 并且 `c` 允许为 `NULL`，但不想在 VALUES 列表中显式写 `NULL`，你可以在 INSERT 语句中省略字段 `c`，然后通过重新添加一个默认值为 `NULL` 来解决（见方案 2）。
>
> 2. **重新为字段 `c` 添加一个默认值（可以默认为 NULL）：**
>
>    - 如果你希望在插入时不指定 
>
>      ```
>      c
>      ```
>
>       的值时，它自动变成 
>
>      ```
>      NULL
>      ```
>
>      ，可以执行：
>
>      SQL
>
>      ```
>      ALTER TABLE t ALTER COLUMN c SET DEFAULT NULL;
>      ```
>
>    - 如果你希望在插入时不指定 
>
>      ```
>      c
>      ```
>
>       的值时，它自动变成 
>
>      ```
>      0
>      ```
>
>      ，可以执行：
>
>      SQL
>
>      ```
>      ALTER TABLE t ALTER COLUMN c SET DEFAULT 0;
>      ```
>
>    在你重新设置了默认值后，再次执行不指定 `c` 的 INSERT 语句就不会报错了（它会使用你设置的新默认值）。
>
> 3. (不推荐) 关闭 MySQL 的严格 SQL 模式：
>
>    这不是一个好的做法，因为它可能隐藏其他潜在的数据问题，并导致数据不一致。但在某些特定情况下，你可以修改 sql_mode 配置，移除 等选项。但这需要服务器权限，且影响全局行为，通常不建议这样做。
>
> **总结：**
>
> 最安全和推荐的解决方案是 **方案 1** (在 INSERT 语句中显式指定值) 或 **方案 2** (根据需要重新设置默认值，如果希望省略时不报错的话)。错误是因为字段没有默认值，且在严格模式下，插入时省略该字段是非法的。

高人（Gemini 2.5）的回答令我豁然开朗，于是我查看了我使用的 MySQL 当前的 `sql_mode` 配置，果然如此，去掉 `STRICT_TRANS_TABLES` 之后，已经不再报错了（还是会有一条告警的信息）。



### Strict SQL Mode

MySQL 文档里面提到了 [`STRICT_TRANS_TABLES`](https://dev.mysql.com/doc/refman/8.4/en/sql-mode.html#sqlmode_strict_trans_tables) 带来了哪些影响：

> Enable strict SQL mode for transactional storage engines, and when possible for nontransactional storage engines. 
>
> Strict mode controls how MySQL handles invalid or missing values in data-change statements such as [`INSERT`](https://dev.mysql.com/doc/refman/8.4/en/insert.html) or [`UPDATE`](https://dev.mysql.com/doc/refman/8.4/en/update.html). A value can be invalid for several reasons. For example, it might have the wrong data type for the column, or it might be out of range. A value is missing when a new row to be inserted does not contain a value for a non-`NULL` column that has no explicit `DEFAULT` clause in its definition. (For a `NULL` column, `NULL` is inserted if the value is missing.) Strict mode also affects DDL statements such as [`CREATE TABLE`](https://dev.mysql.com/doc/refman/8.4/en/create-table.html).

对于字段默认值处理如下：

> - If strict SQL mode is enabled, an error occurs for transactional tables and the statement is rolled back. For nontransactional tables, an error occurs, but if this happens for the second or subsequent row of a multiple-row statement, the preceding rows are inserted.
> - If strict mode is not enabled, MySQL sets the column to the implicit default value for the column data type.



### 如何避免

最后总结下如何避免这种情况的发生：



#### 数据库与版本环境分离

当然，如果新版本使用表结构迁移操作时使用与之前不同的数据库就不会出现这个问题了。



#### 改变 `sql_mode` 配置

从 `sql_mode` 中移除 `STRICT_TRANS_TABLES` 也可以有效的解决这种问题，但是可能会带来一些意想不到的行为，比如，对于明确使用   `NOT NULL` 定义的字段，`INSERT` 时不指定也不会报错：

```sql
CREATE TABLE t (i INT NOT NULL);

INSERT INTO t VALUES();  -- It's ok!
```



#### 使用 `INSERT IGNORE`

使用 `INSERT IGNORE` 同样可以让 MySQL 不抛出异常，带来的其他影响可以参考：[Comparison of the IGNORE Keyword and Strict SQL Mode](https://dev.mysql.com/doc/refman/8.4/en/sql-mode.html#ignore-strict-comparison)



#### 使用 `db_default` 参数（django 5.0+）

我找到了一篇 django 社区[对于在数据库层面保留默认值问题的讨论](https://code.djangoproject.com/ticket/28000)，同时也讨论了保留的可能，最终在 5.0 版本支持保留数据库的默认值，而不是在添加后又 `drop default`， 如果你使用的是 5.0+ 的版本，可以在定义时使用 `db_default` 参数而不是 `default`：

```python
class Article(models.Model):
    
    # 新增字段
    expired = models.IntegerField(null=True, db_default=0)
```



#### 修改字段可为 `NULL`

很奇怪，是不是？我不是已经定义字段可为 `NULL` 了吗？django 显然没有把 `null` 这个定义也 drop 掉，但是，当我再次使用下面的 SQL 更新字段定义后，再次写入就不会报错：

```sql
alter table article modify column expired int null;
```

至于原因，我们可以通过 `show create table article` 窥见一二，在执行 `modify` 语句之前，我通过 `show create table article` 查看当前的表的定义如下：

```sql
create table article (
	...
    expired int
)
```

字段 `expired` 后面没有 `NOT NULL`，说明默认就是 `NULL`，但是当我执行 `modify` 语句后，定义变成了：

```sql
create table article (
	...
    expired int default null
)
```

字段 `expired` 的默认值变为了 `null`，所以我们也可以通过 `show create table` 语句确认相关字段是否有默认值（即使可为 `NULL`），以及是否需要在 `strict mode` 下显式的指定该字段的值。