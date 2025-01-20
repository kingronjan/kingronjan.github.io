---
categories:
- python
- test
date: 2025-01-17 14:20 +0800
id: ec5e45b4-23d1-4a5d-9f26-95a02a4c24c9
layout: post
tags:
- python
- test
title: Python mock usage notes
---

### Difference between `spec` and `spec_set`

According to the `unittest.mock` documentation:

> - *spec*: This can be either a list of strings or an existing object (a class or instance) that acts as the specification for the mock object. If you pass in an object then a list of strings is formed by calling dir on the object (excluding unsupported magic attributes and methods). Accessing any attribute not in this list will raise an [`AttributeError`](https://docs.python.org/3/library/exceptions.html#AttributeError).
>
>   If *spec* is an object (rather than a list of strings) then [`__class__`](https://docs.python.org/3/reference/datamodel.html#object.__class__) returns the class of the spec object. This allows mocks to pass [`isinstance()`](https://docs.python.org/3/library/functions.html#isinstance) tests.
>
> - *spec_set*: A stricter variant of *spec*. If used, attempting to *set* or get an attribute on the mock that isn’t on the object passed as *spec_set* will raise an [`AttributeError`](https://docs.python.org/3/library/exceptions.html#AttributeError).

For example, with `spec`, you can not get unspecified attribute, but can set:

```python
>>> from unittest.mock import Mock
>>> class A:
...     def __init__(self, a, b):
...         self.a = a
...         self.b = b
...
>>> aobj = A(1, 2)



>>> m = Mock(spec=aobj)   # spec
>>> m.c   # get -> fail
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/usr/local/Cellar/python3/3.6.0b4_3/Frameworks/Python.framework/Versions/3.6/lib/python3.6/unittest/mock.py", line 582, in __getattr__
    raise AttributeError("Mock object has no attribute %r" % name)
AttributeError: Mock object has no attribute 'c'
>>> m.c = 9  # set -> success
>>> m.c      # get -> success (although c is not in the spec)
9
```

While with `spec_set`, also, you can not get unspecified attribute, **and can not set unspecified attribute**:

```python
>>> m = Mock(spec_set=aobj)   # spec_set
>>> m.a
<Mock name='mock.a' id='4544967400'>
>>> m.c   # get -> fail
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/usr/local/Cellar/python3/3.6.0b4_3/Frameworks/Python.framework/Versions/3.6/lib/python3.6/unittest/mock.py", line 582, in __getattr__
    raise AttributeError("Mock object has no attribute %r" % name)
AttributeError: Mock object has no attribute 'c'
>>> m.c = 9  # set -> fail
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/usr/local/Cellar/python3/3.6.0b4_3/Frameworks/Python.framework/Versions/3.6/lib/python3.6/unittest/mock.py", line 688, in __setattr__
    raise AttributeError("Mock object has no attribute '%s'" % name)
AttributeError: Mock object has no attribute 'c'
```



### Mock method or function with `spec_set`

Use [create_autospec](https://docs.python.org/3/library/unittest.mock.html#create-autospec "unittest.mock — mock object library — Python 3.13.1 documentation"):

```python
In [1]: from unittest.mock import create_autospec

In [2]: def fn():
   ...:     pass
   ...:

In [3]: m = create_autospec(fn, auto_sepc=True)

In [4]: m()
Out[4]: <MagicMock name='mock()' id='1780749468560'>

In [5]: m(1)
---------------------------------------------------------------------------
TypeError                                 Traceback (most recent call last)
<ipython-input-5-c0fc02733ec9> in <cell line: 0>()
----> 1 m(1)

<string> in fn(*args, **kwargs)

~\AppData\Local\Programs\Python\Python311\Lib\unittest\mock.py in checksig(*args, **kwargs)
    190     func, sig = result
    191     def checksig(*args, **kwargs):
--> 192         sig.bind(*args, **kwargs)
    193     _copy_func_details(func, checksig)
    194

~\AppData\Local\Programs\Python\Python311\Lib\inspect.py in bind(self, *args, **kwargs)
   3210         if the passed arguments can not be bound.
   3211         """
-> 3212         return self._bind(args, kwargs)
   3213
   3214     def bind_partial(self, /, *args, **kwargs):

~\AppData\Local\Programs\Python\Python311\Lib\inspect.py in _bind(self, args, kwargs, partial)
   3131                     param = next(parameters)
   3132                 except StopIteration:
-> 3133                     raise TypeError('too many positional arguments') from None
   3134                 else:
   3135                     if param.kind in (_VAR_KEYWORD, _KEYWORD_ONLY):

TypeError: too many positional arguments

```



### Reference

1. [python - What is spec and spec_set - Stack Overflow](https://stackoverflow.com/questions/25323361/what-is-spec-and-spec-set "python - What is spec and spec_set - Stack Overflow")
2. [unittest.mock — mock object library — Python 3.13.1 documentation](https://docs.python.org/3/library/unittest.mock.html#create-autospec "unittest.mock — mock object library — Python 3.13.1 documentation")
3. [python - How to employ a MagicMock spec_set or spec on a method? - Stack Overflow](https://stackoverflow.com/questions/70585975/how-to-employ-a-magicmock-spec-set-or-spec-on-a-method "python - How to employ a MagicMock spec_set or spec on a method? - Stack Overflow")