---
layout: post
title: "python logger 使用技巧集锦"
date: 2024-07-08 16:40 +0800
categories: [python]
tags: [python, 日志, logging]
cnblogid: 18290266
---

### 1. 简单使用
```python
import logging

# 基本设置
# 如果没有设置，则可以使用该设置用于显示
logging.basicConfig(level='DEBUG', datefmt='%Y-%m-%d %H:%M:%S',
                    format='%(asctime)s [%(name)s] %(levelname)s %(message)s')


logger = logging.getLogger('simple_use')
```



### 2. 为所有 `logger` 设置 `level`
#### 2.1. 使用 `disable`
```python
import logging

# 关闭所有 INFO 以及 INFO 以下的日志输出
logging.disable(logging.INFO)

# 取消上面的设置
logging.disable(logging.NOTSET)
```



#### 2.2. 使用 `root`
```python
import logging

logging.root.setLevel(logging.INFO)
```
设置 `root` 的 `logger` 会影响到所有继承的 `logger`（基本代表了所有的 `logger`）。



#### 2.3. 参考
[Set global minimum logging level across all loggers in Python/Django - Stack Overflow](https://stackoverflow.com/questions/24938907/set-global-minimum-logging-level-across-all-loggers-in-python-django)



### 3. 错误信息追踪
#### 3.1. exc_info 参数解释
关于 `logger` 的记录方法都带有参数 `exc_info`，该值默认为空，可为布尔值。官方解释为：
> If *exc_info* does not evaluate as false, it causes exception information to be added to the logging message. If an exception tuple (in the format returned by [`sys.exc_info()`](https://docs.python.org/3/library/sys.html#sys.exc_info)) or an exception instance is provided, it is used; otherwise, [`sys.exc_info()`](https://docs.python.org/3/library/sys.html#sys.exc_info) is called to get the exception information.


对于 `sys.exc_info()` 的解释为：
> This function returns a tuple of three values that give information about the exception that is currently being handled. The information returned is specific both to the current thread and to the current stack frame. If the current stack frame is not handling an exception, the information is taken from the calling stack frame, or its caller, and so on until a stack frame is found that is handling an exception. Here, “handling an exception” is defined as “executing an except clause.” For any stack frame, only information about the exception being currently handled is accessible.
>
> If no exception is being handled anywhere on the stack, a tuple containing three `None` values is returned. Otherwise, the values returned are `(type, value, traceback)`. Their meaning is: *type* gets the type of the exception being handled (a subclass of [`BaseException`](https://docs.python.org/3/library/exceptions.html#BaseException)); *value* gets the exception instance (an instance of the exception type); *traceback* gets a [traceback object](https://docs.python.org/3/reference/datamodel.html#traceback-objects) which encapsulates the call stack at the point where the exception originally occurred.


简单来说，就是默认从当前环境的栈中自动读取（如果有错误），该方法会返回一个包含三个元素的元组，如果没有错误，三个元素皆为 `None` ；如果有则依次为：错误类型，错误对象，错误追踪对象。
比如：
```python
import logging
import sys

try:
    1 / 0
except ZeroDivisionError:
    print(sys.exc_info())
```
输出为：
```shell
(<class 'ZeroDivisionError'>, ZeroDivisionError('division by zero'), <traceback object at 0x000001A0FEE53608>)
```
如果该参数为 `True`，模块会自动调用 `sys.exc_info()` 方法获取错误信息，但有时候我们需要手动传入错误信息记录，因此，也可自己构造 `exc_info` 参数所需的信息，比如：
```python
import logging

logging.basicConfig(level='DEBUG', datefmt='%Y-%m-%d %H:%M:%S',
                    format='%(asctime)s [%(name)s] %(levelname)s %(message)s')

try:
    1 / 0
except ZeroDivisionError as e:
    err = ValueError('The denominator cannot be 0!')
    logging.info('division wrong: ', 
                 exc_info=(ValueError, err, e.__traceback__))

```
输出为：
```shell
2020-10-21 15:19:28 [root] INFO division wrong: 
Traceback (most recent call last):
  File "D:/OneDrive/works-tmp/gyyenterprise/gyyspider/spiders/products/hc.py", line 13, in <module>
    1 / 0
ValueError: The denominator cannot be 0!
```
当然，如果不需要自定义错误信息，也可使用 `logging.execption(e)` 方法将捕获的错误传入直接记录。



### 4. 带有文件和屏幕双向输出的 `logger`
自定义格式（加入自定义的参数）`-` 文件和屏幕的双向输出：
```python
import logging
import os
import time
import weakref

from lzz.settings import BASE_DIR

_handlers = weakref.WeakValueDictionary()


log_fmt = '%(asctime)s [%(name)s] %(levelname)s %(message)s'
date_fmt = '%Y-%m-%d %H:%M:%S'


def get_logger(name, level='DEBUG', folder=None, filename_fmt=None):
    formatter = logging.Formatter(
        fmt=log_fmt,
        datefmt=date_fmt,
    )
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if 'stream' not in _handlers:
        stream = logging.StreamHandler()
        stream.setFormatter(formatter)
        _handlers['stream'] = stream
    logger.addHandler(_handlers['stream'])

    if folder:
        if 'file' not in _handlers:
            par = os.path.join(BASE_DIR, r'logs\upload\{}'.format(folder))
            if not os.path.exists(par):
                os.makedirs(par)
            filename = f"{time.strftime(filename_fmt or '%Y%m%d')}.log"
            path = os.path.join(par, filename)
            file_handler = logging.FileHandler(filename=path, encoding='utf-8')
            _handlers['file'] = file_handler
        logger.addHandler(_handlers['file'])

    return logger
```



### 5. 参考               
1. [Python logging同时输出到屏幕和文件](https://www.xnathan.com/2017/03/09/logging-output-to-screen-and-file/)        
2. [如何添加自定义字段到Python日志格式字符串？](https://codeday.me/bug/20171130/102047.html)        
3. [python logging模块使用教程](https://www.jianshu.com/p/feb86c06c4f4)            
4. [traceback --- Print or retrieve a stack traceback — Python 3.7.3 文档](https://docs.python.org/zh-cn/3/library/traceback.html)        
5. [模块 logging --- Python 的日志记录工具 — Python 3.7.3 文档](https://docs.python.org/zh-cn/3/library/logging.html)          
