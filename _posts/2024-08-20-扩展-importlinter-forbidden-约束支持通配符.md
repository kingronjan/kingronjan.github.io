---
layout: post
title: "扩展 importlinter forbidden 约束支持通配符"
date: 2024-08-20 11:11 +0800
categories: []
tags: [python]
cnblogid: 18369095
---

#### 1. 前言
`importlinter` 默认的 `forbidden` 约束并不支持通配符，本文通过自定义合约一直 `forbidden_modules` 以支持通配符的方式配置。



#### 2. 实现
在项目根目录中加入 `importlinterc.py` 文件：
```python
from importlinter.application.contract_utils import AlertLevel
from importlinter.contracts.forbidden import ForbiddenContract
from importlinter.domain import fields
from importlinter.domain.helpers import _to_pattern
from importlinter.domain.imports import Module


class FnMatchForbiddenContract(ForbiddenContract):
    
    # 以下字段来自 ForbiddenContract，但仍需要重复定义
    # 因为 importlinter 是通过类的 __dict__ 查找字段定义的
    source_modules = fields.ListField(subfield=fields.ModuleField())
    forbidden_modules = fields.ListField(subfield=fields.ModuleField())
    ignore_imports = fields.SetField(subfield=fields.ImportExpressionField(), required=False)
    allow_indirect_imports = fields.StringField(required=False)
    unmatched_ignore_imports_alerting = fields.EnumField(AlertLevel, default=AlertLevel.ERROR)

    def check(self, graph, verbose):
        self.extend_modules(graph)
        return super().check(graph, verbose)

    def extend_modules(self, graph):
        """扩展包含通配符的 module 为实际对应的 modules"""
        modules = []

        for module in self.forbidden_modules:
            if '*' not in module.name:
                modules.append(module)
            else:
                length = len(modules)
                pattern = _to_pattern(module.name)
                for maybe_forbidden in graph.modules:
                    if pattern.match(maybe_forbidden):
                        modules.append(Module(maybe_forbidden))

                if len(modules) == length:
                    raise ValueError('unrecognized module name {}'.format(module.name))

        self.forbidden_modules = modules

```



#### 3. 配置
`pyproject.toml` 文件中注册：
```toml
[tool.importlinter]
root_packages = ['prettymd']

# 也可以覆盖原名称使用 forbidden
# 会优先使用用户配置的类
contract_types = [
    'fnmatch_forbidden: importlinterc.FnMatchForbiddenContract'
]

# 使用通配符
[[tool.importlinter.contracts]]
name = 'prettymd.db does not import prettymd.service.*'
type = 'fnmatch_forbidden'
source_modules = ['prettymd.db']
forbidden_modules = ['prettymd.service.*']
```



#### 4. 参考
1. [Custom contract types — Import Linter 2.0 documentation](https://import-linter.readthedocs.io/en/v2.0/custom_contract_types.html#step-one-implementing-a-contract-class)
2. to_pattern 匹配的示例可参考：[Options used by multiple contracts](https://import-linter.readthedocs.io/en/v2.0/contract_types.html#options-used-by-multiple-contracts)
