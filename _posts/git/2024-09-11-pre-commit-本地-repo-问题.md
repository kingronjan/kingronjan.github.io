---
categories:
- git
date: 2024-09-11 13:59 +0800
description: 记录使用本地 repo 遇到的问题和解决方案
id: 9ce2045b-addb-4029-8dfa-d805945f1cf4
layout: post
tags:
- git
- pre-commit
title: pre-commit 本地 repo 问题
---

### Use local repos

参考：[pre-commit - Repository local hooks](https://pre-commit.com/#repository-local-hooks)

在网络条件有限时，比如，在公司不能连接外网，使用 local repos 是很方便的做法，只要保证本地的 hooks 能用即可。

同时也可以用于配置自定义的 hooks。

官方示例如下：

```yaml
-   repo: local
    hooks:
    -   id: pylint
        name: pylint
        entry: pylint
        language: system
        types: [python]
        require_serial: true
    -   id: check-x
        name: Check X
        entry: ./bin/check-x.sh
        language: script
        files: \.x$
    -   id: scss-lint
        name: scss-lint
        entry: scss-lint
        language: ruby
        language_version: 2.1.5
        types: [scss]
        additional_dependencies: ['scss_lint:0.52.0']
```



### additional_dependencies

该配置项可用于解决部分 hooks 缺少依赖的问题。比如，在本地创建了一个 hook，是用 python 写的，同时依赖三方包 requests，如果不配置 additional_dependencies，很可能会运行出错（即使已经使用 pip install 安装了 requests），这是因为 pre-commit 的运行环境与项目的运行环境并不一致，为了解决这个问题需要配置 additional_dependencies 让 pre-commit 运行时安装依赖。

参考：[python 3.x - pre-commit not using virtual environment - Stack Overflow](https://stackoverflow.com/questions/70778806/pre-commit-not-using-virtual-environment)

示例：

```yaml
repos:
- repo: local
  hooks:
    - id: clean-assets
      name: clean-asssts
      language: python
      entry: python tool.py assets -c
      files: '\d\.\d+$'
      always_run: true
      additional_dependencies: ['requests']
```



### 不传入更改文件

pre-commit 默认会传入变更文件给 hooks，如果不希望传入文件，可以指定 [pass_filenames](https://pre-commit.com/#hooks-pass_filenames) 参数为 `false`，或者通过指定 `files: '\d\.\d+$'` 这种不常见的文件名匹配模式，以确保不会有文件会被传入



---

1. [pre-commit](https://pre-commit.com/)