The goal is to guarantee that every database-client span produced by our `ExecuteStoredProcedure(..)` helper carries two OpenTelemetry / Jaeger attributes:
• `db.operation` – the stored-procedure name  
• `db.name`      – the logical database name

The change is implemented in two small steps:
1. Introduce a **single, reusable helper** (`DbSpanEnricher`) that extracts the information from a `DbCommand` and attaches it to the currently active `Activity` (span).  
   • It is allocation-free and guarded against `null` arguments.  
   • A compiled regex pulls the sproc name by taking the first token of `CommandText`.
2. Invoke that helper from **`ExecuteStoredProcedure`** right after the `DbCommand` is built but _before_ the command is executed, ensuring the attributes are always present for both success and error paths.

Nothing else in the codebase is touched, so existing behaviour is preserved and the new attributes immediately show up in Jaeger traces.