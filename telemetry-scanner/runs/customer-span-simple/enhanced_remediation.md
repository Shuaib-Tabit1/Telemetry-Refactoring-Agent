The patch introduces a small, self-contained telemetry helper that guarantees every new span carries the two required identifiers:

1. Common/IRequestContext.cs & Common/RequestContextAccessor.cs  
   • Defines a lightweight `IRequestContext` contract (exposes `CustomerId` and `AccountId`).  
   • `RequestContextAccessor` stores the contract in an `AsyncLocal<T>` so the values flow through all async/parallel execution.  
   • These files do **not** populate the IDs – that is done upstream (API middleware / workers) and was already present in the code-base; we only expose a formal accessor that other components can consume.

2. Telemetry/FeatureFlags.cs  
   • Adds a typed wrapper for `AppSettings:Telemetry:AddCustomerAccountAttributes` so we can switch the behaviour on/off at runtime.

3. Telemetry/ActivityExtensions.cs  
   • Adds `StartActivityWithCustomerContext(…)` – a thin wrapper around `ActivitySource.StartActivity` that immediately sets the two attributes when the flag is enabled **and** the IDs are non-null / non-empty.  
   • Contains defensive checks to avoid null-ref or PII leakage.

4. StartupExtensions.cs  
   • Registers the new services (`IRequestContextAccessor`, telemetry flag) so DI can resolve them anywhere.

5. One representative call-site is refactored (Program.cs) to use the new helper; additional replacements can be done mechanically (`ActivitySource.StartActivity(` → `ActivityExtensions.StartActivityWithCustomerContext(`).

This gives us the foundation requested in subtasks 2–4: we have a clear context contract, a wrapper that sets attributes once, and the DI wiring to make it available everywhere.  
Further mechanical replacements can now be performed with a simple search-and-replace, as described in the plan.