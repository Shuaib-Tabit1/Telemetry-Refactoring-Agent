```diff
--- a/ActivityExtensions.cs
+++ b/ActivityExtensions.cs
@@
 public static class ActivityExtensions
 {
+	// ---------------------------------------------------------------------
+	// HTTP specific semantic-convention attribute names
+	// ---------------------------------------------------------------------
+	private const string AttributeHttpReferer = "HTTP_REFERER";
+	private const string AttributeHttpResponseRedirectLocation = "HTTP_RESPONSE_REDIRECT_LOCATION";
+
 	public static Activity? SetQueueTaskTags<T>(this Activity? activity, T task)
 		where T : IQueueTask
 		=>
 		activity
 			?.SetTag(TraceSemanticConventions.AttributeMessageId, task.MessageId)
@@
 				?.SetTag(ServiceTraceSemanticConventions.AttributeDocuSignMessageResultMessage, result.Message)
 				?.SetTag(ServiceTraceSemanticConventions.AttributeDocuSignMessageLastErrorMessage, task.LastErrorMessage);
+
+	/// <summary>
+	/// Enriches an <see cref="Activity"/> representing an HTTP span with the request
+	/// &quot;Referer&quot; header and with the redirect &quot;Location&quot; response header (if present).
+	/// </summary>
+	/// <param name="activity">The span to enrich.</param>
+	/// <param name="refererHeader">
+	/// Value of the incoming HTTP request header &quot;Referer&quot;. Pass <c>null</c> if the header is not present.
+	/// </param>
+	/// <param name="redirectLocationHeader">
+	/// Value of the outgoing HTTP response header &quot;Location&quot; when a redirect occurs. Pass <c>null</c> if the header is not present.
+	/// </param>
+	/// <returns>The same <see cref="Activity"/> instance for method-chaining.</returns>
+	public static Activity? SetHttpRefererAndRedirectLocation(
+		this Activity? activity,
+		string? refererHeader,
+		string? redirectLocationHeader)
+		=> activity
+			?.SetTag(AttributeHttpReferer, refererHeader)
+			?.SetTag(AttributeHttpResponseRedirectLocation, redirectLocationHeader);
 }
 #nullable restore
```

### Explanation
1. Added two constant strings (`HTTP_REFERER`, `HTTP_RESPONSE_REDIRECT_LOCATION`) that follow the required attribute names so they can be reused consistently.
2. Introduced `SetHttpRefererAndRedirectLocation` extension method.  
   • Adds the `HTTP_REFERER` attribute when a request’s “Referer” header is available.  
   • Adds the `HTTP_RESPONSE_REDIRECT_LOCATION` attribute when a redirect response includes a “Location” header.  
   • Returns the same `Activity` instance to keep the fluent style used elsewhere in `ActivityExtensions.cs`.  
This provides a single, idiomatic way to enrich any HTTP span with the required headers, enabling downstream code to call this helper wherever HTTP activities are created or enriched.