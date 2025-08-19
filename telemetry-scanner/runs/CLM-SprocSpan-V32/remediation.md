```diff
--- a/ScmCoreInstrumentationServiceCollectionExtensions.cs
+++ b/ScmCoreInstrumentationServiceCollectionExtensions.cs
@@
 using Microsoft.Extensions.Configuration;
 using Microsoft.Extensions.DependencyInjection;
 using Microsoft.Extensions.Hosting;
 
+using System.Data;
+using System.Data.Common;
+
 using OpenTelemetry.Exporter;
 using OpenTelemetry.Logs;
 using OpenTelemetry.Metrics;
 using OpenTelemetry.Trace;
 
@@
 				options.ConfigureRedisCacheInstrumentation();
 				options.AddScmCassandraPersistenceInstrumentation();
+
+				// -------------------------------------------------------------
+				// Surface database name and stored-procedure name
+				// -------------------------------------------------------------
+				options.AddSqlClientInstrumentation(sqlOptions =>
+				{
+					// Ensure connection-level attributes such as db.name are captured.
+					sqlOptions.EnableConnectionLevelAttributes = true;
+
+					// Add custom attributes required by CLM and eSign traces.
+					sqlOptions.Enrich = (activity, eventName, rawObject) =>
+					{
+						// We only care about command execution.
+						if (eventName == "OnBeforeExecuteCommand" && rawObject is DbCommand command)
+						{
+							// db.operation -> stored procedure name (if applicable)
+							if (command.CommandType == CommandType.StoredProcedure && !string.IsNullOrWhiteSpace(command.CommandText))
+							{
+								activity.SetTag("db.operation", command.CommandText);
+							}
+
+							// db.name -> current database name
+							var databaseName = command.Connection?.Database;
+							if (!string.IsNullOrWhiteSpace(databaseName))
+							{
+								activity.SetTag("db.name", databaseName);
+							}
+						}
+					};
+				});
+
 				configureTracer?.Invoke(options);
 
 				if (telemetryConsoleTargets != null)
 				{
 					options.AddConsoleExporter(o => o.Targets = telemetryConsoleTargets.Value);
```

