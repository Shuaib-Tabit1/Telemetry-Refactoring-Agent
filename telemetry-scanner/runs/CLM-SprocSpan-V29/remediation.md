```diff
--- a/ScmCoreInstrumentationServiceCollectionExtensions.cs
+++ b/ScmCoreInstrumentationServiceCollectionExtensions.cs
@@
 using Microsoft.Extensions.DependencyInjection;
 using Microsoft.Extensions.Hosting;
 
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
 				options.ConfigureRedisCacheInstrumentation();
 				options.AddScmCassandraPersistenceInstrumentation();
+
+				// Capture SQL client spans and enrich them with stored-procedure information.
+				options.AddSqlClientInstrumentation(sqlOptions =>
+				{
+					// Ensure db.statement is populated for stored procedure calls (e.g., "EXEC MyProc").
+					sqlOptions.SetDbStatementForStoredProcedure = true;
+
+					// Add db.operation tag containing the stored procedure name.
+					sqlOptions.Enrich = (activity, eventName, rawObject) =>
+					{
+						if (rawObject is SqlCommand cmd && cmd.CommandType == CommandType.StoredProcedure)
+						{
+							activity?.SetTag("db.operation", cmd.CommandText);
+						}
+					};
+				});
+
 				configureTracer?.Invoke(options);
 
 				if (telemetryConsoleTargets != null)
 				{
 					options.AddConsoleExporter(o => o.Targets = telemetryConsoleTargets.Value);
```

