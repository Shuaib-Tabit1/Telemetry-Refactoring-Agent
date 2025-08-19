```diff
--- a/ScmCoreInstrumentationServiceCollectionExtensions.cs
+++ b/ScmCoreInstrumentationServiceCollectionExtensions.cs
@@
 using OpenTelemetry.Trace;
+using System.Data;
+using System.Data.Common;
 
 namespace ADEXS.ServiceFramework.OpenTelemetry.Extensions;
 
 /// <summary>
 /// Extensions for <see cref="IServiceCollection"/>.
@@ 			options.AddSource("Scm*");
 				options.AddSource("ADEXS.*");
 
 				// Enable azure tracing.
 				options.AddSource("Azure.*");
 
 				// Enable telemetry in end to end tests.
 				options.AddSource("Xunit.DependencyInjection");
 
 				options.AddHttpClientInstrumentation();
 				options.ConfigureRedisCacheInstrumentation();
 				options.AddScmCassandraPersistenceInstrumentation();
+
+				// Capture ADO.NET spans and enrich them with stored-procedure details.
+				options.AddSqlClientInstrumentation(sqlOptions =>
+				{
+					// Attach additional attributes for stored-procedure executions.
+					sqlOptions.Enrich = (activity, eventName, rawObject) =>
+					{
+						// We only care about command events.
+						if (rawObject is DbCommand command &&
+						    command.CommandType == CommandType.StoredProcedure)
+						{
+							// db.operation → stored procedure name.
+							if (!string.IsNullOrWhiteSpace(command.CommandText))
+							{
+								activity.SetTag("db.operation", command.CommandText);
+							}
+
+							// db.name → database name.
+							var dbName = command.Connection?.Database;
+							if (!string.IsNullOrWhiteSpace(dbName))
+							{
+								activity.SetTag("db.name", dbName);
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
```

### Explanation
1. Added `using System.Data;` and `using System.Data.Common;` to access `CommandType` and `DbCommand`.
2. Registered `AddSqlClientInstrumentation` in the tracer pipeline to ensure ADO.NET spans are produced.
3. Implemented an `Enrich` callback:
   • Filters for `DbCommand` instances executing stored procedures (`CommandType.StoredProcedure`).  
   • Adds `db.operation` with the stored-procedure name (`CommandText`).  
   • Adds `db.name` with the target database (`DbConnection.Database`).  
4. No other code paths were affected; this integrates seamlessly with existing instrumentation while respecting OpenTelemetry semantic conventions.