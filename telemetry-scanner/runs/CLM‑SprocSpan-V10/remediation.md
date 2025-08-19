```diff
--- a/ScmCoreInstrumentationServiceCollectionExtensions.cs
+++ b/ScmCoreInstrumentationServiceCollectionExtensions.cs
@@
 
 using OpenTelemetry.Exporter;
 using OpenTelemetry.Logs;
 using OpenTelemetry.Metrics;
 using OpenTelemetry.Trace;
+using System.Diagnostics;
+using System.Data.Common;
+using System.Data;
 
 namespace ADEXS.ServiceFramework.OpenTelemetry.Extensions;
 
 /// <summary>
 /// Extensions for <see cref="IServiceCollection"/>.
@@
 				options.AddHttpClientInstrumentation();
 				options.ConfigureRedisCacheInstrumentation();
 				options.AddScmCassandraPersistenceInstrumentation();
 				options.AddRabbitMQInstrumentation();
+				// Capture additional database attributes for stored-procedure executions.
+				options.AddSqlClientInstrumentation(sqlOptions =>
+				{
+					// Enrich is invoked for every significant ADO.NET event.  We are only interested
+					// in those where a DbCommand is available, so we can safely ignore the rest.
+					sqlOptions.Enrich = (activity, eventName, rawObject) =>
+					{
+						if (rawObject is not DbCommand cmd || activity == null)
+						{
+							return;
+						}
+
+						// Add the database name when available.
+						if (!string.IsNullOrEmpty(cmd.Connection?.Database))
+						{
+							activity.SetTag("db.name", cmd.Connection!.Database);
+						}
+
+						// When a stored procedure is executed, capture its name as a tag.
+						if (cmd.CommandType == CommandType.StoredProcedure
+							&& !string.IsNullOrEmpty(cmd.CommandText))
+						{
+							activity.SetTag("db.sql.procedure", cmd.CommandText);
+						}
+					};
+				});
 
 				configureTracer?.Invoke(options);
 
 				if (telemetryConsoleTargets != null)
 				{
@@
 				options.AddRedisCacheMetrics();
 				options.SetExemplarFilter(ExemplarFilterType.TraceBased);
 				options.AddSqlClientInstrumentation();
 
 				configureMeter?.Invoke(options);
 
 				if (telemetryConsoleTargets != null)
 				{
 					options.AddConsoleExporter(o => o.Targets = telemetryConsoleTargets.Value);
 				}
 			});
```

