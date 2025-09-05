The OpenTelemetry pipeline already registers `AddSqlClientInstrumentation`, which is responsible for creating spans around every `SqlCommand` execution.  
By enriching those spans we can attach additional attributes without touching
any existing data-access code (including `ExecuteStoredProcedure`).

The enrichment callback now:
• Detects when the command represents a stored-procedure invocation  
• Adds the semantic attribute `db.operation` with the procedure name  
• Adds the semantic attribute `db.name` with the database name obtained from the connection  

The logic is fully defensive (null / whitespace guards and a try / catch) so that
any failure in enrichment cannot break the normal execution path.