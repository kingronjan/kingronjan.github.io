---
layout: post
title: "从 mysql 读取数据并通过 stream_load 写入到 doris"
date: 2024-10-18 17:26 +0800
categories: [python, snippets]
tags: [python, snippets]
hidden: true
---

```python
import requests
import uuid
import pymysql

url = 'http://<doris-fe-address>/api/<database>/<table>/_stream_load'
columns = 'id, time1, n, column_4, column_5'

headers = {
    'label': str(uuid.uuid4()),
    'Expect': '100-continue',
    'columns': columns,
    'column_separator': ',',
}

# 读取源端数据
query = f"select {columns} from <mysql-table> where id = '1'"

with pymysql.connect(host='<mysql-host>', port=3309, user='<mysql-user>', passwd='<mysql-pwd>') as cursor:
    cursor.execute(query)
    source_data = cursor.fetchone()
    source_data = ','.join(str(value) for value in source_data)

data = f"""
{columns}
{source_data}
"""

auth = ('<doris-user>', '<doris-passwd>')

resp = requests.put(url, headers=headers, data=data, auth=auth)

# 需要再次携带 auth 信息访问重定向之后的 url (resp.url) 
# 否则会返回认证失败
resp = requests.put(resp.url, headers=headers, data=data, auth=auth)
print(resp.url, resp.status_code)
print(resp.text)

```

