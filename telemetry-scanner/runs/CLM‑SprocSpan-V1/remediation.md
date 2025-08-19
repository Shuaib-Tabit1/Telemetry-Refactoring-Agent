### Explanation

1. Introduced a new static class `TelemetrySetup` to centralize OpenTelemetry configuration.  
2. Added both `AddSqlClientInstrumentation` and `AddDbCommandInstrumentation` so any ADO.NET calls (including stored procedures) are traced.  
3. In each instrumentation, checked for `CommandType.StoredProcedure` and used the command’s `CommandText` to set the span attribute `db.rpc.object`.  
4. Registered a Jaeger exporter so that collected spans are sent to a Jaeger backend.  
5. Removed the original auto-generated assembly-info file contents and replaced it with functional tracing setup.