---
categories:
- python
- snippets
date: 2024-10-18 17:28 +0800
hidden: true
id: f6fcdb00-b639-445a-a3c1-b1b692c6bd7e
layout: post
tags:
- python
- snippets
title: 通过 flink table 在 hudi 建表并写入数据
---

```python
from pyflink.table import EnvironmentSettings, TableEnvironment

# 通过 stream table environment 来执行查询
# env_settings = EnvironmentSettings.in_streaming_mode()
# table_env = TableEnvironment.create(env_settings)

settings = EnvironmentSettings.new_instance().in_batch_mode().use_blink_planner().build()
t_env = TableEnvironment.create(settings)

# 原表
my_source_ddl = """
    CREATE TABLE 
        test_table(uuid VARCHAR(200) PRIMARY KEY NOT ENFORCED,
            name VARCHAR(100)) 
            WITH (
                'connector' = 'hudi',
                'path' = 'hdfs://<hdfs-address>/wls/warehouse/tablespace/external/hive/<hive-db>.db/<hive-table>',
                'table.type' = 'COPY_ON_WRITE',
                'hive_sync.enable' = 'true',
                'hive_sync.table'='<hive-table>',
                'hive_sync.db'='<hive-db>',
                'hive_sync.mode' = 'hms',
                'hive_sync.metastore.uris' = 'thrift://<metastore-uris>'
                )
"""

insert_sql = """
insert into test_table values ('jar','john')
"""

my_sink_ddl = """
    create table mySink (
        word VARCHAR,
        `count` BIGINT
    ) with (
        'connector' = 'filesystem',
        'format' = 'csv',
        'path' = '/tmp/output'
    )
"""

t_env.execute_sql(my_source_ddl)
t_env.execute_sql(insert_sql)
t_env.execute_sql(my_sink_ddl)

```



---

1. [Table API 教程 \| Apache Flink](https://nightlies.apache.org/flink/flink-docs-release-1.13/zh/docs/dev/python/table_api_tutorial/ "Table API 教程 \| Apache Flink")