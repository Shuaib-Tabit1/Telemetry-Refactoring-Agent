```diff
--- a/ScmCoreInstrumentationServiceCollectionExtensions.cs
+++ b/ScmCoreInstrumentationServiceCollectionExtensions.cs
@@
-using Microsoft.Extensions.Hosting;
+using Microsoft.Extensions.Hosting;
+using System.Data;
+using System.Data.Common;
+using System.Diagnostics;
+using OpenTelemetry.Instrumentation.SqlClient;
@@ public static class ScmCoreInstrumentationServiceCollectionExtensions
 			options.AddHttpClientInstrumentation();
 			options.ConfigureRedisCacheInstrumentation();
 			options.AddScmCassandraPersistenceInstrumentation();
 			options.AddRabbitMQInstrumentation();
+			
+			// Instrument SQL client to capture stored procedure names as "db.sproc"
+			options.AddSqlClientInstrumentation(sqlOptions =>
+			{
+				sqlOptions.Enrich = (activity, eventName, rawObject) =>
+				{
+					if (rawObject is DbCommand dbCommand
+					    && dbCommand.CommandType == CommandType.StoredProcedure)
+					{
+						activity.SetTag("db.sproc", dbCommand.CommandText);
+					}
+				};
+			});
 
 			configureTracer?.Invoke(options);
 
 			if (telemetryConsoleTargets != null)
```

### Explanation

- Added the necessary `using` directives (`System.Data`, `System.Data.Common`, `System.Diagnostics`, and `OpenTelemetry.Instrumentation.SqlClient`) to bring in `DbCommand`, `Activity`, and the SQL instrumentation extension.
- In the `configureTracer` section, inserted a call to `AddSqlClientInstrumentation` on the `TracerProviderBuilder`.
- Provided an `Enrich` callback that checks if the `rawObject` is a `DbCommand` representing a stored procedure call, and if so, sets the custom span attribute `"db.sproc"` to the command’s `CommandText`.