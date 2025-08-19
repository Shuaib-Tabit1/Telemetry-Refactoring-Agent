```csharp

using System;
using System.Reflection;
using System.Threading;
using System.Threading.Tasks;
using System.Data.Common;

using ADEXS.Core.Util.Config;
using ADEXS.Core.Util.Core;
using ADEXS.FeatureFlags;
using ADEXS.ServiceFramework.AspNetCore.HealthChecks;
using ADEXS.ServiceFramework.AspNetCore.Options;

using DocuSign.CLM.Monitoring;
using DocuSign.OneConfig.Extensions;

using log4net;

using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Hosting.WindowsServices;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;

using OpenTelemetry;
using OpenTelemetry.Resources;
using OpenTelemetry.Trace;

namespace ADEXS.ServiceFramework.AspNetCore.HostedServices
{
    /// <summary>
    /// Hosted service that runs for the lifetime of the SCM application.
    /// Adds OpenTelemetry tracing for any DbCommand (stored procedures, text commands) and
    /// exports spans (including db.statement) to Jaeger.
    /// </summary>
    internal sealed class ScmLifetimeHostedService : IHostedService, IDisposable
    {
        private readonly IScmLifetimeServiceStatus _scmLifetimeServiceStatus;
        private readonly IWatchedSingletonConfig<ISiteConfig> _siteConfig;
        private readonly IWatchedSingletonConfig<IAppConfig> _appConfig;
        private readonly IOptions<ScmLifetimeHostedServiceOptions> _options;
        private readonly ILogger _logger;

        // OpenTelemetry TracerProvider for auto-instrumentation
        private TracerProvider? _tracerProvider;

        private bool _isFeatureFlagsEnabled;
        private bool _isFeatureFlagsContextEnabled;

        public ScmLifetimeHostedService(
            IScmLifetimeServiceStatus scmLifetimeServiceStatus,
            IWatchedSingletonConfig<ISiteConfig> siteConfig,
            IWatchedSingletonConfig<IAppConfig> appConfig,
            IOptions<ScmLifetimeHostedServiceOptions> options,
            ILogger<ScmLifetimeHostedService> logger)
        {
            _scmLifetimeServiceStatus = scmLifetimeServiceStatus;
            _siteConfig = siteConfig;
            _appConfig = appConfig;
            _options = options;
            _logger = logger;
        }

        /// <inheritdoc />
        public Task StartAsync(CancellationToken cancellationToken)
        {
            try
            {
                var siteConfig = _siteConfig.Value;
                var appConfig = _appConfig.Value;

                _logger.LogInformation(
                    "Initializing http application on {EnvironmentType} {Environment} environment on {Site} site",
                    siteConfig.EnvironmentType,
                    siteConfig.Environment,
                    siteConfig.Site);

                var application = Environment.GetEnvironmentVariable("MONITORING_SYSTEM_APPLICATION") ?? appConfig.AppName;
                var site = siteConfig.Site;

                // 1) Initialize KazMon if configured
                if (_options.Value.KazMonMonitoringEnabled)
                {
                    var assembly = Assembly.GetEntryAssembly() ?? Assembly.GetExecutingAssembly();
                    var environment = Environment.GetEnvironmentVariable("MONITORING_SYSTEM_ENVIRONMENT") ?? siteConfig.Environment;
                    var partition = Environment.GetEnvironmentVariable("MONITORING_SYSTEM_PARTITION");

                    KazmonMonitoring.InitializeKazmon(
                        applicationName: application,
                        appVersion: assembly.GetName().Version!.ToString(),
                        environmentName: environment,
                        siteName: site,
                        partitionName: partition,
                        shouldEnableKazmon: () => Configuration.GetBooleanAppSetting("KazmonEnableMonitoring", true)
                                                  && Configuration.GetBooleanAppSetting($"EnableFeatureFlagsByAppName_{application}", true),
                        shouldEnableSmartMon: () => Configuration.GetBooleanAppSetting("SmartMonEnable", true),
                        shouldEnableLogFileListener: () => Configuration.GetBooleanAppSetting("KazmonEnableLogFileListener", false));
                }

                // 2) Initialize OpenTelemetry Tracing for DbCommand (SQL Client),
                //    automatically tags "db.statement" from DbCommand.CommandText
                if (_options.Value.EnableOpenTelemetryTracing)
                {
                    _tracerProvider = Sdk.CreateTracerProviderBuilder()
                        .SetResourceBuilder(
                            ResourceBuilder.CreateDefault()
                                .AddService(serviceName: application, serviceVersion: "1.0.0"))
                        .AddSqlClientInstrumentation(options =>
                        {
                            // This flag instructs the instrumentation to capture the full SQL/text command (e.g. sproc name)
                            options.SetDbStatementForText = true;
                            // commands that are stored procedures will carry db.system=sql-server and we will get db.statement
                        })
                        .AddJaegerExporter(jaegerOptions =>
                        {
                            jaegerOptions.AgentHost = _options.Value.JaegerHost;
                            jaegerOptions.AgentPort = _options.Value.JaegerPort;
                        })
                        .Build();

                    _logger.LogInformation("OpenTelemetry Tracing initialized (SQLClient auto-instrumentation).");
                }

                // 3) Feature flags
                _isFeatureFlagsEnabled = Configuration.GetBooleanAppSetting("EnableFeatureFlags", true)
                    && Configuration.GetBooleanAppSetting($"EnableFeatureFlagsByAppName_{application}", true);

                _isFeatureFlagsContextEnabled = Configuration.GetBooleanAppSetting("UseOneConfigOverDss", false);

                if (_isFeatureFlagsEnabled)
                {
                    FeatureFlagsBootstrap.Init(site);
                }
                else if (_isFeatureFlagsContextEnabled)
                {
                    FeatureFlagsBootstrap.InitializeContextOnly();
                }

                // mark ready
                _scmLifetimeServiceStatus.IsReady = true;
                _logger.LogInformation("Http application initialized");
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to start http application");

                // If running as a Windows service, exit to trigger recovery
                if (WindowsServiceHelpers.IsWindowsService())
                {
                    Environment.Exit(1);
                }

                throw;
            }

            return Task.CompletedTask;
        }

        /// <inheritdoc />
        public Task StopAsync(CancellationToken cancellationToken)
        {
            try
            {
                _logger.LogInformation("Stopping http application");

                // mark not ready
                _scmLifetimeServiceStatus.IsReady = false;

                // Dispose OpenTelemetry tracer provider to flush spans
                try
                {
                    _tracerProvider?.Dispose();
                    _logger.LogInformation("OpenTelemetry TracerProvider disposed.");
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "Error shutting down OpenTelemetry TracerProvider");
                }

                // Shutdown log4net
                try
                {
                    LogManager.Shutdown();
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "Error shutting down log4net");
                }

                // Uninitialize feature flags
                if (_isFeatureFlagsEnabled || _isFeatureFlagsContextEnabled)
                {
                    FeatureFlagsBootstrap.UnInitialize();
                }

                // Shutdown KazMon if it was started
                if (_options.Value.KazMonMonitoringEnabled)
                {
                    KazmonMonitoring.ShutdownKazmon();
                }

                _logger.LogInformation("Http application stopped");
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to stop http application");
                throw;
            }

            return Task.CompletedTask;
        }

        public void Dispose()
        {
            // Ensure tracer provider is disposed if StopAsync wasn't called
            _tracerProvider?.Dispose();
        }
    }
}

```

### Explanation

- Introduced OpenTelemetry dependencies (`OpenTelemetry`, `OpenTelemetry.Trace`, `OpenTelemetry.Resources`).
- Added a private `TracerProvider? _tracerProvider` to hold the OpenTelemetry pipeline.
- In `StartAsync`, after initializing KazMon, we check a new option flag `EnableOpenTelemetryTracing`. If enabled:
  - Build an OpenTelemetry `TracerProvider` that:
    - Automatically instruments all `DbCommand` operations via `AddSqlClientInstrumentation`.
    - Sets `SetDbStatementForText = true` so each SQL or stored-procedure call span gets a `db.statement` attribute containing the full `DbCommand.CommandText`.
    - Exports spans to Jaeger using host/port from configuration.
- On shutdown (`StopAsync` and `Dispose`), we dispose the `TracerProvider` so any buffered spans are flushed.
- This change ensures that every database call (including stored procedures) is captured as a span with the `db.statement` attribute set to the command text, meeting the instrumentation requirement.