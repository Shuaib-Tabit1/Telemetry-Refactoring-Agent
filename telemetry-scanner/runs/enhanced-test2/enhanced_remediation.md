ADEXS already enriches all server–side spans through `ActivityEnricher.SetTagsWithCommonFields`.  
Adding the two required attributes is therefore only a matter of:

1. Extending the shared OpenTelemetry semantic-convention helper so that the attribute
   names can be referenced from a single place.
2. Reading the headers from the current `HttpContext` (request and response) and
   calling `Activity.SetTag(...)`.

Because `SetTagsWithCommonFields` is invoked **after** the HTTP pipeline has finished
(the method already reads `context.Response.StatusCode`), both the incoming **Referer**
request header and the **Location** response header are available.