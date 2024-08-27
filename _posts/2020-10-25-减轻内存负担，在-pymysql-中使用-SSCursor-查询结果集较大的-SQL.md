---
layout: post
title: 减轻内存负担，在 pymysql 中使用 SSCursor 查询结果集较大的 SQL
date: 2020-10-25 21:04 +0800
categories: [python]
tags: []
cnblogid: 13875223
---
### 前言

默认情况下，使用 pymysql 查询数据使用的游标类是 Cursor，比如：

```python
import pymysql.cursors

# 连接数据库
connection = pymysql.connect(host='localhost',
                             user='user',
                             password='passwd',
                             db='db',
                             charset='utf8mb4')

try:
    with connection.cursor() as cursor:
        # 读取所有数据
        sql = "SELECT `id`, `password` FROM `users` WHERE `email`=%s"
        cursor.execute(sql, ('webmaster@python.org',))
        result = cursor.fetchall()
        print(result)
finally:
    connection.close()
```

这种写法会将查询到的所有数据写入内存中，若在结果较大的情况下，会对内存造成很大的压力，所幸 pymysql 实现了一种 SSCursor 游标类，它允许将查询结果按需返回，而不是一次性全部返回导致内存使用量飙升。

### SSCursor

官方文档的解释为：

> Unbuffered Cursor, mainly useful for queries that return a lot of data,
> or for connections to remote servers over a slow network.
>
> Instead of copying every row of data into a buffer, this will fetch
> rows as needed. The upside of this is the client uses much less memory,
> and rows are returned much faster when traveling over a slow network
> or if the result set is very big.
>
> There are limitations, though. The MySQL protocol doesn't support
> returning the total number of rows, so the only way to tell how many rows
> there are is to iterate over every row returned. Also, it currently isn't
> possible to scroll backwards, as only the current row is held in memory.

大致翻译为：无缓存的游标，主要用于查询大量结果集或网络连接较慢的情况。不同于普通的游标类将每一行数据写入缓存的操作，该游标类会按需读取数据，这样的好处是客户端消耗的内存较小，而在网络连接较慢或结果集较大的情况下，数据的返回也会更快。当然，缺点就是它不支持返回结果的行数（也就是调用 `rowcount` 属性将不会得到正确的结果，一共有多少行数据则需要全部迭代完成才能知道），当然它也不支持往回读取数据（这也很好理解，毕竟是生成器嘛）。

它的写法如下：

```python
from pymysql.cursors import SSCursor

connection = pymysql.connect(host='localhost',
                             user='user',
                             password='passwd',
                             db='db',
                             charset='utf8mb4')

# 创建游标
cur = connection.cursor(SScursor)
cur.execute('SELECT * FROM test_table')

# 读取数据
# 此时的 cur 对内存消耗相对 Cursor 类来说简直微不足道
for data in cur:
    print(data)
```
本质上对所有游标类的迭代都是在不断的调用 `fetchone` 方法，不同的是 SSCursor 对 `fetchone` 方法的实现不同罢了。这一点查看源码即可发现：
Cursor 类 `fetchone` 方法源码（可见它是在根据下标获取列表中的某条数据）：

![](https://raw.githubusercontent.com/kingron117/pics/master/for/pylittleimage-20201025192721127.png)

SSCursor 类 `fetchone` 方法源码（读取数据并不做缓存）：

![](https://raw.githubusercontent.com/kingron117/pics/master/for/pylittleimage-20201025192825032.png)

### 跳坑

当然，如果没有坑就没必要为此写一篇文章了，开开心心的用着不香吗。经过多次使用，发现在使用 SSCursor 游标类（以及其子类 SSDictCursor）时，需要特别注意以下两个问题：

#### 1. 读取数据间隔问题

每条数据间的读取间隔若超过 60s，可能会造成异常，这是由于 MySQL 的 `NET_WRITE_TIMEOUT` 设置引起的错误（该设置值默认为 60），如果读取的数据有处理时间较长的情况，那么则需要考虑更改 MySQL 的相关设置了。（tips: 使用 sql `SET NET_WRITE_TIMEOUT = xx` 更改该设置或修改 MySQL配置文件）

#### 2. 读取数据时对数据库的其它操作行为

因为 SSCursor 是没有缓存的，只要结果集没有被读取完成，就不能使用该游标绑定的连接进行其它数据库操作（包括生成新的游标对象），如果需要做其它操作，应该使用新的连接。比如：

```python
from pymysql.cursors import SSCursor

def connect():
    connection = pymysql.connect(host='localhost',
                                 user='user',
                                 password='passwd',
                                 db='db',
                                 charset='utf8mb4')
    return connection

conn1 = connect()
conn2 = connect()

cur1 = conn1.cursor(SScursor)
cur2 = conn1.cursor()

with conn1.cursor(SSCursor) as ss_cur, conn2.cursor() as cur:
	try:
        ss_cur.execute('SELECT id, name FROM test_table')

        for data in ss_cur:
            # 使用 conn2 的游标更新数据
            if data[0] == 15:
                cur.execute('UPDATE tset_table SET name="kingron" WHERE id=%s', args=[data[0])

            print(data)
    finally:
    	conn1.close()
    	conn2.close()
```

### 参考

1. [Cursor Objects — PyMySQL 0.7.2 documentation](https://pymysql.readthedocs.io/en/latest/modules/cursors.html)
2. [Using SSCursor (streaming cursor) to solve Python using pymysql to query large amounts of data leads to memory usage is too high](https://www.programmersought.com/article/215831210/)
