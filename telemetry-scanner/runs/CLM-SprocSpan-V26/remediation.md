```diff
--- a/ScmCoreInstrumentationServiceCollectionExtensions.cs
+++ b/ScmCoreInstrumentationServiceCollectionExtensions.cs
@@
 using DocuSign.Msf.OpenTelemetry.DotNet.Runtime;
 
 using Microsoft.Extensions.Configuration;
 using Microsoft.Extensions.DependencyInjection;
 using Microsoft.Extensions.Hosting;
+using System.Data;
+using System.Data.Common;
 
 using OpenTelemetry.Exporter;
 using OpenTelemetry.Logs;
 using OpenTelemetry.Metrics;
 using OpenTelemetry.Trace;
@@
 				// Enable telemetry in end to end tests.
 				options.AddSource("Xunit.DependencyInjection");
 
 				options.AddHttpClientInstrumentation();
 				options.ConfigureRedisCacheInstrumentation();
+				// Capture SQL spans with enriched attributes.
+				options.AddSqlClientInstrumentation(sqlOptions =>
+				{
+					// Enrich allows us to add/override attributes on Activity.
+					sqlOptions.Enrich = (activity, eventName, rawObject) =>
+					{
+						// We are only interested in the stop event to avoid setting the same tag multiple times.
+						if (eventName != "OnStopActivity" || rawObject is not DbCommand command)
+						{
+							return;
+						}
+
+						// Capture the database name (if available).
+						if (!string.IsNullOrWhiteSpace(command.Connection?.Database))
+						{
+							activity.SetTag("db.name", command.Connection!.Database);
+						}
+
+						// For stored procedures, record the operation name.
+						if (command.CommandType == CommandType.StoredProcedure &&
+						    !string.IsNullOrWhiteSpace(command.CommandText))
+						{
+							activity.SetTag("db.operation", command.CommandText);
+						}
+					};
+				});
 				options.AddScmCassandraPersistenceInstrumentation();
 				configureTracer?.Invoke(options);
 
 				if (telemetryConsoleTargets != null)
 				{
@@
 				options.AddProcessInstrumentation();
 				options.AddDocuSignDotNetRuntimeInstrumentation();
 				options.AddCassandraInstrumentation();
 				options.AddScmCassandraPersistenceInstrumentation();
 				options.AddRedisCacheMetrics();
-				options.SetExemplarFilter(ExemplarFilterType.TraceBased);
-				options.AddSqlClientInstrumentation();
+				options.SetExemplarFilter(ExemplarFilterType.TraceBased);
+				// SQL metrics are still required on the meter side, so keep the call here.
+				options.AddSqlClientInstrumentation();
 
 				configureMeter?.Invoke(options);
 
 				if (telemetryConsoleTargets != null)
 				{
```

### Explanation
1. Added `using System.Data;` and `using System.Data.Common;` to work with `CommandType` and `DbCommand`.
2. Integrated SQL-client tracing via `options.AddSqlClientInstrumentation` inside the tracer configuration block (it was previously missing).
3. Implemented an `Enrich` callback that:
   • Sets `db.name` from `DbCommand.Connection.Database`.  
   • Sets `db.operation` when the command is a stored procedure (`CommandType.StoredProcedure`), using the procedure name from `CommandText`.
4. Kept the existing meter-side `AddSqlClientInstrumentation` for metrics.
These changes ensure database spans carry both the database name and stored procedure name, following OpenTelemetry semantic conventions.