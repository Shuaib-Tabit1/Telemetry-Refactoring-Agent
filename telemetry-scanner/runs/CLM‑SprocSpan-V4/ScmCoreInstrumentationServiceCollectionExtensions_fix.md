```csharp

using System;
using System.Data;
using System.Data.Common;
using ADEXS.Caching.OpenTelemetry.Extensions;
using ADEXS.CqlCorePersistence.OpenTelemetry;
using ADEXS.ServiceFramework.OpenTelemetry.HostedServices;
using DocuSign.Msf.AspNet.OpenTelemetry;
using DocuSign.Msf.AspNet.OpenTelemetry.ServiceMetrics.Extensions;
using DocuSign.Msf.OpenTelemetry.DotNet.Runtime;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using OpenTelemetry.Exporter;
using OpenTelemetry.Logs;
using OpenTelemetry.Metrics;
using OpenTelemetry.Trace;

namespace ADEXS.ServiceFramework.OpenTelemetry.Extensions
{
    /// <summary>
    /// Extensions for <see cref="IServiceCollection"/>.
    /// </summary>
    public static class ScmCoreInstrumentationServiceCollectionExtensions
    {
        /// <summary>
        /// Adds SCM core instrumentation.
        /// </summary>
        /// <param name="services">The service collection.</param>
        /// <param name="configuration">The configuration.</param>
        /// <param name="serviceName">The service name.</param>
        /// <param name="serviceVersion">The service version.</param>
        /// <param name="configureLogger">The logger configuration.</param>
        /// <param name="configureTracer">The tracer configuration.</param>
        /// <param name="configureMeter">The meter configuration.</param>
        /// <returns>
        /// A reference to the <paramref name="services"/> after the operation has completed.
        /// </returns>
        /// <exception cref="ArgumentNullException">
        /// When <paramref name="services"/> or <paramref name="configuration"/> is <see langword="null"/>.
        /// </exception>
        public static IServiceCollection AddScmCoreInstrumentation(
            this IServiceCollection services,
            IConfiguration configuration,
            string serviceName,
            string? serviceVersion = null,
            Action<OpenTelemetryLoggerOptions>? configureLogger = null,
            Action<TracerProviderBuilder>? configureTracer = null,
            Action<MeterProviderBuilder>? configureMeter = null)
        {
            if (services == null)
            {
                throw new ArgumentNullException(nameof(services));
            }

            if (configuration == null)
            {
                throw new ArgumentNullException(nameof(configuration));
            }

            // Enable experimental Azure SDK ActivitySource support.
            AppContext.SetSwitch("Azure.Experimental.EnableActivitySource", true);

            var telemetryConsoleTargets = configuration
                .GetSection("Telemetry:Console:Targets")
                ?.Get<ConsoleExporterOutputTargets?>();

            services.AddServiceTelemetry(
                serviceName,
                serviceVersion: serviceVersion,
                suppressHealthCheckTelemetry: false,
                configureLogger: configureLogger,
                configureTracer: options =>
                {
                    // CLM specific sources.
                    options.AddSource("Scm*");
                    options.AddSource("ADEXS.*");

                    // Enable Azure telemetry.
                    options.AddSource("Azure.*");

                    // Enable telemetry in end-to-end tests.
                    options.AddSource("Xunit.DependencyInjection");

                    options.AddHttpClientInstrumentation();
                    options.ConfigureRedisCacheInstrumentation();
                    options.AddScmCassandraPersistenceInstrumentation();
                    options.AddRabbitMQInstrumentation();

                    configureTracer?.Invoke(options);

                    if (telemetryConsoleTargets.HasValue)
                    {
                        options.AddConsoleExporter(o => o.Targets = telemetryConsoleTargets.Value);
                    }
                },
                configureMeter: options =>
                {
                    options.AddHttpClientInstrumentation();
                    options.AddServiceMetrics();
                    options.AddProcessInstrumentation();
                    options.AddDocuSignDotNetRuntimeInstrumentation();
                    options.AddCassandraInstrumentation();
                    options.AddScmCassandraPersistenceInstrumentation();
                    options.AddRedisCacheMetrics();

                    // Add SQL Client instrumentation with stored-procedure name tagging.
                    options.AddSqlClientInstrumentation(sqlOptions =>
                    {
                        sqlOptions.Enrich = (activity, eventName, rawObject) =>
                        {
                            if (rawObject is DbCommand command 
                                && command.CommandType == CommandType.StoredProcedure
                                && !string.IsNullOrEmpty(command.CommandText))
                            {
                                // Tag the span with the stored procedure name.
                                activity.SetTag("db.sql.stored_procedure", command.CommandText);
                            }
                        };
                    });

                    configureMeter?.Invoke(options);

                    if (telemetryConsoleTargets.HasValue)
                    {
                        options.AddConsoleExporter(o => o.Targets = telemetryConsoleTargets.Value);
                    }
                });

            services.AddSingleton<IHostedService, ScmCoreInstrumentationLifetimeHostedService>();

            return services;
        }
    }
}

```

### Explanation
- Imported `System.Data` and `System.Data.Common` to inspect `DbCommand` and its `CommandType`.
- In the meter configuration, replaced the plain `options.AddSqlClientInstrumentation()` call with a configured overload.
- Inside `sqlOptions.Enrich`, detected when a command is a stored-procedure (`CommandType.StoredProcedure`) and then added the `"db.sql.stored_procedure"` attribute using the command’s `CommandText` (the stored-procedure name).
- This ensures each SQL Client span for stored procedures carries the exact stored-procedure name in its attributes.