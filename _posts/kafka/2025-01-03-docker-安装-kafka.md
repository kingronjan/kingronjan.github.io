---
categories:
- kafka
date: 2025-01-03 15:27 +0800
id: 7436463c-3619-400d-b973-f14578f4e621
layout: post
tags:
- kafka
title: docker 安装 kafka
---

地址：https://hub.docker.com/r/apache/kafka



```bash
docker run -d  \
  --name broker \
  -p 9092:9092 -p 8083:8083 \
  -e KAFKA_NODE_ID=1 \
  -e KAFKA_ZOOKEEPER_CONNECT=0.0.0.0:2181 \
  -e KAFKA_LISTENERS=PLAINTEXT://0.0.0.0:9092 \
  -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092 \
  hub.geekery.cn/apache/kafka
```



启动失败，查看日志：

```bash
docker logs <container id>
```