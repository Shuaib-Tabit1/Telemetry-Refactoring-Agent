# Telemetry Refactoring Remediation Report

## Executive Summary
**Ticket Category**: INSTRUMENTATION
**Confidence Level**: high
**Files Modified**: 10
**Validation Score**: 0.63/1.0
**Risk Assessment**: HIGH

## Intent Analysis
**Semantic Description**: Add missing HTTP_REFERER and HTTP_RESPONSE_REDIRECT_LOCATION attributes to existing HTTP server spans in the CLM web application.
**Operation Type**: multi_file
**Complexity Score**: 4/10
**Estimated Impact**: 2 files

### Sub-tasks Identified
1. Search the CLM-Web solution for the existing OpenTelemetry / ActivitySource setup and any custom middleware that wraps HttpContext. Focus on files that reference `ActivitySource`, `OpenTelemetry`, `AddOpenTelemetryInstrumentation`, or `SetTag`.
2. Decide whether to (a) extend an existing custom middleware or (b) create a new middleware to enrich Activity.Current with the two new tags. The hook must run:
  • Early enough to read the incoming Referer header (Request.Headers["Referer"])
  • Late enough to read the final response headers (Response.Headers["Location"])
3. Inside the chosen middleware, add logic to read the Referer header and set the tag if non-empty:
```
var referer = context.Request.Headers["Referer"].FirstOrDefault();
if (!string.IsNullOrWhiteSpace(referer))
{
    Activity.Current?.SetTag("HTTP_REFERER", referer);
}
```
4. After `await _next(context)` (i.e., when the response is final), add logic to capture redirect target when status code is 3xx and Location header exists:
```
if (context.Response.StatusCode >= 300 && context.Response.StatusCode < 400)
{
    var location = context.Response.Headers["Location"].FirstOrDefault();
    if (!string.IsNullOrWhiteSpace(location))
    {
        Activity.Current?.SetTag("HTTP_RESPONSE_REDIRECT_LOCATION", location);
    }
}
```
5. Write unit tests for the middleware using TestServer/WebApplicationFactory. Scenarios:
  • GET with Referer, expect tag present
  • 302 response with Location, expect tag present
  • Missing headers, expect no tags (or tag not added)
Use ActivityListener or InMemoryExporter to assert tags.
6. Run CLM-Web locally, exercise redirect pages, and inspect emitted spans with OTLP console or Jaeger UI to ensure tags appear.
7. If risk is high, guard the new logic behind an `IOptions<TelemetryFlags>` flag (default ON in Demo). Allows quick disable in production.
8. Submit PR with:
  • Middleware changes
  • Unit tests
  • Update to release notes / CHANGELOG
  • Kusto validation query in PR description
9. Deploy to Demo environment via standard pipeline. Run the expected Kusto query:
```
OtlpSpanEvents
| where Environment == "Demo"
| where HTTP_REFERER !~ "" or HTTP_RESPONSE_REDIRECT_LOCATION !~ ""
| limit 50
```
10. Roll out to Prod using ringed deployment (e.g., 5% → 25% → 100%) while monitoring:
  • Span error rates
  • GC/CPU per node
  • Any spike in 5xx responses
11. Re-run expanded Kusto query on Prod after full rollout to confirm attribute presence on key pages:
```
OtlpSpanEvents
| where url_path in ("/clm/Documents/BrowseDocuments.aspx", "/clm/SSO/SSOEndpoint.ashx")
| where http_status_code between (300 .. 399)
| project Timestamp, url_path, HTTP_REFERER, HTTP_RESPONSE_REDIRECT_LOCATION
| take 100
```

## Code Changes
```diff
The HTTP server spans are created/enriched in two main places:

1. `LogAsyncRequestHttpMiddleware` – all ASP-NET Core requests flow through this middleware.
2. `BaseApiHandler` – legacy Web Forms handlers that sometimes issue 307 redirects.

By enriching the existing `Activity` objects in those two places we guarantee the new
attributes are always present and no new spans/middleware are required.

Changes made:

1. `WebNet/Middlewares/LogAsyncRequestHttpMiddleware.cs`
   • After the downstream pipeline executes, capture and attach  
     • `HTTP_REFERER` from the request header.  
     • `HTTP_RESPONSE_REDIRECT_LOCATION` from the response header.

2. `Web.Common/Helpers/BaseApiHandler.cs`
   • When the request first begins, add `HTTP_REFERER` to the current span.  
   • When a redirect is generated (inside `Redirect`), capture the target URL and
     tag the span with `HTTP_RESPONSE_REDIRECT_LOCATION`.

Assumptions:
• Headers may be missing – we guard with null/empty checks.
• `Activity.Current`/`Activity` may be null – guarded accordingly.
• Attribute names are exactly as required.
```

## Implementation Details
--- a/Users/shuaib.tabit/Documents/Atlas/src/WebNet/Middlewares/LogAsyncRequestHttpMiddleware.cs
+++ b/Users/shuaib.tabit/Documents/Atlas/src/WebNet/Middlewares/LogAsyncRequestHttpMiddleware.cs
@@
 			activity?.SetTagsWithCommonFields(context);
 			await base.Invoke(context);
+			// ─────────────────────────────────────────────────────────────────────────────
+			// Enrich span with additional HTTP attributes
+			// ---------------------------------------------------------------------------
+			var referer = context.Request.Headers["Referer"].ToString();
+			if (!string.IsNullOrEmpty(referer))
+			{
+				activity?.SetTag("HTTP_REFERER", referer);
+			}
+
+			var redirectLocation = context.Response.Headers["Location"].ToString();
+			if (!string.IsNullOrEmpty(redirectLocation))
+			{
+				activity?.SetTag("HTTP_RESPONSE_REDIRECT_LOCATION", redirectLocation);
+			}
+
 			activity?.SetStatus(context?.Response.StatusCode < 400 ? ActivityStatusCode.Ok : ActivityStatusCode.Error);
 		}
 		catch (Exception ex) when (ex.TraceAndIgnore(activity, ActivityStatusCode.Error))
--- a/Users/shuaib.tabit/Documents/Atlas/src/Web.Common/Helpers/BaseApiHandler.cs
+++ b/Users/shuaib.tabit/Documents/Atlas/src/Web.Common/Helpers/BaseApiHandler.cs
@@
 			{
 				PopulateFeatureFlagContext(AtlasContext.Current.UserAccount, context);
 				Activity.Current?.SetTagsWithCommonFields(context);
+
+				// Add HTTP_REFERER attribute to current span if available
+				var referer = context?.Request?.Headers?["Referer"];
+				if (!string.IsNullOrEmpty(referer))
+				{
+					Activity.Current?.SetTag("HTTP_REFERER", referer);
+				}
 			}
 			catch (Exception ex)
 			{
 				Logger.ErrorNoPII($"Failed to Populate Feature Flag Context: {LogData()}", ex);
 			}
@@
 			// Set the Location header with the new Controller URL
 			context.Response.AddHeader("Location", newUrl);
+
+			// Expose redirect location via telemetry
+			Activity.Current?.SetTag("HTTP_RESPONSE_REDIRECT_LOCATION", newUrl);
 
 		}
 		catch (ThreadAbortException)
 		{
 			// Do nothing intentionally.

## Impact Analysis
**Direct Impact**: 20 files
**Indirect Impact**: 46 files
**Risk Score**: 10/10

### Affected Architectural Patterns
- dependency_injection
- factory
- singleton

### Potential Breaking Changes
- Service registration changes may affect dependency injection
- Startup configuration changes may affect application boot

### Test Requirements
- Integration tests for telemetry data collection
- OpenTelemetry span validation tests
- Middleware pipeline integration tests
- Service registration validation tests
- Unit tests for modified methods

## Validation Results
**Overall Score**: 0.63/1.0
**Tests Passed**: 7/12

### Recommendations
- Address failing tests before deployment
- Improve implementation for low-scoring areas
- Validate telemetry data collection in staging environment

## Reasoning Summary

### File Selection Reasoning
These four files are the only ones in the candidate list that sit in the HTTP-server path and can enrich the “incoming_http_request” span; the other six files are processors, workers, or workflow helpers that never see HttpContext and therefore cannot supply HTTP_REFERER or redirect-location information.

### Patch Generation Reasoning
are finalised (middleware) and immediately after we add the Location header in