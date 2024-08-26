---
layout: post
title: try...finally..的优雅实现
date: 2024-08-26 21:35 +0800
categories: [python]
tags: [python, exception]
---


### 1. 关于 try.. finally..

假如上帝用 python 为每一个来到世界的生物编写程序，那么除去中间过程的种种复杂实现，最不可避免的就是要保证每个实例最后都要挂掉。代码可简写如下：

```python
try:
    born()  # 出生

    # 正常降临世界
    # do something..

except ValueError:
    # 安排错误
    # do something...

except AttributeError:
    # 特征错误
    # do something...

except TypeError:
    # 种类错误
    # do something...

...  # 等等杂七杂八的错误

finally:
    go_die()  # 挂掉
    come_to_see_me()  # 然后来见我
    reincarnate()  # 下一轮，安排！
```

这就是 `finally` 的作用和实例。就算捕获异常后再次出现异常，最终也能保证 `go_die` 方法会执行，但是，如果 `go_die` 方法出现错误，那么就不能正常去见上帝了。为了保证每个生物（不管有没有挂掉）都能见到上帝他老人家，并开始下一个轮回（不管有没有见到），需要做如下处理：

```python
...

finally:
    try:
        go_die()
    finally:
        try:
            come_to_see_me()
        finally:
            reincarnate()
```

OK，功能虽然实现了，但按照 `The Zen of Python` 所说：`Flat is better than nested.`（扁平优于嵌套），那么这段代码就略显丑陋了。为了遵循 python 美学，我们可以对这段进行优化，使它看起来更为美观。

### 2. 错误的上下文：`__context__`

在此之前，需要引入一个新的概念： `__context__`，`__context__` 的字面意思就是上下文，它属于错误的一个属性。在错误捕获中，它意味着当你处理一个错误时，另一个错误发生了。也就是说，你所捕获的错误虽然被成功捕获了，但当捕获完成时，你的一些操作导致另一个错误发生，而这个错误并没有被捕获。通常情况下，如果处理的好，那么**当前错误**的 `__context__` 的值为 `None`，如果处理不好那就是你所捕获的错误。比如下面的代码：

```python
def type_err():
    raise TypeError('this is a type error.')

def after_type_err():
    raise ValueError('this is a value error.')

try:
    type_err()
except TypeError:
    after_type_err()
```

执行结果为：

```python
Traceback (most recent call last):
  File "<ipython-input-4-189a22d65266>", line 8, in <module>
    type_err()
  File "<ipython-input-4-189a22d65266>", line 2, in type_err
    raise TypeError('this is a type error.')
TypeError: this is a type error.

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "C:\Users\lineu\AppData\Local\Programs\Python\Python37\lib\site-packages\IPython\core\interactiveshell.py", line 3326, in run_code
    exec(code_obj, self.user_global_ns, self.user_ns)
  File "<ipython-input-4-189a22d65266>", line 10, in <module>
    after_type_err()
  File "<ipython-input-4-189a22d65266>", line 5, in after_type_err
    raise ValueError('this is a value error.')
ValueError: this is a value error.
```

在上面的错误信息中，当前错误类型为 `ValueError`，它的 `__context__` 属性值为 `TypeError` 实例，而 `TypeError` 实例的 `__context__` 为 `None`。

### 3. FinalExecutor：优雅的 finally

有了 `__context__` 的概念，我们就可以基于此实现一个优雅的“轮回”了。基本思路为：依次执行方法，如果方法报错，那么就将该错误的 `__context__` 值设置为上一个错误（如果有）。最后等到所有方法执行完毕，再抛出最后一个错误，那么此时的错误将包含所有可能被引发的错误信息。具体代码如下：

```python
class FinalExecutor(object):
    """终极执行器
    用于确保你所有的方法都会被执行（不管中途有没有方法报错）
    同时能看到正确的错误信息
    """

    def __init__(self):
        self.last_err = None  # 保存最近发生的错误

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 如果有发生错误，则抛出
        if self.last_err:
            raise self.last_err

    def call(self, func, *args, **kwargs):
        """调用执行方法"""
        try:
            func(*args, **kwargs)
        except Exception as e:
            # Exception 捕获所有继承自它或它子类的错误类型
            # 捕获它等于捕获几乎所有错误

            if self.last_err:
                # 将本次错误的上下文定义为上一次错误
                e.__context__ = self.last_err

            # 更新为当前错误
            self.last_err = e
```

我们的终极执行器使用示例为：

```python
# 定义 3 个方法用于测试
def type_err():
    print('type error')
    raise TypeError('x')


def value_err():
    print('value error')
    raise ValueError('x')


def attr_err():
    print('attr error')
    raise AttributeError('x')


# 使用 with 语句来启动终极执行器
with FinalExecutor() as e:
    e.call(type_err)
    e.call(value_err)
    e.call(attr_err)
```

运行可以看到方法最终都被执行了，且错误信息一个不漏：

```python
type error
value error
attr error
Traceback (most recent call last):
  File "<ipython-input-5-1b07c576630b>", line 19, in call
    func(*args, **kwargs)
  File "<ipython-input-6-d602d89ed0e7>", line 3, in type_err
    raise TypeError('x')
TypeError: x

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "<ipython-input-5-1b07c576630b>", line 19, in call
    func(*args, **kwargs)
  File "<ipython-input-6-d602d89ed0e7>", line 8, in value_err
    raise ValueError('x')
ValueError: x

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "C:\Users\lineu\AppData\Local\Programs\Python\Python37\lib\site-packages\IPython\core\interactiveshell.py", line 3326, in run_code
    exec(code_obj, self.user_global_ns, self.user_ns)
  File "<ipython-input-6-d602d89ed0e7>", line 19, in <module>
    e.call(attr_err)
  File "<ipython-input-5-1b07c576630b>", line 15, in __exit__
    raise self.last_err
  File "<ipython-input-5-1b07c576630b>", line 19, in call
    func(*args, **kwargs)
  File "<ipython-input-6-d602d89ed0e7>", line 13, in attr_err
    raise AttributeError('x')
AttributeError: x
```

### 4. 使用 ExitStack

有了我们的终极执行器，上帝就可以优雅的写代码了。为了让每个人都能这样优雅的写 python 代码，python 为我们提供了一个封装好的功能，当然它的实现要比我们的终极执行器复杂一些（考虑的也更周到一些~）。我们可以通过 `contextlib` 模块导入该方法并使用：

```python
from contextlib import ExitStack


with ExitStack() as stack:
    stack.callback(type_err)
    stack.callback(value_err)
    stack.callback(attr_err)
```

注意该 `ExitStack` 与 `FinalExecutor` 不同的是，它是倒序执行的。

---

*Over.*