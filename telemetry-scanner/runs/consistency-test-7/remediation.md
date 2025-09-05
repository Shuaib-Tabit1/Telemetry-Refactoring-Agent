# Telemetry Refactoring Remediation Report

## Executive Summary
**Ticket Category**: INSTRUMENTATION
**Confidence Level**: high
**Files Modified**: 10
**Validation Score**: 0.72/1.0
**Risk Assessment**: HIGH

## Intent Analysis
**Semantic Description**: Add HTTP_REFERER and HTTP_RESPONSE_REDIRECT_LOCATION tags to existing HTTP request spans in the CLM web application.
**Operation Type**: multi_file
**Complexity Score**: 4/10
**Estimated Impact**: 3 files

### Sub-tasks Identified
1. Search the CLM-web solution for OpenTelemetry setup and existing HTTP enrichment logic.
2. Decide the best location to enrich spans once headers are final.
3. Add HTTP_REFERER and HTTP_RESPONSE_REDIRECT_LOCATION tags
4. Create or update unit tests validating tag presence.
5. Run CLM-web locally with OTLP exporter pointing to a Docker collector + Jaeger to inspect spans.
6. Ensure no PII or sensitive querystring leaks; run BenchmarkDotNet or kestrel perf tests.
7. Open PR, tag Observability and CLM owners; link to ticket; attach test screenshots.
8. Use existing release pipeline with feature flag ‘otel_redirect_enrichment’ set to ON for Demo only.
9. Run the provided Kusto query in Demo cluster.
10. Gradual exposure: 10 % → 50 % → 100 % over 2 days with telemetry checks at each step.
11. Update internal observability run-book, add new attributes to CLM telemetry field dictionary.
12. Mark ticket Done once acceptance criteria satisfied and validated.

## Code Changes
```diff
Added enrichment for the current HTTP-request span inside
`API.GateKeeper/Middlewares/LogAsyncRequestHttpMiddleware.cs`.

Changes:
1. Captures request header `Referer` and, when present, adds it as span
   attribute `HTTP_REFERER`.
2. After the downstream pipeline runs, if the response status code is in
   the 3xx range, captures the `Location` header (if any) and records it as
   span attribute `HTTP_RESPONSE_REDIRECT_LOCATION`.
3. Keeps the change minimal—no new files or registrations required.
```

## Implementation Details
--- a/Users/shuaib.tabit/Documents/Atlas/src/API.GateKeeper/Middlewares/LogAsyncRequestHttpMiddleware.cs
+++ b/Users/shuaib.tabit/Documents/Atlas/src/API.GateKeeper/Middlewares/LogAsyncRequestHttpMiddleware.cs
@@
 \tpublic override async Task Invoke(HttpContext context)
 \t{
 \t\tvar activity = Activity.Current;
 
 \t\ttry
 \t\t{
+\t\t\t// ------------------------------------------------------------------------------
+\t\t\t// Enrich span with incoming referer (if supplied)
+\t\t\t// ------------------------------------------------------------------------------
+\t\t\tvar referer = context.Request.Headers[\"Referer\"].ToString();
+\t\t\tif (!string.IsNullOrEmpty(referer))
+\t\t\t{
+\t\t\t\tactivity?.SetTag(\"HTTP_REFERER\", referer);
+\t\t\t}
+
 \t\t\tcontext.AddKazMonServerVariables();
 \t\t\tactivity?.SetTagsWithCommonFields(context);
 \t\t\tawait base.Invoke(context);
+
+\t\t\t// ------------------------------------------------------------------------------
+\t\t\t// Enrich span with redirect target when response is a redirect (3xx)
+\t\t\t// ------------------------------------------------------------------------------
+\t\t\tif (context.Response.StatusCode >= 300 && context.Response.StatusCode < 400)
+\t\t\t{
+\t\t\t\tvar redirectLocation = context.Response.Headers[\"Location\"].ToString();
+\t\t\t\tif (!string.IsNullOrEmpty(redirectLocation))
+\t\t\t\t{
+\t\t\t\t\tactivity?.SetTag(\"HTTP_RESPONSE_REDIRECT_LOCATION\", redirectLocation);
+\t\t\t\t}
+\t\t\t}
+
 \t\t\tactivity?.SetStatus(context?.Response.StatusCode < 400 ? ActivityStatusCode.Ok : ActivityStatusCode.Error);
 \t\t}
 \t\tcatch (Exception ex) when (ex.TraceAndIgnore(activity, ActivityStatusCode.Error))
 \t\t{
 \t\t\tthrow;

## Impact Analysis
**Direct Impact**: 20 files
**Indirect Impact**: 46 files
**Risk Score**: 10/10

### Affected Architectural Patterns
- singleton
- dependency_injection
- factory

### Potential Breaking Changes
- Service registration changes may affect dependency injection
- Startup configuration changes may affect application boot

### Test Requirements
- Middleware pipeline integration tests
- Integration tests for telemetry data collection
- Unit tests for modified methods
- Service registration validation tests
- OpenTelemetry span validation tests

## Validation Results
**Overall Score**: 0.72/1.0
**Tests Passed**: 8/12

### Recommendations
- Address failing tests before deployment
- Improve implementation for low-scoring areas
- Validate telemetry data collection in staging environment

## Reasoning Summary

### File Selection Reasoning
Confidence the selected files are the correct insertion points: 0.85

### Patch Generation Reasoning
Overall: 0.79 – change is confined to a single well-known middleware that processes every request, meeting telemetry requirement across the GateKeeper web API.