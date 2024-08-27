---
layout: post
title: [转] MySQL binlog 日志自动清理及手动删除
date: 2024-06-21 21:41 +0800
categories: [mysql]
tags: [MySQL]
cnblogid: 18261558
---
### 参考
转载自 [mysql binlog日志自动清理及手动删除 - 景岳 - 博客园](https://www.cnblogs.com/xxoome/p/9802684.html)



### 说明
当开启 `mysql` 数据库主从时，会产生大量如 `mysql-bin.00000* log` 的文件，这会大量耗费您的硬盘空间。
```
mysql-bin.000001
mysql-bin.000002
mysql-bin.000003
mysql-bin.000004
mysql-bin.000005
…
```
有三种解决方法：
1. 关闭 `mysql` 主从，关闭 `binlog;`
2. 开启 `mysql` 主从，设置 `expire_logs_days;`
3. 手动清除 `binlog` 文件
   ```sql
   PURGE MASTER LOGS TO 'MySQL-bin.010'
   ```



### 实现
#### 关闭 `mysql` 主从，关闭 `binlog`
```bash
vim /etc/my.cnf  # 注释掉log-bin, binlog_format

# Replication Master Server (default)
# binary logging is required for replication
# log-bin=mysql-bin
# binary logging format - mixed recommended
# binlog_format=mixed
```
然后重启数据库。



#### 开启 `mysql` 主从，设置 `expire_logs_days`
```bash
vim /etc/my.cnf  # 修改 expire_logs_days, x 是自动删除的天数，一般将 x 设置为短点，如 10

# expire_logs_days = x  //二进制日志自动删除的天数。默认值为 0,表示“没有自动删除”
```
此方法需要重启 `mysql`，附录有关于 `expire_logs_days` 的英文说明
当然也可以不重启 `mysql`，开启 `mysql` 主从，直接在 `mysql` 里设置 `expire_logs_days`
```sql
> show binary logs;
> show variables like '%log%';
> set global expire_logs_days = 10;
```



#### 手动清除 `binlog` 文件
```sql
-- 删除10天前的 MySQL binlog 日志
-- 更多用法参考
PURGE MASTER LOGS BEFORE DATE_SUB(CURRENT_DATE, INTERVAL 10 DAY);
show master logs;
```
也可以重置 `master`，删除所有 `binlog` 文件：
```sql
reset master;  
```



### 附录：
#### expire_logs_days 英文说明
> Where X is the number of days you’d like to keep them around. I would recommend 10, but this depends on how busy your MySQL server is and how fast these log files grow. 
> Just make sure it is longer than the slowest slave takes to replicate the data from your master.
>
> Just a side note: You know that you should do this anyway, but make sure you back up your mysql database. 
> The binary log can be used to recover the database in certain situations; so having a backup ensures that if your database server does crash, you will be able to recover the data.



#### PURGE MASTER LOGS 手动删除用法及示例
`MASTER` 和 `BINARY` 是同义词
```sql
> PURGE {MASTER | BINARY} LOGS TO 'log_name'
> PURGE {MASTER | BINARY} LOGS BEFORE 'date'
```
删除指定的日志或日期之前的日志索引中的所有二进制日志。这些日志也会从记录在日志索引文件中的清单中被删除 `MySQL BIN-LOG` 日志，这样被给定的日志成为第一个。
实例：
```sql
-- 清除MySQL-bin.010日志
PURGE MASTER LOGS TO 'MySQL-bin.010';  

-- 清除2008-06-22 13:00:00前binlog日志
PURGE MASTER LOGS BEFORE '2008-06-22 13:00:00';   

-- 清除3天前binlog日志BEFORE，变量的date自变量可以为'YYYY-MM-DD hh:mm:ss'格式
PURGE MASTER LOGS BEFORE DATE_SUB( NOW( ), INTERVAL 3 DAY);  
```



#### 清除 `binlog` 时，对从 `mysql` 的影响
> 如果您有一个活性的从属服务器，该服务器当前正在读取您正在试图删除的日志之一，则本语句不会起作用，而是会失败，并伴随一个错误。
> 不过，如果从属服务器是休止的，并且您碰巧清理了其想要读取的日志之一，则从属服务器启动后不能复制。当从属服务器正在复制时，本语句可以安全运行。您不需要停止它们。

