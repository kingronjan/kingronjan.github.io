---
categories:
- python
- celery
date: 2025-05-23 17:53 +0800
id: b6ef6ebd-3eb4-4fc7-a2d5-a88d0b71ef36
layout: post
tags:
- python
- celery
title: 关于 celery worker 重复执行相同 id 任务的问题
---

### 现象

查看 celery 日志发现有的任务被重复的接收和执行了：

```
[2025-05-23 17:47:19,386: INFO/MainProcess] Task myapp.hello[1c464ff7-ee5f-4a27-943b-0854eeab3083] received
[2025-05-23 17:47:19,907: INFO/MainProcess] Task myapp.hello[9bf3bb88-e2cd-4ece-ba07-feb9f7a4f0fd] received
[2025-05-23 17:47:22,819: WARNING/ForkPoolWorker-1] waitting
[2025-05-23 17:47:22,821: INFO/MainProcess] Task myapp.hello[7bd1e485-6083-4def-81d7-653848db99f3] received
[2025-05-23 17:47:27,828: WARNING/ForkPoolWorker-1] waitting
[2025-05-23 17:47:27,830: INFO/MainProcess] Task myapp.hello[ffeb9b07-c623-419e-98d8-f8a55f148536] received
[2025-05-23 17:47:32,836: WARNING/ForkPoolWorker-1] waitting
[2025-05-23 17:47:32,838: INFO/MainProcess] Task myapp.hello[1c464ff7-ee5f-4a27-943b-0854eeab3083] received
[2025-05-23 17:47:37,844: INFO/ForkPoolWorker-1] Task myapp.hello[1c464ff7-ee5f-4a27-943b-0854eeab3083] succeeded in 5.008163110000169s: 'hello world'
[2025-05-23 17:47:37,845: WARNING/ForkPoolWorker-1] waitting
[2025-05-23 17:47:37,847: INFO/MainProcess] Task myapp.hello[9bf3bb88-e2cd-4ece-ba07-feb9f7a4f0fd] received
[2025-05-23 17:47:42,854: INFO/ForkPoolWorker-1] Task myapp.hello[9bf3bb88-e2cd-4ece-ba07-feb9f7a4f0fd] succeeded in 5.008809007000309s: 'hello world'
[2025-05-23 17:47:42,855: WARNING/ForkPoolWorker-1] waitting
[2025-05-23 17:47:42,858: INFO/MainProcess] Task myapp.hello[7bd1e485-6083-4def-81d7-653848db99f3] received
[2025-05-23 17:47:47,863: INFO/ForkPoolWorker-1] Task myapp.hello[7bd1e485-6083-4def-81d7-653848db99f3] succeeded in 5.008066221999798s: 'hello world'
[2025-05-23 17:47:47,864: WARNING/ForkPoolWorker-1] waitting
[2025-05-23 17:47:47,866: INFO/MainProcess] Task myapp.hello[ffeb9b07-c623-419e-98d8-f8a55f148536] received
[2025-05-23 17:47:52,872: INFO/ForkPoolWorker-1] Task myapp.hello[ffeb9b07-c623-419e-98d8-f8a55f148536] succeeded in 5.007953701999213s: 'hello world'
[2025-05-23 17:47:52,873: WARNING/ForkPoolWorker-1] waitting
[2025-05-23 17:47:52,875: INFO/MainProcess] Task myapp.hello[4d187035-d76c-443f-b592-0fe5fd7dbe41] received
[2025-05-23 17:47:57,880: INFO/ForkPoolWorker-1] Task myapp.hello[1c464ff7-ee5f-4a27-943b-0854eeab3083] succeeded in 5.007223296999655s: 'hello world'
[2025-05-23 17:47:57,882: WARNING/ForkPoolWorker-1] waitting
[2025-05-23 17:47:57,884: INFO/MainProcess] Task myapp.hello[36f1bacb-d03b-4f9b-b94f-e51b2789830c] received
[2025-05-23 17:48:02,888: INFO/ForkPoolWorker-1] Task myapp.hello[9bf3bb88-e2cd-4ece-ba07-feb9f7a4f0fd] succeeded in 5.00692129700019s: 'hello world'
[2025-05-23 17:48:02,889: WARNING/ForkPoolWorker-1] waitting
[2025-05-23 17:48:02,892: INFO/MainProcess] Task myapp.hello[792671c4-c53b-4866-b307-cea92d43d6f7] received
[2025-05-23 17:48:07,897: INFO/ForkPoolWorker-1] Task myapp.hello[7bd1e485-6083-4def-81d7-653848db99f3] succeeded in 5.007225551000374s: 'hello world'
[2025-05-23 17:48:07,898: WARNING/ForkPoolWorker-1] waitting
[2025-05-23 17:48:12,905: INFO/ForkPoolWorker-1] Task myapp.hello[ffeb9b07-c623-419e-98d8-f8a55f148536] succeeded in 5.007138986000427s: 'hello world'
[2025-05-23 17:48:12,906: WARNING/ForkPoolWorker-1] waitting
[2025-05-23 17:48:17,914: INFO/ForkPoolWorker-1] Task myapp.hello[4d187035-d76c-443f-b592-0fe5fd7dbe41] succeeded in 5.00834930200017s: 'hello world'
[2025-05-23 17:48:17,915: WARNING/ForkPoolWorker-1] waitting
[2025-05-23 17:48:22,923: INFO/ForkPoolWorker-1] Task myapp.hello[36f1bacb-d03b-4f9b-b94f-e51b2789830c] succeeded in 5.0081579010002315s: 'hello world'
[2025-05-23 17:48:22,925: WARNING/ForkPoolWorker-1] waitting
[2025-05-23 17:48:27,932: INFO/ForkPoolWorker-1] Task myapp.hello[792671c4-c53b-4866-b307-cea92d43d6f7] succeeded in 5.007721992999905s: 'hello world'
```





### 参考

1. [Using Redis — Celery 5.5.2 documentation](https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/redis.html#id3)
2. [Optimizing — Celery 5.5.2 documentation](https://docs.celeryq.dev/en/stable/userguide/optimizing.html#prefetch-limits)