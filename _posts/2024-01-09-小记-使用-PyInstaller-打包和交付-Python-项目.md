---
layout: post
title: "小记 | 使用 PyInstaller 打包和交付 Python 项目"
date: 2024-01-09 10:14 +0800
categories: [python]
tags: []
cnblogid: 17953781
---

[PyInstaller](https://github.com/pyinstaller/pyinstaller) 可以将 Python 项目打包成一个可执行文件，或是一个文件夹，包含可执行文件以及依赖包。方便我们将 Python 项目交付给用户，方便用户使用的同时也可以一定程度的保护项目源代码。本文将介绍如何简单使用 PyInstaller 打包。

### 安装

使用 `pip` 安装即可：

```
pip install pyinstaller
```

### 简单使用

让我们新建一个项目命名为 `miniapp`，文件结构如下：

```
miniapp
	app
		__init__.py
		app.py
```

其中项目核心文件为 `app.py`，内容如下：

```python
def run():
    print('欢迎使用 miniapp')


if __name__ == '__main__':
    run()
```

现在，进入到项目根目录 `miniapp`，运行如下命令:

```bash
pyinstaller -D app/app.py -n miniapp --clean
```

初次运行可能会出现下面的错误：

```
OSError: Python library not found: libpython3.7.so.1.0, libpython3.7mu.so.1.0, libpython3.7m.so, libpython3.7.so, libpython3.7m.so.1.0
    This means your Python installation does not come with proper shared library files.
    This usually happens due to missing development package, or unsuitable build parameters of the Python installation.

    * On Debian/Ubuntu, you need to install Python development packages:
      * apt-get install python3-dev
      * apt-get install python-dev
    * If you are building Python by yourself, rebuild with `--enable-shared` (or, `--enable-framework` on macOS).
```

这是因为 PyInstaller 需要 python-dev 环境，如果是使用 `pyenv` 可以用以下命令重新安装 Python:

```bash
env PYTHON_CONFIGURE_OPTS="--enable-shared" pyenv install 3.5.0
```

或者，可以安装 python-devel 版本，比如在 CentOS 上可以通过下面的命令查看可用版本：

```bash
# yum search python | grep devel
...
python3-devel.i686 : Libraries and header files needed for Python development
...
```

安装 `python3-devel.i686` 即可。

成功运行后目录下会多出来一些文件，现在的结构如下：

```
miniapp
	app
		__init__.py
		app.py
	build
		miniapp
			...
	dist
		miniapp
			_internal
				...
			miniapp
	miniapp.spec
```

其中 `dist/miniapp/miniapp` 就是打包出来的可执行文件了，我们现在可以将 `dist/miniapp` 整个文件夹压缩并打包交付给用户。用户拿到后解压并运行 `miniapp` 文件即可。以下是运行后的结果

```bash
# ./dist/miniapp/miniapp
欢迎使用 miniapp
```

也可以通过指定 `-F` 参数将依赖包与项目文件打成一个文件：

```
pyinstaller -F app/app.py -n miniapp --clean
```

此时可执行文件路径为：

```
# ./dist/miniapp
欢迎使用 miniapp
```

相对与单个文件的形式，单个文件夹在启动时会更快，而且在后期更新时，在没有依赖更新的情况下，仅需要交给客户项目文件即可，可以一定程度减少文件传输。

### 打包模块

一般来说，我们的项目很少会只有一个文件。现在，让我们为 `miniapp` 创建一个新的文件 `core.py`，作为核心逻辑的存放位置。现在的目录结构如下：

```
miniapp
	app
		__init__.py
		app.py
		core.py
	...
```

`core.py` 文件内容为：

```python
def hello():
    print('这里是核心文件')

```

通常情况下，如果我们在 `app.py` 中有导入 `app.core` 的话，PyInstaller 会在打包时将 `core.py` 也一同编译进去，但若是涉及到动态导入的话，则 `core.py` 文件会缺失导致导入失败，比如现在将 `app.py` 逻辑更新如下：

```python
import importlib


def run():
    print('欢迎使用 miniapp')
    core = importlib.import_module('app.core')
    core.hello()

if __name__ == '__main__':
    run()
```

再次打包并运行，会报错找不到模块 `app`：

```bash
# pyinstaller -D app/app.py -n miniapp --clean
# ./dist/miniapp/miniapp
Traceback (most recent call last):
  File "app/app.py", line 39, in <module>
    run()
  File "app/app.py", line 34, in run
    core = importlib.import_module('app.core')
  File "importlib/__init__.py", line 127, in import_module
  File "<frozen importlib._bootstrap>", line 1030, in _gcd_import
  File "<frozen importlib._bootstrap>", line 1007, in _find_and_load
  File "<frozen importlib._bootstrap>", line 972, in _find_and_load_unlocked
  File "<frozen importlib._bootstrap>", line 228, in _call_with_frames_removed
  File "<frozen importlib._bootstrap>", line 1030, in _gcd_import
  File "<frozen importlib._bootstrap>", line 1007, in _find_and_load
  File "<frozen importlib._bootstrap>", line 984, in _find_and_load_unlocked
ModuleNotFoundError: No module named 'app'
[15561] Failed to execute script 'app' due to unhandled exception!
```

可以通过指定 `--hiddenimport` 参数告诉 PyInstaller `app` 模块需要被一块打包，通过这样的方式再次打包后就可以正常运行了：

```bash
pyinstaller -D app/app.py -y -n miniapp --clean --hiddenimport app.core
```

### 使用 hooks

如果只有一个 `app.core` 是动态导入，通过传入 `--hiddenimport` 即可，如果项目中存在多个模块或依赖库存在动态导入，那么命令行的参数只会越来越长变得难以阅读，为此 PyInstaller 提供了 `hook` 模式可以便于我们通过 Python 文件维护这些动态导入的模块。

下面效仿 `django` 为项目添加一个 `backends` 模块，分别提供了对 MySQL 和 Oracle 数据库的支持，现在项目结构如下：

```
miniapp
	app
		__init__.py
		app.py
		core.py
		backends
			__init__.py
			mysql
				__init__.py
			oracle
				__init__.py
	...
```

`app.py` 中增加对支持的数据库的加载并打印到屏幕：

```python
import importlib
import os
from pkgutil import iter_modules

support_backends = ()


def load_support_backends():
    global support_backends

    backends = importlib.import_module('app.backends')

    modules = []
    modpath = os.path.dirname(backends.__file__)
    for _, subpath, ispkg in iter_modules([modpath]):
        if not ispkg:
            continue
        module = importlib.import_module('app.backends.' + subpath)
        modules.append((subpath, module))

    support_backends = tuple(modules)


def run():
    print('欢迎使用 miniapp')

    core = importlib.import_module('app.core')
    core.hello()

    print('正在加载可用的数据库')
    load_support_backends()

    print('可用的数据库有: %s' % ', '.join(path for path, _ in support_backends))


if __name__ == '__main__':
    run()

```

现在在项目中新增一个文件夹用于管理 `hooks`，命名为 `pyinstallerhooks`，项目结构如下：

```
miniapp
	app
		...
	pyinstallerhooks
	...
```

在 `pyinstallerhooks` 下新建一个名为 `hook-app.py` 的文件，内容如下：

```python
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules('app')
```

然后使用命令重新打包，指定 `--additional-hooks-dir` 为 `pyinstallerhooks` 文件夹路径，同时将 `--hiddenimport` 改为 `app`：

```bash
pyinstaller -D app/app.py -y -n miniapp --clean --hiddenimport app --additional-hooks-dir pyinstallerhooks
```

再次运行，可以看到不管是 `app.backends` 还是 `app.core` 模块都有被正常加载：

```bash
# ./dist/miniapp/miniapp
欢迎使用 miniapp
这里是核心文件
正在加载可用的数据库
可用的数据库有: oracle, mysql
```

如果我们想要提供的包只支持 `oracle`，那么可以在 `pyinstallerhooks` 中对 `app.backends` 模块做更精细的控制。首先修改 `hook-app.py` 为：

```python
from PyInstaller.utils.hooks import collect_submodules


def filter_backends(name):
    """排除 app.backends 下面的非 oracle 子模块"""
    if not name.startswith('app.backends'):
        return True
    
    return name.startswith(('app.backends.oracle'))


hiddenimports = collect_submodules('app', filter=filter_backends)

```

如果想对 `app.backends.oracle` 下面的子模块提供更进一步的控制，可以在 `pyinstallerhooks` 下面新建一个 `hook-app.backends.oracle.py` 文件，并写上具体逻辑，PyInstaller 会在打包时自动找到该文件并应用，同理其他模块也是如此。

再次打包并运行，结果如下：

```bash
# ./dist/miniapp/miniapp
欢迎使用 miniapp
这里是核心文件
正在加载可用的数据库
可用的数据库有: oracle
```

### 添加静态文件

项目增加了一些模板文件需要提供给用户，放在 `templates` 目录下：

```
miniapp
	app
		__init__.py
		app.py
		core.py
		backends
			...
		templates
			config.txt
	...
```

那么如何将 `templates` 下面的文件能被一起打包并被程序识别到呢，可以通过 `--add-data` 参数将文件放入指定的相对路径，现在将打包命令更改为：

```bash
pyinstaller -D app/app.py -y -n miniapp --clean --hiddenimport app --additional-hooks-dir pyinstallerhooks \
--add-data "./app/templates/:./templates"
```

其中 `:` 前的 `./app/templates/` 是我们打包时 `templates` 所在的相对路径，`:` 后的 `./templates` 是期望打包后文件所在的路径。后者的 `.` 代表了打包后项目运行时的根目录。

将 `app.py` 文件修改为如下以获取可用的模板文件：

```python
import importlib
import os
from pkgutil import iter_modules

support_backends = ()

# 获取项目的根路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def load_support_backends():
    global support_backends

    backends = importlib.import_module('app.backends')

    modules = []
    modpath = os.path.dirname(backends.__file__)
    for _, subpath, ispkg in iter_modules([modpath]):
        if not ispkg:
            continue
        module = importlib.import_module('app.backends.' + subpath)
        modules.append((subpath, module))

    support_backends = tuple(modules)


def run():
    print('欢迎使用 miniapp')

    core = importlib.import_module('app.core')
    core.hello()

    print('正在加载可用的数据库')
    load_support_backends()

    print('可用的数据库有: %s' % ', '.join(path for path, _ in support_backends))

    templates_path = os.path.join(BASE_DIR, 'templates')
    print('可用的模板文件有: %s' % ', '.join(os.listdir(templates_path)))


if __name__ == '__main__':
    run()

```

重新打包并运行，可以看到模板文件已经被正常加载：

```bash
# ./dist/miniapp/miniapp
欢迎使用 miniapp
这里是核心文件
正在加载可用的数据库
可用的数据库有: oracle
可用的模板文件有: config.txt
```

### 自省

如何判断当前代码是在打包后的环境运行，还是非打包环境运行呢，可以通过如下方式：

```python
import sys

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    print('正在 PyInstaller 打包环境中运行')
else:
    print('正在非打包环境运行')
```

PyInstaller 会在运行时将打包文件放在 `sys._MEIPASS` 所指向的路径下，对于以文件夹方式打包的项目，该路径实际上就是 `./dist/miniapp/_internal`，而对于单个文件的方式，这个路径实际上指向的是某个临时文件夹路径（比如 Linux 下的 `/tmp/..`），如果项目需要生成一些需要保留的文件，可以通过参数 `--runtime-tmpdir` 重新指定该路径。

### 参考：

更多用法可参考官方文档：[PyInstaller Manual — PyInstaller 6.3.0 documentation](https://pyinstaller.org/en/stable/)

