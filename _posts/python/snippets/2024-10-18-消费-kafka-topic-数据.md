---
categories:
- python
- snippets
date: 2024-10-18 17:26 +0800
hidden: true
id: ca730ed2-7657-4158-b034-b3e0ed52dab7
layout: post
tags:
- python
- snippets
title: 消费 kafka topic 数据
---

```python
from contextlib import contextmanager
from kafka import KafkaAdminClient, KafkaConsumer, KafkaProducer
from kafka.admin import NewTopic
from kafka.consumer.fetcher import ConsumerRecord


@contextmanager
def consumer(topic_name, bootstrap_servers):
    c = KafkaConsumer(
        topic_name,
        bootstrap_servers=bootstrap_servers,
        auto_offset_reset='earliest',
        enable_auto_commit=True,
    )
    try:
        yield c
    finally:
        c.close()


with consumer(
        '<topic-name>',
        bootstrap_servers='<bootstrap-server>',
) as c:
    # ConsumerRecord
    for message in c:
        value = message.value
        print(message)
        break

```