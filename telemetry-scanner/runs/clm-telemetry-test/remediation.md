```diff
--- /dev/null
+++ b/Clm.Web/Telemetry/RedirectFlowTelemetryMiddleware.cs
@@
+using System.Diagnostics;
+using System.Threading.Tasks;
+using Microsoft.AspNetCore.Http;
+using Microsoft.Extensions.Primitives;
+
+namespace Clm.Web.Telemetry
+{
+    /// <summary>
+    /// Middleware that enriches the automatically-generated
+    /// Microsoft.AspNetCore.Hosting.HttpRequestIn span with additional HTTP
+    /// redirect flow information (Referer & Location headers).
+    /// </summary>
+    internal sealed class RedirectFlowTelemetryMiddleware
+    {
+        private static readonly int[] _redirectStatusCodes = { 301, 302, 303, 307, 308 };
+
+        private readonly RequestDelegate _next;
+
+        public RedirectFlowTelemetryMiddleware(RequestDelegate next)
+        {
+            _next = next;
+        }
+
+        public async Task InvokeAsync(HttpContext context)
+        {
+            Activity? activity = Activity.Current;
+
+            // 1. Add the incoming request's Referer header (if any) as soon as possible
+            if (activity != null &&
+                context.Request.Headers.TryGetValue("Referer", out StringValues referer) &&
+                !StringValues.IsNullOrEmpty(referer))
+            {
+                // Semantic-convention compliant attribute name
+                activity.SetTag("http.request.header.referer", referer.ToString());
+            }
+
+            // 2. Register a callback that runs right before the response is sent
+            //    so that we can inspect the final status code and Location header.
+            context.Response.OnStarting(state =>
+            {
+                var (httpContext, requestActivity) = ((HttpContext, Activity?))state;
+
+                if (requestActivity != null &&
+                    Array.Exists(_redirectStatusCodes, sc => sc == httpContext.Response.StatusCode) &&
+                    httpContext.Response.Headers.TryGetValue("Location", out var location) &&
+                    !StringValues.IsNullOrEmpty(location))
+                {
+                    requestActivity.SetTag("http.response.header.location", location.ToString());
+                }
+
+                return Task.CompletedTask;
+            }, (context, activity));
+
+            await _next(context);
+        }
+    }
+}
+
--- a/Clm.Web/Startup.cs
+++ b/Clm.Web/Startup.cs
@@
         public void Configure(IApplicationBuilder app, IWebHostEnvironment env)
        {
             // existing middleware registrations …
 
+            // Enrich the incoming request spans with Referer & redirect Location information
+            app.UseMiddleware<Clm.Web.Telemetry.RedirectFlowTelemetryMiddleware>();
+
             app.UseRouting();
 
             // remaining middleware registrations …
        }
}
```

### Explanation
1. Introduced `RedirectFlowTelemetryMiddleware`:
   • Adds the incoming request’s “Referer” header to the current `Activity` under the semantic-convention key `http.request.header.referer`.  
   • Registers an `OnStarting` callback so that, for redirect status codes (301, 302, 303, 307, 308), the resulting “Location” response header is captured as `http.response.header.location`.

2. Updated `Startup.Configure` to insert this middleware early in the pipeline (just after any built-in middleware already present) ensuring every `Microsoft.AspNetCore.Hosting.HttpRequestIn` span created by the ASP.NET Core instrumentation receives the new attributes.