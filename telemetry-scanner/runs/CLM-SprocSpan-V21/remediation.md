```diff
--- a/ScmCoreInstrumentationServiceCollectionExtensions.cs
+++ b/ScmCoreInstrumentationServiceCollectionExtensions.cs
@@
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
+				// Capture ADO.NET (SqlClient) spans and enrich them with the stored-procedure name
+				// using the OpenTelemetry semantic-convention attribute `db.operation`.
+				options.AddSqlClientInstrumentation(sqlOptions =>
+				{
+					sqlOptions.Enrich = (activity, eventName, rawObject) =>
+					{
+						// We only care about the start of a command execution.
+						if (eventName != "OnStart")
+						{
+							return;
+						}
+
+						if (rawObject is DbCommand command && command.CommandType == CommandType.StoredProcedure)
+						{
+							// Attach the executed stored-procedure name.
+							activity.SetTag("db.operation", command.CommandText);
+						}
+					};
+				});
+
 				options.ConfigureRedisCacheInstrumentation();
 				options.AddScmCassandraPersistenceInstrumentation();
 				configureTracer?.Invoke(options);
 
 				if (telemetryConsoleTargets != null)
```

### Explanation
1. Added `System.Data` and `System.Data.Common` namespaces for `CommandType` and `DbCommand`.
2. Registered `AddSqlClientInstrumentation` in the tracer configuration (spans) with a custom `Enrich` delegate.
3. When a `DbCommand` with `CommandType.StoredProcedure` starts, the delegate sets the semantic-convention attribute `db.operation` to the procedure name (`CommandText`), making it visible in Jaeger traces.