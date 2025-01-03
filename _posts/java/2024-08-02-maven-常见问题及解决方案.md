---
categories:
- java
cnblogid: 18338354
date: 2024-08-02 11:15 +0800
id: 5330e021-914e-4ae9-aaa7-c061924f860c
layout: post
tags:
- java
- maven
title: maven 常见问题及解决方案
---

### resolution will not be reattempted until the update interval of nexus
强制更新
```bash
mvn clean install -U
```



### Could not find artifact
如果可以通过其他途径获取到相关的 jar 包，可以把 jar 包安装到本地仓库：
示例：demo.jar 包上传后，项目中设置的依赖为
```xml
<dependency>
    <groupId>com.abc</groupId>
    <artifactId>demo</artifactId>
    <version>3.3.0</version>
</dependency>
```
操作步骤为：
1. 打开命令行终端。
2. 使用 cd 命令导航到 JAR 文件所在的目录。
3. 运行以下命令将 JAR 文件安装到本地仓库：
```bash
# 替换 yourfile.jar 为实际的 JAR 文件名
# your.groupId、your.artifactId 和 your.version 为实际的项目组织 ID、项目 ID 和版本号
mvn install:install-file -Dfile=yourfile.jar -DgroupId=your.groupId -DartifactId=your.artifactId -Dversion=your.version -Dpackaging=jar
```



### ide 中创建项目时的 archetype 选择

maven 项目便于维护和部署，同时构建也很方便。在 ide 中选择创建 maven 项目时，会有一个选项 "create from archetype"，下面列举了很多，初学者往往一头雾水不知道该选什么，这些选项一般对应着不同框架所约定的文件目录结构，像在 python 中创建 flask，django，scrapy 等项目一样，如果对于简单的项目可以跳过该选项直接开始。

一些常见的 archetype 目录可以参考：[使用 IDEA 创建 Maven 项目，该如何选择 archetype ？ - 人人编程网](https://www.hxstrive.com/article/1265.htm#catalogue_16)

当然也可以做一个自己的 archetype 并注册到 ide 中，参考：[在 Idea 选择自己的 Archetype 创建项目前言 今天和大家分享下如何通过自己的模板项目来快速创建项目；通常项 - 掘金](https://juejin.cn/post/7340573362216271913)



### 使用 log4j

- 在 pom.xml 中添加依赖

  ```xml
          <dependency>
              <groupId>org.slf4j</groupId>
              <artifactId>slf4j-api</artifactId>
              <version>2.0.12</version>
          </dependency>
  
          <dependency>
              <groupId>org.slf4j</groupId>
              <artifactId>slf4j-log4j12</artifactId>
              <version>2.0.12</version>
          </dependency>
  ```

- 在 resources 下面新建 `log4j.properties` 文件

  ```properties
  log4j.rootLogger=INFO, stdout
  log4j.appender.stdout=org.apache.log4j.ConsoleAppender
  log4j.appender.stdout.Target=System.out
  log4j.appender.stdout.layout=org.apache.log4j.PatternLayout
  log4j.appender.stdout.layout.ConversionPattern=%d{yy/MM/dd HH:mm:ss} %p %c{2}: %m%n
  ```

  

### 参考
1. [maven执行报错resolution will not be reattempted until the update interval of nexus h - huojiao2006 - 博客园](https://www.cnblogs.com/huojiao2006/articles/5195965.html)
2. [解决Maven出现 Could not find artifact的 各种方法，亲测有效！！！-CSDN博客](https://blog.csdn.net/2301_79779756/article/details/138077045)
3. [Maven如何将JAR包上传至本地仓库及私服_maven发布到本地仓库_maven批量上传jar到本地库-CSDN博客](https://blog.csdn.net/2401_83703835/article/details/137472299)