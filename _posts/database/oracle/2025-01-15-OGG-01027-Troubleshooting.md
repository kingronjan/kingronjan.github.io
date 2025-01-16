---
categories:
- database
- oracle
date: 2025-01-15 22:11 +0800
id: a415bc64-ff97-42ae-9c1b-c8e0445834cf
layout: post
tags:
- database
- oracle
title: OGG-01027 Troubleshooting
---

When using Oracle GoldenGate for data extraction, sometimes the following log may appear:

```
2020-10-30T18:10:08.469BEIST WARNING OGG-01027 Long Running Transaction: XID 993.6.69598, Items 1,Extract EX0123, Redo Thread 1, SCN 3918.1906392113 (16829588257841),Redo Seq #631053, Redo RBA 506349584.
```

By using the `INFO` command, you can see that there is a large value of `Lag at Chkpt` in the process：

```
ggsci> info EX0123
Lag at Chkpt: 155:17:01
...
```

The following lists several troubleshooting approaches for this issue.



### Check if there are any long-running transactions in the database

You can use the following SQL to check if there are any long-running transactions in the database (**for oracle**):

```sql
sql> select
	a.sid,
	a.serial#,
	a.username,
	b.addr,
	b.USED_UBLK,
	b.USED_UREC,
	b.START_TIME,
	b.xidusn,
	b.XIDSLOT, 
	b.xidsqn
from
	v$transaction b, 
	v$session a
where b.addr in (select a.taddr from v$session a where a.sid = '') and b.addr=a.taddr 
order by start_time
```

If there are long-running transactions, they should be promptly committed or rolled back.



### Check the transactions currently being processed

The syntax is:

```
send extract <group name>, showtrans [thread n] [count n]
```

For example：

```
ggsci> send extract EX0123, showtrans

------------------------------------
XID:			0.14.13.18652286
Items:			0
Extract:		EX0123
Redo Thread:	1
Start Time:		2025-01-08 T 09:13:41.0002
SCN:		    4436.1276535842(19053751460898)
Redo Seq:		1036794
Redo RBA:		719467324
Status:			Running 

...
```

You can see several transactions that are currently being processed, and you can also use the following command to view the latest information:

```sql
ggsci> send extract EX0123, status
```



##### Use LogMiner to mine transaction logs and locate the problematic SQL

If the transaction can no longer be found through the above SQL query during troubleshooting, you can try using LogMiner to mine the archived logs and locate the relevant SQL. The specific steps are as follows:

1. View the file path of archived logs

   You can use the `showtrans` or `info <exgroup>, showch` commands to view the current extracted `redo seq`.

   ```sql
   sql> SELECT THREAD#, SEQUENCE#, NAME, FIRST_CHANGE#, NEXT_CHANGE#, STATUS
   	FROM V$ARCHIVED_LOG
   	WHERE  SEQUENCE# = 377;
   ```
   
   Example query result:

   ```
   
   THREAD# SEQUENCE# NAME                                        FIRST_CHANGE#     NEXT_CHANGE# STATUS
   ------- --------- ---------------------------------------- ---------------- ---------------- ----------
         1       377 +FRADG/honor/archivelog/2022_05_07/threa      21489950070      21489950244 A
                     d_1_seq_377.390.1104057109
   ```
   
2. Create a LogMiner session

   ```sql
   -- add archive file
   BEGIN
   
   dbms_logmnr.add_logfile(logfilename=>'+FRADG/honor/archivelog/2022_05_07/thread_1_seq_377.390.1104057109',options=>dbms_logmnr.NEW);
   
   END;
   
   /
   
   -- set scn scale, you can use the value of FIRST_CHANGE#, NEXT_CHANGE#
   BEGIN
   
   dbms_logmnr.START_LOGMNR(
       STARTSCN => '21489950070', 
       ENDSCN => '21489950244', 
       OPTIONS => DBMS_LOGMNR.DICT_FROM_ONLINE_CATALOG
   );
   
   END;
   ```

4. View the SQL corresponding to a specific `XID` (Transaction ID) using LogMiner

   ```sql
   -- ex: XID=138.29.311639792
   sql> SELECT SESSION#,SERIAL#,sql_redo,XIDUSN,XIDSLT,XIDSQN  
   	FROM v$logmnr_contents where XIDUSN='138' and XIDSLT='29' and XIDSQN='311639792';
   ```

   Example query result:

   ```
   SESSION#   SERIAL#  sql_redo  					    XIDUSN XIDSLT  XIDSQN
   --------   -------  ------------------------------ 	  ----  ------  ----------------
    5378       9303    update "USER_1"."TABLE_A" set ...  138   29     311639792
   ```

5. End LogMiner session

   ```sql
   EXECUTE dbms_logmnr.END_LOGMNR;  
   ```

   

### Skip the transactions currently being processed

If necessary, you can skip the transactions currently being processed by the ongoing process.

The `Items` field of the `SHOWTRANS` output shows the number of operations in the transaction that have been captured by Oracle GoldenGate so far, not the total number of operations in the transaction. If none of the operations are for configured tables, or if only some of them are, then `Items` could be 0 or any value less than the total number of operations.

You may have noticed a parameter called `skipemptytrans` that can help handle situations like `Item = 0`, however, according to the [official documentation](https://asktom.oracle.com/ords/asktom.search?tag=how-does-skipemptytrans-work), `skipemptytrans` has been made a hidden parameter as of the GG 23ai release and its use is strongly discouraged, as it will likely lead to data divergence.

The command to skip the transactions currently being processed is:

```
# 0.14.13.18652286 is the XID field of the showtrans output.
ggsci> send extract EX0123, skiptrans 0.14.13.18652286
```

To use `SKIPTRANS`, the specified transaction must be the oldest one in the list of transactions shown with `SHOWTRANS`. You can repeat the command for other transactions in order of their age.

If you don't want the confirmation dialog to appear, you can add the `FORCE` keyword at the end:

```
ggsci> send extract EX0123, skiptrans 0.14.13.18652286 force
```

After using `SKIPTRANS`, wait at least five minutes if you intend to issue `SEND EXTRACT` with `FORCESTOP`. Otherwise, the transaction is still present. Note that skipping a transaction may cause data loss in the target database.

In addition to `skiptrans`, you can also use `forcetrans` to force the transaction to be considered as committed, the syntax is:

```
SEND EXTRACT group_name FORCETRANS transaction_ID [THREAD n] [FORCE]
```



### Reference

1. [Oracle GoldenGate (OGG)——OGG运维手册 - 拓扑园](https://www.topunix.com/post-607.html "Oracle GoldenGate (OGG)——OGG运维手册 - 拓扑园")
2. [查看OGG当前正在处理的事物_oracle ogg查看事物-CSDN博客](https://blog.csdn.net/weixin_44524950/article/details/86483585 "查看OGG当前正在处理的事物_oracle ogg查看事物-CSDN博客")
3. [OGG集成抽取模式丢失归档处理_ITPUB博客](https://blog.itpub.net/31439444/viewspace-2892888/ "OGG集成抽取模式丢失归档处理_ITPUB博客")
4. [OGG数据同步异常问题总结 - 墨天轮](https://www.modb.pro/db/40810 "OGG数据同步异常问题总结 - 墨天轮")
5. [大事务导致的OGG抽取进程每天7：39定时延时，运行极其缓慢_ITPUB博客](https://blog.itpub.net/69996316/viewspace-2936710/ "大事务导致的OGG抽取进程每天7：39定时延时，运行极其缓慢_ITPUB博客")
6. [SEND EXTRACT](https://docs.oracle.com/en/middleware/goldengate/core/19.1/gclir/send-extract.html "SEND EXTRACT")
7. [how does SKIPEMPTYTRANS work? - Ask TOM](https://asktom.oracle.com/ords/asktom.search?tag=how-does-skipemptytrans-work "how does SKIPEMPTYTRANS work? - Ask TOM")