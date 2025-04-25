---
categories:
- linux
date: 2025-04-10 17:35 +0800
id: ede9614f-88ef-449e-9541-61eacbf42e34
layout: post
tags:
- linux
title: 使用 expect 实现自动 ssh 登陆
---

简单实现：

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

参考：[tcl - Expect: extract specific string from output - Stack Overflow](https://stackoverflow.com/questions/27089739/expect-extract-specific-string-from-output)