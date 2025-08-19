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
 
@@ 	public static IServiceCollection AddScmCoreInstrumentation(
 				options.AddSource("Azure.*");
 
 				// Enable telemetry in end to end tests.
 				options.AddSource("Xunit.DependencyInjection");
 
+				// Add SQL client instrumentation with custom enrichment for stored procedures.
+				options.AddSqlClientInstrumentation(sqlOptions =>
+				{
+					// Attach db.name and db.operation (stored procedure name) to the span.
+					sqlOptions.Enrich = (activity, eventName, rawObject) =>
+					{
+						if (rawObject is DbCommand command && command.CommandType == CommandType.StoredProcedure)
+						{
+							if (!string.IsNullOrWhiteSpace(command.CommandText))
+							{
+								activity.SetTag("db.operation", command.CommandText);
+							}
+
+							var databaseName = command.Connection?.Database;
+							if (!string.IsNullOrWhiteSpace(databaseName))
+							{
+								activity.SetTag("db.name", databaseName);
+							}
+						}
+					};
+				});
+
 				options.AddHttpClientInstrumentation();
 				options.ConfigureRedisCacheInstrumentation();
 				options.AddScmCassandraPersistenceInstrumentation();
 				configureTracer?.Invoke(options);
```

### Explanation
1. Added `using System.Data;` and `using System.Data.Common;` for access to `CommandType` and `DbCommand`.
2. Registered `AddSqlClientInstrumentation` in the tracer pipeline (it was previously only in the meter pipeline).
3. Implemented an `Enrich` callback to:
   • Detect `DbCommand` executions that are `CommandType.StoredProcedure`.  
   • Add `db.operation` (stored-procedure name) and `db.name` (database name) span attributes in compliance with OpenTelemetry semantic conventions.