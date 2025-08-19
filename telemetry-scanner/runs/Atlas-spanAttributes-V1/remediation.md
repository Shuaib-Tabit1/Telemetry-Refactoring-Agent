```diff
--- a/Program.cs
+++ b/Program.cs
@@
 app.UseProfileMiddleware();
 
 HttpContextHelper.Configure(app.Services.GetRequiredService<IHttpContextAccessor>());
 
 app.Use(async (context, next) =>
 {
+	// Capture referer header and potential redirect location for telemetry
+	// We run this *around* the request so we have access to both the request
+	// headers (for Referer) and the final response headers (for Location).
+	//
+	// NOTE: This must execute before any short–circuiting middleware
+	// that could return a redirect response, but after OpenTelemetry
+	// instrumentation has started the Activity for the request (so that
+	// Activity.Current is available).
+	await next();
+
+	// Only record attributes when the response is a redirect (3xx).
+	if (context.Response.StatusCode == StatusCodes.Status302Found
+	    || context.Response.StatusCode == StatusCodes.Status301MovedPermanently
+	    || context.Response.StatusCode == StatusCodes.Status307TemporaryRedirect
+	    || context.Response.StatusCode == StatusCodes.Status308PermanentRedirect)
+	{
+		var activity = System.Diagnostics.Activity.Current;
+		if (activity != null)
+		{
+			// Add the HTTP referer request header value, if present.
+			if (context.Request.Headers.TryGetValue("Referer", out var refererValue)
+			    && !string.IsNullOrWhiteSpace(refererValue))
+			{
+				activity.SetTag("http.referer", refererValue.ToString());
+			}
+
+			// Add the redirect target (Location response header).
+			if (context.Response.Headers.TryGetValue("Location", out var locationValue)
+			    && !string.IsNullOrWhiteSpace(locationValue))
+			{
+				activity.SetTag("http.response_redirect_location", locationValue.ToString());
+			}
+		}
+	}
+});
+
+app.Use(async (context, next) =>
+{
 	// Log the incoming X-Forwarded-For & X-Original-For headers (if any)
 	var xForwardedFor = context.Request.Headers[ForwardedHeadersDefaults.XForwardedForHeaderName].ToString();
 	var xOriginalFor = context.Request.Headers[ForwardedHeadersDefaults.XOriginalForHeaderName].ToString();
 	var remoteIp = context.Connection.RemoteIpAddress;
 	var logger = context.RequestServices.GetRequiredService<ILoggerFactory>().CreateLogger("ADEXS.Web.XForwardedLogger");
 
 	logger.LogInformation("Remote IP: {RemoteIp}, X-Forwarded-For: {XForwardedFor}, X-Original-For: {XOriginalFor}", remoteIp, xForwardedFor, xOriginalFor);
 
 	await next();
 });
```

