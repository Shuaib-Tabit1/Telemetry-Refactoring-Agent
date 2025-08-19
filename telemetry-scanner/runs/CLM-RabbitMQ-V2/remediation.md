```diff
--- a/ScmCoreInstrumentationServiceCollectionExtensions.cs
+++ b/ScmCoreInstrumentationServiceCollectionExtensions.cs
@@
 using OpenTelemetry.Exporter;
 using OpenTelemetry.Logs;
 using OpenTelemetry.Metrics;
 using OpenTelemetry.Trace;
+using OpenTelemetry.Instrumentation.RabbitMQ; // Added for RabbitMQ instrumentation
 
 namespace ADEXS.ServiceFramework.OpenTelemetry.Extensions;
@@
 				options.AddHttpClientInstrumentation();
 				options.ConfigureRedisCacheInstrumentation();
 				options.AddScmCassandraPersistenceInstrumentation();
+
+				// -----------------------------------------------------------------
+				// RabbitMQ CLIENT INSTRUMENTATION
+				// -----------------------------------------------------------------
+				// This enables automatic tracing for IModel.BasicPublish /
+				// IModel.BasicConsume operations following the OpenTelemetry
+				// semantic conventions:
+				//   - messaging.system           = "rabbitmq"
+				//   - messaging.destination_kind = "queue"
+				//   - messaging.destination      = <routing key / queue name>
+				//   - messaging.operation        = "publish" / "receive"
+				//
+				// Span Name example: "RabbitMQ Publish"
+				// -----------------------------------------------------------------
+				options.AddRabbitMQClientInstrumentation();
+
 				configureTracer?.Invoke(options);
 
 				if (telemetryConsoleTargets != null)
 				{
 					options.AddConsoleExporter(o => o.Targets = telemetryConsoleTargets.Value);
```

### Explanation
1. Added a `using` directive for `OpenTelemetry.Instrumentation.RabbitMQ`.
2. Registered the RabbitMQ client instrumentation inside the tracer configuration via `options.AddRabbitMQClientInstrumentation();`.  
   • This automatically creates spans around `IModel.BasicPublish` and `IModel.BasicConsume` with the required attributes:
     - `messaging.system = rabbitmq`  
     - `messaging.destination_kind = queue`  
     - `messaging.destination = <routingKey>`  
     - `messaging.operation = publish/receive`  
   • The span name conventionally becomes “RabbitMQ Publish”, satisfying the intent.