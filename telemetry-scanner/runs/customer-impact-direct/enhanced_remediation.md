The implementation introduces a single, reusable enrichment point that guarantees every span created in the service carries customer.id and account.id attributes.

1. Context resolution  
   • `ICurrentCustomerContext` abstracts how the two identifiers are obtained.  
   • `CurrentCustomerContext` provides a default, HTTP-claim based implementation.

2. Span enrichment helper  
   • `ActivityExtensions.EnrichWithCustomerContext` sets the two attributes in a null-safe way.  
   • The helper can be called right after every `ActivitySource.StartActivity` invocation or from processors/listeners if preferred.

3. DI registration  
   • `Program.cs` now registers both `IHttpContextAccessor` and `ICurrentCustomerContext`, making the context injectable everywhere.

These three changes are enough to start adding `span.EnrichWithCustomerContext(_customerContext);` to each existing StartActivity call without boilerplate duplications.