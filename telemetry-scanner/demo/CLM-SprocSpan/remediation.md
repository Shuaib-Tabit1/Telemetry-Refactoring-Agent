```diff
--- a/ScmCoreInstrumentationServiceCollectionExtensions.cs
+++ b/ScmCoreInstrumentationServiceCollectionExtensions.cs
@@
 				options.ConfigureRedisCacheInstrumentation();
 				options.AddScmCassandraPersistenceInstrumentation();
+				// Capture SQL client spans so that db.name and db.operation
+				// (stored-procedure name) are recorded as standard OpenTelemetry
+				// attributes and surface in Jaeger traces.
+				options.AddSqlClientInstrumentation();
 				configureTracer?.Invoke(options);
 
 				if (telemetryConsoleTargets != null)
 				{
 					options.AddConsoleExporter(o => o.Targets = telemetryConsoleTargets.Value);
```

### Explanation
The tracer pipeline was missing SQL client instrumentation, so spans for database calls did not include standard attributes such as `db.name` and `db.operation`.  
By invoking `options.AddSqlClientInstrumentation()` on the `TracerProviderBuilder`, every SQL client span now automatically records these attributes according to OpenTelemetry semantic conventions, enabling them to appear in Jaeger traces.