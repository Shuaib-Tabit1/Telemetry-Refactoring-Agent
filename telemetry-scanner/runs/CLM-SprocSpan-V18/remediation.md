```diff
--- a/ScmCoreInstrumentationServiceCollectionExtensions.cs
+++ b/ScmCoreInstrumentationServiceCollectionExtensions.cs
@@
 using Microsoft.Extensions.Hosting;
 
 using OpenTelemetry.Exporter;
 using OpenTelemetry.Logs;
 using OpenTelemetry.Metrics;
+using OpenTelemetry.Trace;
+
+using System.Data;
+using System.Data.Common;
+
 using OpenTelemetry.Trace;
 
 namespace ADEXS.ServiceFramework.OpenTelemetry.Extensions;
@@ 				options.AddSource("Xunit.DependencyInjection");
 
 				options.AddHttpClientInstrumentation();
 				options.ConfigureRedisCacheInstrumentation();
 				options.AddScmCassandraPersistenceInstrumentation();
+
+				// Add SQL Client tracing with enrichment for stored procedures and database name.
+				options.AddSqlClientInstrumentation(cfg =>
+				{
+					// Enrich each SQL span with db.operation and db.name when applicable.
+					cfg.Enrich = (activity, eventName, rawObject) =>
+					{
+						if (rawObject is DbCommand command)
+						{
+							// Attach stored-procedure name (if any) to db.operation.
+							if (command.CommandType == CommandType.StoredProcedure)
+							{
+								activity?.SetTag("db.operation", command.CommandText);
+							}
+
+							// Always record the target database name.
+							if (command.Connection is { Database: { Length: > 0 } database })
+							{
+								activity?.SetTag("db.name", database);
+							}
+						}
+					};
+				});
+
 				configureTracer?.Invoke(options);
 
 				if (telemetryConsoleTargets != null)
 				{
 					options.AddConsoleExporter(o => o.Targets = telemetryConsoleTargets.Value);
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
1. Added `using System.Data` and `using System.Data.Common` to work with `CommandType` and `DbCommand`.
2. Registered SQL Client tracing (`AddSqlClientInstrumentation`) inside the tracer configuration.
3. Implemented `Enrich` callback:
   • When the executed command is a stored procedure, adds `db.operation` attribute with the procedure name (`CommandText`).  
   • Always adds `db.name` attribute using `SqlConnection.Database`.  
4. These attributes follow OpenTelemetry semantic conventions, making stored-procedure operations and database names visible in Jaeger traces.