---
categories:
- python
- snippets
date: 2024-10-18 17:26 +0800
hidden: true
id: 7cc39cf1-df48-4ffb-86b0-ae220d4e558e
layout: post
tags:
- python
- snippets
title: 生产 kafka topic 数据
---

```python
import json

from ast import literal_eval

from kafka import KafkaAdminClient, KafkaConsumer, KafkaProducer
from kafka.errors import TopicAlreadyExistsError
from kafka.admin import NewTopic

bootstrap_servers = '127.0.0.1:9092'
topic_name = '<topic-name>'

config = {
    "num_partitions": 1,
    "replication_factor": 1,
    "topic_configs": {
        "cleanup.policy": "delete"
    }
}

new_topic = NewTopic(topic_name, **config)

print('正在创建 Topic %s，使用配置: \n%s' % (topic_name, json.dumps(config, indent=4)))

cli = KafkaAdminClient(bootstrap_servers=bootstrap_servers)

cli.delete_topics([topic_name])

try:
    cli.create_topics([new_topic])
except TopicAlreadyExistsError:
    print('Topic %s 已存在' % topic_name)

cli.close()


def serialize_value(val):
    return json.dumps(val).encode('ascii')

producer = KafkaProducer(
    bootstrap_servers=bootstrap_servers,
    value_serializer=serialize_value,
    max_request_size=10 * 1024 * 1024,
)

# 从 dict
producer.send(topic_name, key='xxx', value={'id': 1, 'name': 'x'}).get(timeout=10)


# 从通过 str 保存的消息文件读取
producer = KafkaProducer(
    bootstrap_servers=bootstrap_servers,
    max_request_size=10 * 1024 * 1024,
)

with open('<stringfy-py-message-file>', 'r') as f:
    message = literal_eval(f.read())
    producer.send(topic_name, key=message['key'], value=message['value']).get(timeout=10)

```