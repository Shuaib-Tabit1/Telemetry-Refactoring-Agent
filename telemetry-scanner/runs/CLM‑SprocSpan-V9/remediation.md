```diff
--- a/ScmCoreInstrumentationServiceCollectionExtensions.cs
+++ b/ScmCoreInstrumentationServiceCollectionExtensions.cs
@@ ... @@
 				options.AddScmCassandraPersistenceInstrumentation();
 				options.AddRabbitMQInstrumentation();
+
+                // Instrument DbCommand (for tracing stored procedure execution) to add db.statement attribute with sproc name.
+                options.AddSqlClientInstrumentation(sqlOptions =>
+                {
+                    sqlOptions.Enrich = (activity, eventName, rawCommand) =>
+                    {
+                        if (rawCommand is System.Data.Common.DbCommand cmd)
+                        {
+                            // If this is a stored procedure, set the db.statement to its name (cmd.CommandText),
+                            // otherwise preserve typical behavior.
+                            if (cmd.CommandType == System.Data.CommandType.StoredProcedure)
+                            {
+                                activity.SetTag("db.statement", cmd.CommandText);
+                            }
+                        }
+                    };
+                });
 
 				configureTracer?.Invoke(options);
 
@@ ... @@
```

### Explanation

- Added an `options.AddSqlClientInstrumentation(...)` call to the OpenTelemetry tracer configuration delegate in `AddScmCoreInstrumentation`.
- Inside this call, used the `Enrich` callback to check if `DbCommand` is executing a stored procedure (`CommandType.StoredProcedure`) and, if so, sets the span attribute `db.statement` to the stored procedure's name (`cmd.CommandText`).
- This directly targets the database sproc execution trace and adds the desired attribute as requested.  
- No other code is modified; the change is as narrowly scoped as possible while integrating with the .NET OpenTelemetry instrumentation chain.