```diff
--- a/ScmCoreInstrumentationServiceCollectionExtensions.cs
+++ b/ScmCoreInstrumentationServiceCollectionExtensions.cs
@@
 
 using Microsoft.Extensions.Configuration;
 using Microsoft.Extensions.DependencyInjection;
 using Microsoft.Extensions.Hosting;
 
+using System.Data;
+using System.Data.Common;
+using OpenTelemetry.Instrumentation.SqlClient;
 
 namespace ADEXS.ServiceFramework.OpenTelemetry.Extensions;
 
 /// <summary>
 /// Extensions for <see cref="IServiceCollection"/>.
@@
 				options.AddHttpClientInstrumentation();
 				options.ConfigureRedisCacheInstrumentation();
 				options.AddScmCassandraPersistenceInstrumentation();
+
+				// Add SQL client instrumentation and enrich spans with stored procedure details.
+				options.AddSqlClientInstrumentation(sqlOptions =>
+				{
+					// Make sure the command text is captured for stored procedures (db.statement).
+					sqlOptions.SetDbStatementForStoredProcedure = true;
+
+					// Enrich spans with additional semantic attributes.
+					sqlOptions.Enrich = (activity, eventName, rawObject) =>
+					{
+						// We only want to set attributes when the command activity starts.
+						if (eventName == "OnStartActivity" && rawObject is DbCommand command)
+						{
+							// Capture stored-procedure name.
+							if (command.CommandType == CommandType.StoredProcedure &&
+							    !string.IsNullOrWhiteSpace(command.CommandText))
+							{
+								activity.SetTag("db.operation", command.CommandText);
+							}
+
+							// Capture database name.
+							if (command.Connection is { } connection &&
+							    !string.IsNullOrWhiteSpace(connection.Database))
+							{
+								activity.SetTag("db.name", connection.Database);
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

### Explanation
1. Added `using` directives for:
   • `System.Data` and `System.Data.Common` to access `CommandType` and `DbCommand`.  
   • `OpenTelemetry.Instrumentation.SqlClient` to access `SqlClientInstrumentationOptions`.

2. Registered SQL client tracing via `options.AddSqlClientInstrumentation(...)` inside the tracer configuration block.

3. Enabled `SetDbStatementForStoredProcedure` so `db.statement` is populated automatically for stored procedures.

4. Implemented an `Enrich` delegate that:
   • Adds `db.operation` with the stored-procedure name when `CommandType` is `StoredProcedure`.  
   • Adds `db.name` with the database name from the active connection.

These changes ensure Jaeger traces include both the invoked stored-procedure name (`db.operation`) and the database name (`db.name`) following OpenTelemetry semantic conventions.