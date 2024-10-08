---
layout: post
title: "解决 supervisord 重启时没有停止运行中的 celery 进程"
date: 2024-09-29 14:06 +0800
categories: [python, celery]
tags: [python, celery]
---

使用 supervisor 服务管理 celery 进程时遇到这样一个问题：

如果重启 supervisor 服务前（使用命令 `shutdown`，然后运行 `supervisord`），存在正在运行中的 celery worker 进程，那么重启后这个进程还在，而且成为了僵尸进程，通过 celery 的 `inspect` 接口也无法查询到对应的信息，即也无法通过之前保存的 `uuid` 获取对应的进程信息。

supervisor 的配置如下：

```ini
[program:celery-worker]
command=celery -A myapp worker -l INFO -E -Q myapp_q --autoscale=10,4 -n celeryworker@%%h
directory=/home/kingron/app/myapp
autostart=true
process_name=%(program_name)s ; process_name expr (default %(program_name)s)
numprocs=1                    ; number of processes copies to start (def 1)
stopsignal=QUIT               ; signal used to kill process (default TERM)
redirect_stderr=true          ; redirect proc stderr to stdout (default false)
stdout_logfile=/home/kingron/app/myapp/log/celery-worker.log        ; stdout log path, NONE for none; default AUTO
```

通过检索发现 supervisor 提供了一个参数 `killasgroup`，默认为 `false`，如果设置为 `true`，那么在关闭进程时会作为进程组关闭，通过翻阅源码可知，具体操作就是在进程名前加上一个负号（`unix/linux` 系统），官方文档描述如下：

> killasgroup
>
> If true, when resorting to send SIGKILL to the program to terminate it send it to its whole process group instead, taking care of its children as well, useful e.g with Python programs using multiprocessing.
>
> Default: false
>
> Required: No.
>
> Introduced: 3.0a11

加上 `killasgroup=true` 的配置后，正在运行中的 celery 进程确实会被关闭，但也引来了另外一个问题：

- 由于在 celery 任务中还有通过 shell 发起 `nohup` 的进程调用，如果加上该配置，那么这些通过 `nohup` 调用的进程也会被 kill。

所以尽管进程是通过 `nohup` 启动，但它仍然是 celery worker 进程的子进程（虽然我们通过 `ps` 看到的父进程号已经不是 celery worker 进程对应的进程号了）。这其实有点反直觉，查询相关文档后才知道，原来 shell 会在登出前清理并发送信号 `SIGNUP` 给自己可控制的进程，在使用的终端设备（键盘输入、屏幕输出等）也会被关闭，而 `nohup` 的作用只是确保 `SIGNUP` 信号会被忽略，且屏幕等终端设备不会被使用。这样通过 `nohup` 调用的进程才可以在登出 shell 后继续运行。

但是 `nohup` 并不会破坏进程的继承关系，所以当通过进程组关闭时，`nohup` 调用的进程也不会成为漏网之鱼。

那么如果想要保留 `nohup` 调用的进程，但是停止 celery worker 进程呢？

- 一种方法是不用 `nohup`，而是 `fork` 一个新的进程，然后关闭自身，保留 `fork` 的进程。

- 另外一种方法是保留 `nohup` 的调用逻辑，在停止 celery worker 进程的地方做调整，具体的说，就是去掉 `killasgroup=true` 的配置，并在停止 supervisor 前记录下正在运行的 celery worker 进程的进程号，然后在 supervisor 停止后 kill 记录下的进程号，这样 celery worker 进程就可以被正常关闭。

本文使用第二种方法做一个简单的实现：

```shell
echo "正在记录当前运行的 celery 进程到 celery-worker-pid.txt"
python manage.py celery savepid celery-worker-pid.txt
supervisorctl -c supervisord.conf shutdown

# 如果有在运行的 celery worker 进程，就关闭掉
celerypid=`cat celery-worker-pid.txt`
if [ -n "${celerypid}" ]; then
    echo "正在清理残留的 celery 进程"
    kill -9 $celerypid
fi

echo "正在启动服务"
supervisord -c supervisord.conf
```

其中 `python manage.py celery savepid celery-worker-pid.txt` 是通过自定义 `django` 命令实现的收集正在运行的 celery 进程号，具体逻辑如下：

```python
from django.core.management.base import BaseCommand

from dbus.celery import app, revoke


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('args', metavar='method', nargs='*')

    def handle(self, method, *args, **options):
        getattr(self, method)(*args)

    def savepid(self, filepath):
        """记录正在运行的任务 pid 到指定文件"""
        i = app.control.inspect()
        active_tasks = i.active() or {}
        workers = []

        for _, tasks in active_tasks.items():
            for task in tasks:
                print(task)
                workers.append(str(task['worker_pid']))

        with open(filepath, 'w', encoding='utf8') as f:
            f.write(' '.join(workers))
```
{: file='/home/kingron/app/myapp/myapp/management/commands/celery.py' }


---

1. [python - Make supervisor stop Celery workers correctly - Stack Overflow](https://stackoverflow.com/questions/31800447/make-supervisor-stop-celery-workers-correctly "python - Make supervisor stop Celery workers correctly - Stack Overflow")
2. [python - Process started with nohup is not detached from parent - Stack Overflow](https://stackoverflow.com/questions/42608290/process-started-with-nohup-is-not-detached-from-parent "python - Process started with nohup is not detached from parent - Stack Overflow")
