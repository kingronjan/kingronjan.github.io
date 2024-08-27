---
layout: post
title: Python __new__ 方法解释与使用
date: 2020-09-24 23:57 +0800
categories: [python]
tags: []
cnblogid: 13727461
---
# 解释

我们通常把 `__init__` 称为构造方法，这是从其他语言借鉴过来的术语。

其实，用于构建实例的是特殊方法 `__new__`：这是个类方法（使用特殊方式处理，因此不必使用 `@classmethod` 装饰器），必须返回一个实例。返回的实例会作为第一个参数（即 `self`）传给 `__init__` 方法。

因为调用 `__init__` 方法时要传入实例，而且禁止返回任何值，所以 `__init__` 方法其实是“初始化方法”。真正的构造方法是 `__new__`。

我们几乎不需要自己编写 `__new__` 方法，因为从 `object` 类继承的实现已经足够了。刚才说明的过程，即从`__new__` 方法到`__init__` 方法，是最常见的，但不是唯一的。 `__new__` 方法也可以返回其他类的实例，此时，解释器不会调用 `__init__` 方法。

也就是说，Python 构建对象的过程可以使用下述伪代码概括：

```py
# 构建对象的伪代码 
def object_maker(the_class, some_arg):     
	new_object = the_class.__new__(some_arg)     
	if isinstance(new_object, the_class):         
		the_class.__init__(new_object, some_arg)     
	return new_object 
 
# 下述两个语句的作用基本等效 
x = Foo('bar') 
x = object_maker(Foo, 'bar')
```

# 示例：对JSON的解析

```py
import keyword


class FrozenJSON(object):
    """一个只读接口
    使用属性表示访问JSON类对象
    """

    def __init__(self, mapping):
        self._data = {}
        for k, v in mapping.items():
            if keyword.iskeyword(k):
                k += '_'
            self._data[k] = v

    def __getattr__(self, name):
        if hasattr(self._data, name):
            return getattr(self._data, name)
        else:
            return FrozenJSON.build(self._data[name])

    @classmethod
    def build(cls, obj):
        if isinstance(obj, abc.Mapping):
            return cls(obj)
        elif isinstance(obj, abc.MutableSequence):
            return [cls.build(item) for item in obj]
        else:
            return obj


class FrozenJSON2(object):
    """通过定义 __new__ 方法完成实例创建时的行为"""
    def __new__(cls, arg):
        if isinstance(arg, abc.Mapping):
            return super().__new__(cls)
        elif isinstance(arg, abc.MutableSequence):
            return [cls(item) for item in arg]
        else:
            return arg

    def __init__(self, mapping):
        self._data = {}
        for k, v in mapping.items():
            if keyword.iskeyword(k):
                k += '_'
            self._data[k] = v

    def __getattr__(self, name):
        if hasattr(self._data, name):
            return getattr(self._data, name)
        else:
            return FrozenJSON(self._data[name])
```

*摘自《流畅的Python》 19.1.3 使用__new__方法以灵活的方式创建对象*
