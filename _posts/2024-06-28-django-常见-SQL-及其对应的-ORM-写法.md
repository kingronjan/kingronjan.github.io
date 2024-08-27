---
layout: post
title: django | 常见 SQL 及其对应的 ORM 写法
date: 2024-06-28 23:35 +0800
categories: [python, django]
tags: [django, MySQL, orm, python]
cnblogid: 18274515
---
#### 1. 子查询用 count 作为返回值
期望的 SQL 类似于:
```sql
select (select count(*) from child where child.pid = parent.id) as auth_exists from parent
```
写法：
```sql
subquery = Subquery(Child.objects.filter(parent_id=OuterRef('id')).order_by()
                    .values('parent').annotate(count=Count('pk'))
                    .values('count'), output_field=IntegerField())
Parent.objects.annotate(child_count=Coalesce(subquery, 0))
```
解释：
- `.order_by()` 取消可能存在排序的列
- 第一个 `values` 调用 `.values('parent')` 生成一个分组
- `.annotate(count=Count('pk'))` 生成 `count` 的列
- 第二个 `values` 调用 `.values('count')` 将 `count` 作为读出的列
- `Coalesce` 返回 `count` 的结果，如果是 `null`，则返回 `0`

参考：[mysql - Django Count lines in a Subquery - Stack Overflow](https://stackoverflow.com/questions/65600321/django-count-lines-in-a-subquery)



#### 2. 分组并 COUNT 每个组的数量
期望的 SQL 类似于:
```sql
SELECT player_type, COUNT(*) FROM players GROUP BY player_type;
```
写法:
```python
result = Books.objects.values('author')
                      .order_by('author')
                      .annotate(count=Count('author'))
```
参考：[Django Tutorial => GROUB BY ... COUNT/SUM Django ORM equivalent (riptutorial.com)](https://riptutorial.com/django/example/30595/groub-by-----count-sum-django-orm-equivalent)



#### 3. 子查询
期望的 SQL 类似于:
```sql
SELECT * FROM book WHERE author_id IN (SELECT id FROM author WHERE name LIKE 'kingron%')
```
写法：
```python
authores = Author.objects.filter(name__startswith='kingron')

# 默认使用 pk 作为查询的列
books = Book.objects.filter(author_id__in=authores)
```
参考：[如何在 django 中用 orm 写子查询 - kingron - 博客园](https://www.cnblogs.com/kingron/p/18259854)



#### 4. 窗口函数
期望的 SQL 类似于:
```sqlite
select *, row_number() over (partition by c1 order by c2 desc) as rn from my_table
```
写法：
```python
from django.db.models import F, Window
from django.db.models.functions import RowNumber

MyModel.objects.annotate(rn=Window(expression=RowNumber(), partition_by=[F('c1')], order_by=F('c2').desc()))
```
参考：[在 django 中使用窗口函数 - kingron - 博客园](https://www.cnblogs.com/kingron/p/18233047)



#### 5. 根据某个字段的值排序，并自定义排序依据
期望的 SQL 类似于：
```sql
-- 将状态为 error 放在最前面，running 其次，其他状态放在后面
select 
	id, 
	status, 
	case 
		when status = 'error' then 1 
		when status = 'running' then 2
         else 3
    end as order_status
from my_table 
	order by order_status
```
写法：
```python
from django.db.models import Case, Value, When

when = [
    When(status='error', then=Value(1)),
    When(status='running', then=Value(2))
]

case = Case(*when, default=Value(3))

MyModel.objects.annotate(order_status=case).order_by('order_status')
```
