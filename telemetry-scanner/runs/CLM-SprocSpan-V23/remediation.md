```diff
--- a/ScmCoreInstrumentationServiceCollectionExtensions.cs
+++ b/ScmCoreInstrumentationServiceCollectionExtensions.cs
@@
 using OpenTelemetry.Exporter;
 using OpenTelemetry.Logs;
 using OpenTelemetry.Metrics;
 using OpenTelemetry.Trace;
+using OpenTelemetry.Instrumentation.SqlClient;
 
 namespace ADEXS.ServiceFramework.OpenTelemetry.Extensions;
 
 /// <summary>
 /// Extensions for <see cref="IServiceCollection"/>.
@@
 				options.AddHttpClientInstrumentation();
 				options.ConfigureRedisCacheInstrumentation();
 				options.AddScmCassandraPersistenceInstrumentation();
+
+				// Capture SQL spans (including stored procedure calls) and enrich them with the
+				// stored procedure name so that Jaeger can display them as "(dbname sprocname)".
+				options.AddSqlClientInstrumentation(sqlOptions =>
+				{
+					sqlOptions.Enrich = (activity, eventName, rawObject) =>
+					{
+						// The instrumentation invokes Enrich for several events. We are interested in
+						// command-related events where the rawObject is a SqlCommand instance.
+						if (rawObject is System.Data.SqlClient.SqlCommand legacyCommand &&
+							legacyCommand.CommandType == System.Data.CommandType.StoredProcedure &&
+							!string.IsNullOrWhiteSpace(legacyCommand.CommandText))
+						{
+							activity.SetTag("db.operation", legacyCommand.CommandText);
+						}
+#if NET6_0_OR_GREATER
+						// Support the Microsoft.Data.SqlClient package as well.
+						if (rawObject is Microsoft.Data.SqlClient.SqlCommand modernCommand &&
+							modernCommand.CommandType == System.Data.CommandType.StoredProcedure &&
+							!string.IsNullOrWhiteSpace(modernCommand.CommandText))
+						{
+							activity.SetTag("db.operation", modernCommand.CommandText);
+						}
+#endif
+					};
+				});
+
 				configureTracer?.Invoke(options);
 
 				if (telemetryConsoleTargets != null)
 				{
 					options.AddConsoleExporter(o => o.Targets = telemetryConsoleTargets.Value);
```

