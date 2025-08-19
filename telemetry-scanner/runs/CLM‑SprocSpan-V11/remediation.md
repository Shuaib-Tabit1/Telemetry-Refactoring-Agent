```diff
--- a/ScmCoreInstrumentationServiceCollectionExtensions.cs
+++ b/ScmCoreInstrumentationServiceCollectionExtensions.cs
@@
 ﻿using System;
+using System.Data;
 
 using ADEXS.Caching.OpenTelemetry.Extensions;
 using ADEXS.CqlCorePersistence.OpenTelemetry;
 using ADEXS.ServiceFramework.OpenTelemetry.HostedServices;
@@
 				options.ConfigureRedisCacheInstrumentation();
 				options.AddScmCassandraPersistenceInstrumentation();
 				options.AddRabbitMQInstrumentation();
+				// Add SQL client instrumentation with custom enrichment so that the name of a
+				// stored procedure executed by the DbCommand is surfaced on the span as the
+				// 'db.operation' attribute.
+				options.AddSqlClientInstrumentation(sqlOptions =>
+				{
+					// We only need to enrich for stored procedures; guard with a try/catch
+					// so telemetry never impacts the actual application flow.
+					sqlOptions.EnrichWithIDbCommand = (activity, command) =>
+					{
+						try
+						{
+							if (command.CommandType == CommandType.StoredProcedure)
+							{
+								// Per semantic conventions, surface the procedure name as db.operation.
+								activity?.SetTag("db.operation", command.CommandText);
+							}
+						}
+						catch
+						{
+							// Swallow any exceptions to avoid affecting the business logic.
+						}
+					};
+				});
 
 				configureTracer?.Invoke(op tions);
 
 				if (telemetryConsoleTargets != null)
```

### Explanation
1. Added `using System.Data;` so we can access `CommandType`.
2. Registered SQL Client tracing instrumentation (`AddSqlClientInstrumentation`) inside the tracer configuration.
3. Implemented an `EnrichWithIDbCommand` callback that:
   • Checks if the command is a stored procedure (`CommandType.StoredProcedure`).  
   • Adds the stored-procedure name to the span via the OpenTelemetry tag `db.operation`.  
   • Wraps logic in a try/catch to ensure enrichment never breaks application flow.

This fulfills the requirement to expose the stored procedure name on telemetry spans.