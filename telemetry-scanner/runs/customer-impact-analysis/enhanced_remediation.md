To guarantee that every span emitted by the service contains `customer.id` and `account.id`, we add a dedicated `CustomerAttributeProcessor`.  
The processor is registered with OpenTelemetry during application start-up and enriches every non-internal Activity (span) **as soon as it starts**:

1. It tries to obtain the current `HttpContext` through `IHttpContextAccessor`.
2. It extracts the customer and account identifiers from:
   • HTTP headers `X-Customer-Id` / `X-Account-Id`  
   • Authenticated user claims (`customer_id`, `customerId`, `cid`, `account_id`, `accountId`, `aid`)
3. If either value is found, it sets the span attributes `customer.id` and `account.id`.

Because the processor runs for *all* Activities, the attributes will also propagate to any child spans created afterwards.