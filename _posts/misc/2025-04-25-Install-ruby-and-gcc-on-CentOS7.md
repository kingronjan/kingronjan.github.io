---
categories:
- misc
date: 2025-04-25 13:15 +0800
id: 67d135a9-ac7b-4bee-bce4-3b234e2a80a2
layout: post
tags:
- misc
title: Install ruby and gcc on CentOS7
---

## Install ruby and gcc9 on CentOS 7 (docker)



### Run docker

```shell
docker run -itd -v $PWD:/jekyll/data -p 4000:4000 centos:7
docker cp /etc/yum.repos.d/CentOS-Base.repo efdba3312a44:/etc/yum.repos.d/CentOS-Base.repo
docker exec -it efdba3312a44 bash
```



### Install dependences

```shell
yum -y install wget
yum -y install which
```



### Set alias

Cause the docker image which I use not have this command yet.

```shell
alias cp='cp -i'
alias egrep='egrep --color=auto'
alias fgrep='fgrep --color=auto'
alias grep='grep --color=auto'
alias l.='ls -d .* --color=auto'
alias ll='ls -l --color=auto'
alias ls='ls --color=auto'
alias mv='mv -i'
alias rm='rm -i'
alias which='alias | /usr/bin/which --tty-only --read-alias --show-dot --show-tilde'
```

### Install RVM

```shell
gpg2 --keyserver keyserver.ubuntu.com --recv-keys 409B6B1796C275462A1703113804BB82D39DC0E3 7D2BAF1CF37B13E2069D6956105BD0E739499BDB
curl -sSL https://get.rvm.io | bash -s stable
```

### Install GCC v9

```shell
yum install centos-release-scl -y
```

Modify `/etc/yum.repos.d/CentOS-SCLo-scl.repo`:

```shell
$ vi /etc/yum.repos.d/CentOS-SCLo-scl.repo

# Remeber to remove the old config.
[centos-sclo-sclo]
name=CentOS-7 - SCLo sclo
baseurl=https://mirrors.aliyun.com/centos/7/sclo/x86_64/sclo/
# mirrorlist=http://mirrorlist.centos.org?arch=$basearch&release=7&repo=sclo-sclo
gpgcheck=0
enabled=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-SIG-SCLo

```

Modify `/etc/yum.repos.d/CentOS-SCLo-scl-rh.repo`:

```shell
$ vi /etc/yum.repos.d/CentOS-SCLo-scl-rh.repo

# Remeber to remove the old config.
[centos-sclo-rh]
name=CentOS-7 - SCLo rh
baseurl=https://mirrors.aliyun.com/centos/7/sclo/x86_64/rh/
# mirrorlist=http://mirrorlist.centos.org?arch=$basearch&release=7&repo=sclo-rh
gpgcheck=0
enabled=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-SIG-SCLo
```

Flush caches:

```shell
yum repolist
yum clean all
yum makecache
```

Check repos:

```shell
yum repolist enabled
```

And if you see this:

```shell
$ yum repolist enabled
Loaded plugins: fastestmirror, ovl
Repository centos-sclo-rh is listed more than once in the configuration
Repository centos-sclo-sclo is listed more than once in the configuration
Loading mirror speeds from cached hostfile
 * base: mirrors.cloud.aliyuncs.com
 * extras: mirrors.cloud.aliyuncs.com
 * updates: mirrors.cloud.aliyuncs.com
repo id                                                                               repo name                                                                                              status
base/7/x86_64                                                                         CentOS-7 - Base - mirrors.aliyun.com                                                                   10072
centos-sclo-rh/x86_64                                                                 CentOS-6.10 - SCLo rh                                                                                   3835
centos-sclo-sclo/x86_64                                                               CentOS-6.10 - SCLo sclo                                                                                  436
extras/7/x86_64                                                                       CentOS-7 - Extras - mirrors.aliyun.com                                                                   526
updates/7/x86_64                                                                      CentOS-7 - Updates - mirrors.aliyun.com                                                                 6173
repolist: 21042
```

You will notice that `centos-sclo-rh/x86_64`，`centos-sclo-sclo/x86_64` is still for ` CentOS-6.10`，thats will produce error like below when you try to install gcc by use command `yum install devtoolset-9-gcc* -y`，so disable them and put `/etc/yum.repos.d/CentOS-SCLo-scl.repo` and `/etc/yum.repos.d/CentOS-SCLo-scl-rh.repo` content to relate files.

The error will be like this:

```
$ yum install devtoolset-9-gcc* -y

...
---> Package libselinux-utils.x86_64 0:2.5-15.el7 will be installed
--> Finished Dependency Resolution
Error: Package: devtoolset-8-gcc-c++-8.3.1-3.2.el6.x86_64 (centos-sclo-rh)
           Requires: libmpfr.so.1()(64bit)
Error: Package: devtoolset-8-gcc-gfortran-8.3.1-3.2.el6.x86_64 (centos-sclo-rh)
           Requires: libgmp.so.3()(64bit)
Error: Package: devtoolset-8-gcc-8.3.1-3.2.el6.x86_64 (centos-sclo-rh)
           Requires: libmpfr.so.1()(64bit)
Error: Package: devtoolset-8-gcc-8.3.1-3.2.el6.x86_64 (centos-sclo-rh)
           Requires: libgmp.so.3()(64bit)
Error: Package: devtoolset-8-gcc-c++-8.3.1-3.2.el6.x86_64 (centos-sclo-rh)
           Requires: libgmp.so.3()(64bit)
Error: Package: devtoolset-8-gcc-gfortran-8.3.1-3.2.el6.x86_64 (centos-sclo-rh)
           Requires: libmpfr.so.1()(64bit)
 You could try using --skip-broken to work around the problem
 You could try running: rpm -Va --nofiles --nodigest
```

You can use ` grep 6.10 /etc/yum.repos.d/*` find which file shoud be modify, in my case is:

```shell
$ grep 6.10 /etc/yum.repos.d/*
/etc/yum.repos.d/CentOS-Base.repo:name=CentOS-6.10 - SCLo rh
/etc/yum.repos.d/CentOS-Base.repo:baseurl=http://vault.centos.org/centos/6.10/sclo/$basearch/rh/
/etc/yum.repos.d/CentOS-Base.repo:name=CentOS-6.10 - SCLo sclo
/etc/yum.repos.d/CentOS-Base.repo:baseurl=http://vault.centos.org/centos/6.10/sclo/$basearch/sclo/
```

So I change it, new content is:

```shell
# /etc/yum.repos.d/CentOS-Base.repo

...

# disable the 6.10 version
[centos-sclo-rh]
name=CentOS-6.10 - SCLo rh
baseurl=http://vault.centos.org/centos/6.10/sclo/$basearch/rh/
gpgcheck=1
enabled=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-SIG-SCLo

[centos-sclo-sclo]
name=CentOS-6.10 - SCLo sclo
baseurl=http://vault.centos.org/centos/6.10/sclo/$basearch/sclo/
gpgcheck=1
enabled=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-SIG-SCLo


[centos-sclo-sclo]
name=CentOS-7 - SCLo sclo
baseurl=https://mirrors.aliyun.com/centos/7/sclo/x86_64/sclo/
# mirrorlist=http://mirrorlist.centos.org?arch=$basearch&release=7&repo=sclo-sclo
gpgcheck=0
enabled=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-SIG-SCLo

[centos-sclo-rh]
name=CentOS-7 - SCLo rh
baseurl=https://mirrors.aliyun.com/centos/7/sclo/x86_64/rh/
# mirrorlist=http://mirrorlist.centos.org?arch=$basearch&release=7&repo=sclo-rh
gpgcheck=0
enabled=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-SIG-SCLo
```

Now check the repo again:

```shell
$ yum repolist enabled
Loaded plugins: fastestmirror, ovl
Repository centos-sclo-rh is listed more than once in the configuration
Repository centos-sclo-sclo is listed more than once in the configuration
Loading mirror speeds from cached hostfile
 * base: mirrors.cloud.aliyuncs.com
 * extras: mirrors.cloud.aliyuncs.com
 * updates: mirrors.cloud.aliyuncs.com
repo id                                                                            repo name                                                                                                 status
base/7/x86_64                                                                      CentOS-7 - Base - mirrors.aliyun.com                                                                      10072
centos-sclo-rh                                                                     CentOS-7 - SCLo rh                                                                                         3835
centos-sclo-sclo                                                                   CentOS-7 - SCLo sclo                                                                                        436
extras/7/x86_64                                                                    CentOS-7 - Extras - mirrors.aliyun.com                                                                      526
updates/7/x86_64                                                                   CentOS-7 - Updates - mirrors.aliyun.com                                                                    6173
repolist: 21042
```

all is for `CentOS-7`.

Install gcc-9:

```shell
yum install devtoolset-9-gcc* -y
```

and enable it:

```shell
scl enable devtoolset-9 bash

# Or use this for current bash
# source /opt/rh/devtoolset-9/enable
```

check the version, it's right:

```shell
$ gcc -v
Using built-in specs.
COLLECT_GCC=gcc
COLLECT_LTO_WRAPPER=/opt/rh/devtoolset-9/root/usr/libexec/gcc/x86_64-redhat-linux/9/lto-wrapper
Target: x86_64-redhat-linux
Configured with: ../configure --enable-bootstrap --enable-languages=c,c++,fortran,lto --prefix=/opt/rh/devtoolset-9/root/usr --mandir=/opt/rh/devtoolset-9/root/usr/share/man --infodir=/opt/rh/devtoolset-9/root/usr/share/info --with-bugurl=http://bugzilla.redhat.com/bugzilla --enable-shared --enable-threads=posix --enable-checking=release --enable-multilib --with-system-zlib --enable-__cxa_atexit --disable-libunwind-exceptions --enable-gnu-unique-object --enable-linker-build-id --with-gcc-major-version-only --with-linker-hash-style=gnu --with-default-libstdcxx-abi=gcc4-compatible --enable-plugin --enable-initfini-array --with-isl=/builddir/build/BUILD/gcc-9.3.1-20200408/obj-x86_64-redhat-linux/isl-install --disable-libmpx --enable-gnu-indirect-function --with-tune=generic --with-arch_32=x86-64 --build=x86_64-redhat-linux
Thread model: posix
gcc version 9.3.1 20200408 (Red Hat 9.3.1-2) (GCC)
```

### Install Ruby

Before install, you can also modify RVM's ruby installation source to Ruby China's ruby mirror server, which can import the installation speed for China.

```shell
echo "ruby_url=https://cache.ruby-china.com/pub/ruby" > /usr/local/rvm/user/db
```

And install compile dependencies:

```shell
yum install -y libyaml-dev
```

And install:

```
CC=/opt/rh/devtoolset-9/root/usr/bin/gcc rvm install 3.2.4
```

If any error occur, you reinstall it using the reinstall command after repair:

```shell
CC=/opt/rh/devtoolset-9/root/usr/bin/gcc rvm reinstall 3.2.4
```

Now check the version use `rvm list` or `ruby -v`:

```shell
$ ruby -v
ruby 3.2.4 (2024-04-23 revision af471c0e01) [x86_64-linux]
```

### Change gem source



```shell
# Add new and remove default.
$ gem sources --add https://gems.ruby-china.com/ --remove https://rubygems.org/

# list current sources.
$ gem sources -l
# shoud be one only.

# Config the bundler source
$ bundle config mirror.https://rubygems.org https://gems.ruby-china.com/
```

### Reference

1. [CentOS7下安装Ruby3.2.4的实施路径_centos7安装ruby-CSDN博客](https://blog.csdn.net/fredricen/article/details/142205493)
1. [Build failed: `psych` Could not be configured. It will not be installed. · Issue #386 · asdf-vm/asdf-ruby](https://github.com/asdf-vm/asdf-ruby/issues/386)
1. [Ruby 源代码镜像服务 · Ruby China](https://ruby-china.org/wiki/ruby-mirror)
1. [rubygems \| 镜像站使用帮助 \| 清华大学开源软件镜像站 \| Tsinghua Open Source Mirror](https://mirrors.tuna.tsinghua.edu.cn/help/rubygems/)
1. [Ruby - 国内镜像源 \| hyperzsb's ideas](https://hyperzsb.io/posts/ruby-mirror-source/)
1. [RVM 实用指南 · Ruby China](https://ruby-china.org/wiki/rvm-guide)