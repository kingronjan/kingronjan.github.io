---
layout: post
title: "debezium oracle 源码学习"
date: 2024-09-01 07:48 +0800
categories: [java, debezium]
tags: [java, debezium]
description: "dbezium 数据抽取源码学习笔记"
---



### 启动分析

```java
// io.debezium.connector.oracle.OracleConnectorTask#start
ChangeEventSourceCoordinator<OraclePartition, OracleOffsetContext> coordinator = new ChangeEventSourceCoordinator<>(
  previousOffsets,
  errorHandler,
  OracleConnector.class,
  connectorConfig,
  new OracleChangeEventSourceFactory(connectorConfig, connectionFactory, errorHandler, dispatcher, clock, schema, jdbcConfig, taskContext,
                                     streamingMetrics, snapshotterService),
  new OracleChangeEventSourceMetricsFactory(streamingMetrics),
  dispatcher,
  schema, signalProcessor,
  notificationService, snapshotterService);

// 最终调用该方法启动
coordinator.start(taskContext, this.queue, metadataProvider);

return coordinator;
```



`coordinator.start` 方法：

```java
previousLogContext.set(taskContext.configureLoggingContext("snapshot"));
snapshotMetrics.register();
streamingMetrics.register();
LOGGER.info("Metrics registered");

context = new ChangeEventSourceContextImpl();
LOGGER.info("Context created");

snapshotSource = changeEventSourceFactory.getSnapshotChangeEventSource(snapshotMetrics, notificationService);
executeChangeEventSources(taskContext, snapshotSource, previousOffsets, previousLogContext, context);
```



最终执行了：`executeChangeEventSources`

```java
// io.debezium.pipeline.ChangeEventSourceCoordinator#executeChangeEventSources
protected void executeChangeEventSources(CdcSourceTaskContext taskContext, SnapshotChangeEventSource<P, O> snapshotSource, Offsets<P, O> previousOffsets,
                                         AtomicReference<LoggingContext.PreviousContext> previousLogContext, ChangeEventSourceContext context)
  throws InterruptedException {
  final P partition = previousOffsets.getTheOnlyPartition();
  final O previousOffset = previousOffsets.getTheOnlyOffset();

  previousLogContext.set(taskContext.configureLoggingContext("snapshot", partition));
  
  // 做了一次快照并拿到了 offset
  SnapshotResult<O> snapshotResult = doSnapshot(snapshotSource, context, partition, previousOffset);

  getSignalProcessor(previousOffsets).ifPresent(s -> s.setContext(snapshotResult.getOffset()));

  LOGGER.debug("Snapshot result {}", snapshotResult);

  if (running && snapshotResult.isCompletedOrSkipped()) {
    if (snapshotResult.isCompleted()) {
      delayStreamingIfNeeded(context);
    }
    previousLogContext.set(taskContext.configureLoggingContext("streaming", partition));
    // 最终调用
    streamEvents(context, partition, snapshotResult.getOffset());
  }
}

protected void streamEvents(ChangeEventSourceContext context, P partition, O offsetContext) throws InterruptedException {
  initStreamEvents(partition, offsetContext);
  getSignalProcessor(previousOffsets).ifPresent(signalProcessor -> registerSignalActionsAndStartProcessor(signalProcessor,
                                                                                                          eventDispatcher, this, connectorConfig));

  if (snapshotterService != null && !snapshotterService.getSnapshotter().shouldStream()) {
    LOGGER.info("Streaming is disabled for snapshot mode {}", snapshotterService.getSnapshotter().name());
    return;
  }

  LOGGER.info("Starting streaming");
  // 调用了 LogMinerStreamingChangeEventSource#execute 方法
  streamingSource.execute(context, partition, offsetContext);
  LOGGER.info("Finished streaming");
}
```



### CDC数据解析

#### [OpenLogReplicator](https://www.bersler.com/openlogreplicator/)

```java
// debezium-connector-oracle/src/main/java/io/debezium/connector/oracle/olr/OpenLogReplicatorStreamingChangeEventSource.java

    public void execute(ChangeEventSourceContext context, OraclePartition partition, OracleOffsetContext offsetContext) throws InterruptedException {
        final Scn startScn = connectorConfig.getAdapter().getOffsetScn(offsetContext);
        final Long startScnIndex = offsetContext.getScnIndex();

        this.client = new OlrNetworkClient(connectorConfig);
        if (client.connect(startScn, startScnIndex)) {
            while (client.isConnected() && context.isRunning()) {
                final StreamingEvent event = client.readEvent();
                if (event != null) {
                    onEvent(event);
                }
            }
        }
```



`OlrNetworkClient` 读取配置：

```java
    public OlrNetworkClient(OracleConnectorConfig connectorConfig) {
        this.hostName = connectorConfig.getOpenLogReplicatorHostname();
        this.port = connectorConfig.getOpenLogReplicatorPort();
        this.sourceName = connectorConfig.getOpenLogReplicatorSource();
    }
```



### Logminner

启动

```java
// debezium-connector-oracle/src/main/java/io/debezium/connector/oracle/logminer/LogMinerStreamingChangeEventSource.java
    public void execute(ChangeEventSourceContext context, OraclePartition partition, OracleOffsetContext offsetContext) {
            this.effectiveOffset = offsetContext;
            startScn = connectorConfig.getAdapter().getOffsetScn(this.effectiveOffset);
            snapshotScn = offsetContext.getSnapshotScn();
            Scn firstScn = jdbcConnection.getFirstScnInLogs(archiveLogRetention, archiveDestinationName)
                    .orElseThrow(() -> new DebeziumException("Failed to calculate oldest SCN available in logs"));

            try (LogWriterFlushStrategy flushStrategy = resolveFlushStrategy()) {
                try (LogMinerEventProcessor processor = createProcessor(context, partition, offsetContext)) {
                    if (archiveLogOnlyMode && !waitForStartScnInArchiveLogs(context, startScn)) {
                        return;
                    }

                    initializeRedoLogsForMining(jdbcConnection, false, startScn);

                    int retryAttempts = 1;
                    Stopwatch sw = Stopwatch.accumulating().start();
                    while (context.isRunning()) {
                        streamingMetrics.setDatabaseTimeDifference(getDatabaseSystemTime(jdbcConnection));
                        if (archiveLogOnlyMode && !waitForStartScnInArchiveLogs(context, startScn)) {
                            break;
                        }
                        Instant start = Instant.now();
                        endScn = calculateUpperBounds(startScn, endScn);
                        flushStrategy.flush(jdbcConnection.getCurrentScn());
                        if (context.isRunning()) {
                            if (!startMiningSession(jdbcConnection, startScn, endScn, retryAttempts)) {
                                retryAttempts++;
                            }
                            else {
                                retryAttempts = 1;
                                // 读取和解析 startScn 和 endScn 之间的数据
                                startScn = processor.process(startScn, endScn);
                                streamingMetrics.setLastBatchProcessingDuration(Duration.between(start, Instant.now()));
                                captureSessionMemoryStatistics(jdbcConnection);
                            }
                            pauseBetweenMiningSessions();
                        }

```



再看处理方法

```java
    public Scn process(Scn startScn, Scn endScn) throws SQLException, InterruptedException {
        counters.reset();

        try (PreparedStatement statement = createQueryStatement()) {
            statement.setFetchSize(getConfig().getQueryFetchSize());
            statement.setFetchDirection(ResultSet.FETCH_FORWARD);
            statement.setString(1, startScn.toString());
            statement.setString(2, endScn.toString());

            Instant queryStart = Instant.now();
            try (ResultSet resultSet = statement.executeQuery()) {
                metrics.setLastDurationOfFetchQuery(Duration.between(queryStart, Instant.now()));

                Instant startProcessTime = Instant.now();
                // 处理两个 scn 之间的数据
                processResults(this.partition, resultSet);

                Duration totalTime = Duration.between(startProcessTime, Instant.now());
                metrics.setLastCapturedDmlCount(counters.dmlCount);

                if (counters.rows == 0) {
                    return startScn;
                }
                else {
                    return calculateNewStartScn(endScn, offsetContext.getCommitScn().getMaxCommittedScn());
                }
            }
        }
    }
```



### StartScn

```java
// in io.debezium.connector.oracle.logminer.LogMinerStreamingChangeEventSource#execute
startScn = connectorConfig.getAdapter().getOffsetScn(this.effectiveOffset);

// io.debezium.connector.oracle.logminer.LogMinerAdapter#getOffsetScn
@Override
public Scn getOffsetScn(OracleOffsetContext offsetContext) {
  return offsetContext.getScn();
}

// 所以又回到了 this.effectiveOffset
// io.debezium.connector.oracle.logminer.LogMinerStreamingChangeEventSource#execute
@Override
public void execute(ChangeEventSourceContext context, OraclePartition partition, OracleOffsetContext offsetContext) {
    prepareConnection(false);
    this.effectiveOffset = offsetContext;
    startScn = connectorConfig.getAdapter().getOffsetScn(this.effectiveOffset);
}

// io.debezium.connector.oracle.OracleOffsetContext#getScn
public Scn getScn() {
  return sourceInfo.getScn();
}
```



### 参考文档

1. [Debezium 特性深入介绍 - 亚马逊AWS官方博客](https://aws.amazon.com/cn/blogs/china/debezium-deep-dive/)：讲到了 dbz 的快照机制，单机和分布式的工作模式，些微提及了水位线算法
2. [Flink oracle cdc - Oracle Logminer CDC性能问题_flink oracle cdc-CSDN博客](https://blog.csdn.net/qiuqiufangfang1314/article/details/129095438)：默认的 logminner 存在性能问题，每秒处理数据不超过 1w，这篇文章讲了通过异步转移日志到不影响业务的 Oracle 实例，然后并发解析 logminner 的方法已提升性能
3. [LogMiner详细讲解 - 三鹿专供 - 博客园](https://www.cnblogs.com/sanlu/p/6150327.html) logminer 的使用方法介绍，包括添加、删除日志文件等

