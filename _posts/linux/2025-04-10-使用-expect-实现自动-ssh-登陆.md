---
categories:
- linux
date: 2025-04-10 17:35 +0800
id: ede9614f-88ef-449e-9541-61eacbf42e34
layout: post
tags:
- linux
- expect
- ssh
title: 使用 expect 实现自动 ssh 登陆
---

### 简单实现

```shell
#!/bin/bash

expect -c '
spawn ssh user@domain
expect "assword:"
send -- "mypasswordhere\n"
interact
'
```

`expect` 会在  `interact` 的地方把终端的控制权交给用户。



### 暂停、输入、继续 expect

如果中途需要停下来，手动输入密码，然后继续后面的步骤，比如二次验证的密码等，可以使用：

```shell
#!/bin/bash

expect -c '
spawn ssh user@domain
expect "assword:"
send -- "mypasswordhere\n"

expect "2nd password:"
stty -echo
expect_user -re "(.*)\[\r\n]"
stty echo
send "$expect_out(buffer)\r"

interact
'
```

默认情况下，用户输入的字符都会显示在终端，为了防止输入的密码被别人看到，这里使用了 `stty -echo` 关闭输入回显，并使用 `stty echo` 再次打开。

通常，`expect` 会把所有匹配到的内容保存在 `expect_out(0,string)`, 另外还会把所有的输出都保存到 `expect_out(buffer)`，每一个子匹配则会被顺序放到 `expect_out`，可以通过  `expect_out(1,string)`, `expect_out(2,string)` 等方式获取到，其关系图如下：

![](https://i.sstatic.net/vJqY8.png)



如果需要获取输出的内容，并存储为变量，可以使用如下方式：

```shell
#!/bin/bash
expect -c '
spawn ssh user@domain
expect "password"
send "mypasswordhere\r"
expect "\\\$" { puts matched_literal_dollar_sign}
send "cat input_file\r"; # Replace this code with your java program commands
expect -re {-\r\n(.*?)\s\s}
set output $expect_out(1,string)
#puts $expect_out(1,string)
puts "Result : $output"
'
```



### 使用 expect 而不是 bash

上面的脚本都是用 `#!/bin/bash` 作为执行文件，实际上也可以指定 `expect` 作为执行文件，通常为 `#!/usr/bin/expect`，例如：

```shell
#!/usr/bin/expect

# 可以使用 exec 执行 bash 命令
exec source env.sh

spawn ssh user@domain
expect "assword:"
send -- "mypasswordhere\n"

interact
```

这样做的好处是不用把所有命令都写到 `expect -c ` 所指定的单引号范围内了，尤其是在命令本身包含单引号时，这样可以避免很多麻烦的转义。



参考：[tcl - Expect: extract specific string from output - Stack Overflow](https://stackoverflow.com/questions/27089739/expect-extract-specific-string-from-output)