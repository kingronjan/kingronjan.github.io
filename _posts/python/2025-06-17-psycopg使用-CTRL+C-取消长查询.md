---
categories:
- python
date: 2025-06-17 09:04 +0800
id: 545d089a-fd51-49ab-b355-8e789c5d3dd7
layout: post
tags:
- python
title: psycopg使用 CTRL+C 取消长查询
---

在使用 **Psycopg** 驱动连接 PostgreSQL 数据库时，如果遇到慢查询，或者连接时出现网络超时等，往往需要等待很长时间，而且无法使用 CTRL+C 中断，只能被动等待或者 kill 查询程序，最近查阅官方文档发现原来官方也对这一情况提供了解决办法：

> Normally the interactive shell becomes unresponsive to Ctrl-C when running a query. Using a connection in green mode allows Python to receive and handle the interrupt, although it may leave the connection broken, if the async callback doesn’t handle the `KeyboardInterrupt` correctly.
>
> Starting from psycopg 2.6.2, the [`wait_select`](https://www.psycopg.org/docs/extras.html#psycopg2.extras.wait_select) callback can handle a Ctrl-C correctly. For previous versions, you can use [this implementation](https://www.psycopg.org/articles/2014/07/20/cancelling-postgresql-statements-python/).
>
> ```
> >>> psycopg2.extensions.set_wait_callback(psycopg2.extras.wait_select)
> >>> cnn = psycopg2.connect('')
> >>> cur = cnn.cursor()
> >>> cur.execute("select pg_sleep(10)")
> ^C
> Traceback (most recent call last):
>   File "<stdin>", line 1, in <module>
>   QueryCanceledError: canceling statement due to user request
> 
> >>> cnn.rollback()
> >>> # You can use the connection and cursor again from here
> ```

简单的说 Psycopg 默认情况下并没有在查询时处理 Interrupt 信号，需要设置为 `select` 模式，Interrupt 才会被正常处理。



### Reference

1. [Frequently Asked Questions — Psycopg 2.9.10 documentation](https://www.psycopg.org/docs/faq.html)