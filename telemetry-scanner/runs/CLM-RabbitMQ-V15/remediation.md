```diff
--- a/ScmCoreInstrumentationServiceCollectionExtensions.cs
+++ b/ScmCoreInstrumentationServiceCollectionExtensions.cs
@@
 using OpenTelemetry.Metrics;
 using OpenTelemetry.Trace;
+using OpenTelemetry.Instrumentation.RabbitMQ.Client;
+
+using RabbitMQ.Client;
+using RabbitMQ.Client.Events;
+using System.Text;
 
 namespace ADEXS.ServiceFramework.OpenTelemetry.Extensions;
@@
 				options.AddHttpClientInstrumentation();
 				options.ConfigureRedisCacheInstrumentation();
 				options.AddScmCassandraPersistenceInstrumentation();
+
+				// RabbitMQ client instrumentation
+				options.AddRabbitMQClientInstrumentation(
+					o =>
+					{
+						// Enrich spans with CorrelationToken header and rename publish spans.
+						o.Enrich = (activity, eventName, obj) =>
+						{
+							if (activity == null)
+							{
+								return;
+							}
+
+							// Rename publish spans to 'rabbitmq.publish' as per semantic convention.
+							if (eventName == RabbitMQClientInstrumentationEventNames.BasicPublish)
+							{
+								activity.DisplayName = "rabbitmq.publish";
+							}
+
+							// Attempt to extract CorrelationToken header for both publish & consume paths.
+							IBasicProperties? basicProperties = obj switch
+							{
+								IBasicProperties props => props,
+								BasicDeliverEventArgs deliverEvent => deliverEvent.BasicProperties,
+								_ => null
+							};
+
+							if (basicProperties?.Headers != null &&
+							    basicProperties.Headers.TryGetValue("CorrelationToken", out var headerValue) &&
+							    headerValue is not null)
+							{
+								string correlationId = headerValue switch
+								{
+									byte[] bytes => Encoding.UTF8.GetString(bytes),
+									_ => headerValue.ToString() ?? string.Empty
+								};
+
+								if (!string.IsNullOrWhiteSpace(correlationId))
+								{
+									activity.SetTag("messaging.conversation_id", correlationId);
+								}
+							}
+						};
+					});
+
 				configureTracer?.Invoke(options);
 
 				if (telemetryConsoleTargets != null)
 				{
 					options.AddConsoleExporter(o => o.Targets = telemetryConsoleTargets.Value);
```

