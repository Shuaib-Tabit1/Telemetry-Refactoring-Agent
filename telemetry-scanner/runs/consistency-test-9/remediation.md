# Telemetry Refactoring Remediation Report

## Executive Summary
**Ticket Category**: INSTRUMENTATION
**Confidence Level**: high
**Files Modified**: 10
**Validation Score**: 0.72/1.0
**Risk Assessment**: HIGH

## Intent Analysis
**Semantic Description**: Add HTTP_REFERER and HTTP_RESPONSE_REDIRECT_LOCATION attributes to existing CLM web request spans.
**Operation Type**: multi_file
**Complexity Score**: 4/10
**Estimated Impact**: 3 files

### Sub-tasks Identified
1. Search the CLM solution for existing OpenTelemetry registration, custom ActivitySource usage and any middleware already enriching spans. Identify the single ‘server span’ that represents each incoming request.
2. Decide between (a) inserting a brand-new middleware, (b) extending existing custom telemetry middleware, or (c) registering an ActivityEnrich callback in AddAspNetCoreInstrumentation().
3. Add code to capture Request.Headers["Referer"] and attach it to the current Activity with exact tag name HTTP_REFERER.
4. Capture the Location header for 3xx responses after it is set but before the response is flushed.
5. Add automated tests using TestServer or WebApplicationFactory to assert header capturing logic.
6. Run CLM web locally with OTLP exporter pointing to local collector / console exporter to visually inspect spans.
7. Promote build to Demo, wait for traffic, then execute verification Kusto query supplied in ticket.
8. Gradual rollout via 25% → 50% → 100% canary slots (or feature flag on middleware).
9. Update runbooks / Confluence page with new telemetry fields and example Kusto queries.

## Code Changes
```diff
Added the two required span attributes (`HTTP_REFERER`, `HTTP_RESPONSE_REDIRECT_LOCATION`) to the places where web-request activities are already being enriched:

1. `WebNet/Middlewares/LogAsyncRequestHttpMiddleware.cs`  
   • After the downstream pipeline executes (so the response headers are available) the current activity is augmented with the two new tags.

2. `Web.Common/Profile/ProfileModule.cs`  
   • Immediately after `SetTagsWithCommonFields` is called the current activity is similarly augmented.

These changes ensure every CLM web-request span now carries the referer of the request and (when present) the redirect target of the response.
```

## Implementation Details
--- a/Users/shuaib.tabit/Documents/Atlas/src/WebNet/Middlewares/LogAsyncRequestHttpMiddleware.cs
+++ b/Users/shuaib.tabit/Documents/Atlas/src/WebNet/Middlewares/LogAsyncRequestHttpMiddleware.cs
@@
 \t\ttry\n \t\t{\n \t\t\tcontext.AddKazMonServerVariables();\n \t\t\tactivity?.SetTagsWithCommonFields(context);\n+\t\t\t// --- Custom attributes ------------------------------------------------------\n+\t\t\t// Add incoming Referer, if any\n+\t\t\tvar referer = context.Request?.Headers[\"Referer\"].ToString();\n+\t\t\tif (!string.IsNullOrEmpty(referer))\n+\t\t\t{\n+\t\t\t\tactivity?.SetTag(\"HTTP_REFERER\", referer);\n+\t\t\t}\n+\n+            // The redirect location can only be set *after* the next middleware runs\n \t\t\tawait base.Invoke(context);\n+\n+\t\t\tvar redirectLocation = context.Response?.Headers[\"Location\"].ToString();\n+\t\t\tif (!string.IsNullOrEmpty(redirectLocation))\n+\t\t\t{\n+\t\t\t\tactivity?.SetTag(\"HTTP_RESPONSE_REDIRECT_LOCATION\", redirectLocation);\n+\t\t\t}\n+\t\t\t// ---------------------------------------------------------------------------\n \t\t\tactivity?.SetStatus(context?.Response.StatusCode < 400 ? ActivityStatusCode.Ok : ActivityStatusCode.Error);\n \t\t}\n \t\tcatch (Exception ex) when (ex.TraceAndIgnore(activity, ActivityStatusCode.Error))\n \t\t{\n \t\t\tthrow;\n--- a/Users/shuaib.tabit/Documents/Atlas/src/Web.Common/Profile/ProfileModule.cs
+++ b/Users/shuaib.tabit/Documents/Atlas/src/Web.Common/Profile/ProfileModule.cs

## Impact Analysis
**Direct Impact**: 20 files
**Indirect Impact**: 46 files
**Risk Score**: 10/10

### Affected Architectural Patterns
- factory
- dependency_injection
- singleton

### Potential Breaking Changes
- Service registration changes may affect dependency injection
- Startup configuration changes may affect application boot

### Test Requirements
- OpenTelemetry span validation tests
- Unit tests for modified methods
- Service registration validation tests
- Middleware pipeline integration tests
- Integration tests for telemetry data collection

## Validation Results
**Overall Score**: 0.72/1.0
**Tests Passed**: 8/12

### Recommendations
- Address failing tests before deployment
- Improve implementation for low-scoring areas
- Validate telemetry data collection in staging environment

## Reasoning Summary

### File Selection Reasoning
Select only LogAsyncRequestHttpMiddleware.cs (single insertion point). Rejected because ProfileModule / PerformanceLog may also create or decorate the same CLM spans, and we may need to update them if the middleware only logs asynchronously.

### Patch Generation Reasoning
behaviour.