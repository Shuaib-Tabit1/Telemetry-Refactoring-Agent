```diff
--- a/ScmCoreInstrumentationServiceCollectionExtensions.cs
+++ b/ScmCoreInstrumentationServiceCollectionExtensions.cs
@@
 using OpenTelemetry.Metrics;
 using OpenTelemetry.Trace;
+using OpenTelemetry.Instrumentation.RabbitMQ.Client;
 
 namespace ADEXS.ServiceFramework.OpenTelemetry.Extensions;
 
 /// <summary>
@@
 				options.ConfigureRedisCacheInstrumentation();
 				options.AddScmCassandraPersistenceInstrumentation();
+				// RabbitMQ client instrumentation
+				// This will create spans for publish/consume operations and
+				// automatically populate all OpenTelemetry messaging attributes
+				// (e.g., messaging.system = "rabbitmq", messaging.destination, routing_key, message_id, etc.).
+				options.AddRabbitMQClientInstrumentation();
 				configureTracer?.Invoke(options);
 
 				if (telemetryConsoleTargets != null)
 				{
 					options.AddConsoleExporter(o => o.Targets = telemetryConsoleTargets.Value);
```

### Explanation
1. Added `using OpenTelemetry.Instrumentation.RabbitMQ.Client;` to bring the extension method into scope.  
2. Registered `AddRabbitMQClientInstrumentation()` in the tracer builder.  
   • This automatically creates spans around `IModel.BasicPublish`/`BasicDeliver` and fills in all required OpenTelemetry messaging attributes (`messaging.system`, `messaging.destination`, `messaging.operation`, `messaging.rabbitmq.routing_key`, `messaging.message_id`, `messaging.rabbitmq.correlation_id`, etc.), ensuring RabbitMQ activity appears in Jaeger traces.