---
layout: post
title: oracle stream pool size
date: 2024-07-17 18:09 +0800
categories: [oracle]
tags: [oracle]
cnblogid: 18308044
---
See: [STREAMS_POOL_SIZE](https://docs.oracle.com/en/database/oracle/oracle-database/21/refrn/STREAMS_POOL_SIZE.html)

---



## STREAMS_POOL_SIZE 参数详解

STREAMS_POOL_SIZE 初始化参数用于帮助确定 Streams 池的大小。它是一个大整数类型参数，其语法为 STREAMS_POOL_SIZE = integer [K | M | G]，默认值为 0。该参数可通过 ALTER SYSTEM 修改，但在可插拔数据库 (PDB) 中不可修改。

该参数的取值范围为最小值 0（大于 0 的值将向上取整到最近的粒度大小），最大值为操作系统相关的。

**自动共享内存管理 (Automatic Shared Memory Management)**

当 SGA_TARGET 初始化参数设置为非零值时，Oracle 的自动共享内存管理功能会管理 Streams 池的大小。如果 STREAMS_POOL_SIZE 初始化参数也设置为非零值，则自动共享内存管理会使用此值作为 Streams 池的最小值。

如果 SGA_TARGET 设置为非零值，而 STREAMS_POOL_SIZE 未指定或设置为 NULL 值，则自动共享内存管理会将 0 字节用作 Streams 池的最小值。

**手动设置 Streams 池大小**

如果 STREAMS_POOL_SIZE 初始化参数设置为非零值，而 SGA_TARGET 参数设置为 0，则 Streams 池的大小将由 STREAMS_POOL_SIZE 参数指定的字节数确定。

**默认行为**

如果 STREAMS_POOL_SIZE 和 SGA_TARGET 初始化参数均设置为 0，则在数据库中首次请求 Streams 池内存时，将从缓冲区高速缓存中转移等于共享池 10% 的内存量到 Streams 池。

**使用 Streams 池的组件**

使用 Streams 池的产品和功能包括 Oracle GoldenGate、XStream、Oracle 高级排队和 Oracle Data Pump。

**内存分配**

Streams 池是一个共享资源，进程从 Streams 池中使用的内存量由应用程序决定。对于 Oracle GoldenGate 或 XStream，可以控制捕获或应用参数 MAX_SGA_SIZE。对于 Oracle 高级排队，请使用 dbms_aqadm 包中的过程来控制所需的 Streams 池数量。

**更多信息**

有关为 XStream Out 配置配置 Streams 池的信息，请参见《Oracle 数据库 XStream 指南》。

有关为 XStream In 配置配置 Streams 池的信息，请参见《Oracle 数据库 XStream 指南》。

有关 dbms_aqadm 包的更多信息，请参见《Oracle 数据库 PL/SQL 包和类型参考》。

