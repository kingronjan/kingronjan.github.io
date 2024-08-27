---
layout: post
title: 使用 mockito 替代 unitest.mock
date: 2024-06-26 09:50 +0800
categories: [python, pytest]
tags: [pytest, mock]
cnblogid: 18268291
---
### 介绍
`mockito` 是一个 `pytest` 插件，相比于 `unitest.mock`，具有如下特点：
- 所有对象都自动为 `autospec`，无需担心模拟对象被错误的调用而不被发现
- 不使用字符串参数作为模拟对象，可以减少拼写错误
- 提供的返回值或抛出错误更加冗长，但也更明确和具体



### 安装
使用 `pip` 安装即可：
```bash
pip install pytest-mockito
```



### 与 `unitest.mock` 的对比
比如对以下内容中的 `main` 方法测试，文件名为 `my_life_work.py`：
```python
def transform(param):
    return param * 2

def check(param):
    return "bad" not in param

def calculate(param):
    return len(param)

def main(param, option):
    if option:
        param = transform(param)
    if not check(param):
        raise ValueError("Woops")
    return calculate(param)
```
使用 `unitest.mock`，写法如下：
```python
import pytest

from unittest.mock import patch
from my_life_work import main

@patch("my_life_work.transform")
@patch("my_life_work.check")
@patch("my_life_work.calculate")
def test_main(calculate, check, transform):
    check.return_value = True
    calculate.return_value = 5

    assert main("param", False) == calculate.return_value
    transform.assert_not_called()
    check.assert_called_with("param")
    calculate.assert_called_once_with("param")

    transform.return_value = "paramparam"
    calculate.return_value = 10
    assert main("param", True) == calculate.return_value
    transform.assert_called_with("param")
    check.assert_called_with("paramparam")
    calculate.assert_called_with("paramparam")

    with pytest.raises(ValueError):
        check.side_effect = ValueError
        main("bad_param", False)
        check.assert_called_with("param")
        transform.assert_not_called()
        calculate.assert_not_called()
```
再看下使用 `mockito` 的写法：
```python
import pytest
import my_life_work # 导入以使用 mock
from my_life_work import main

def test_main(expect):

    expect(my_life_work, times=1).check("param").thenReturn(True)
    expect(my_life_work, times=1).calculate("param").thenReturn(5)
    # '...' 表示任意的参数，这里不期望 transform 会被调用
    expect(my_life_work, times=0).transform(...)
    assert main("param", False) == 5

    expect(my_life_work, times=1).transform("param").thenReturn("paramparam")
    expect(my_life_work, times=1).check("paramparam").thenReturn(True)
    expect(my_life_work, times=1).calculate("paramparam").thenReturn(10)
    assert main("param", True) == 10

    expect(my_life_work, times=1).check("bad_param").thenReturn(False)
    expect(my_life_work, times=0).transform(...)
    expect(my_life_work, times=0).calculate(...)
    with pytest.raises(ValueError):
        main("bad_param", False)
```
在 `mockito` 中，原来 `mock` 的写法
```python
@patch("my_life_work.check")
...
check.return_value = True
check.assert_called_with("param")
```
写法变为：
```python
expect(my_life_work, times=1).check("param").thenReturn(True)
```
更清晰，也不容易出错。



### 更多使用案例
#### 处理行内导入的情况
如果方法里面有行内导入，想要处理行内导入的情况呢？将模块名换位行内导入的模块名即可。
需要测试的代码：
```python
# my_life_work.py

...

def main():
    from my_another_work import work
    result = work()
    ...

```
测试代码：
```python
# test_main.py
import my_another_work

def test_main(expect):
    expect(my_another_work, times=1).work(...).thenReturn(10)
```



#### 不作为 fixture 使用
`mockito` 也支持直接导入使用 `expect`，`when` 等模块，比如：
```python
from mockito import expect

import my_another_work

def test_main():
    with expect(my_another_work, times=1).work(...).thenReturn(10):
        ...
```



#### 减少检查的参数
有时候测试的函数会传递很多参数，而写 `expect` 时只需要检查部分参数，写完整反而会容易混淆，这时候可以使用 `args` , `kwargs` 以减少需要匹配的参数项。比如：
需要测试的代码：
```python
# my_life_work.py
def transfer(p1, p2, p3, p4=None, p5='no.1'):
    ...
```
测试代码只需要测试 `p1` 传入 `1` 时就返回 `1`，那么可以这样写：
```python
from mockito import args, kwargs

import my_life_work


def test_main(expect):
    expect(my_life_work, times=1).transfer(1, *args, **kwargs).thenReturn(1)
    ...
```



#### 不检查调用次数
使用 `expect` 时总要传入 `times` 参数，可以使用 `when` 代替 `expect` 不检查调用次数，用法与 `expect` 相同，只是不要要传入 `times` 参数，比如：
```python
from mockito import when

import my_another_work

def test_main():
    with when(my_another_work).work(...).thenReturn(10):
        ...
```
也可以作为 fixture 使用。



### 参考
1. [Testing with Python (part 6): Fake it... - Bite code!](https://www.bitecode.dev/p/testing-with-python-part-6-fake-it)
2. [Install — mockito-python 1.5.1.dev documentation](https://mockito-python.readthedocs.io/en/latest/)
