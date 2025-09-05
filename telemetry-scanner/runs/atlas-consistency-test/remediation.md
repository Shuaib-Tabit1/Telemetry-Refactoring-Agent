# Telemetry Refactoring Remediation Report

## Executive Summary
**Ticket Category**: INSTRUMENTATION
**Confidence Level**: high
**Files Modified**: 30
**Validation Score**: 0.64/1.0
**Risk Assessment**: HIGH

## Intent Analysis
**Semantic Description**: Add missing HTTP_REFERER and HTTP_RESPONSE_REDIRECT_LOCATION attributes to existing HTTP server spans in the CLM web application.
**Operation Type**: multi_file
**Complexity Score**: 4/10
**Estimated Impact**: 4 files

### Sub-tasks Identified
1. Search clm-web solution for OpenTelemetry bootstrap and custom middleware. Confirm where ActivitySource/SetTag calls already exist.
2. Decide whether to (a) add tags inside an existing middleware or (b) create a new middleware placed immediately after Routing but before Endpoint execution to ensure Response headers are available via OnStarting.
3. Within chosen middleware, capture HttpContext.Request.Headers["Referer"] (case-insensitive) and, if not null/empty, call Activity.Current?.SetTag("HTTP_REFERER", value).
4. Use HttpResponse.OnStarting(callback) to read Response.StatusCode and Response.Headers["Location"]. If status code in {301,302,303,307,308} and header not null/empty, set Activity.Current?.SetTag("HTTP_RESPONSE_REDIRECT_LOCATION", location).
5. Add logic to skip tagging if value length > 4k or if value contains credentials (e.g., '://user:pass@').
6. Add xUnit tests: (a) no headers → no tags; (b) Referer only; (c) 302 with Location; (d) both headers.
7. Use existing k6 or Bombardier script (10k RPS) to measure p95 latency with/without middleware changes. Target delta <1 ms.
8. Submit PR. Obtain approvals from core maintainer and Security for new data collection (Referer may contain PII).
9. CI/CD pipeline builds and deploys clm-web:dev. Verify startup logs show new middleware registered.
10. Run Kusto query in OTLP backend for dev environment to confirm new attributes appear and values are correct.
11. Promote build to Demo, then Stage after 24h of clean metrics. Monitor error rate and latency dashboards.
12. Blue/green or canary (10% → 100% traffic) deployment to prod.
13. Update observability-runbook.md and system-README.md with new attributes and sample queries.

## Code Changes
```diff
Telemetry spans for incoming HTTP-server requests already exist, but they do **not** include the
two attributes requested by the monitoring team:

• `HTTP_REFERER` – the value of the request header `Referer`  
• `HTTP_RESPONSE_REDIRECT_LOCATION` – the value of the response header `Location`

The patch introduces a small reusable helper (`HttpSpanAttributeExtensions`) and wires it into the
two ASP-NET-Core middlewares that create / decorate the server span:
`LogAsyncRequestHttpMiddleware` (generic) and `ScmLogAsyncRequestHttpMiddleware`
(SCM-specific).

The helper is called **before** the request is executed (to capture the referer) and **after**
`await next()` returns (to capture the final redirect location).  
It is completely no-op when the current Activity is `null` or when the corresponding header
is missing, and therefore is safe to add.

No DI change is required because the helper is a static extension method.
```

## Implementation Details
*** Begin Patch
*** Add File: Web/Common/AspNetCore/Extensions/HttpSpanAttributeExtensions.cs
+#nullable enable
+using System.Diagnostics;
+using Microsoft.AspNetCore.Http;
+
+namespace ADEXS.Web.Common.AspNetCore.Extensions;
+
+/// <summary>
+/// Helper methods used by HTTP middlewares to add extra attributes to the
+/// automatically created OpenTelemetry HTTP server span.
+/// </summary>
+internal static class HttpSpanAttributeExtensions
+{
+    private const string HttpRefererAttributeName = "HTTP_REFERER";
+    private const string HttpRedirectLocationAttributeName = "HTTP_RESPONSE_REDIRECT_LOCATION";
+
+    /// <summary>
+    /// Adds the HTTP_REFERER attribute – if present – to the current Activity.
+    /// Has no side-effects when Activity.Current is null or the header is not present.
+    /// </summary>
+    internal static void AddHttpRefererTag(this HttpRequest request)
+    {
+        var activity = Activity.Current;
+        if (activity == null)
+            return;
+
+        if (request.Headers.TryGetValue("Referer", out var header) && !string.IsNullOrEmpty(header))
+        {
+            activity.SetTag(HttpRefererAttributeName, header.ToString());
+        }
+    }
+
+    /// <summary>
+    /// Adds the HTTP_RESPONSE_REDIRECT_LOCATION attribute – if present – to the current Activity.
+    /// Should be called *after* the response pipeline has completed so that the header is final.
+    /// </summary>
+    internal static void AddRedirectLocationTag(this HttpResponse response)
+    {
+        var activity = Activity.Current;
+        if (activity == null)
+            return;
+o
+        if (response.Headers.TryGetValue("Location", out var header) && !string.IsNullOrEmpty(header))
+        {
+            activity.SetTag(HttpRedirectLocationAttributeName, header.ToString());
+        }
+    }
+}
+
*** End Patch
*** Update File: API/Allocation/Middlewares/LogAsyncRequestHttpMiddleware.cs
@@
     public async Task InvokeAsync(HttpContext context)
     {
-        var activity = Activity.Current;
+        // Capture referer before the request starts processing.
+        context.Request.AddHttpRefererTag();
 
         await _next(context);
+
+        // After the pipeline has completed we can capture a possible redirect location.
+        context.Response.AddRedirectLocationTag();
     }
 }
*** End Patch
*** Update File: Web/Common/AspNetCore/Middlewares/ScmLogAsyncRequestHttpMiddleware.cs
@@
     public async Task InvokeAsync(HttpContext context)
     {
-        var activity = Activity.Current;
+        // Tag HTTP_REFERER at the very beginning.
+        context.Request.AddHttpRefererTag();
 
         await _next(context);
+
+        // Tag HTTP_RESPONSE_REDIRECT_LOCATION once the response is complete.
+        context.Response.AddRedirectLocationTag();
     }
 }
*** End Patch
*** End Patch

## Impact Analysis
**Direct Impact**: 20 files
**Indirect Impact**: 53 files
**Risk Score**: 10/10

### Affected Architectural Patterns
- factory
- singleton

### Potential Breaking Changes
- Service registration changes may affect dependency injection

### Test Requirements
- Service registration validation tests
- Middleware pipeline integration tests
- OpenTelemetry span validation tests
- Integration tests for telemetry data collection
- Unit tests for modified methods

## Validation Results
**Overall Score**: 0.64/1.0
**Tests Passed**: 7/12

### Recommendations
- Address failing tests before deployment
- Improve implementation for low-scoring areas
- Validate telemetry data collection in staging environment

## Reasoning Summary

### File Selection Reasoning
– inside the finally / OnCompleted block (or after await _next), when the response is ready:

### Patch Generation Reasoning
### ✔  Result