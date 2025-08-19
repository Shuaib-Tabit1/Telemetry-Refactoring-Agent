```diff
--- /dev/null
+++ b/Telemetry/RabbitMQInstrumentationExtensions.cs
@@
+using Microsoft.Extensions.DependencyInjection;
+using OpenTelemetry.Trace;
+using RabbitMQ.Client.Events;
+
+namespace ADEXS.ServiceFramework.Telemetry
+{
+    /// <summary>
+    /// Extension helpers to register RabbitMQ instrumentation with the
+    /// required OpenTelemetry semantic-convention attributes.
+    /// </summary>
+    public static class RabbitMQInstrumentationExtensions
+    {
+        /// <summary>
+        /// Adds OpenTelemetry tracing for RabbitMQ, ensuring that mandatory
+        /// messaging attributes are attached to every produced / consumed span.
+        /// Must be called during application start-up <c>IServiceCollection</c>
+        /// configuration.
+        /// </summary>
+        public static TracerProviderBuilder AddConfiguredRabbitMQInstrumentation(
+            this TracerProviderBuilder builder)
+        {
+            // Register official RabbitMQ instrumentation and enrich spans so that
+            // they always contain the standard messaging attributes, even when
+            // the underlying instrumentation fails to populate them.
+            return builder.AddRabbitMQInstrumentation(options =>
+            {
+                options.Enrich = static (activity, eventName, rawObject) =>
+                {
+                    if (activity == null)
+                    {
+                        return;
+                    }
+
+                    // OpenTelemetry semantic convention: the messaging system name
+                    activity.SetTag("messaging.system", "rabbitmq");
+
+                    switch (rawObject)
+                    {
+                        // Message was **published**
+                        case (string exchange, string routingKey, _):
+                            {
+                                activity.SetTag("messaging.destination_kind", "queue");
+                                activity.SetTag("messaging.destination", exchange);
+                                activity.SetTag("messaging.rabbitmq.routing_key", routingKey);
+                                break;
+                            }
+
+                        // Message was **consumed**
+                        case BasicDeliverEventArgs deliverArgs:
+                            {
+                                var routingKey = deliverArgs.RoutingKey;
+                                var queueName  = deliverArgs.Exchange; // Fallback when queue name is not available
+
+                                activity.SetTag("messaging.destination_kind", "queue");
+                                activity.SetTag("messaging.destination", queueName);
+                                activity.SetTag("messaging.rabbitmq.routing_key", routingKey);
+                                break;
+                            }
+                    }
+                };
+            });
+        }
+    }
+}
```

### Explanation
1. Introduced a new `Telemetry/RabbitMQInstrumentationExtensions.cs` file to encapsulate the RabbitMQ-specific OpenTelemetry setup.  
2. Added an extension method `AddConfiguredRabbitMQInstrumentation` that:
   • Calls `AddRabbitMQInstrumentation` to enable automatic producer / consumer spans.  
   • Supplies an `Enrich` delegate that attaches the standard messaging semantic-convention attributes:  
     - `messaging.system = rabbitmq`  
     - `messaging.destination` (queue / exchange name)  
     - `messaging.destination_kind = queue`  
     - `messaging.rabbitmq.routing_key`  
3. Handles both publish and consume scenarios using pattern matching on the `rawObject` provided by the instrumentation package.  
4. This unified diff is additive and non-breaking; consumers just chain `.AddConfiguredRabbitMQInstrumentation()` on their existing `TracerProviderBuilder`.