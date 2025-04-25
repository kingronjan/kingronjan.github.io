---
categories:
- database
- oracle
date: 2025-03-03 18:14 +0800
id: b12be78c-5d9a-48a5-9a7c-23239076d988
layout: post
tags:
- database
- oracle
title: The null comparison on where clause
---

I have been using [cx_Oracle](https://github.com/oracle/python-cx_Oracle) to handle Oracle queries, and recently I encountered an issue regarding the comparison of null values in the WHERE condition.

Below are the table I am using:

```sql
sql > select * from s.tab1
c1				c2			c3
----------------------------------
12009249172906	  1		 	 NULL
```

I defined a Python function to facilitate the querying process:

```python
import cx_Oracle

def query(sql, params=None):
    with cx_Oracle.Connection(...) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params) if params else cur.execute(sql)
            return cur.fetchall()
```

Initially, I executed the following SQL query on the table, expecting to retrieve a single row of data, but the result returned was empty:

```python
>>> query('select * from s.tab1 where (c2, c3) in ((:p00, :p01))', [1, None])
()
```

Then I realized there might be an issue. When I use `(c2, c3) IN (1, null)`, it is essentially performing `c2 = 1 AND c3 = null`, ss for why `c3 = null` doesn't work, you can refer to [this article](https://stackoverflow.com/questions/9581745/sql-is-null-and-null).

What should I do? I don't want to change the parameter passing logic or concatenate a long SQL query like: `WHERE (c2 IS NULL AND c3 = :p00) OR (c2 = :p10 AND c3 IS NULL) ...`. Therefore, I Googled the issue and found a few solutions that seemed quite suitable.

One solution is to use the `NVL` function:

```sql
>>> query('select * from s.tab1 where (nvl(c2, 0), nvl(c3, 0)) in ((:p00, :p01))', [1, 0])
((12009249172906, 1, None),)
```

The `NVL` function checks whether the value of the field is null; if it is, it converts it to 0, allowing the comparison to work. However, it is important to note that 0 is too common a value. In practical applications, you may need to specify a more complex value to avoid retrieving unexpected data.

BE CAREFUL:

The `nvl` value's data type must matched the column's data type, otherwise the error will raised:

```
ORA-01722: invalid number
```



### Reference

1. [sql - Determine Oracle null == null - Stack Overflow](https://stackoverflow.com/questions/191640/determine-oracle-null-null)