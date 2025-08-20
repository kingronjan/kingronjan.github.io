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



参考：

- [Docker安装Kafka - SpringCore - 博客园](https://www.cnblogs.com/fanqisoft/p/18092082)
- [kafka/docker/examples/docker-compose-files/single-node/plaintext/docker-compose.yml at trunk · apache/kafka](https://github.com/apache/kafka/blob/trunk/docker/examples/docker-compose-files/single-node/plaintext/docker-compose.yml)



```bash
export MACHINE_IP=`ifconfig eth0 | grep "inet " | awk -F " " '{print $2}'`
```



docker compose 配置:

```yaml
$ cat docker-compose.yml
version: '2'
services:
  broker:
    image: hub.rat.dev/apache/kafka
    hostname: broker
    container_name: broker
    ports:
      - '9092:9092'
    environment:
      KAFKA_NODE_ID: 1
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: 'CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT'
      KAFKA_ADVERTISED_LISTENERS: 'PLAINTEXT_HOST://172.19.36.143:9092,PLAINTEXT://broker:19092'
      KAFKA_PROCESS_ROLES: 'broker,controller'
      KAFKA_CONTROLLER_QUORUM_VOTERS: '1@broker:29093'
      KAFKA_LISTENERS: 'CONTROLLER://:29093,PLAINTEXT_HOST://:9092,PLAINTEXT://:19092'
      KAFKA_INTER_BROKER_LISTENER_NAME: 'PLAINTEXT'
      KAFKA_CONTROLLER_LISTENER_NAMES: 'CONTROLLER'
      CLUSTER_ID: '4L6g3nShT-eMCtK--X86sw'
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS: 0
      KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1
      KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1
      KAFKA_SHARE_COORDINATOR_STATE_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_SHARE_COORDINATOR_STATE_TOPIC_MIN_ISR: 1
      KAFKA_LOG_DIRS: '/tmp/kraft-combined-logs'
```



启动：

```shell
docker compose up -d
```





启动失败，查看日志：

```bash
docker logs <container id>
```