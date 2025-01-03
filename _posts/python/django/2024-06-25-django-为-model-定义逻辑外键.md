---
categories:
- python
- django
cnblogid: 18267977
date: 2024-06-25 22:36 +0800
id: 6d19d11a-340f-4ba1-b97e-5d2f6f0d116b
layout: post
tags:
- django
- orm
- python
title: django | 为 model 定义逻辑外键
---

### 问题
想要在 `orm` 中定义外键，便于关联查询，但不想在数据库中生成实际的外键约束。



### 解决方式
`Django` 的 `ForeignKey` 和数据库的 `FOREIGN KEY` 并不一样。`Django` 的 `ForeignKey` 是一种逻辑上的两个表的关联关系，可以指定是否使用数据库的 `FOREIGN KEY` 约束。
如：
```python
from django.db import models


class Province(models.Model):
    name = models.CharField(max_length=16)

    def __unicode__(self):
        return self.name


class City(models.Model):
    name = models.CharField(max_length=16)
    province = models.ForeignKey(Province, null=True, on_delete=models.DO_NOTHING, related_name='cities', db_constraint=False)
```
如果 `ForeignKey` 不添加 `db_constraint=False` 参数，会在数据库中使用外键约束。
另外，`ForeignKey` 的 `on_delete` 参数默认为 `on_delete=models.CASCADE`，表示使用数据库的级联删除，使用 `on_delete=models.SET_NULL` 可以使删除 `Province` 时将关联的 `City` 表对应的 `province_id` 值设为 `NULL`。
使用这种方式不会破坏 `Django` 的反向关联查询。



### 参考
[Django 的 ForeignKey 与数据库的 FOREIGN KEY约束_我的总结积累与分享-CSDN博客](https://blog.csdn.net/Focus_on_linux/article/details/90521503)