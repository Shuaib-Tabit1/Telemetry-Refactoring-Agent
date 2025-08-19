```diff
--- a/ScmCoreInstrumentationServiceCollectionExtensions.cs
+++ b/ScmCoreInstrumentationServiceCollectionExtensions.cs
@@
 				options.AddSource("Azure.*");
 
 				// Enable telemetry in end to end tests.
 				options.AddSource("Xunit.DependencyInjection");
 
+				// RabbitMQ publish / consume spans.
+				// This automatically creates spans for BasicPublish and BasicConsume
+				// with the standard messaging semantic-convention attributes:
+				// messaging.system=rabbitmq, messaging.destination=<queue>, messaging.operation=publish/receive.
+				options.AddRabbitMQClientInstrumentation();
+
 				options.AddHttpClientInstrumentation();
 				options.ConfigureRedisCacheInstrumentation();
 				options.AddScmCassandraPersistenceInstrumentation();
 				configureTracer?.Invoke(options);
 
@@
 				options.AddProcessInstrumentation();
 				options.AddDocuSignDotNetRuntimeInstrumentation();
 				options.AddCassandraInstrumentation();
 				options.AddScmCassandraPersistenceInstrumentation();
 				options.AddRedisCacheMetrics();
+				// Propagate RabbitMQ metrics (if exposed by the instrumentation package).
+				options.AddMeter("OpenTelemetry.Instrumentation.RabbitMQ");
 				options.SetExemplarFilter(ExemplarFilterType.TraceBased);
 				options.AddSqlClientInstrumentation();
 
 				configureMeter?.Invoke(options);
```

### Explanation
1. Added the RabbitMQ client instrumentation to the tracer pipeline with `options.AddRabbitMQClientInstrumentation()`.  
   • This automatically creates spans for `BasicPublish` and `BasicConsume` that contain the standard OpenTelemetry messaging attributes (`messaging.system`, `messaging.destination`, `messaging.operation`).  
2. Registered the corresponding meter name (`OpenTelemetry.Instrumentation.RabbitMQ`) so any metrics emitted by the RabbitMQ instrumentation are captured.