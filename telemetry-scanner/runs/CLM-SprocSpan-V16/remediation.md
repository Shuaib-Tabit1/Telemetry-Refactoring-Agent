```diff
--- a/ScmCoreInstrumentationServiceCollectionExtensions.cs
+++ b/ScmCoreInstrumentationServiceCollectionExtensions.cs
@@
 
 using Microsoft.Extensions.Configuration;
 using Microsoft.Extensions.DependencyInjection;
 using Microsoft.Extensions.Hosting;
 
+using System.Data;
+using System.Data.Common;
 
 using OpenTelemetry.Exporter;
 using OpenTelemetry.Logs;
 using OpenTelemetry.Metrics;
 using OpenTelemetry.Trace;
@@				options.ConfigureRedisCacheInstrumentation();
 				options.AddScmCassandraPersistenceInstrumentation();
+
+				// Add SQL Client tracing with enrichment for stored procedures.
+				options.AddSqlClientInstrumentation(sqlOptions =>
+				{
+					// Ensure the full text of stored-procedure calls is captured.
+					sqlOptions.SetDbStatementForStoredProcedure = true;
+
+					// Enrich spans with db.operation (stored-procedure name) and db.name.
+					sqlOptions.Enrich = (activity, eventName, rawObject) =>
+					{
+						if (eventName == "OnStartActivity" && rawObject is DbCommand command &&
+						    command.CommandType == CommandType.StoredProcedure)
+						{
+							// db.operation holds the stored-procedure name.
+							activity.SetTag("db.operation", command.CommandText);
+
+							// db.name holds the current database name.
+							var databaseName = command.Connection?.Database;
+							if (!string.IsNullOrEmpty(databaseName))
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
@@				options.AddRedisCacheMetrics();
 				options.SetExemplarFilter(ExemplarFilterType.TraceBased);
 				options.AddSqlClientInstrumentation();
 
 				configureMeter?.Invoke(options);
```

### Explanation
1. Added `using System.Data` and `using System.Data.Common` for access to `DbCommand` and `CommandType`.
2. Registered SQL-client tracing (`AddSqlClientInstrumentation`) in the tracer pipeline.
3. Enabled `SetDbStatementForStoredProcedure` so `db.statement` is populated for stored procedures.
4. Implemented an `Enrich` callback that, on `OnStartActivity`, adds:
   • `db.operation` – the stored-procedure name (`SqlCommand.CommandText`).  
   • `db.name` – the current database name from `SqlConnection.Database`.
These attributes now appear on all spans generated for stored-procedure executions, fulfilling the instrumentation gap.