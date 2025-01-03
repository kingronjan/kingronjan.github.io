---
categories:
- database
- mysql
cnblogid: 15007512
date: 2021-07-13 17:26 +0800
id: bbb13b05-c032-4598-9161-6ffae552ae9b
layout: post
tags:
- database
- mysql
- centos
title: CentOS 7 安装 MySQL
---

1. 下载安装包

   ```bash
   # 下载地址参考 https://dev.mysql.com/downloads/
   wget -i -c https://repo.mysql.com//mysql80-community-release-el7-3.noarch.rpm
   ```

2. 运行安装包

   ```bash
   yum -y install mysql80-community-release-el7-3.noarch.rpm
   ```

3. 安装数据库，这步可能会花些时间

   ```bash
   yum install mysql-community-server
   ```

4. 启动服务

   ```bash
   systemctl start mysqld.service
   ```

5. 找密码

   ```bash
   grep password /var/log/mysqld.log
   ```

   内容如下：

   ```
   2019-10-16T04:24:00.078079Z 1 [Note] A temporary password is generated for root@  
   
   localhost: oQ+-SPrhh4Bu
   ```

6. 登录 mysql 并输入密码

   ```bash
   mysql -uroot -p
   ```

7. 修改密码

   ```sql
   ALTER USER 'root'@'localhost' IDENTIFIED BY '1234';
   ```

   修改提示 `Your password does not satisfy the current policy requirements`，先执行下面的 sql 再修改：

   ```sql
   SET GLOBAL validate_password.policy = 0;
   SET GLOBAL validate_password.length = 4;
   ```

8. 修改远程访问密码

   ```sql
   grant all privileges on *.* to 'root'@'%' identified by '123456' with grant option;
   flush privileges;
   
   -- MySQL 8.0 中使用
   -- 1. 更新域属性，'%'表示允许外部访问
   update mysql.user set host='%' where user ='root';
   -- 2. 刷新权限
   flush privileges;
   -- 3. 授权
   GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' WITH GRANT OPTION;
   ```

9. 开放端口

   ```shell
   # 开放 3306 端口
   firewall-cmd --zone=public --add-port=3306/tcp --permanent
   
   # 重新启动防火墙
   firewall-cmd --reload
   ```