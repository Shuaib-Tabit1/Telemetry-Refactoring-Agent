```diff
--- a/ScmCoreInstrumentationServiceCollectionExtensions.cs
+++ b/ScmCoreInstrumentationServiceCollectionExtensions.cs
@@
 using OpenTelemetry.Exporter;
 using OpenTelemetry.Logs;
 using OpenTelemetry.Metrics;
 using OpenTelemetry.Trace;
+using OpenTelemetry.Instrumentation.RabbitMQ;
+using RabbitMQ.Client;
+using System.Text;
 
 namespace ADEXS.ServiceFramework.OpenTelemetry.Extensions;
@@
 				options.ConfigureRedisCacheInstrumentation();
 				options.AddScmCassandraPersistenceInstrumentation();
+
+				// Enable RabbitMQ tracing (publish/consume).
+				options.AddRabbitMQInstrumentation(rabbitOptions =>
+				{
+					// Attach correlation token from message headers, if present.
+					rabbitOptions.Enrich = (activity, eventName, rawObject) =>
+					{
+						if (rawObject is IBasicProperties props &&
+							props.Headers is not null &&
+							props.Headers.TryGetValue("CorrelationToken", out var headerValue))
+						{
+							switch (headerValue)
+							{
+								case byte[] bytes:
+									activity.SetTag("correlation_token", Encoding.UTF8.GetString(bytes));
+									break;
+								default:
+									activity.SetTag("correlation_token", headerValue?.ToString());
+									break;
+							}
+						}
+					};
+				});
+
 				configureTracer?.Invoke(options);
 
 				if (telemetryConsoleTargets != null)
 				{
 					options.AddConsoleExporter(o => o.Targets = telemetryConsoleTargets.Value);
 				}
```

