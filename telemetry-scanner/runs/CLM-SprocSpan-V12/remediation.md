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
 				options.AddHttpClientInstrumentation();
 				options.ConfigureRedisCacheInstrumentation();
 				options.AddScmCassandraPersistenceInstrumentation();
 				options.AddRabbitMQInstrumentation();
+
+				// Capture details about SQL stored-procedure executions so the proc and database
+				// names are surfaced as span attributes (db.operation / db.name).
+				options.AddSqlClientInstrumentation(sqlOptions =>
+				{
+					// Ensure that db.statement is populated for stored procedures as well.
+					sqlOptions.SetDbStatementForStoredProcedure = true;
+
+					// Enrich the activity with additional tags.
+					sqlOptions.Enrich = (activity, eventName, rawObject) =>
+					{
+						// We only care about the start of the activity where the DbCommand is available.
+						if (eventName == "OnStartActivity" && rawObject is DbCommand command)
+						{
+							string? operationName = null;
+
+							// Prefer the command text when it's a stored procedure invocation.
+							if (command.CommandType == CommandType.StoredProcedure)
+							{
+								operationName = command.CommandText;
+							}
+							else if (!string.IsNullOrWhiteSpace(command.CommandText))
+							{
+								// Heuristic: try to extract the sproc name from an EXEC statement.
+								var text = command.CommandText.Trim();
+								if (text.StartsWith("exec", StringComparison.OrdinalIgnoreCase))
+								{
+									// exec  dbo.MyProc @param = 1
+									var parts = text.Split(new[] { ' ', '\t', '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries);
+									if (parts.Length >= 2)
+									{
+										operationName = parts[1];
+									}
+								}
+							}
+
+							if (!string.IsNullOrEmpty(operationName))
+							{
+								activity.SetTag("db.operation", operationName);
+							}
+
+							var dbName = command.Connection?.Database;
+							if (!string.IsNullOrEmpty(dbName))
+							{
+								activity.SetTag("db.name", dbName);
+							}
+						}
+					};
+				});
 
 				configureTracer?.Invoke(options);
 
 				if (telemetryConsoleTargets != null)
 				{
@@
 				options.AddProcessInstrumentation();
 				options.AddDocuSignDotNetRuntimeInstrumentation();
 				options.AddCassandraInstrumentation();
 				options.AddScmCassandraPersistenceInstrumentation();
 				options.AddRedisCacheMetrics();
 				options.SetExemplarFilter(ExemplarFilterType.TraceBased);
 				options.AddSqlClientInstrumentation();
 
 				configureMeter?.Invoke(options);
 
 				if (telemetryConsoleTargets != null)
 				{
```

### Explanation
1. Added `using System.Data;` and `using System.Data.Common;` for access to `CommandType`, `DbCommand`, etc.
2. Within the tracer configuration, wired up `AddSqlClientInstrumentation` with custom options:
   • `SetDbStatementForStoredProcedure = true` so `db.statement` is populated.
   • Custom `Enrich` delegate inspects the `DbCommand` at `OnStartActivity` to:
     – Extract the stored-procedure name (`db.operation`) from either `CommandText` when `CommandType.StoredProcedure` or by parsing `EXEC` text.  
     – Capture the database name from `command.Connection.Database` into `db.name`.
3. Existing calls remain unchanged, and the new instrumentation ensures Jaeger traces include `db.operation` and `db.name` attributes for SQL stored-procedure calls.