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
 				options.AddSource("ADEXS.*");
 
 				// Enable azure tracing.
 				options.AddSource("Azure.*");
 
 				// Enable telemetry in end to end tests.
 				options.AddSource("Xunit.DependencyInjection");
 
 				options.AddHttpClientInstrumentation();
 				options.ConfigureRedisCacheInstrumentation();
 				options.AddScmCassandraPersistenceInstrumentation();
+
+				// Add SQL client instrumentation and enrich spans with database details.
+				options.AddSqlClientInstrumentation(sqlOptions =>
+				{
+					// Also capture full SQL text for text commands.
+					sqlOptions.SetDbStatementForText = true;
+
+					// Enrich the activity with db.name and db.operation (sproc name) when available.
+					sqlOptions.Enrich = (activity, eventName, obj) =>
+					{
+						if (eventName != "OnStart" || obj is not DbCommand command)
+						{
+							return;
+						}
+
+						// db.name -> the database name from the connection.
+						var database = command.Connection?.Database;
+						if (!string.IsNullOrEmpty(database))
+						{
+							activity.SetTag("db.name", database);
+						}
+
+						// db.operation -> stored procedure name when applicable.
+						if (command.CommandType == CommandType.StoredProcedure &&
+						    !string.IsNullOrWhiteSpace(command.CommandText))
+						{
+							activity.SetTag("db.operation", command.CommandText);
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
 				options.SetExemplarFilter(ExemplarFilterType.TraceBased);
 				options.AddSqlClientInstrumentation();
 
 				configureMeter?.Invoke(options);
```

### Explanation
1. Added `using System.Data;` and `using System.Data.Common;` to access `CommandType` and `DbCommand`.
2. Registered SQL client tracing instrumentation via `options.AddSqlClientInstrumentation`.
3. In the instrumentation options:
   • Enabled `SetDbStatementForText` to capture full SQL statements.  
   • Implemented `Enrich` callback to populate:
     • `db.name` from `command.Connection.Database`.  
     • `db.operation` with the stored-procedure name when `CommandType` is `StoredProcedure`.
4. The enrichment executes only on `OnStart` to ensure attributes are set at span creation time.