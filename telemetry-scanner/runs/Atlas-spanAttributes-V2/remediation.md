```diff
--- a/Program.cs
+++ b/Program.cs
@@
 using Microsoft.Extensions.FileProviders;
 using Microsoft.Extensions.Hosting;
 using Microsoft.Extensions.Logging;
+using Microsoft.Extensions.Options;
 using Microsoft.IdentityModel.Logging;
 
 using Newtonsoft.Json;
 
+using OpenTelemetry.Instrumentation.AspNetCore;
+
 using Yarp.ReverseProxy.Forwarder;
@@
 builder.Services.AddHttpContextAccessor();
 builder.Services.AddSingleton<IActionContextAccessor, ActionContextAccessor>();
 builder.Services.AddRouting();
 builder.Services.AddSingleton<IUrlHelperFactory, UrlHelperFactory>();
 builder.Services.AddConditionalEndpoints<ConditionalEndpointSelector>();
+
+// ------------------------------------------------------------------------
+// OpenTelemetry enrichment:
+// Add Referer and Redirect Location headers to AspNetCore request spans.
+// This is achieved by configuring AspNetCoreInstrumentationOptions via the
+// options pattern so it will be applied regardless of where the
+// instrumentation is added.
+// ------------------------------------------------------------------------
+builder.Services.ConfigureOptions<RefererRedirectEnricherOptionsSetup>();
 
 builder.Services.AddWebCommonUi();
@@
 app.RunScmWebService();
 
+
+// ReSharper disable once ClassNeverInstantiated.Global
+file sealed class RefererRedirectEnricherOptionsSetup : IConfigureNamedOptions<AspNetCoreInstrumentationOptions>
+{
+	// Configure the default (unnamed) options instance
+	public void Configure(AspNetCoreInstrumentationOptions options) => Configure(Options.DefaultName, options);
+
+	// Configure a named options instance (name is ignored – we always apply)
+	public void Configure(string? name, AspNetCoreInstrumentationOptions options)
+	{
+		// Enrich span with the incoming HTTP Referer header
+		options.EnrichWithHttpRequest = (activity, request) =>
+		{
+			if (activity == null || request == null)
+			{
+				return;
+			}
+
+			if (request.Headers.TryGetValue("Referer", out var referer) && !string.IsNullOrWhiteSpace(referer))
+			{
+				activity.SetTag("http.referer", referer.ToString());
+			}
+		};
+
+		// Enrich span with the outgoing HTTP Location header (redirect target)
+		options.EnrichWithHttpResponse = (activity, response) =>
+		{
+			if (activity == null || response == null)
+			{
+				return;
+			}
+
+			if (response.Headers.TryGetValue("Location", out var location) && !string.IsNullOrWhiteSpace(location))
+			{
+				activity.SetTag("http.response.redirect_location", location.ToString());
+			}
+		};
+	}
+}
+
```

### Explanation
1. Added required `using` directives for `OpenTelemetry.Instrumentation.AspNetCore` and `Microsoft.Extensions.Options`.
2. Registered custom OpenTelemetry enrichment with `builder.Services.ConfigureOptions<RefererRedirectEnricherOptionsSetup>();`.
3. Implemented `RefererRedirectEnricherOptionsSetup`, an `IConfigureNamedOptions<AspNetCoreInstrumentationOptions>` that:
   • Adds `http.referer` attribute from the incoming `Referer` request header.  
   • Adds `http.response.redirect_location` attribute from the outgoing `Location` response header.
4. These enrichers automatically apply to all AspNetCore request spans, fulfilling the telemetry requirements without altering existing OpenTelemetry setup.