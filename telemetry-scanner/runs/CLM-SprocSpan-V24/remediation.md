```diff
--- a/ScmCoreInstrumentationServiceCollectionExtensions.cs
+++ b/ScmCoreInstrumentationServiceCollectionExtensions.cs
@@
 using OpenTelemetry.Exporter;
 using OpenTelemetry.Logs;
 using OpenTelemetry.Metrics;
 using OpenTelemetry.Trace;
+using OpenTelemetry.Instrumentation.SqlClient;
@@
 				options.AddHttpClientInstrumentation();
 				options.ConfigureRedisCacheInstrumentation();
 				options.AddScmCassandraPersistenceInstrumentation();
+
+				// Capture SQL-client spans and include the stored-procedure name.
+				options.AddSqlClientInstrumentation(sqlOptions =>
+				{
+					// Enable db.statement for stored procedures so that the sproc
+					// name is visible in CLM and Jaeger traces alongside db.name.
+					sqlOptions.SetDbStatementForStoredProcedure = true;
+				});
+
 				configureTracer?.Invoke(options);
 
 				if (telemetryConsoleTargets != null)
 				{
 					options.AddConsoleExporter(o => o.Targets = telemetryConsoleTargets.Value);
@@
 				options.AddSqlClientInstrumentation();
 
+				// Ensure metrics and traces use the same SQL client options.
+				options.AddSqlClientInstrumentation(sqlOptions =>
+				{
+					sqlOptions.SetDbStatementForStoredProcedure = true;
+				});
+
 				configureMeter?.Invoke(options);
 
 				if (telemetryConsoleTargets != null)
 				{
 					options.AddConsoleExporter(o => o.Targets = telemetryConsoleTargets.Value);
 				}
 			});
```

### Explanation
1. Added `using OpenTelemetry.Instrumentation.SqlClient;` to access `SqlClientInstrumentationOptions`.
2. In the tracer configuration, registered `AddSqlClientInstrumentation` and set `SetDbStatementForStoredProcedure = true` so that spans include the stored-procedure name (`db.statement` and `db.operation`).
3. Added the same instrumentation call (with identical option) to the meter configuration for consistency.