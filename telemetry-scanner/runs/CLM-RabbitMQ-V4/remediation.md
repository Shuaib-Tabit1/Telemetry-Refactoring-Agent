```diff
--- a/ScmCoreInstrumentationServiceCollectionExtensions.cs
+++ b/ScmCoreInstrumentationServiceCollectionExtensions.cs
@@
 				options.AddScmCassandraPersistenceInstrumentation();
+				// Enable RabbitMQ tracing to surface publish/consume operations.
+				options.AddRabbitMQInstrumentation();
 				configureTracer?.Invoke(options);
@@
 				options.AddCassandraInstrumentation();
 				options.AddScmCassandraPersistenceInstrumentation();
 				options.AddRedisCacheMetrics();
+				// Capture RabbitMQ metrics (e.g., delivered / published message counts).
+				options.AddRabbitMQInstrumentation();
 				options.SetExemplarFilter(ExemplarFilterType.TraceBased);
 				options.AddSqlClientInstrumentation();
 
 				configureMeter?.Invoke(options);
```

### Explanation
Added `AddRabbitMQInstrumentation()` to both the `TracerProviderBuilder` and `MeterProviderBuilder` configuration sections.  
This activates the official OpenTelemetry RabbitMQ instrumentation, which automatically creates spans for publish and consume operations with the correct semantic‐convention attributes (`messaging.system = rabbitmq`, `messaging.destination`, `messaging.rabbitmq.routing_key`, etc.), making RabbitMQ activity visible in Jaeger traces and metrics.