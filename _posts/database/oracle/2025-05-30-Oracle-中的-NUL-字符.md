---
categories:
- database
- oracle
date: 2025-05-30 17:11 +0800
id: bacb74a0-718b-4caf-84b4-97a8b1d913bd
layout: post
tags:
- database
- oracle
title: Oracle 中的 NUL 字符
---

有次同事找到我说我们的数据比对工具有问题，命名两个相同的值但比对出来不一致：



这是 Oracle 中的数据：

```sql
oracle> select id, name from test_table where id = 1;
+----+------+
| ID | NAME |
+----+------+
| 1  | abc  |
+----+------+
```



这是 PG 中的数据：

```sql
postgres> select id, name from test_table where id = 1;
+----+------+
| id | name |
+----+------+
| 1  | abc  |
+----+------+
```



咋一看还真是，字段 `name` 的值在两个库看着都是一样的，经过一番自我怀疑，发现原来是 `NUL` 字符在搞鬼。原来在 Oracle 中，`NAME` 字段的末尾包含了一个 `\x00` 字符(ASCII 值 0，即 `NUL` 字符)虽然可以存储在 VARCHAR 字段中，但它是一个非打印字符，直接查询时可能会显示不出来。但是我们可以通过一些其他的方式来发现它，比如，用 `length` 函数：

```sql
oracle> select id, name, length(name), length('abc') from test_table where id = 1;
+----+------+--------------+---------------+
| ID | NAME | LENGTH(NAME) | LENGTH('ABC') |
+----+------+--------------+---------------+
| 1  | abc  | 4            | 3             |
+----+------+--------------+---------------+
```



可以看到，我们看到的 NAME 值是 `abc`，`length('abc') = 3`，但是 `length(name) = 4`，说明 NAME 中包含了我们看不见的字符。怎么确定它是不是 `NUL` 字符呢，可以用 `replace` 函数将 `NUL` 字符替换成其他字符，如果替换成功，那么就是它了：



```sql
oracle> select id, name, replace(name, chr(0), '<nul>') from test_table where id = 1;
+----+------+------------------------------+
| ID | NAME | REPLACE(NAME,CHR(0),'<NUL>') |
+----+------+------------------------------+
| 1  | abc  | <nul>abc                     |
+----+------+------------------------------+
```

注意，如果直接使用 `\x00`，这里替换是不会成功的，应该使用 `chr(0)` 函数，它表示 ASCII 0，`\x00` 是它的十六进制表示。



顺带一提，在 PG 中，默认情况下是不允许把 `NUL` 字符保存到 TEXT 或 VARCHAR 等字符串字段中的，如果写入时包含了 `NUL` 字符，PG 会抛出异常提示你不能这么做：

```sql
postgres> insert into test_nul_char values (1, 'abc' || chr(0));
ERROR: null character not permitted
```

如果需要在 PG 中保存 `NUL` 字符，需要使用 BYTEA 类型的字段。



至于为什么会有 `NUL` 这种字符，查阅资料发现，它的存在原因可以追溯到计算机科学和字符编码的早期历史，特别是在 ASCII 标准中，作为 ASCII 标准的一部分，它主要有下面几个作用：

- 字符串终止符，用于表示字符结尾
- 填充字符，早期串行通信和数据传输中，`NUL` 字符有时用于填充数据块，以确保数据以特定长度传输
- 设备控制，在一些低级通信协议和设备控制中，`NUL` 字符可能被用来表示特定的控制信号，如设备重置或等待