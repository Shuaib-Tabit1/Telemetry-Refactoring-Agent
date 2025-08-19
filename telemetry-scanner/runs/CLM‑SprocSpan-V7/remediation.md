```diff
--- a/ScmCoreInstrumentationServiceCollectionExtensions.cs
+++ b/ScmCoreInstrumentationServiceCollectionExtensions.cs
@@
 using OpenTelemetry.Trace;
+using OpenTelemetry.Instrumentation.SqlClient;
@@ public static IServiceCollection AddScmCoreInstrumentation(
 			configureTracer: options =>
 			{
 				// CLM specific sources.
 				options.AddSource("Scm*");
 				options.AddSource("ADEXS.*");
 
 				// Enable azure tracing.
 				options.AddSource("Azure.*");
 
 				// Enable telemetry in end to end tests.
 				options.AddSource("Xunit.DependencyInjection");
 
 				options.AddHttpClientInstrumentation();
 				options.ConfigureRedisCacheInstrumentation();
 				options.AddScmCassandraPersistenceInstrumentation();
 				options.AddRabbitMQInstrumentation();
+				// Instrument SQL client to capture stored procedure names in db.statement
+				options.AddSqlClientInstrumentation(sqlOptions =>
+				{
+					// Capture full CommandText for text and stored-procedure calls
+					sqlOptions.SetDbStatementForText = true;
+					sqlOptions.SetDbStatementForStoredProcedure = true;
+				});
 
 				configureTracer?.Invoke(options);
 
 				if (telemetryConsoleTargets != null)
 				{
 					options.AddConsoleExporter(o => o.Targets = telemetryConsoleTargets.Value);
 				}
 			},
```

### Explanation

- Added a `using OpenTelemetry.Instrumentation.SqlClient;` directive so that the `AddSqlClientInstrumentation` extension is available.
- In the tracer configuration lambda, after existing RabbitMQ instrumentation, invoked `options.AddSqlClientInstrumentation(...)`.
- Configured the SQL client instrumentation to capture the `SqlCommand.CommandText` (including stored‐procedure names) into the `db.statement` semantic attribute by setting `SetDbStatementForText` and `SetDbStatementForStoredProcedure` to `true`. This ensures all database stored-procedure spans will include the procedure name.