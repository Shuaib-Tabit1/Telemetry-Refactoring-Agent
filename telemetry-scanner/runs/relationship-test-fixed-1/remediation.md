# Telemetry Refactoring Remediation Report

## Executive Summary
**Ticket Category**: INSTRUMENTATION
**Confidence Level**: high
**Files Modified**: 17
**Strategy Used**: direct instrumentation

## Intent Analysis
**Semantic Description**: Add HTTP_REFERER and HTTP_RESPONSE_REDIRECT_LOCATION headers as attributes on existing incoming HTTP request spans in the CLM web app.
**Operation Type**: multi_file
**Complexity Score**: 4/10
**Estimated Impact**: 3 files

### Sub-tasks Identified
1. Find the OpenTelemetry bootstrap code that registers ActivitySource / AspNet instrumentation for clm-web. Typical locations are Startup.cs, Program.cs, or custom extension classes (e.g. OpenTelemetryConfigExtensions.cs). Also search for AddOpenTelemetryTracing in *.cs files.
2. Create (or update) an enrichment delegate that is executed for every Server span. Within that delegate, copy the Request.Headers["Referer"] value into the span tag HTTP_REFERER if it exists.
3. Inside the same middleware/enrichment code, subscribe to HttpContext.Response.OnStarting to capture the final status code + Location header. If status code is 301, 302, 303, 307, or 308 and Location header exists, set Activity.SetTag("HTTP_RESPONSE_REDIRECT_LOCATION", locationValue).
4. Add defensive checks: only set tags when header values are non-null/non-empty; ensure no exceptions are thrown when headers missing. Benchmark with a simple load test (e.g. wrk for 1k rps) to confirm <1% overhead compared to baseline.
5. 1) Unit test middleware with mocked HttpContext to verify tags. 2) Integration test in the Demo environment using a feature branch deployment; execute Kusto query provided in ticket to assert tags are present.
6. Submit PR; reviewers confirm naming matches EXACTLY (HTTP_REFERER, HTTP_RESPONSE_REDIRECT_LOCATION) and no sensitive headers accidentally logged.
7. Promote to Dev → Demo. Monitor OpenTelemetry exporter throughput & error budgets.
8. Deploy via canary (e.g. 10% of pods for 1 hour) then full rollout. Continue Kusto monitoring plus Grafana latency dashboards.
9. Update internal wiki / observability runbook with the new span attributes and sample queries.

## Code Changes
```diff
The common helper `ActivityEnricher.SetTagsWithCommonFields` is already invoked at the *beginning* and again at the *end* of every request across
• ASP.NET Framework modules (ProfileModule, BaseApiHandler, …)  
• ASP.NET Core middleware (ProfileMiddleware, ScmLogAsyncRequestHttpMiddleware, etc.).

By extending this single, central method we enrich the **same incoming HTTP-request span** with the two new attributes whenever
they are available, without touching multiple pipelines.

Path changed:
• `src/Core.Domain/Utilities/ActivityEnricher.cs`

Assumptions:
1. Not every request will have a Referer or a redirect Location header – we only tag when a value exists.
2. Multiple calls are harmless; already-set tags are not overwritten.
```

## Implementation Details
--- a/Users/shuaib.tabit/Documents/Atlas/src/Core.Domain/Utilities/ActivityEnricher.cs
+++ b/Users/shuaib.tabit/Documents/Atlas/src/Core.Domain/Utilities/ActivityEnricher.cs
@@
 \t\tSetAccountIdTag(activity);
 \t\tSetUserIdTag(activity);
 \t\tSetSessionIdTag(activity, context);
+\t\tSetRequestRefererTag(activity, context);
+\t\tSetResponseRedirectLocationTag(activity, context);
 \t}
@@
 \t}
 
+#region HTTP header helpers
+\tprivate static void SetRequestRefererTag(Activity activity, HttpContext context)
+\t{
+\t\t// Do not overwrite if already present (method could be called twice).
+\t\tif (activity.GetTagItem(\"HTTP_REFERER\") != null)
+\t\t{
+\t\t\treturn;
+\t\t}
+
+#if NETFRAMEWORK
+\t\tvar referer = context?.Request?.Headers?[\"Referer\"];
+#else
+\t\tvar referer = context?.Request?.Headers[\"Referer\"].FirstOrDefault();
+#endif
+\t\tif (!string.IsNullOrEmpty(referer))
+\t\t{
+\t\t\tactivity.SetTag(\"HTTP_REFERER\", referer);
+\t\t}
+\t}
+
+\tprivate static void SetResponseRedirectLocationTag(Activity activity, HttpContext context)
+\t{
+\t\t// Do not overwrite if already present (method could be called twice).
+\t\tif (activity.GetTagItem(\"HTTP_RESPONSE_REDIRECT_LOCATION\") != null)
+\t\t{
+\t\t\treturn;
+\t\t}
+
+#if NETFRAMEWORK
+\t\tvar redirectLocation = context?.Response?.Headers?[\"Location\"];
+#else
+\t\tvar redirectLocation = context?.Response?.Headers[\"Location\"].FirstOrDefault();
+#endif
+\t\tif (!string.IsNullOrEmpty(redirectLocation))
+\t\t{
+\t\t\tactivity.SetTag(\"HTTP_RESPONSE_REDIRECT_LOCATION\", redirectLocation);
+\t\t}
+\t}
+#endregion
+
 #if NETFRAMEWORK
 \tprivate static void SetSessionIdTag(Activity activity, HttpContext context)
@@
 #endif
 
 }

## Batch Selection Analysis
**Total Search Results Processed**: 75
**Files with Telemetry Potential**: 0
**Final Files Selected**: 17
**Selection Efficiency**: 22.7%

## Reasoning Summary

### File Selection Reasoning
Batch 1 (LogAsyncRequestHttpMiddleware.cs): • LogAsyncRequestHttpMiddleware sits in the ASP.NET Core request pipeline and already performs span / Activity work (it inherits from AbstractLogRequestHttpMiddleware and references DocuSign.Monitoring).  
• Because it receives the HttpContext, it has direct access to both the incoming request headers (for “Referer”) and the outgoing response headers (for “Location”).  
• The middleware executes while the “Incoming HTTP Request” Activity created by the auto-instrumentation is still the current Activity, so we can safely call Activity.Current?.SetTag("HTTP_REFERER", …) and Activity.Current?.SetTag("HTTP_RESPONSE_REDIRECT_LOCATION", …).  
• No other files are required—one strategic middleware can capture both headers for every request, minimising code changes and adhering to the “single strategic file” rule.
Batch 2 (BaseApiHandler.cs): • BaseApiHandler.cs is an IHttpHandler used as the entry point for legacy ‑> .NET 6 migration calls. It owns the ProcessRequest(HttpContext) method, giving it direct access to:
  – HttpContext.Request.Headers (to read “Referer”)  
  – HttpContext.Response.Headers (to read or set “Location” when a redirect is issued).

• The file already references DocuSign.Monitoring and System.Diagnostics, indicating it creates or enriches Activity/Span objects. Therefore the existing telemetry infrastructure is present and can be extended with Activity.Current?.SetTag(…) (or equivalent) calls.

• Because every incoming ASHX request flows through this single base handler, adding the two attributes here satisfies “add HTTP_REFERER and HTTP_RESPONSE_REDIRECT_LOCATION headers as attributes on existing incoming HTTP request spans” for the whole CLM web app without touching other files.

• No other files are required; this one strategic entry-point file is sufficient and minimizes changes.
Batch 3 (ProfileModule.cs): • ProfileModule.cs is an IHttpModule that executes for every incoming HTTP request, giving it direct access to HttpContext, Request headers (e.g., “Referer”) and Response headers (e.g., “Location”).  
• The file already references DocuSign.CLM.Monitoring / DocuSign.Monitoring, indicating that spans or activities are created or at least accessible during request processing.  
• Within BeginRequest, EndRequest, or similar handlers, the code can retrieve Activity.Current (or the span object used by the monitoring SDK) and call SetTag / SetAttribute to add:  
 – HTTP_REFERER  → context.Request.Headers["Referer"]  
 – HTTP_RESPONSE_REDIRECT_LOCATION → context.Response.Headers["Location"]  
• Because ProfileModule runs for every request and already participates in telemetry, it is a single strategic location that can satisfy the telemetry requirement without touching additional files.

Thus, modifying only ProfileModule.cs is sufficient to add the required attributes to the existing incoming HTTP request spans.
Batch 4 (WinsService.cs): Cannot solve gap - The telemetry requirement targets normal incoming HTTP request spans and needs access to standard HTTP request/response headers (“Referer” and “Location”).  

WinsService.cs is a gRPC service implementation.  
• Its execution context is a gRPC ServerCallContext, not a classic ASP.NET Core HTTP context.  
• Redirect-related “Location” headers do not apply to gRPC calls, and the typical HTTP “Referer” header is usually absent as well.  
• Although the file references OpenTelemetry, the spans it deals with are gRPC-specific, not the HTTP spans produced by ASP.NET Core middleware.  

Therefore, this file group cannot meaningfully add the required attributes to the existing incoming HTTP request spans for the CLM web application.
Batch 5 (WinsService.Trace.cs): Cannot solve gap - The only file in this group (WinsService.Trace.cs) shows a helper that starts Activities for internal service methods (StartActivity). It does not run in the HTTP pipeline, has no access to HttpRequest or HttpResponse objects, and is unrelated to the incoming-request spans produced by ASP.NET. Therefore it cannot capture or add the HTTP_REFERER or HTTP_RESPONSE_REDIRECT_LOCATION attributes required. No files in this group are suitable for the requested instrumentation, so the gap cannot be solved here.
Batch 6 (LogAsyncRequestHttpMiddleware.cs): • LogAsyncRequestHttpMiddleware sits in the ASP.NET Core request pipeline and already performs span / activity work for every incoming HTTP call (it inherits from AbstractLogRequestHttpMiddleware and references DocuSign-specific OpenTelemetry helpers).  
• Because it receives the HttpContext, it can easily read Request.Headers["Referer"] and Response.Headers["Location"] at the same point where it currently enriches or finalizes the request span.  
• Adding two Activity-tag (or SetTag / SetAttribute) calls inside this middleware will attach the required attributes to the existing “Incoming HTTP Request Span,” satisfying the telemetry requirement without touching any other file.  
• No other files are necessary; this single strategic middleware covers every incoming request and is the canonical place the app already uses for HTTP telemetry enrichment.
Batch 7 (LogAsyncRequestHttpMiddleware.cs): • LogAsyncRequestHttpMiddleware is an ASP.NET Core middleware that already intercepts every incoming HTTP request and has full access to HttpContext.Request and HttpContext.Response.  
• The middleware already performs telemetry work (uses PropertyBagEventSource, inherits from AbstractLogRequestHttpMiddleware) so adding extra span attributes fits naturally here.  
• Because this code executes both before and after the downstream pipeline (it wraps the await _next(context) call), it can read the Referer header before the call and the final Location header after the call — exactly the two values required.  
• Activity/Span context is available via Activity.Current inside middleware; thus we can directly call Activity.Current?.SetTag("HTTP_REFERER", …) and Activity.Current?.SetTag("HTTP_RESPONSE_REDIRECT_LOCATION", …).  
• No other files are needed: one strategic middleware file can satisfy the entire requirement while keeping changes minimal.
Batch 8 (ProfileMiddleware.cs): • ProfileMiddleware.cs is an ASP.NET Core middleware that receives every incoming HTTP request (via HttpContext) and already references DocuSign.Monitoring as well as System.Diagnostics.  
• Inside its Invoke / InvokeAsync method it can access both:
  – Request.Headers["Referer"] before calling _next()  
  – Response.Headers["Location"] after _next() completes.  
• The current incoming request span is available as Activity.Current (created by existing ASP.NET Core / OpenTelemetry instrumentation). Adding tags to Activity.Current satisfies “ADD_ATTRIBUTES” on the existing span.  
• Because this single middleware sits early in the pipeline and already participates in telemetry, no additional files are required. Only ProfileMiddleware.cs needs a few extra lines:

```csharp
var activity = Activity.Current;
if (activity != null)
{
    if (context.Request.Headers.TryGetValue("Referer", out var referer))
        activity.SetTag("HTTP_REFERER", referer.ToString());

    await _next(context);   // continue pipeline

    if (context.Response.Headers.TryGetValue("Location", out var location))
        activity.SetTag("HTTP_RESPONSE_REDIRECT_LOCATION", location.ToString());
}
else
{
    await _next(context);
}
```

Thus the single strategic file ProfileMiddleware.cs can fully implement the telemetry requirement.
Batch 9 (ScmLogAsyncRequestHttpMiddleware.cs): • The requirement targets incoming HTTP request spans. ScmLogAsyncRequestHttpMiddleware is the central ASP.NET Core middleware responsible for logging/telemetry of every incoming request (inherits from AbstractLogRequestHttpMiddleware and already uses IServiceInstrumentation).  
• Being a middleware, it receives both the HttpContext.Request and HttpContext.Response objects and executes code both before and after the downstream pipeline. This provides direct access to:  
  – Request.Headers["Referer"] (needed for HTTP_REFERER)  
  – Response.Headers["Location"] (available after the next() call, needed for HTTP_RESPONSE_REDIRECT_LOCATION)  
• The middleware already creates/updates telemetry (KazMon / Activity / Span) via IServiceInstrumentation, so adding two additional Activity/Span attributes is a small, localized change.  
• No other files are necessary; modifying this single, strategic middleware meets the requirement while respecting the “minimize file count” rule.
Batch 10 (MvcAuditedRequestAttribute.cs): • MvcAuditedRequestAttribute is an MVC ActionFilter that runs for every incoming HTTP request (OnActionExecuting / OnActionExecuted).  
• The file already references telemetry infrastructure (DocuSign.CLM.Monitoring, DocuSign.Monitoring) and therefore has access to Activity/Span objects currently representing the “Incoming HTTP Request Span”.  
• Within this filter we can reliably read:  
  - Request.Headers["Referer"] (before the action executes)  
  - Response.Headers["Location"] (after the action executes)  
• Because Activity.Current is available inside the filter, we can call `SetTag` (or equivalent attribute-adding API) on the existing span without creating new spans.  
• No other files are required—this single, central filter runs on every request and is the minimal, strategic place to attach the two requested attributes.
Batch 11 (HttpRequestAuditHelper.cs): • The requirement targets “existing incoming HTTP request spans.”  
• HttpRequestAuditHelper.cs already handles request-level telemetry: it imports DocuSign.CLM.Monitoring / DocuSign.Monitoring and is clearly designed to start / enrich spans or counters for every MVC request.  
• Because this helper sits in the request pipeline and receives HttpContext (Request / Response), it can easily read:
  – Request.Headers["Referer"]  
  – Response.Headers["Location"]  
  and then call Activity.SetTag / span.SetAttribute on the current span.  
• Therefore, modifying this single strategic helper file is sufficient—no other files need changes.
Batch 12 (SSOEndpoint.ashx.cs): • SSOEndpoint.ashx.cs is an ASP-NET HttpHandler that directly receives an incoming HTTP request (it implements ProcessRequest on HttpContext) and constructs the HTTP response—including redirects that set Response.Headers["Location"].  
• The handler already references System.Diagnostics, so Activity.Current is readily available for extending existing incoming HTTP spans generated by ASP-NET/OpenTelemetry auto-instrumentation.  
• From this central request-handling point we can:
  – Read the inbound Referer header via context.Request.Headers["Referer"].  
  – Inspect the outbound redirect header (context.Response.Headers["Location"]) right before the response is flushed.  
  – Add both values to the active span with Activity.Current?.SetTag("HTTP_REFERER", …) and Activity.Current?.SetTag("HTTP_RESPONSE_REDIRECT_LOCATION", …).  
• Because this file fully owns the request/response lifecycle for its endpoint, no additional files or middleware need modification to satisfy the requirement for this execution path, keeping changes minimal as per prioritization rules.
Batch 13 (UploadFiles.ashx.cs): Cannot solve gap - The requirement is to add the HTTP_REFERER and HTTP_RESPONSE_REDIRECT_LOCATION headers as attributes on every incoming HTTP-request span in the entire CLM web application. That instrumentation should be performed at a centralized entry-point (e.g., Global.asax, an HTTP module, middleware, or another common request pipeline component) so that it uniformly affects every request.

The only file in this group, UploadFiles.ashx.cs, is a specific IHttpHandler for file uploads.  
• It handles just one endpoint, so modifying it would not cover all incoming requests.  
• There is no existing Activity/telemetry code here that could be simply extended.  
• Adding instrumentation here would only address this single handler, leaving the broader requirement unmet.

Because this file cannot provide the needed application-wide instrumentation and there is no other strategic file in the group, the group cannot solve the telemetry gap.
Batch 14 (AttributesController.cs): • The requirement is to add two tags (HTTP_REFERER, HTTP_RESPONSE_REDIRECT_LOCATION) to the existing incoming HTTP-request span.  
• In ASP.NET MVC, the active span for an HTTP request is available through System.Diagnostics.Activity.Current while the request is being processed inside a controller action.  
• AttributesController.cs is an MVC controller; its action methods execute in the context of the active request Activity, so it can call Activity.Current?.SetTag(..) with the needed header values.  
• There is no more strategic, central file (e.g., Global.asax, middleware, or a custom action filter) present in this group. Therefore the simplest, lowest-impact place to instrument is directly inside this controller (or by adding a small private helper inside the same file that runs in OnActionExecuting / OnResultExecuted overrides).  
• No other files are needed to meet the requirement, so choosing only AttributesController.cs adheres to the “minimize file count” rule.
Batch 15 (ActivityEnricher.cs): • The requirement is to add HTTP_REFERER and HTTP_RESPONSE_REDIRECT_LOCATION attributes to the existing “Incoming HTTP Request” spans.  
• ActivityEnricher.cs is already an enrichment utility that receives both the Activity (span) and the HttpContext and sets multiple custom tags using activity.SetTag(...).  
• Because it has direct access to context.Request.Headers and context.Response.Headers, this single file can be extended to read:  
  – context.Request.Headers["Referer"] → “HTTP_REFERER” tag  
  – context.Response.Headers["Location"] → “HTTP_RESPONSE_REDIRECT_LOCATION” tag  
• No other files are needed; the enrichment logic is centralized here, so modifying ActivityEnricher.cs satisfies the telemetry gap with minimal surface area.
Batch 16 (ScmHttpApplication.cs): • The requirement targets incoming HTTP request spans. ScmHttpApplication.cs is the application-wide HTTP entry point (acts like Global.asax) and already wires up OpenTelemetry (see OpenTelemetry.Trace, AddAspNetInstrumentation references).  
• Because the OpenTelemetry pipeline is configured here, we can extend it in one place:
  – Either via AddAspNetInstrumentation(options => options.Enrich = …) or  
  – In Application_BeginRequest / Application_EndRequest by updating Activity.Current.  
  Both approaches let us add the two headers as attributes on the existing span.
• No other files are needed; a small enrichment block in this single strategic file meets the requirement while keeping modification scope minimal.
Batch 17 (Global.asax.cs): • Global.asax.cs is the ASP .NET application entry point and already references OpenTelemetry.Trace.  
• In Application_BeginRequest/EndRequest (or similar) it has access to HttpContext and Activity.Current, which corresponds to the “Incoming HTTP Request Span” created by ASP.NET instrumentation.  
• From that location we can read Request.Headers["Referer"] and Response.Headers["Location"] and attach them to the current Activity with SetTag / SetCustomProperty.  
• No other files are needed—adding two lines in Global.asax.cs during the request lifecycle instruments every incoming span, fulfilling the requirement while keeping the change minimal.
Batch 18 (Program.cs): • The requirement is to add two HTTP header values (Referer and Location) as attributes on the existing “Incoming HTTP Request” spans.  
• Such attributes are normally added through the ASP.NET Core (or general HTTP) instrumentation enrichment delegate that is registered at application start-up.  
• Program.cs is the single, strategic bootstrapping file that builds the WebApplication/Host, registers OpenTelemetry tracing, and configures all middleware and services. This is exactly where AddOpenTelemetryTracing / AddAspNetCoreInstrumentation is typically set up.  
• By adding or modifying the Enrich callback in Program.cs we can read:
  – context.Request.Headers["Referer"] → set tag “HTTP_REFERER”  
  – context.Response.Headers["Location"] → set tag “HTTP_RESPONSE_REDIRECT_LOCATION”  
  and attach them to the Activity that represents the incoming HTTP request span.  
• No controller, middleware, or other file needs to be touched—one central change in Program.cs is sufficient, satisfying the “prefer single strategic files” rule.
Batch 19 (Startup.cs): Startup.cs wires up the ASP.NET Core request pipeline and already configures OpenTelemetry components through various “.OpenTelemetry” extension methods. That makes it the single strategic place where we can:

1. Insert a small custom middleware (or register an OpenTelemetry “Enrich” delegate) that runs for every incoming HTTP request.
2. Read Request.Headers["Referer"] and, after the response is generated, Response.Headers["Location"].
3. Add those values as tags on the current Activity (the existing “Incoming HTTP Request” span created by ASP.NET Core instrumentation).

Because Startup.cs controls both service registration and middleware ordering, no other files are required to implement this telemetry enrichment.
Batch 20 (CoreInstrumentationLifetimeService.cs): • CoreInstrumentationLifetimeService.cs is the central location where the application wires-up OpenTelemetry (adds TracerProviderBuilder, MeterProviderBuilder, etc.).  
• Incoming HTTP request spans are automatically created by the ASP.NET Core instrumentation that is registered from this file; therefore, the file already has direct access to configure enrichment callbacks (e.g., `builder.AddAspNetCoreInstrumentation(options => { … })`).  
• The requirement—adding HTTP_REFERER and HTTP_RESPONSE_REDIRECT_LOCATION as attributes on those spans—can be met by adding an `Enrich` or `OnEndActivity`/`OnStartActivity` delegate inside this same builder configuration.  
• No other files in the group deal with HTTP processing or OpenTelemetry configuration, so modifying just this strategic file keeps the change minimal and maintainable.
Batch 21 (WorkflowActivitiesController.cs): Cannot solve gap - • The requirement is to add the headers as attributes on the existing “incoming HTTP request” span created for every request to the CLM web app.  
• That span is started by ASP.NET Core middleware before any controller code runs and is finished after the response is sent.  
• Capturing both the request header (“Referer”) and the response header (“Location”) reliably therefore needs code that executes in the middleware pipeline (or a global action filter) – not only inside an individual controller action.  
• The only file in this group, WorkflowActivitiesController.cs, is a single controller specific to workflow-activities. It cannot see or modify every request/response, and adding SetTag logic here would instrument only this controller’s endpoints, leaving the rest of the app uncovered.  
• There is no existing custom middleware or base controller in this file where a reusable instrumentation hook could be placed.  
• Consequently, this file group, by itself, cannot implement the telemetry requirement in a correct, application-wide manner, so no file in the group is selected for modification.

### Patch Generation Reasoning
ReasoningChain(strategy=<ReasoningStrategy.CHAIN_OF_THOUGHT: 'chain_of_thought'>, steps=[ReasoningStep(step_number=1, description='3. Implementation is cross-framework (#if NETFRAMEWORK vs ASP.NET Core) and requires no changes elsewhere because all existing middleware / filters already call SetTagsWithCommonFields(…).', reasoning='3. Implementation is cross-framework (#if NETFRAMEWORK vs ASP.NET Core) and requires no changes elsewhere because all existing middleware / filters already call SetTagsWithCommonFields(…).\n\nCode patch:', conclusion='Code patch:', confidence=0.8, evidence=['LLM analysis'])], final_conclusion='This single edit satisfies the requirement across the entire CLM web application because all existing middleware / filters invoke `SetTagsWithCommonFields`, ensuring every incoming HTTP request span now carries the new attributes.', overall_confidence=0.8, alternative_approaches=[])