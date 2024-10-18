---
layout: post
title: "消费 kafka topic 数据"
date: 2024-10-18 17:26 +0800
categories: [python, snippets]
tags: [python, snippets]
hidden: true
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

