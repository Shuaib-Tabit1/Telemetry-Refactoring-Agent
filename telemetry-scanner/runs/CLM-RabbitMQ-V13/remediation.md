```diff
--- a/ScmCoreInstrumentationServiceCollectionExtensions.cs
+++ b/ScmCoreInstrumentationServiceCollectionExtensions.cs
@@
 				options.AddHttpClientInstrumentation();
 				options.ConfigureRedisCacheInstrumentation();
+				// Capture RabbitMQ producer/consumer activities following
+				// OpenTelemetry semantic conventions for messaging systems.
+				options.AddRabbitMQInstrumentation();
 				options.AddScmCassandraPersistenceInstrumentation();
 				configureTracer?.Invoke(options);
@@
 				options.AddProcessInstrumentation();
 				options.AddDocuSignDotNetRuntimeInstrumentation();
 				options.AddCassandraInstrumentation();
+				// Collect RabbitMQ metrics (e.g., delivered / published message counts).
+				options.AddRabbitMQInstrumentation();
 				options.AddScmCassandraPersistenceInstrumentation();
 				options.AddRedisCacheMetrics();
 				options.SetExemplarFilter(ExemplarFilterType.TraceBased);
```

### Explanation
Added `AddRabbitMQInstrumentation()` to both the `TracerProviderBuilder` and `MeterProviderBuilder` configuration blocks.  
This enables automatic creation of RabbitMQ spans and metrics with standard OpenTelemetry messaging attributes (`messaging.system=rabbitmq`, `messaging.destination`, `messaging.destination_kind=queue`, `messaging.operation`, etc.), allowing the clm-web service to emit RabbitMQ telemetry that will surface in Jaeger traces.