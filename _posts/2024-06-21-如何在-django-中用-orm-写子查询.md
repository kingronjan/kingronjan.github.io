---
layout: post
title: 如何在 django 中用 orm 写子查询
date: 2024-06-21 08:37 +0800
categories: [python, django]
tags: [django, orm, python]
cnblogid: 18259854
---
如果想实现下面的 SQL：

```sql
SELECT * FROM book WHERE author_id IN (SELECT id FROM author WHERE name LIKE 'kingron%')
```

可以这样写：

```python
authores = Author.objects.filter(name__startswith='kingron')

# 默认使用 pk 作为查询的列
books = Book.objects.filter(author_id__in=authores)
```

也可以通过 values 指定子查询的列
```python
authores = authores.values('name')
books = Book.objects.filter(author_name__in=authores)
```

对应的 SQL 类似于：
```sql
SELECT * FROM book WHERE author_name IN (SELECT name FROM author WHERE name LIKE 'kingron%')
```

