```diff
--- /dev/null
+++ b/Telemetry/TelemetryExtensions.cs
@@
+using System;
+using OpenTelemetry.Instrumentation.RabbitMQ.Client;
+using OpenTelemetry.Trace;
+
+namespace ADEXS.ServiceFramework.Telemetry
+{
+	/// <summary>
+	/// Extension methods for wiring up OpenTelemetry instrumentation that the application
+	/// relies on.  By keeping this in a dedicated method we make it simple for every
+	/// service to opt-in to the same baseline instrumentation set while giving each
+	/// service the flexibility to compose its own <see cref="TracerProviderBuilder"/>.
+	/// </summary>
+	public static class TelemetryExtensions
+	{
+		/// <summary>
+		/// Adds the default set of messaging-related instrumentations (currently RabbitMQ)
+		/// to the supplied <see cref="TracerProviderBuilder"/>.
+		/// </summary>
+		/// <param name="builder">The <see cref="TracerProviderBuilder"/> being configured.</param>
+		/// <returns>The same builder instance so that calls can be chained.</returns>
+		/// <exception cref="ArgumentNullException">Thrown when <paramref name="builder"/> is <c>null</c>.</exception>
+		public static TracerProviderBuilder AddMessagingInstrumentation(this TracerProviderBuilder builder)
+		{
+			if (builder == null) throw new ArgumentNullException(nameof(builder));
+
+			// Capture publish / consume operations performed through RabbitMQ.Client and enrich the resulting
+			// spans with the standard OpenTelemetry messaging semantic attributes such as:
+			//   • messaging.system                = "rabbitmq"
+			//   • messaging.destination           = &lt;queue / exchange name&gt;
+			//   • messaging.destination_kind      = "queue" | "exchange"
+			//   • messaging.rabbitmq.routing_key  = &lt;routing key used&gt;
+			//
+			// The library automatically populates these attributes; we simply need to register it.
+			return builder.AddRabbitMQClientInstrumentation();
+		}
+	}
+}
```

### Explanation
1. Added a new `Telemetry/TelemetryExtensions.cs` file that introduces an extension method `AddMessagingInstrumentation`.
2. Inside this method we register `AddRabbitMQClientInstrumentation()` against the provided `TracerProviderBuilder`.
3. This ensures RabbitMQ publish/consume spans are automatically captured and enriched with the OpenTelemetry messaging semantic-convention attributes (`messaging.system`, `messaging.destination`, `messaging.destination_kind`, `messaging.rabbitmq.routing_key`), making them visible with full metadata in back-ends like Jaeger.