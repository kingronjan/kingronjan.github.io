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
title: django | ORM 外键使用笔记
---

### 使用逻辑外键

想要在 `orm` 中定义外键，便于关联查询，但不想在数据库中生成实际的外键约束。

`Django` 的 `ForeignKey` 和数据库的 `FOREIGN KEY` 并不一样。`Django` 的 `ForeignKey` 是一种逻辑上的两个表的关联关系，可以指定是否使用数据库的 `FOREIGN KEY` 约束。
如：

```python
from django.db import models


class Province(models.Model):
    name = models.CharField(max_length=16)

class City(models.Model):
    name = models.CharField(max_length=16)
    province = models.ForeignKey(Province, null=True, on_delete=models.DO_NOTHING, related_name='cities', db_constraint=False)
```
如果 `ForeignKey` 不添加 `db_constraint=False` 参数，会在数据库中使用外键约束。
另外，`ForeignKey` 的 `on_delete` 参数默认为 `on_delete=models.CASCADE`，表示使用数据库的级联删除，使用 `on_delete=models.SET_NULL` 可以使删除 `Province` 时将关联的 `City` 表对应的 `province_id` 值设为 `NULL`。
使用这种方式不会破坏 `Django` 的反向关联查询。



### 将整形字段改为逻辑外键

有时候处于某些原因，我们没有使用外键，而是用了一个 integer 字段，视为外键。比如：

```python
from django.db import models


class Province(models.Model):
    name = models.CharField(max_length=16)


class City(models.Model):
    name = models.CharField(max_length=16)
    province_id = models.IntegerField(null=True)
```

这样没有任何问题，但是却无法使用 django 的关联查询，比如查询 `City` 中 `Province.name = 'Chongqing'` 的时候，如果像正常外键那样的写法：

```python
City.objects.filter(province__name='Chongqing')
```

django 会报错提示 `province` 字段不存在：

```
Traceback (most recent call last):
  ...
  raise FieldError(
django.core.exceptions.FieldError: Cannot resolve keyword 'province' into field. Choices are: id, name, province_id
```

当然也有其他的方式可以实现类似的查询，比如子查询，只是略为繁琐：

```python
from django.db.models import Subquery, OuterRef

City.objects.annotate(province_name=Subquery(Province.objects.filter(id=OuterRef('province_id')).values('name'))).filter(province_name='Chongqing')
```

如果你受够了这样的写法，还想体验使用双下划线的写法，需要把字段再改为逻辑外键：

```python
from django.db import models


class Province(models.Model):
    name = models.CharField(max_length=16)

class City(models.Model):
    name = models.CharField(max_length=16)
    province = models.ForeignKey(Province, null=True, on_delete=models.DO_NOTHING, related_name='cities', db_constraint=False)
```

实际上，django 也会在数据库中把 `City.province` 字段保存为 `province_id`，这样写看起来没啥问题，至少更改前后字段类型、名称都是一致的，但是当我们做 migration 的时候会发现 django 可不这么认为：

```shell
$ uv run manage.py makemigrations
Migrations for 'fk':
  fk/migrations/0002_remove_city_province_id_city_province.py
    - Remove field province_id from city
    - Add field province to city
```

如果这样还不够明显，可以看看具体要执行的 SQL：

```shell
$ uv run manage.py sqlmigrate fk 0002_remove_city_province_id_city_province
BEGIN;
--
-- Remove field province_id from city
--
ALTER TABLE "fk_city" DROP COLUMN "province_id";
--
-- Add field province to city
--
ALTER TABLE "fk_city" ADD COLUMN "province_id" bigint NULL;
CREATE INDEX "fk_city_province_id_8eb2bf6f" ON "fk_city" ("province_id");
COMMIT;
```

竟然要删除字段，再重新添加，如果字段之前已经保存了很多数据，这样做可是非常危险的。

显然 django 认为 `province_id` 和 `province` 并不一致，为了达到目的，可以略微修改下 migrations 文件:

```python
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("fk", "0001_initial"),
    ]

    operations = [
        # 移除删除字段的操作，改为重命名字段
        #migrations.RemoveField(
        #    model_name="city",
        #    name="province_id",
        #),
        migrations.RenameField(
            model_name="city",
            old_name="province_id",
            new_name="province"
        ),
		
        # 将添加字段改为修改字段属性
        #migrations.AddField(
        migrations.AlterField(
            model_name="city",
            name="province",
            field=models.ForeignKey(
                db_constraint=False,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="cities",
                to="fk.province",
            ),
        ),
    ]
```

再看看要执行的 SQL，总算避免了历史数据被清空的命运：

```shell
$ uv run manage.py sqlmigrate fk 0002_remove_city_province_id_city_province
BEGIN;
--
-- Rename field province_id on city to province
--
ALTER TABLE "fk_city" RENAME COLUMN "province_id" TO "province";
--
-- Alter field province on city
--
CREATE TABLE "new__fk_city" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "name" varchar(16) NOT NULL, "province_id" bigint NULL);
INSERT INTO "new__fk_city" ("id", "name", "province_id") SELECT "id", "name", "province" FROM "fk_city";
DROP TABLE "fk_city";
ALTER TABLE "new__fk_city" RENAME TO "fk_city";
CREATE INDEX "fk_city_province_id_8eb2bf6f" ON "fk_city" ("province_id");
COMMIT;
```



> 对于 AlterField 操作，不同的数据库可能会有不同的 SQL 产生，这里使用的是 sqllite
{: .prompt-info }



这样操作后，再次执行 `makemigrations` 命令，django 也不会产生新的 migrations 文件。



### INNER JOIN OR LEFT JOIN

如果外键字段的 `null=False`，django 会在关联查询时使用 `INNER JOIN`，比如对于查询：

```python
qs = City.objects.select_related('province')
```

当外键 `province` `null=True` 时，产生的 SQL 使用了 `LEFT JOIN`：

```sql
>>> print(qs.query)
SELECT "fk_city"."id", "fk_city"."name", "fk_city"."province_id", "fk_province"."id", "fk_province"."name" FROM "fk_city" LEFT OUTER JOIN "fk_province" ON ("fk_city"."province_id" = "fk_province"."id")
```

而当 `null=False` 时，产生的 SQL 则使用了 `INNER JOIN`：

```python
>>> print(qs.query)
SELECT "fk_city"."id", "fk_city"."name", "fk_city"."province_id", "fk_province"."id", "fk_province"."name" FROM "fk_city" INNER JOIN "fk_province" ON ("fk_city"."province_id" = "fk_province"."id")
```



### 参考
- [Django 的 ForeignKey 与数据库的 FOREIGN KEY约束_我的总结积累与分享-CSDN博客](https://blog.csdn.net/Focus_on_linux/article/details/90521503)
- [mysql - How To Migrate IntegerField To ForeignKey - Stack Overflow](https://stackoverflow.com/questions/67267218/how-to-migrate-integerfield-to-foreignkey)