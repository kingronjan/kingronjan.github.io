---
categories:
- python
cnblogid: 17729426
date: 2023-09-26 09:46 +0800
id: 8afec278-efc0-4ee7-8ff5-7bd469585935
layout: post
tags:
- python
title: 记一次 pickle 对象引发的 stack overflow 异常
---

### 问题

工程中有一个类是代理类，大概实现如下：

```python
class Wrapper(object):
    
    def __init__(self, obj):
        self._obj = obj
        
    def __getattr__(self, item):
        return getattr(self._obj, item)
```

多数情况下这块代码运行正常，但是在我们通过 celery 调用时，如果返回该对象构造的实例，会引发一个 `RecursionError: maximum recusion depth exceeded while calling a Python object` 异常，从而导致整个代码异常退出。

### 分析

通过 DEBUG 发现，unpickle `Wrapper` 实例时，首先会查看该实例是否有定义 `__setattr__` 方法：

```c
// Modules/_pickle.c
static int
load_build(UnpicklerObject *self)
{
    PyObject *state, *inst, *slotstate;
    PyObject *setstate;
    int status = 0;
    _Py_IDENTIFIER(__setstate__);


    inst = self->stack->data[Py_SIZE(self->stack) - 1];
	
    // 查看实例是否有定义 __setstate__ 方法
    if (_PyObject_LookupAttrId(inst, &PyId___setstate__, &setstate) < 0) {
        Py_DECREF(state);
        return -1;
    }
    if (setstate != NULL) {
        PyObject *result;

        /* The explicit __setstate__ is responsible for everything. */
        result = _Pickle_FastCall(setstate, state);
        Py_DECREF(setstate);
        if (result == NULL)
            return -1;
        Py_DECREF(result);
        return 0;
    }

```

官方文档描述为：

> object.**\_\_setstate\_\_**(state)
>
> 当解封时，如果类定义了 [`__setstate__()`](https://docs.python.org/zh-cn/3/library/pickle.html?highlight=__setstate__#object.__setstate__)，就会在已解封状态下调用它。此时不要求实例的 state 对象必须是 dict。没有定义此方法的话，先前封存的 state 对象必须是 dict，且该 dict 内容会在解封时赋给新实例的 __dict__。
>
> 备注: 如果 [`__getstate__()`](https://docs.python.org/zh-cn/3/library/pickle.html?highlight=__setstate__#object.__getstate__) 返回 False，那么在解封时就不会调用 [`__setstate__()`](https://docs.python.org/zh-cn/3/library/pickle.html?highlight=__setstate__#object.__setstate__) 方法。



此时相当于调用了 `getattr(wrapper, '__setstate__')`，显然没有，但是解释器发现实例定义了 `__getattr__` 方法，于是转而调用了 `__getattr__` 方法，此时走到了这一行：

```python
    def __getattr__(self, item):
        # self 没有 _obj 属性
        return getattr(self._obj, item)
```

但此时反序列化尚未完成，实例的 `__dict__` 里面还没有 `_obj` 这个属性，于是转而又去调用实例的 `__getattr__` 方法，导致一直循环调用自己，引发了 `RecursionError`。

### 修复

修复问题的方式有很多种，比如定义 `__setstate__` 方法等，这里我使用的方式为：

```python
class Wrapper(object):
    
    def __init__(self, obj):
        self._obj = obj
        
    def __getattr__(self, item):
        # 通过调用 object.__getattribute__ 避免引发循环调用
        o = object.__getattribute__(self, '_obj')
        return getattr(o, item)
```

对于 `object.__getattribute__`，官方文档如下：

> object.**\_\_getattribute\_\_**(*self*, *name*)[¶](https://docs.python.org/zh-cn/3/reference/datamodel.html?highlight=__getattribute__#object.__getattribute__)
>
> 此方法会无条件地被调用以实现对类实例属性的访问。如果类还定义了 [`__getattr__()`](https://docs.python.org/zh-cn/3/reference/datamodel.html?highlight=__getattribute__#object.__getattr__)，则后者不会被调用，除非 [`__getattribute__()`](https://docs.python.org/zh-cn/3/reference/datamodel.html?highlight=__getattribute__#object.__getattribute__) 显式地调用它或是引发了 [`AttributeError`](https://docs.python.org/zh-cn/3/library/exceptions.html#AttributeError)。此方法应当返回（找到的）属性值或是引发一个 [`AttributeError`](https://docs.python.org/zh-cn/3/library/exceptions.html#AttributeError) 异常。为了避免此方法中的无限递归，其实现应该总是调用具有相同名称的基类方法来访问它所需要的任何属性，例如 `object.__getattribute__(self, name)`。
>
> 备注：此方法在作为通过特定语法或内置函数隐式地调用的结果的情况下查找特殊方法时仍可能会被跳过。参见 [特殊方法查找](https://docs.python.org/zh-cn/3/reference/datamodel.html?highlight=__getattribute__#special-lookup)。
>
> 引发一个 [审计事件](https://docs.python.org/zh-cn/3/library/sys.html#auditing) `object.__getattr__`，附带参数 `obj`, `name`。