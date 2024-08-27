---
layout: post
title: kafka 如何消费 topic 最新的 n 条数据
date: 2024-06-04 17:55 +0800
categories: [kafka]
tags: [kafka]
cnblogid: 18231420
---
### 使用 kafka 命令行

获取最大的 offset 值和对应的分区信息:

```bash
bin/kafka-run-class.sh kafka.tools.GetOffsetShell --broker-list localhost:9092 --topic mytopic

mytopic:2:11
mytopic:1:7
mytopic:0:15
mytopic:3:8
```

取最大 offset 值减去想要看到的数据条数，作为消费时的 offset 参数值，这里取分区 0，展示 5 条数据 (=15-10)

```bash
bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic mytopic --offset 10 --partition 0
```

需要注意的是，如果 topic 数据变动很频繁，这里消费到的数据可能不只 5 条，对此，消费时可以使用 `--max-message` 参数控制消费到的最大数据量。



### 使用 python 获取

原理和通过命令行获取相同，具体代码如下：

```python
from collections import defaultdict

from kafka import KafkaAdminClient, KafkaConsumer, KafkaProducer, TopicPartition


topic = 'mystopic'
max_consume_num = 5

c = KafkaConsumer(
	bootstrap_servers='localhost:9092',
    auto_offset_reset='earliest',
    enable_auto_commit=True
)

consumer.subscribe([topic])

# 获取分区和 offset
partitions = [TopicPartition(topic, partition) for partition in consumer.partitions_for_topic(topic)]
end_offsets = consumer.end_offsets(partitions)

# 获取每个分区最大的消费数量
partition_offsets = {}
for partition in partitions:
    if not end_offsets[partition]:
        partition_offsets[partition.partition] = 0
        continue

    offset = end_offsets[partition] - max_consume_num
    if offset < 0:
        # 分区的数据量小于最大的消费量
        # 因此从 0 开始消费即可
        offset = 0
        partition_offsets[partition.partition] = end_offsets[partition]

    else:
        partition_offsets[partition.partition] = max_consume_num

    consumer.seek(partition, offset)


# 所有分区加起来要消费的数据量
actual_max_consume_num = sum(partition_offsets.values())
if not actual_max_consume_num:
    # topic 数据为空
    print('Empty.')

else:
    consumed = defaultdict(int)

    for m in consumer:
        if m.partition not in partition_offsets:
            continue
        
        consumed[m.partition] += 1
        if consumed[m.partition] > partition_offsets[m.partition]:
            if all(v >= partition_offsets[k] for k, v in consumed.items()):
                # 如果全部分区都已经消费到了最大的数据量
                # 则终止消费
                break
            continue

        print(m)

consumer.close()

```

