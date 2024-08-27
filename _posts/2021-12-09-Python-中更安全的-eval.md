---
layout: post
title: Python 中更安全的 eval
date: 2021-12-09 15:24 +0800
categories: [python]
tags: []
cnblogid: 15667558
---
### 问题

想要将一段列表形式的字符串转为 `list`，但是担心这个动态的字符串可能是恶意的代码？使用 `eval` 将带来安全隐患。比如：

```python
# 期望是
eval('[1, 2, 3]')

# 实际上是
eval("os.popen('rm -rf *')")
```

### 解决方案

使用 `ast.literal_eval` 可以很好的避免这个问题，该函数可以安全执行仅包含文字的表达式字符串。支持的对象有字符串、字节、数字、元组、列表、字典、集合、 布尔值、`None` 和 `Ellipsis`。这些是可以嵌套的，比如以字典作为元素的列表：

```python
>>> from ast import literal_eval
>>> literal_eval("[{'name': 'john', 'location': 'halo7'}]")
[{'name': 'john', 'location': 'halo7'}]
```

注意 `literal_eval` 不可以执行任何复杂的表达式，比如包含运算符或是有索引的表达式都是不支持的，会直接抛出异常。这也保证了它不会执行恶意代码。

### 拓展

- 使用 `literal_eval` 时，足够复杂或是巨大的字符串可能导致 Python 解释器的崩溃，因为 Python 的 AST 编译器是有栈深限制的
- `literal_eval` 解析异常时，可能会抛出 `ValueError`, `TypeError`, `SyntaxError`, `MemoryError` 或 `RecursionError`，这取决于传入的字符串

