# Telemetry Refactoring Remediation Report

## Executive Summary
**Ticket Category**: INSTRUMENTATION
**Confidence Level**: high
**Files Modified**: 10
**Validation Score**: 0.63/1.0
**Risk Assessment**: HIGH

## Intent Analysis
**Semantic Description**: Add missing HTTP_REFERER and HTTP_RESPONSE_REDIRECT_LOCATION attributes to existing HTTP request spans in CLM web application.
**Operation Type**: multi_file
**Complexity Score**: 4/10
**Estimated Impact**: 5 files

### Sub-tasks Identified
1. Search the CLM web solution for OpenTelemetry configuration, ActivitySource declarations, and existing middleware where SetTag/SetCustomProperty is called.
2. Decide the exact injection point that has visibility of BOTH request headers and the final response (after status code & Location header are written). Normally this is a custom ASP.NET Core middleware placed immediately after UseRouting() and before UseEndpoints().
3. Create or update a middleware class (e.g., Telemetry/RedirectEnrichmentMiddleware.cs). In Invoke/InvokeAsync:
  a. Extract referer = context.Request.Headers["Referer"].FirstOrDefault();
  b. Call await _next(context);
  c. After _next, if (context.Response.StatusCode >= 300 && context.Response.StatusCode < 400) { location = context.Response.Headers["Location"].FirstOrDefault(); }
  d. var activity = Activity.Current; if (activity != null) { activity.SetTag("HTTP_REFERER", referer ?? string.Empty); if (!string.IsNullOrEmpty(location)) activity.SetTag("HTTP_RESPONSE_REDIRECT_LOCATION", location); }
4. In Startup.cs (Configure method) or equivalent, add app.UseMiddleware<RedirectEnrichmentMiddleware>(); in correct order as determined in step 2.
5. Add unit tests using TestServer/WebApplicationFactory:
  • GET request with Referer header, expect Activity has HTTP_REFERER.
  • 302 response with Location header, expect Activity has HTTP_RESPONSE_REDIRECT_LOCATION.
6. Run application locally with OpenTelemetry exporter pointed to console/OTLP collector. Generate a request flow that triggers redirect and examine emitted spans to confirm new tags are present and non-empty where applicable.
7. Run quick load test (e.g., 1000 req/s for 1 min) with and without middleware; compare p95 latency and CPU usage. Ensure overhead < 2 ms per request.
8. Open Pull Request with middleware, tests, and documentation update. Tag Observability and CLM owners; address feedback.
9. Merge to main → trigger CI/CD to Demo environment. Execute manual redirect scenarios on /clm/Documents/BrowseDocuments.aspx; run target Kusto query provided in ticket to confirm new columns populated.
10. If Demo validation passes for 24 h, promote deployment to Staging then Production. Monitor Application Insights dashboards / Kusto queries for error rate, latency, and tag presence.

## Code Changes
```diff
The CLM web application already creates HTTP request spans through `AspNetInstrumentation` (ASP.NET Framework) and `AspNetCoreInstrumentation` (ASP.NET Core).  
We simply enrich those spans at the single, central place where the
instrumentation is configured and attach two new attributes:

• `HTTP_REFERER` – taken from the incoming request header  
• `HTTP_RESPONSE_REDIRECT_LOCATION` – taken from the `Location` response
header when the status code is 3xx

No new middleware, no duplicate spans – we only extend the existing
instrumentation pipeline, keeping the solution DRY and easy to maintain.
```

## Implementation Details
diff --git a/ScmHttpApplication.cs b/ScmHttpApplication.cs
@@
-                    .AddAspNetInstrumentation(options =>
-                    {
-
-                    })
+                    .AddAspNetInstrumentation(options =>
+                    {
+                        // Enrich every HTTP span with Referer / Redirect-Location
+                        options.Enrich = (activity, eventName, obj) =>
+                        {
+                            if (eventName == "OnStartActivity" && obj is HttpContext ctxStart)
+                            {
+                                var referer = ctxStart?.Request?.Headers["Referer"];
+                                if (!string.IsNullOrEmpty(referer))
+                                {
+                                    activity.SetTag("HTTP_REFERER", referer);
+                                }
+                            }
+                            else if (eventName == "OnStopActivity" && obj is HttpContext ctxStop)
+                            {
+                                var status = ctxStop?.Response?.StatusCode ?? 0;
+                                if (status >= 300 && status < 400)
+                                {
+                                    var location = ctxStop?.Response?.Headers["Location"];
+                                    if (!string.IsNullOrEmpty(location))
+                                    {
+                                        activity.SetTag("HTTP_RESPONSE_REDIRECT_LOCATION", location);
+                                    }
+                                }
+                            }
+                        };
+                    })
diff --git a/Program.cs b/Program.cs
@@
 using OpenTelemetry.Metrics;
+using OpenTelemetry.Instrumentation.AspNetCore;
+using System.Linq;
@@
 builder.Services.AddComponentsInstrumentation();
+
+// Enrich ASP.NET Core HTTP spans with Referer / Redirect-Location headers
+builder.Services.Configure<HttpRequestInInstrumentationOptions>(options =>
+{
+    options.Enrich = (activity, eventName, raw) =>
+    {
+        if (eventName == "OnStartActivity" && raw is Microsoft.AspNetCore.Http.HttpRequest req)
+        {
+            var referer = req.Headers["Referer"].FirstOrDefault();
+            if (!string.IsNullOrEmpty(referer))
+            {
+                activity.SetTag("HTTP_REFERER", referer);
+            }
+        }
+        else if (eventName == "OnStopActivity" && raw is Microsoft.AspNetCore.Http.HttpResponse res)
+        {
+            if (res.StatusCode >= 300 && res.StatusCode < 400)
+            {
+                var location = res.Headers["Location"].FirstOrDefault();
+                if (!string.IsNullOrEmpty(location))
+                {
+                    activity.SetTag("HTTP_RESPONSE_REDIRECT_LOCATION", location);
+                }
+            }
+        }
+    };
+});

## Impact Analysis
**Direct Impact**: 18 files
**Indirect Impact**: 130 files
**Risk Score**: 10/10

### Affected Architectural Patterns
- factory
- singleton
- dependency_injection

### Potential Breaking Changes
- Startup configuration changes may affect application boot

### Test Requirements
- Unit tests for modified methods
- OpenTelemetry span validation tests
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
Confidence: 0.63

### Patch Generation Reasoning
инчи