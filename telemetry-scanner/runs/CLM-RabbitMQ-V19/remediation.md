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
 
 /// <summary>
@@
 				options.AddScmCassandraPersistenceInstrumentation();
+
+				// RabbitMQ instrumentation with custom enrichment for additional semantic attributes.
+				options.AddRabbitMQInstrumentation(rabbitOptions =>
+				{
+					rabbitOptions.Enrich = (activity, eventName, rawObject) =>
+					{
+						if (activity == null || rawObject == null)
+						{
+							return;
+						}
+
+						try
+						{
+							IBasicProperties? basicProperties = null;
+
+							// Direct cast when the raw object is IBasicProperties (e.g., EasyNetQ publish).
+							if (rawObject is IBasicProperties directProps)
+							{
+								basicProperties = directProps;
+							}
+							else
+							{
+								// Fallback for RabbitMQ.Client event args (publish / deliver).
+								var basicPropsProperty = rawObject.GetType().GetProperty("BasicProperties");
+								if (basicPropsProperty != null)
+								{
+									basicProperties = basicPropsProperty.GetValue(rawObject) as IBasicProperties;
+								}
+							}
+
+							if (basicProperties != null)
+							{
+								// messaging.message_id
+								if (!string.IsNullOrEmpty(basicProperties.MessageId))
+								{
+									activity.SetTag("messaging.message_id", basicProperties.MessageId);
+								}
+
+								// app.correlation_token (custom header)
+								if (basicProperties.Headers != null &&
+									basicProperties.Headers.TryGetValue("CorrelationToken", out var corrObj) &&
+									corrObj is byte[] corrBytes)
+								{
+									var correlationToken = Encoding.UTF8.GetString(corrBytes);
+									if (!string.IsNullOrEmpty(correlationToken))
+									{
+										activity.SetTag("app.correlation_token", correlationToken);
+									}
+								}
+
+								// Ensure messaging.operation is present (publish / consume).
+								if (activity.GetTagItem("messaging.operation") == null)
+								{
+									var op =
+										eventName?.StartsWith("basic.publish", StringComparison.OrdinalIgnoreCase) == true
+											? "publish"
+											: "consume";
+									activity.SetTag("messaging.operation", op);
+								}
+							}
+						}
+						catch
+						{
+							// Swallow enrichment exceptions to avoid impacting application flow.
+						}
+					};
+				});
+
 				configureTracer?.Invoke(options);
 
 				if (telemetryConsoleTargets != null)
 				{
 					options.AddConsoleExporter(o => o.Targets = telemetryConsoleTargets.Value);
@@
 				options.AddRedisCacheMetrics();
+				// Add RabbitMQ metrics instrumentation.
+				options.AddRabbitMQInstrumentation();
 				options.SetExemplarFilter(ExemplarFilterType.TraceBased);
 				options.AddSqlClientInstrumentation();
 
 				configureMeter?.Invoke(options);
```

