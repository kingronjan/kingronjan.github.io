---
categories:
- python
date: 2024-09-11 14:35 +0800
description: 命令分支再多也不慌
id: 2ef1388f-9451-415f-b472-d66f1806427b
layout: post
tags:
- python
title: argparse subparser 使用
---

### Add subparser

引用官方的例子 [subparser](https://docs.python.org/zh-cn/3/library/argparse.html#sub-commands)：

```python
import argparse
import sys

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='subcmd')
    checkout = subparsers.add_parser('checkout', aliases=['co'])
    checkout.add_argument('num')
    args = parser.parse_args(sys.argv[1:])

    print(f'{args.subcmd=}, {args.num=}')

```
{: file="foo.py" }



其中，subcmd 指向的是子命令的值，如 checkout:

```bash
$ python .\foo.py checkout 11
args.subcmd='checkout', args.num='11'
```

也可以传入 `aliases` 中的值作为子命令：

```bash
$ python .\foo.py co 11
args.subcmd='co', args.num='11'
```

> 注意此时 `arg.sbcmd` 指向的值为传入的子命令别名而不是本身
{: .prompt-info }



### 为每个子命令调用对应的函数

一般情况下，每个子命令会对应不同的分支，如果使用 `if...else...` 的语法判断走向的话会很繁琐，特别是还要考虑到别名的情况，这个时候可以使用 [set_defaults()](https://docs.python.org/zh-cn/3/library/argparse.html#argparse.ArgumentParser.set_defaults) 来为每个分支设定调用的函数，不仅高效，代码也很简洁，比如：



```python
import argparse
import sys


def checkout(args):
    print(f'On checkout, {args.subcmd=}, {args.num=}')


def commit(args):
    print(f'On commit, {args.subcmd=}, {args.file=}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='subcmd')
    
    ch_parser = subparsers.add_parser('checkout', aliases=['co'])
    ch_parser.add_argument('num')
    ch_parser.set_defaults(func=checkout)
    
    co_parser = subparsers.add_parser('commit')
    co_parser.add_argument('file')
    co_parser.set_defaults(func=commit)
    
    args = parser.parse_args(sys.argv[1:])
    args.func(args)
```
{: file="fool.py"}

这样，当传入子命令时，会自动调用对应的方法，而且对于别名也同样生效，比如 checkout 和 co 是走向同一个方法的:

```bash
$ python .\foo.py checkout 11
On checkout, args.subcmd='checkout', args.num='11'

$ python .\foo.py co 11      
On checkout, args.subcmd='co', args.num='11'
```