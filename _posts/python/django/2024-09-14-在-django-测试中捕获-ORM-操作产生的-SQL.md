---
layout: post
title: "在 django 测试中捕获 ORM 操作产生的 SQL"
date: 2024-09-14 16:24 +0800
categories: [python, django]
tags: [python, django]
---



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

