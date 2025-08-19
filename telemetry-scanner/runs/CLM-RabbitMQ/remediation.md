```diff
--- a/ScmCoreInstrumentationServiceCollectionExtensions.cs
+++ b/ScmCoreInstrumentationServiceCollectionExtensions.cs
@@
 
 using OpenTelemetry.Exporter;
 using OpenTelemetry.Logs;
 using OpenTelemetry.Metrics;
 using OpenTelemetry.Trace;
+using OpenTelemetry.Instrumentation.RabbitMQ;
 
 namespace ADEXS.ServiceFramework.OpenTelemetry.Extensions;
 
 /// <summary>
 /// Extensions for <see cref="IServiceCollection"/>.
@@
 				options.AddHttpClientInstrumentation();
 				options.ConfigureRedisCacheInstrumentation();
 				options.AddScmCassandraPersistenceInstrumentation();
+				// Enable distributed tracing for RabbitMQ publishers/consumers.
+				// This will automatically create spans such as
+				//   - name: "rabbitmq.publish"
+				//   - attributes: "messaging.system" = "rabbitmq",
+				//                 "messaging.destination" = queue / exchange name,
+				//                 "messaging.rabbitmq.routing_key" = routing key
+				// according to OpenTelemetry semantic conventions.
+				options.AddRabbitMQInstrumentation();
 				configureTracer?.Invoke(options);
 
 				if (telemetryConsoleTargets != null)
 				{
 					options.AddConsoleExporter(o => o.Targets = telemetryConsoleTargets.Value);
 				}
```

