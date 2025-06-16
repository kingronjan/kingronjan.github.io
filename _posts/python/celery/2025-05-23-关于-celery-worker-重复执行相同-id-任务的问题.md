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

### Visibility timeout

If a task isn’t acknowledged within the [Visibility Timeout](https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/redis.html#redis-visibility-timeout) the task will be redelivered to another worker and executed.

This causes problems with ETA/countdown/retry tasks where the time to execute exceeds the visibility timeout; in fact if that happens it will be executed again, and again in a loop.

To remediate that, you can increase the visibility timeout to match the time of the longest ETA you’re planning to use. However, this is not recommended as it may have negative impact on the reliability. Celery will redeliver messages at worker shutdown, so having a long visibility timeout will only delay the redelivery of ‘lost’ tasks in the event of a power failure or forcefully terminated workers.

Broker is not a database, so if you are in need of scheduling tasks for a more distant future, database-backed periodic task might be a better choice. Periodic tasks won’t be affected by the visibility timeout, as this is a concept separate from ETA/countdown.

You can increase this timeout by configuring all of the following options with the same name (required to set all of them):

```
app.conf.broker_transport_options = {'visibility_timeout': 43200}
app.conf.result_backend_transport_options = {'visibility_timeout': 43200}
app.conf.visibility_timeout = 43200
```

The value must be an int describing the number of seconds.

Note: If multiple applications are sharing the same Broker, with different settings, the _shortest_ value will be used. This include if the value is not set, and the default is sent

### Prefetch Limits

*Prefetch* is a term inherited from AMQP that’s often misunderstood by users.

The prefetch limit is a **limit** for the number of tasks (messages) a worker can reserve for itself. If it is zero, the worker will keep consuming messages, not respecting that there may be other available worker nodes that may be able to process them sooner [[†\]](https://docs.celeryq.dev/en/stable/userguide/optimizing.html#id5), or that the messages may not even fit in memory.

The workers’ default prefetch count is the [`worker_prefetch_multiplier`](https://docs.celeryq.dev/en/stable/userguide/configuration.html#std-setting-worker_prefetch_multiplier) setting multiplied by the number of concurrency slots [[‡\]](https://docs.celeryq.dev/en/stable/userguide/optimizing.html#id6) (processes/threads/green-threads).

If you have many tasks with a long duration you want the multiplier value to be *one*: meaning it’ll only reserve one task per worker process at a time.

However – If you have many short-running tasks, and throughput/round trip latency is important to you, this number should be large. The worker is able to process more tasks per second if the messages have already been prefetched, and is available in memory. You may have to experiment to find the best value that works for you. Values like 50 or 150 might make sense in these circumstances. Say 64, or 128.

If you have a combination of long- and short-running tasks, the best option is to use two worker nodes that are configured separately, and route the tasks according to the run-time (see [Routing Tasks](https://docs.celeryq.dev/en/stable/userguide/routing.html#guide-routing)).



### Reference

1. [Using Redis — Celery 5.5.2 documentation](https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/redis.html#id3)
2. [Optimizing — Celery 5.5.2 documentation](https://docs.celeryq.dev/en/stable/userguide/optimizing.html#prefetch-limits)