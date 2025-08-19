```diff
--- a/ScmCoreInstrumentationServiceCollectionExtensions.cs
+++ b/ScmCoreInstrumentationServiceCollectionExtensions.cs
@@
 using OpenTelemetry.Metrics;
 using OpenTelemetry.Trace;
+using OpenTelemetry.Instrumentation.MassTransit;
 
 namespace ADEXS.ServiceFramework.OpenTelemetry.Extensions;
@@
 				options.ConfigureRedisCacheInstrumentation();
 				options.AddScmCassandraPersistenceInstrumentation();
+
+				// Instrument MassTransit (RabbitMQ) publish/consume pipelines.
+				// This will automatically create spans with standard messaging attributes:
+				// - messaging.system = "rabbitmq"
+				// - messaging.destination = <queue / exchange>
+				// - messaging.operation = "publish" | "receive"
+				// - messaging.message_id = <BasicProperties.MessageId>
+				options.AddMassTransitInstrumentation();
+
 				configureTracer?.Invoke(options);
 
 				if (telemetryConsoleTargets != null)
 				{
 					options.AddConsoleExporter(o => o.Targets = telemetryConsoleTargets.Value);
 				}
 			},
```

### Explanation
1. Added `using OpenTelemetry.Instrumentation.MassTransit;` to bring the MassTransit instrumentation extension into scope.
2. Registered MassTransit instrumentation via `options.AddMassTransitInstrumentation();` inside the tracer configuration block.  
   • This captures RabbitMQ publish and consume operations, emitting spans with the required OpenTelemetry semantic-convention attributes (`messaging.system`, `messaging.destination`, `messaging.operation`, and `messaging.message_id`).