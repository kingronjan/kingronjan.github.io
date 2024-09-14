---
layout: post
title: "使用 pre-commit 检查 django migrations 文件完整性"
date: 2024-09-14 16:26 +0800
categories: [python, django]
tags: [python, django, pre-commit]
---



最近项目中老是遇到有的同事没有做了 ORM 表结构更改，但是没有生成相关的迁移文件，或者虽然生成了，但是存在冲突，没有解决就推到代码库了，导致项目部署时没有应用到最新的表结构，这种低级错误本来应该在代码提交时就可以发现，这个时候用 pre-commit 检查就很有必要了。

通过查阅 [django 官方文档](https://docs.djangoproject.com/zh-hans/5.1/ref/django-admin/#makemigrations)发现，`makrmigrations` 命令有两个参数很适合用来检查迁移文件未生成或存在冲突的情况：

- `--dry-run` 显示在不向磁盘写入任何迁移文件的情况下进行的迁移
- `--check` 在检测到模型更改而没有迁移时，使 `makemigrations` 以非零状态退出

当加上这两个参数运行 `makemigrations` 时，如果遇到模型更改而没有迁移时，不会生成新的迁移文件，而且还会让程序以非零状态退出。

> 考虑到可能存在冲突的迁移文件，需要手动介入处理，因此只做检查而不自动生成新的迁移文件最好不过
{: .prompt-tip }

下面是添加 pre-commit 配置：

```yaml
repos:
- repo: local
  hooks:
  -  id: check-migrations
     name: check migrations
     entry: python manage.py makemigrations --check --dry-run
     language: system
     types: [python]
     files: '(model|migrations).*\.py'
     pass_filenames: false
```
{: file='.pre-commit-config.yaml' }



> files 选项指定了这个检查会在匹配到 python 文件，且基于项目根目录的相对路径中包含 'model' 或 'migrations' 字符串才会运行，增加文件匹配可以提升与模型文件不想关的变动提交的速度，实际使用中，该匹配模式可能需要根据项目的命名规范调整
{: .prompt-info }
