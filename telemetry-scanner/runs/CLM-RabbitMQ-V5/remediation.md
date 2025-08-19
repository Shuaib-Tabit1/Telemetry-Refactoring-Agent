```diff
--- a/ScmCoreInstrumentationServiceCollectionExtensions.cs
+++ b/ScmCoreInstrumentationServiceCollectionExtensions.cs
@@
 				options.AddHttpClientInstrumentation();
 				options.ConfigureRedisCacheInstrumentation();
 				options.AddScmCassandraPersistenceInstrumentation();
+				// Capture RabbitMQ publish/consume operations.
+				// This adds spans with the following semantic-convention attributes:
+				//   • messaging.system            = "rabbitmq"
+				//   • messaging.destination       = <exchange | queue name>
+				//   • messaging.destination_kind  = "queue" | "exchange"
+				//   • messaging.operation         = "publish" | "consume"
+				//   • messaging.rabbitmq.routing_key = <routing key>
+				// The instrumentation automatically sets the span name (e.g., "RabbitMQ publish")
+				// in accordance with the OpenTelemetry messaging conventions.
+				options.AddRabbitMQInstrumentation();
 				configureTracer?.Invoke(options);
 
 				if (telemetryConsoleTargets != null)
 				{
 					options.AddConsoleExporter(o => o.Targets = telemetryConsoleTargets.Value);
```

### Explanation
1. Added `options.AddRabbitMQInstrumentation();` to the `TracerProviderBuilder` configuration.  
2. This automatically creates tracing spans for both publishing and consuming messages via RabbitMQ, enriching them with the proper OpenTelemetry messaging attributes (`messaging.system`, `messaging.destination`, `messaging.destination_kind`, `messaging.operation`, `messaging.rabbitmq.routing_key`, etc.), which will now appear in Jaeger.