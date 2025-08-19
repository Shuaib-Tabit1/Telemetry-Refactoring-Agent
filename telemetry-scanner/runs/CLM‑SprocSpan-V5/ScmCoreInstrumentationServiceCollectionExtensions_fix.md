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
using OpenTelemetry.Instrumentation.SqlClient;

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

            // https://devblogs.microsoft.com/azure-sdk/introducing-experimental-opentelemetry-support-in-the-azure-sdk-for-net/
            AppContext.SetSwitch("Azure.Experimental.EnableActivitySource", true);

            var telemetryConsoleTargets = configuration.GetSection("Telemetry:Console:Targets")?.Get<ConsoleExporterOutputTargets?>();

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

                    // Enable azure tracing.
                    options.AddSource("Azure.*");

                    // Enable telemetry in end to end tests.
                    options.AddSource("Xunit.DependencyInjection");

                    options.AddHttpClientInstrumentation();
                    options.ConfigureRedisCacheInstrumentation();
                    options.AddScmCassandraPersistenceInstrumentation();
                    options.AddRabbitMQInstrumentation();

                    // Add SQL client instrumentation and enrich stored-proc spans with the sproc name
                    options.AddSqlClientInstrumentation(sqlOptions =>
                    {
                        // preserve the raw command text if needed
                        sqlOptions.SetDbStatementForText = true;

                        // Enrich activity with the stored procedure name
                        sqlOptions.Enrich = (activity, eventName, rawObject) =>
                        {
                            if (rawObject is DbCommand command
                                && command.CommandType == CommandType.StoredProcedure
                                && !string.IsNullOrWhiteSpace(command.CommandText))
                            {
                                activity.SetTag("db.sql.sproc_name", command.CommandText);
                            }
                        };
                    });

                    configureTracer?.Invoke(options);

                    if (telemetryConsoleTargets != null)
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
                    options.SetExemplarFilter(ExemplarFilterType.TraceBased);
                    options.AddSqlClientInstrumentation();

                    configureMeter?.Invoke(options);

                    if (telemetryConsoleTargets != null)
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
- Added `using System.Data;` and `using System.Data.Common;` to access `DbCommand` and `CommandType`.
- Imported `OpenTelemetry.Instrumentation.SqlClient` so we can configure SQL client tracing.
- In the tracer setup (`configureTracer`), inserted `options.AddSqlClientInstrumentation(...)`:
  - Set `SetDbStatementForText = true` to retain the command text for visibility.
  - Provided an `Enrich` callback that checks if the `DbCommand` is a stored procedure (`CommandType.StoredProcedure`) and, if so, sets the `db.sql.sproc_name` tag from `command.CommandText`.
- This ensures every SQL span for stored-proc execution carries the `db.sql.sproc_name` attribute in Jaeger/OTel traces.