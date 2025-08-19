```diff
--- a/ScmCoreInstrumentationServiceCollectionExtensions.cs
+++ b/ScmCoreInstrumentationServiceCollectionExtensions.cs
@@
 using OpenTelemetry.Metrics;
 using OpenTelemetry.Trace;
+using OpenTelemetry.Instrumentation.RabbitMQ; // RabbitMQ client instrumentation
 
 namespace ADEXS.ServiceFramework.OpenTelemetry.Extensions;
@@
 				options.AddScmCassandraPersistenceInstrumentation();
+
+				// Enable RabbitMQ client tracing with standard messaging attributes.
+				// This instrumentation automatically populates:
+				//  • messaging.system = "rabbitmq"
+				//  • messaging.destination (queue / exchange name)
+				//  • messaging.destination_kind = "queue"
+				//  • messaging.rabbitmq.routing_key
+				//  • messaging.operation = "publish" / "receive"
+				options.AddRabbitMQClientInstrumentation();
+
 				configureTracer?.Invoke(options);
 
 				if (telemetryConsoleTargets != null)
 				{
 					options.AddConsoleExporter(o => o.Targets = telemetryConsoleTargets.Value);
```

### Explanation
1. Added `using OpenTelemetry.Instrumentation.RabbitMQ` to bring the extension‐method namespace into scope.
2. Registered RabbitMQ client tracing via `AddRabbitMQClientInstrumentation()` inside the tracer configuration block.  
   • The built-in instrumentation automatically attaches the standard OpenTelemetry messaging attributes (`messaging.system`, `messaging.destination`, `messaging.destination_kind`, `messaging.rabbitmq.routing_key`, `messaging.operation`) for both publish and consume spans, fulfilling the stated intent without custom attribute handling.