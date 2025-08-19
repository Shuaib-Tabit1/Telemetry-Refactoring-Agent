```diff
--- a/ScmCoreInstrumentationServiceCollectionExtensions.cs
+++ b/ScmCoreInstrumentationServiceCollectionExtensions.cs
@@
 
 using OpenTelemetry.Exporter;
 using OpenTelemetry.Logs;
 using OpenTelemetry.Metrics;
 using OpenTelemetry.Trace;
+using Microsoft.Data.SqlClient;
+using System.Data;
 
 namespace ADEXS.ServiceFramework.OpenTelemetry.Extensions;
 
 /// <summary>
 /// Extensions for <see cref="IServiceCollection"/>.
@@
 				options.AddHttpClientInstrumentation();
 				options.ConfigureRedisCacheInstrumentation();
 				options.AddScmCassandraPersistenceInstrumentation();
 				options.AddRabbitMQInstrumentation();
+
+				// SQL client tracing with custom enrichment so that stored procedures and database name
+				// are visible as attributes on the span (e.g. shown in Jaeger as '(dbname sprocname)').
+				options.AddSqlClientInstrumentation(sqlOptions =>
+				{
+					sqlOptions.Enrich = (activity, eventName, rawObject) =>
+					{
+						// We only care about the beginning of a command execution.
+						if (eventName != "OnStartActivity" || rawObject is not SqlCommand command)
+						{
+							return;
+						}
+
+						// Capture the stored-procedure name if this is a stored-procedure execution.
+						if (command.CommandType == CommandType.StoredProcedure)
+						{
+							activity?.SetTag("db.sql.procedure", command.CommandText);
+						}
+
+						// Always capture the database name, if available.
+						if (command.Connection != null)
+						{
+							activity?.SetTag("db.name", command.Connection.Database);
+						}
+					};
+				});
 
 				configureTracer?.Invoke(options);
 
 				if (telemetryConsoleTargets != null)
 				{
```

