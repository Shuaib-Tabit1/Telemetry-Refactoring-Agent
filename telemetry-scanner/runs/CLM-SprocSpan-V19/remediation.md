```diff
--- a/ScmCoreInstrumentationServiceCollectionExtensions.cs
+++ b/ScmCoreInstrumentationServiceCollectionExtensions.cs
@@
 using DocuSign.Msf.OpenTelemetry.DotNet.Runtime;
 
+using System.Data;
+using System.Data.Common;
+
 using Microsoft.Extensions.Configuration;
 using Microsoft.Extensions.DependencyInjection;
 using Microsoft.Extensions.Hosting;
 
 using OpenTelemetry.Exporter;
@@
 				options.ConfigureRedisCacheInstrumentation();
 				options.AddScmCassandraPersistenceInstrumentation();
+
+				// Capture SQL client spans and enrich them with the executed stored-procedure name.
+				options.AddSqlClientInstrumentation(sqlOptions =>
+				{
+					// Ensure the db.operation attribute is present for stored procedures.
+					sqlOptions.Enrich = (activity, eventName, rawObject) =>
+					{
+						if (eventName.Equals("OnBeforeCommandExecute", StringComparison.Ordinal) &&
+						    rawObject is DbCommand command &&
+						    command.CommandType == CommandType.StoredProcedure)
+						{
+							// Semantic convention: https://opentelemetry.io/docs/specs/semconv/database/
+							activity.SetTag("db.operation", command.CommandText);
+						}
+					};
+				});
+
 				configureTracer?.Invoke(options);
 
 				if (telemetryConsoleTargets != null)
 				{
 					options.AddConsoleExporter(o => o.Targets = telemetryConsoleTargets.Value);
```

