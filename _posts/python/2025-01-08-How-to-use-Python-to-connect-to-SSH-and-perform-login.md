---
categories:
- python
date: 2025-01-08 17:07 +0800
id: 90523c75-b997-4e9d-a320-04bc2520a647
layout: post
tags:
- python
title: How to use Python to connect to SSH and perform login
---

This article presents two methods to show how to use SSH connections and login in Python.

### pexpect

The [pexpect](https://github.com/pexpect/pexpect "pexpect/pexpect: A Python module for controlling interactive programs in a pseudo-terminal") module provides a very useful class called [pxssh](https://pexpect.readthedocs.io/en/stable/api/pxssh.html "pxssh - control an SSH session — Pexpect 4.8 documentation"), specifically designed for SSH connections.

Here is the introduction of pxssh in the [official manual](https://pexpect.readthedocs.io/en/stable/api/pxssh.html "pxssh - control an SSH session — Pexpect 4.8 documentation"):

This adds methods for login, logout, and expecting the shell prompt. It does various tricky things to handle many situations in the SSH login process. For example, if the session is your first login, then pxssh automatically accepts the remote certificate; or if you have public key authentication setup then pxssh won’t wait for the password prompt.

pxssh uses the shell prompt to synchronize output from the remote host. In order to make this more robust it sets the shell prompt to something more unique than just $ or #. This should work on most Borne/Bash or Csh style shells.

Example that runs a few commands on a remote server and prints the result:

```python
import getpass
from pexpect import pxssh

try:
    s = pxssh.pxssh()
    hostname = raw_input('hostname: ')
    username = raw_input('username: ')
    password = getpass.getpass('password: ')
    s.login(hostname, username, password)
    s.sendline('uptime')   # run a command
    s.prompt()             # match the prompt
    print(s.before)        # print everything before the prompt.
    s.sendline('ls -l')
    s.prompt()
    print(s.before)
    s.sendline('df')
    s.prompt()
    print(s.before)
    s.logout()
except pxssh.ExceptionPxssh as e:
    print("pxssh failed on login.")
    print(e)
```

Example showing how to specify SSH options:

```python
from pexpect import pxssh
s = pxssh.pxssh(options={
                    "StrictHostKeyChecking": "no",
                    "UserKnownHostsFile": "/dev/null"})
...
```



### frabic2+

Fabric2 and above versions provide a very convenient ssh connection function, it builds on top of [Invoke](https://pyinvoke.org/) (subprocess command execution and command-line features) and [Paramiko](https://paramiko.org/) (SSH protocol implementation), extending their APIs to complement one another and provide additional functionality. The following is an example of how to use it:

- Simple use

  ```python
  from fabric2 import Connection
  
  host = 'user@localhost'
  pwd = 'your root password'
  
  conn = Connection(host, connect_kwargs={'password': pwd})
  ```

- Use sudo with sudo user

  ```python
  from fabric import Connection, Config
  
  host = 'user@localhost'
  sudo_user = 'sudouser'
  
  config = Config(overrides={'sudo': {'user': sudo_user}})
  c = Connection(host, config=config)
  
  c.sudo('whoami')
  ```

- Use sudo with password

  ```python
  from fabric import Connection, Config
  
  host = 'user@localhost'
  sudo_pass = 'your sudo password'
  sudo_user = 'sudouser'
  
  config = Config(overrides={'sudo': {'password': sudo_pass}})
  c = Connection(host, config=config)
  
  c.sudo('/bin/bash -l -c whoami', user=sudo_user)
  ```

- Use su if you don't have sudo privileges but have the root user's password

  ```python
  from invoke.watchers import Responder
  from fabric2 import Connection
  
  host = 'user@localhost'
  pwd = 'your user password'
  root_pwd = 'your root password'
  
  responder = Responder(pattern=r'Password:.*?', response=root_pwd + '\n')
  conn = Connection(host, connect_kwargs={'password': pwd})
  conn.run('su root -c whoami', watchers=[responder])
  ```

  

### Reference

1. [pxssh - control an SSH session — Pexpect 4.8 documentation](https://pexpect.readthedocs.io/en/stable/api/pxssh.html "pxssh - control an SSH session — Pexpect 4.8 documentation")
2. [Welcome to Fabric! — Fabric documentation](https://www.fabfile.org/index.html "Welcome to Fabric! — Fabric documentation")
3. [Python Fabric Sudo su - user - Stack Overflow](https://stackoverflow.com/questions/54638426/python-fabric-sudo-su-user "Python Fabric Sudo su - user - Stack Overflow")