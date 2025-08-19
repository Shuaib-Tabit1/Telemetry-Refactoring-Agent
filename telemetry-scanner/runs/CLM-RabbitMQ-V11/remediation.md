```diff
--- a/ScmCoreInstrumentationServiceCollectionExtensions.cs
+++ b/ScmCoreInstrumentationServiceCollectionExtensions.cs
@@
 
 using Microsoft.Extensions.Configuration;
 using Microsoft.Extensions.DependencyInjection;
 using Microsoft.Extensions.Hosting;
 
+using OpenTelemetry.Instrumentation.RabbitMQ;
 using OpenTelemetry.Exporter;
 using OpenTelemetry.Logs;
 using OpenTelemetry.Metrics;
 using OpenTelemetry.Trace;
 
@@
 				options.AddSource("Xunit.DependencyInjection");
 
 				options.AddHttpClientInstrumentation();
 				options.ConfigureRedisCacheInstrumentation();
 				options.AddScmCassandraPersistenceInstrumentation();
+				// Enable automatic RabbitMQ producer/consumer spans with
+				// semantic-convention compliant messaging.* attributes.
+				options.AddRabbitMQInstrumentation();
 				configureTracer?.Invoke(options);
 
 				if (telemetryConsoleTargets != null)
 				{
 					options.AddConsoleExporter(o => o.Targets = telemetryConsoleTargets.Value);
@@
 				options.AddCassandraInstrumentation();
 				options.AddScmCassandraPersistenceInstrumentation();
 				options.AddRedisCacheMetrics();
 				options.SetExemplarFilter(ExemplarFilterType.TraceBased);
 				options.AddSqlClientInstrumentation();
+				// Add RabbitMQ metrics (e.g., delivery/ack counters) following the
+				// OpenTelemetry messaging metric conventions.
+				options.AddRabbitMQInstrumentation();
 
 				configureMeter?.Invoke(options);
 
 				if (telemetryConsoleTargets != null)
 				{
```

### Explanation
1. Added `using OpenTelemetry.Instrumentation.RabbitMQ;` to access the extension methods.
2. In the TracerProvider configuration, invoked `AddRabbitMQInstrumentation()` so publish/consume spans are automatically produced with the correct `messaging.*` attributes.
3. In the MeterProvider configuration, invoked the same method to emit RabbitMQ-related metrics.
These minimal changes integrate RabbitMQ instrumentation into the existing OpenTelemetry pipeline without altering existing conventions.