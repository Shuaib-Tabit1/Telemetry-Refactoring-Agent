```diff
--- a/Program.cs
+++ b/Program.cs
@@
 
 using Microsoft.AspNetCore.Builder;
 using Microsoft.Extensions.DependencyInjection;
+using Microsoft.AspNetCore.Http;
+using OpenTelemetry.Trace;
+using System.Diagnostics;
 
 const string serviceName = "clm-esignature";
 
 var builder = ScmWebApplication.CreateScmService(args);
@@
 builder.Services.AddComponentsInstrumentation();
 
 builder.Services.AddServicedComponent<ESignatureComponent>();
+
+// ---------------------------------------------------------------------------
+// OpenTelemetry span enrichment for incoming ASP.NET Core HTTP requests.
+// Adds:
+//   • http.referer                     – value of the incoming "Referer" header
+//   • http.response.redirect_location  – value of the outgoing "Location" header
+// ---------------------------------------------------------------------------
+builder.Services.AddOpenTelemetryTracing(tracerProviderBuilder =>
+{
+    tracerProviderBuilder
+        // The instrumentation itself may have already been registered by
+        // AddComponentsInstrumentation(); we register it again here only to
+        // supply a custom Enrich delegate.  Multiple registrations are safe
+        // and the SDK will merge the options.
+        .AddAspNetCoreInstrumentation(options =>
+        {
+            options.Enrich = static (activity, eventName, rawObject) =>
+            {
+                if (activity is null || rawObject is null)
+                {
+                    return;
+                }
+
+                switch (eventName)
+                {
+                    // Capture the incoming "Referer" header.
+                    case "OnStartActivity" when rawObject is HttpRequest request:
+                        if (request.Headers.TryGetValue("Referer", out var refererValues))
+                        {
+                            var referer = refererValues.ToString();
+                            if (!string.IsNullOrWhiteSpace(referer))
+                            {
+                                activity.SetTag("http.referer", referer);
+                            }
+                        }
+                        break;
+
+                    // Capture the outgoing "Location" header (typically on 3xx responses).
+                    case "OnStopActivity" when rawObject is HttpResponse response:
+                        if (response.Headers.TryGetValue("Location", out var locationValues))
+                        {
+                            var location = locationValues.ToString();
+                            if (!string.IsNullOrWhiteSpace(location))
+                            {
+                                activity.SetTag("http.response.redirect_location", location);
+                            }
+                        }
+                        break;
+                }
+            };
+        });
+});
 
 var app = builder.Build();
 
 app.UseCommonScmServices();
 app.MapServiceHealthChecks();
```

