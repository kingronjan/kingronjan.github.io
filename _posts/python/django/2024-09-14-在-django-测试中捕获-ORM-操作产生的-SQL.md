---
categories:
- python
- django
date: 2024-09-14 16:24 +0800
id: 1dcda07b-7823-4a21-a1fd-857c9ac73c89
layout: post
tags:
- python
- django
title: 在 django 测试中捕获 ORM 操作产生的 SQL
---

### 方法

示例代码：

```python
from django.db import connection
from django.test.utils import CaptureQueriesContext

def test_no_update_when_get_items():
    
    with CaptureQueriesContext(connection) as ctx:
        # do get items
        ...
        
        assert 'UPDATE' not in str(ctx.captured_queries)

```



其中，`ctx.captured_queries` 是一个元素为 `{'sql': <实际执行的SQL>, 'time': <执行的时间, str 类型>}` 的列表。



> 如果在 logging 中为 `logger` `django.db.backends` 设置了 `level` 且没有被过滤，该方法同样也会在实际触发时在日志中打印对应的 SQL，如果你遇到过虽然配置过 settings 中的 `LOGGING`，但 ORM 的 SQL 任然没有出现在日志中，不妨试试该方法
{: .prompt-info }



### See also

##### [基于Python探针完成调用库的数据提取 - So1n blog](https://so1n.me/2020/11/18/%E5%9F%BA%E4%BA%8EPython%E6%8E%A2%E9%92%88%E5%AE%8C%E6%88%90%E8%B0%83%E7%94%A8%E5%BA%93%E7%9A%84%E6%95%B0%E6%8D%AE%E6%8F%90%E5%8F%96/)

通过 hook python 的导入行为来改写 mysql 驱动包的查询方法，可以打印出每次查询的语句、参数和耗时