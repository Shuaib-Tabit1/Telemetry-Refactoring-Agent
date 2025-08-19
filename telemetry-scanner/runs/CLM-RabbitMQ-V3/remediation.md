```diff
--- a/ScmCoreInstrumentationServiceCollectionExtensions.cs
+++ b/ScmCoreInstrumentationServiceCollectionExtensions.cs
@@
 using OpenTelemetry.Trace;
+using OpenTelemetry.Instrumentation.RabbitMQ; // Added
 
 namespace ADEXS.ServiceFramework.OpenTelemetry.Extensions;
@@
 				options.AddScmCassandraPersistenceInstrumentation();
+
+				// RabbitMQ tracing
+				// This automatically creates spans around BasicPublish/BasicConsume
+				// with the proper OpenTelemetry semantic conventions, such as:
+				//   messaging.system             = "rabbitmq"
+				//   messaging.destination        = <queue or exchange>
+				//   messaging.destination_kind   = "queue"
+				//   messaging.rabbitmq.routing_key
+				//   messaging.message_id
+				//   messaging.operation          = "publish" | "receive"
+				options.AddRabbitMQInstrumentation();
+
 				configureTracer?.Invoke(options);
 
 				if (telemetryConsoleTargets != null)
 				{
 					options.AddConsoleExporter(o => o.Targets = telemetryConsoleTargets.Value);
```

### Explanation
1. Added `using OpenTelemetry.Instrumentation.RabbitMQ;` to bring the RabbitMQ instrumentation extension method into scope.
2. Registered `AddRabbitMQInstrumentation()` inside the tracer builder.  
   • This enables automatic creation of spans for all `BasicPublish`, `BasicDeliver`, and related operations.  
   • The instrumentation sets the required semantic-convention attributes (`messaging.system`, `messaging.destination`, `messaging.destination_kind`, `messaging.rabbitmq.routing_key`, `messaging.message_id`, and `messaging.operation`) without additional manual code.