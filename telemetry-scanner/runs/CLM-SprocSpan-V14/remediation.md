```diff
--- a/ScmCoreInstrumentationServiceCollectionExtensions.cs
+++ b/ScmCoreInstrumentationServiceCollectionExtensions.cs
@@
 using OpenTelemetry.Exporter;
 using OpenTelemetry.Logs;
 using OpenTelemetry.Metrics;
 using OpenTelemetry.Trace;
+using System.Data;
+using System.Data.Common;
 
 namespace ADEXS.ServiceFramework.OpenTelemetry.Extensions;
 
 /// <summary>
 /// Extensions for <see cref="IServiceCollection"/>.
@@
 				options.AddScmCassandraPersistenceInstrumentation();
 				options.AddRabbitMQInstrumentation();
+
+				// Add SQL-Client tracing with enrichment for stored-procedures.
+				options.AddSqlClientInstrumentation(sqlOptions =>
+				{
+					sqlOptions.Enrich = (activity, eventName, rawObject) =>
+					{
+						// We are only interested in command execution events.
+						if (rawObject is not DbCommand command)
+						{
+							return;
+						}
+
+						// Only add attributes for stored-procedure executions.
+						if (command.CommandType == CommandType.StoredProcedure)
+						{
+							// db.operation: name of the stored-procedure.
+							activity.SetTag("db.operation", command.CommandText);
+
+							// db.name: database name from the active connection, if available.
+							var databaseName = command.Connection?.Database;
+							if (!string.IsNullOrWhiteSpace(databaseName))
+							{
+								activity.SetTag("db.name", databaseName);
+							}
+						}
+					};
+				});
 
 				configureTracer?.Invoke(options);
 
 				if (telemetryConsoleTargets != null)
 				{
```

