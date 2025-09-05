# Telemetry Refactoring Remediation Report

## Executive Summary
**Ticket Category**: INSTRUMENTATION
**Confidence Level**: high
**Files Modified**: 19
**Validation Score**: 0.63/1.0
**Risk Assessment**: HIGH

## Intent Analysis
**Semantic Description**: Add HTTP_REFERER and HTTP_RESPONSE_REDIRECT_LOCATION attributes to existing HTTP request spans in the CLM web application for better redirect flow tracing.
**Operation Type**: multi_file
**Complexity Score**: 4/10
**Estimated Impact**: 4 files

### Sub-tasks Identified
1. Search the CLM solution for existing OpenTelemetry setup and any custom Activity enrichment logic.
• grep / VS Code search for: "AddOpenTelemetry", "ActivitySource", "SetTag", "Enrich", "HTTP_"
• Typical files: Startup.cs / Program.cs, TelemetryExtensions.cs, OpenTelemetryConfig.cs, Middleware/*Telemetry*.cs
2. Pick the most reliable location that has access to both Request and Response.
Preferred: ASP.NET Core middleware registered early AFTER diagnostic listener instrumentation so we mutate the already-created Activity.
3. 1. Create e.g. file Middlewares/TelemetryEnrichmentMiddleware.cs
2. In Invoke(HttpContext ctx):
   a. var activity = Activity.Current;
   b. if (activity != null)
        ▸ string referer = ctx.Request.Headers["Referer"].ToString();
        ▸ if (!string.IsNullOrWhiteSpace(referer)) activity.SetTag("HTTP_REFERER", referer);
   c. await _next(ctx);
   d. if (activity != null && ctx.Response.StatusCode >= 301 && ctx.Response.StatusCode <= 308)
        ▸ string location = ctx.Response.Headers["Location"].ToString();
        ▸ if (!string.IsNullOrWhiteSpace(location)) activity.SetTag("HTTP_RESPONSE_REDIRECT_LOCATION", location);
4. In Startup.Configure(...) or Program.cs add:
app.UseMiddleware<TelemetryEnrichmentMiddleware>();
Place immediately after app.UseRouting() and before app.UseEndpoints() to guarantee visibility of final status code.
5. Run CLM locally with dotnet-collector logging:
• Trigger a normal request and a redirect response with curl/Postman.
• Inspect exported OTLP data via console exporter or WireShark to confirm new tags exist.
6. Add unit/integration tests using WebApplicationFactory:
• Test 1: GET /Target with Referer header => span contains HTTP_REFERER
• Test 2: Endpoint that returns 302 with Location header => span contains HTTP_RESPONSE_REDIRECT_LOCATION
7. Introduce appsetting: Telemetry:AddRedirectHeaders (bool, default true) so behaviour can be disabled quickly.
8. Run k6/locust load comparing before/after to ensure <1 ms added latency per request and no GC spikes.
9. Merge PR to develop; let CI build and deploy to Demo slot.
10. Run provided Kusto query in Demo workspace to confirm attributes present.
11. Stage -> QA -> Prod using blue/green. Monitor dashboards for error or perf anomalies for 24 h.
12. Update internal wiki with new attribute list and sample query; close Jira ticket.

## Code Changes
```diff
Redirect flows are currently hard to trace because the **Referer** sent by the browser and the **Location** header returned by the server are not recorded on the existing HTTP-request spans.  
The patch introduces two new span attributes:

1. `HTTP_REFERER` – value taken from `Request.Headers["Referer"]`
2. `HTTP_RESPONSE_REDIRECT_LOCATION` – value taken from `Response.Headers["Location"]`

To keep the code DRY and future-proof, a small helper/extension class is added.  
`ScmHttpApplication` (our `global.asax.cs` replacement) is the single place that already handles ASP-NET request/response instrumentation, so we only need to call the helper there.
```

## Implementation Details
*** Begin Patch
*** Add File: Telemetry/HttpHeaderTelemetryExtensions.cs
+﻿#nullable enable
+using System.Diagnostics;
+#if NETFRAMEWORK
+using System.Web;
+#endif
+
+namespace ADEXS.Core.Telemetry.Extensions;
+
+/// <summary>
+/// Helper extensions that enrich the current Activity with
+/// HTTP Referer / Redirect-Location information so that
+/// redirect flows can be analysed in traces.
+/// </summary>
+internal static class HttpHeaderTelemetryExtensions
+{
+    public const string HTTP_REFERER                       = "HTTP_REFERER";
+    public const string HTTP_RESPONSE_REDIRECT_LOCATION    = "HTTP_RESPONSE_REDIRECT_LOCATION";
+
+#if NETFRAMEWORK
+    /// <summary>
+    /// Adds the HTTP_REFERER attribute to the span (if any).
+    /// </summary>
+    internal static void SetHttpReferer(this Activity? activity, HttpRequest request)
+    {
+        if (activity is null) return;
+
+        var referer = request?.Headers["Referer"];
+        if (!string.IsNullOrEmpty(referer))
+        {
+            activity.SetTag(HTTP_REFERER, referer);
+        }
+    }
+
+    /// <summary>
+    /// Adds the HTTP_RESPONSE_REDIRECT_LOCATION attribute to the span (if any).
+    /// Captured only for 3xx responses.
+    /// </summary>
+    internal static void SetRedirectLocation(this Activity? activity, HttpResponse response)
+    {
+        if (activity is null) return;
+
+        // We only care about redirects (3xx)
+        if (response.StatusCode is < 300 or >= 400) return;
+
+        var location = response.Headers["Location"];
+        if (!string.IsNullOrEmpty(location))
+        {
+            activity.SetTag(HTTP_RESPONSE_REDIRECT_LOCATION, location);
+        }
+    }
+#endif
+}
+
*** End Patch
*** End Patch

## Impact Analysis
**Direct Impact**: 19 files
**Indirect Impact**: 132 files
**Risk Score**: 10/10

### Affected Architectural Patterns
- factory
- singleton
- dependency_injection

### Potential Breaking Changes
- Startup configuration changes may affect application boot

### Test Requirements
- OpenTelemetry span validation tests
- Unit tests for modified methods
- Integration tests for telemetry data collection

## Validation Results
**Overall Score**: 0.63/1.0
**Tests Passed**: 7/12

### Recommendations
- Address failing tests before deployment
- Improve implementation for low-scoring areas
- Validate telemetry data collection in staging environment

## Reasoning Summary

### File Selection Reasoning
• Add a delegating handler if using HttpClient, but requirement is for incoming server requests, not outgoing client calls.

### Patch Generation Reasoning
Fallback conclusion due to reasoning error