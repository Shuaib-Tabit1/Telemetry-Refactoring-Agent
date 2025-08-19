```diff
--- a/ScmCoreInstrumentationServiceCollectionExtensions.cs
+++ b/ScmCoreInstrumentationServiceCollectionExtensions.cs
@@
 				options.AddHttpClientInstrumentation();
 				options.ConfigureRedisCacheInstrumentation();
 				options.AddScmCassandraPersistenceInstrumentation();
+
+				// Capture SQL client spans and enrich them with the stored-procedure name
+				// so that it is available under the OpenTelemetry-defined `db.operation`
+				// attribute. This enables CLM Jaeger traces to clearly surface the
+				// specific stored procedure that was executed.
+				options.AddSqlClientInstrumentation(sqlOptions =>
+				{
+					// Ensure the full command text is still captured when a stored
+					// procedure is executed.
+					sqlOptions.SetDbStatementForStoredProcedure = true;
+
+					// Enrich the activity with the stored procedure name.
+					sqlOptions.Enrich = (activity, eventName, rawObject) =>
+					{
+						if (rawObject is System.Data.Common.DbCommand command &&
+							command.CommandType == System.Data.CommandType.StoredProcedure)
+						{
+							// According to OpenTelemetry semantic conventions.
+							activity.SetTag("db.operation", command.CommandText);
+						}
+					};
+				});
 				configureTracer?.Invoke(options);
 
 				if (telemetryConsoleTargets != null)
 				{
 					options.AddConsoleExporter(o => o.Targets = telemetryConsoleTargets.Value);
 				}
 			},
```

### Explanation
1. Added `AddSqlClientInstrumentation` to the tracer configuration so SQL operations are traced.
2. Enabled `SetDbStatementForStoredProcedure` to keep the complete SQL statement when executing stored procedures.
3. Implemented `Enrich` callback that adds the stored-procedure name to each span using the OpenTelemetry semantic-convention attribute `db.operation` when the command type is `StoredProcedure`.