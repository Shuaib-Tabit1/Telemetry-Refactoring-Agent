```diff
--- a/Program.cs
+++ b/Program.cs
@@
 using Microsoft.AspNetCore.Mvc.Infrastructure;
 using Microsoft.AspNetCore.Mvc.Routing;
 using Microsoft.AspNetCore.Rewrite;
+using System.Diagnostics; // Needed for custom telemetry middleware
+using ADEXS.Web.Telemetry; // Namespace for the new middleware
 using Microsoft.Extensions.Caching.Memory;
 using Microsoft.Extensions.DependencyInjection;
 using Microsoft.Extensions.FileProviders;
@@
 
 app.UseProfileMiddleware();
 
+// Capture Referer & redirect location telemetry for BrowseDocuments legacy endpoint
+app.UseMiddleware<RefererAndRedirectTelemetryMiddleware>();
+
 HttpContextHelper.Configure(app.Services.GetRequiredService<IHttpContextAccessor>());
 
 app.Use(async (context, next) =>
 {
```

```diff
--- /dev/null
+++ b/Telemetry/RefererAndRedirectTelemetryMiddleware.cs
@@
+using System;
+using System.Diagnostics;
+using System.Threading.Tasks;
+using Microsoft.AspNetCore.Http;
+
+namespace ADEXS.Web.Telemetry
+{
+    /// <summary>
+    /// Middleware that enriches the current OpenTelemetry span / System.Activity
+    /// with:
+    ///   • HTTP_REFERER                       – value of the incoming HTTP Referer header
+    ///   • HTTP_RESPONSE_REDIRECT_LOCATION    – value of the Location header set on a 302 response
+    ///
+    /// The enrichment is only applied for the legacy BrowseDocuments endpoint
+    /// that still serves a 302 redirect (<service>/clm/Documents/BrowseDocuments.aspx).
+    /// </summary>
+    internal sealed class RefererAndRedirectTelemetryMiddleware
+    {
+        private readonly RequestDelegate _next;
+
+        public RefererAndRedirectTelemetryMiddleware(RequestDelegate next)
+        {
+            _next = next ?? throw new ArgumentNullException(nameof(next));
+        }
+
+        public async Task InvokeAsync(HttpContext context)
+        {
+            var activity = Activity.Current;
+
+            // Apply only if we are dealing with the legacy BrowseDocuments endpoint
+            var isBrowseDocumentsRequest =
+                context.Request.Path.Value?.EndsWith("/Documents/BrowseDocuments.aspx", StringComparison.OrdinalIgnoreCase) == true;
+
+            if (isBrowseDocumentsRequest && activity is { IsAllDataRequested: true })
+            {
+                AddRefererTag(context, activity);
+            }
+
+            await _next(context);
+
+            if (isBrowseDocumentsRequest && activity is { IsAllDataRequested: true })
+            {
+                AddRedirectLocationTag(context, activity);
+            }
+        }
+
+        private static void AddRefererTag(HttpContext context, Activity activity)
+        {
+            if (!activity.Tags.Any(t => t.Key == "HTTP_REFERER"))
+            {
+                var referer = context.Request.Headers["Referer"].ToString();
+                if (!string.IsNullOrWhiteSpace(referer))
+                {
+                    activity.SetTag("HTTP_REFERER", referer);
+                }
+            }
+        }
+
+        private static void AddRedirectLocationTag(HttpContext context, Activity activity)
+        {
+            if (context.Response.StatusCode == StatusCodes.Status302Found)
+            {
+                var location = context.Response.Headers["Location"].ToString();
+                if (!string.IsNullOrWhiteSpace(location))
+                {
+                    activity.SetTag("HTTP_RESPONSE_REDIRECT_LOCATION", location);
+                }
+            }
+        }
+    }
+}
```
### Explanation
1. **Program.cs**
   • Added `using` directives for `System.Diagnostics` and the new middleware namespace.  
   • Inserted `app.UseMiddleware<RefererAndRedirectTelemetryMiddleware>();` after existing profiling middleware so every request/response pair is enriched before other loggers run.

2. **Telemetry/RefererAndRedirectTelemetryMiddleware.cs**
   • New middleware that:
     – Checks for the legacy `…/Documents/BrowseDocuments.aspx` path.  
     – On request, captures the `Referer` header and tags the current `Activity` (`HTTP_REFERER`).  
     – After the downstream pipeline executes, if the response is a 302 redirect, captures the `Location` header and tags the `Activity` (`HTTP_RESPONSE_REDIRECT_LOCATION`).  

   • Ensures tags are only added when the `Activity` is collecting data (`IsAllDataRequested`).