```diff
--- a/ScmCoreInstrumentationServiceCollectionExtensions.cs
+++ b/ScmCoreInstrumentationServiceCollectionExtensions.cs
@@
 				options.AddHttpClientInstrumentation();
 				options.ConfigureRedisCacheInstrumentation();
 				options.AddScmCassandraPersistenceInstrumentation();
+
+				// Add SQL Client tracing with enrichment so stored-procedure
+				// executions expose their name using the OpenTelemetry
+				// semantic-convention attribute `db.operation`.
+				options.AddSqlClientInstrumentation(sqlOptions =>
+				{
+					sqlOptions.Enrich = (activity, eventName, rawObject) =>
+					{
+						// We are only interested in command execution events.
+						if (rawObject is System.Data.SqlClient.SqlCommand command &&
+						    command.CommandType == System.Data.CommandType.StoredProcedure)
+						{
+							// Populate the stored procedure name so Jaeger can
+							// display it alongside the database name.
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
 				options.AddCassandraInstrumentation();
 				options.AddScmCassandraPersistenceInstrumentation();
 				options.AddRedisCacheMetrics();
 				options.SetExemplarFilter(ExemplarFilterType.TraceBased);
-				options.AddSqlClientInstrumentation();
+				// Keep the existing SQL Client metrics instrumentation.
+				options.AddSqlClientInstrumentation();
 
 				configureMeter?.Invoke(options);
 
 				if (telemetryConsoleTargets != null)
 				{
```

### Explanation
1. Added SQL-Client tracing enrichment inside the `configureTracer` lambda:
   • Uses `AddSqlClientInstrumentation` with an `Enrich` callback.  
   • When the callback receives a `SqlCommand` whose `CommandType` is `StoredProcedure`, it sets the span attribute `db.operation` to the stored procedure’s name (`SqlCommand.CommandText`).  
   • This follows the OpenTelemetry semantic convention for database operations, enabling Jaeger to show the procedure name.

2. Left the pre-existing metrics instrumentation (`options.AddSqlClientInstrumentation()`) unchanged in the meter section so metrics behaviour is not affected.