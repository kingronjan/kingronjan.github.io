---
layout: post
title: "通过 api 发起 Jenkins 构建并持续打印 console 日志"
date: 2024-10-18 17:28 +0800
categories: [python, snippets]
tags: [python, snippets]
hidden: true
---

```python
import time
from subprocess import check_output

from jenkinsapi.jenkins import Jenkins
from jenkinsapi.job import Job

job_name = '<jenkins-job>'
job_url = 'http://<jenkins-address>/job/' + job_name

username = '<jenkins-user>'
password = '<jenkins-pwd>'

# 读取当前分支信息
git_status = check_output(['git', 'status'], text=True)
branch = git_status.split('\n')[0]
branch = branch.rsplit()[-1]

# 构建参数
params = {
    'tag': 'origin/%s' % branch,
}

base_url, *_, name = job_url.rsplit('/', maxsplit=2)

j = Jenkins(base_url, username=username, password=password)
job = Job(job_url, name, j)


def show_last_output():
    """打印最后一次的构建的输出信息"""
    last_build = job.get_last_build()
    bulid_output(last_build)


def make_new_build():
    """发起新的调用，并打印新调用的输出信息"""
    last_build = job.get_last_build()
    job.invoke(delay=0, build_params=params)

    print('Build invoked with params:')
    print('\n'.join('%s: %s' % (k, v) for k, v in params.items()))
    print('Fetching build no...')

    new_build = None
    while True:
        new_build = job.get_last_build()
        if new_build.buildno != last_build.buildno:
            break
        time.sleep(1)

    bulid_output(new_build)


def bulid_output(build):
    """打印 build 的输出信息"""
    print('Console output of build', build)
    print('-' * 120)

    super_get_url = job.jenkins.requester.get_url

    def get_url(*a, **kw):
        resp = super_get_url(*a, **kw)
        resp._content = resp.text
        return resp

    job.jenkins.requester.get_url = get_url

    for text in build.stream_logs(1):
        print(text)


if __name__ == '__main__':
    # show_last_output()
    make_new_build()

```

