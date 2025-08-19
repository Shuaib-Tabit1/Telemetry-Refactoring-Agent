```csharp

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Data;
using System.Data.Common;
using System.Reflection;
using System.Threading;
using System.Threading.Tasks;
using System.Reactive.Linq;
using System.Reactive.Disposables;

using ADEXS.Core.Util.Config;
using ADEXS.Core.Util.Core;
using ADEXS.Core.Util.Loggers;
using ADEXS.Core.Util.ServiceLocator;
using DocuSign.Monitoring;
using log4net;

#if !NET
using System.ServiceProcess;
#endif

namespace ADEXS.ServiceFramework
{
    /// <summary>
    /// Base class to subclass for services.  Handles the managing of worker processes,
    /// worker groups, and remotable objects via the Register* methods.
    /// Also initializes telemetry instrumentation for stored‐procedure database calls.
    /// </summary>
    public abstract class ScmServicedComponent : IServicedComponent, IDisposable
    {
        public const int EXIT_FAIL_TO_BOOTSTRAP = 1;
        public const int EXIT_FAIL_TO_START = 2;
        public const int EXIT_FAIL_HELTH_CHECK = 3;
        public const int EXIT_FAIL_TO_BEFORE_START = 4;

        // core logger
        protected static readonly IDiscreetLogger _log = DiscreetLogger.GetLogger(typeof(ScmServicedComponent));
        private bool _running = false;
        protected List<AbstractServiceWorkerGroup> _groups = new List<AbstractServiceWorkerGroup>();
        protected List<AbstractServiceWorker> _workers = new List<AbstractServiceWorker>();

        // ActivitySource for manual DB instrumentation (fallback)
        private static readonly ActivitySource DbActivitySource = new ActivitySource("CLM.Service.Database");

        // subscription for diagnostic listeners
        private IDisposable _diagListenerSubscription;

        public ScmServicedComponent()
        {
            // Subscribe to DiagnosticListener to catch ADO.NET events
            _diagListenerSubscription = DiagnosticListener.AllListeners
                .Subscribe(new DbDiagnosticListener());
        }

        public bool Join(int joinTimeout)
        {
            foreach (AbstractServiceWorker worker in _workers)
            {
                if (!worker.Join(joinTimeout)) return false;
            }
            foreach (AbstractServiceWorkerGroup group in _groups)
            {
                if (!group.Join(joinTimeout)) return false;
            }
            return true;
        }

        /// <summary>
        /// Starts the worker, and adds it to the management pool.
        /// </summary>
        public AbstractServiceWorker RegisterWorker(AbstractServiceWorker worker)
        {
            _workers.Add(worker);
            worker.Start();
            return worker;
        }
        /// <summary>
        /// Creates a worker of the specified type, and adds it to the management pool.
        /// </summary>
        public AbstractServiceWorker RegisterWorker(Type workerType)
        {
            Type baseType = typeof(AbstractServiceWorker);
            if (!workerType.IsSubclassOf(baseType))
                throw new ArgumentException($"Type {workerType.Name} does not subclass expected type {baseType.Name}");

            ConstructorInfo constructor = workerType.GetConstructor(new Type[] { GetType() });
            if (constructor == null)
                throw new ArgumentException($"Type {workerType.Name} does not contain a (ScmServicedComponent) constructor");

            AbstractServiceWorker worker = (AbstractServiceWorker)constructor.Invoke(new object[] { this });
            return RegisterWorker(worker);
        }
        /// <summary>
        /// Creates a worker that will call the passed in delegates, and adds it to the management pool.
        /// </summary>
        public AbstractServiceWorker RegisterWorker(string name, DelegateServiceWorker.RunDelegate runDelegate, DelegateServiceWorker.SleepSecondsDelegate sleepSecondsDelegate)
        {
            DelegateServiceWorker worker = new DelegateServiceWorker(name, this, runDelegate, sleepSecondsDelegate);
            return RegisterWorker(worker);
        }

        /// <summary>
        /// Starts the workers in the group, and adds the group and workers to the management pool.
        /// </summary>
        public AbstractServiceWorkerGroup RegisterWorkerGroup(AbstractServiceWorkerGroup group)
        {
            _groups.Add(group);
            group.AdjustWorkers();
            return group;
        }
        /// <summary>
        /// Creates a worker group of the specified type, and adds it to the management pool.
        /// </summary>
        public AbstractServiceWorkerGroup RegisterWorkerGroup(Type groupType)
        {
            Type baseType = typeof(AbstractServiceWorkerGroup);
            if (!groupType.IsSubclassOf(baseType))
                throw new ArgumentException($"Type {groupType.Name} does not subclass expected type {baseType.Name}");

            ConstructorInfo constructor = groupType.GetConstructor(new Type[] { GetType() });
            if (constructor == null)
                throw new ArgumentException($"Type {groupType.Name} does not contain a (ScmServicedComponent) constructor");

            AbstractServiceWorkerGroup group = (AbstractServiceWorkerGroup)constructor.Invoke(new object[] { this });
            return RegisterWorkerGroup(group);
        }
        /// <summary>
        /// Creates a worker group that will call the passed in delegates, and adds it to the management pool.
        /// </summary>
        public AbstractServiceWorkerGroup RegisterWorkerGroup(
            string groupName,
            string workerName,
            DelegateServiceWorkerGroup.DesiredWorkerCountDelegate desiredWorkerCountDelegate,
            DelegateServiceWorker.RunDelegate runDelegate,
            DelegateServiceWorker.SleepSecondsDelegate sleepSecondsDelegate)
        {
            DelegateServiceWorkerGroup group = new DelegateServiceWorkerGroup(
                groupName, workerName, this, desiredWorkerCountDelegate, runDelegate, sleepSecondsDelegate);
            return RegisterWorkerGroup(group);
        }

        public void UnRegisterWorkerGroup(AbstractServiceWorkerGroup group)
        {
            for (int i = 0; i < _groups.Count; i++)
            {
                if (_groups[i] == group)
                {
                    _groups[i].Stop();
                    _groups.RemoveAt(i);
                    break;
                }
            }
        }

        /// <summary>
        /// Called by the ServiceInvocationFramework when the service is started
        /// </summary>
        public void Run()
        {
            _log.InfoNoPII($"This is {Process.GetCurrentProcess().ProcessName} {GetType().Assembly.GetName().Version} © SpringCM {DateTime.UtcNow:yyyy}.");

            if (ConfigWrapper.UseOneConfig)
                BootstrapServices();

            try
            {
                OnBeforeRun();
            }
            catch (Exception e)
            {
                _log.FatalNoPII("OnBeforeRun failed", e);
                Exit(EXIT_FAIL_TO_BEFORE_START);
            }

            if (!ConfigWrapper.UseOneConfig)
                BootstrapServices();

            if (Configuration.GetBooleanAppSetting("DebugOnStartup", false))
                System.Diagnostics.Debugger.Launch();

            RunHealthCheck();

            _log.WarnNoPII("Starting service.");

            AppDomain.CurrentDomain.UnhandledException += new UnhandledExceptionEventHandler(appDomain_UnhandledException);

            _running = true;
            InitializeFeatureFlags();

            try
            {
                OnRun();
            }
            catch (Exception e)
            {
                _log.FatalNoPII("OnRun failed", e);
                Exit(EXIT_FAIL_TO_START);
            }

            StartManager();
            StartAll();
            _log.InfoNoPII($"{_workers.Count} workers and {_groups.Count} groups running.");
        }

        protected virtual List<IServiceRegistry> GetServiceRegistries() => new List<IServiceRegistry>();

        public static void appDomain_UnhandledException(object sender, UnhandledExceptionEventArgs e)
        {
            string senderTxt = $"{sender.GetType().FullName} ({sender})".Replace('\n', ' ').Replace("\r", "");
            Exception ex;
            string msg;
            if (e.ExceptionObject is Exception exception)
            {
                msg = $"Unhandled exception from '{senderTxt}'. IsTerminating: {e.IsTerminating}";
                ex = exception;
            }
            else
            {
                msg = $"Unhandled exception from '{senderTxt}' with exception object '{e.ExceptionObject.GetType().FullName}'. IsTerminating: {e.IsTerminating}.";
                ex = new Exception(msg);
            }

            if (e.IsTerminating)
                _log.FatalNoPII(msg, ex);
            else
                _log.ErrorNoPII(msg, ex);
        }

        public bool Running => _running;

        public void Stop()
        {
            _log.WarnNoPII("Stopping service.");

            if (Configuration.GetBooleanAppSetting("EnableServicesForcedShutdown", false) ||
                Configuration.GetBooleanAppSetting($"EnableServiceForcedShutdown_{AppConfig.AppName()}", false))
            {
                int delay = Configuration.GetInt32AppSetting("ForcedShutdownDelay", 600000);
                Task.Delay(delay).ContinueWith(x => ScmServicedComponent.ForcedShutdown(),
                    CancellationToken.None, TaskContinuationOptions.None, TaskScheduler.Default);
            }

            try
            {
                OnBeforeStop();
            }
            catch (Exception e)
            {
                _log.ErrorNoPII("OnBeforeStop failed", e);
            }

            _running = false;
            StopManager();
            StopAll();

            try
            {
                OnStop();
            }
            catch (Exception e)
            {
                _log.ErrorNoPII("OnStop failed", e);
            }

            _log.InfoNoPII("Stopping code completed.");
        }

#if NET
        public bool IsService() => true;
#else
        private bool _isService;
        public bool IsService()
        {
            if (!_isService)
            {
                try
                {
                    Assembly entryAssembly = Assembly.GetEntryAssembly();
                    MethodInfo methodInfo = entryAssembly.EntryPoint;
                    Type entryType = methodInfo.DeclaringType;
                    _isService = typeof(ServiceBase).IsAssignableFrom(entryType);
                }
                catch (Exception ex)
                {
                    _log.ErrorNoPII("Failed to determine if this is service execution.", ex);
                }
            }
            return _isService;
        }
#endif

        public virtual void RunHealthCheck() { }

        public virtual void InitializeFeatureFlags() { }

        protected virtual void OnBeforeRun() { }

        protected abstract void OnRun();

        protected abstract void OnStop();

        protected virtual void OnBeforeStop() { }

        protected virtual void Exit(int exitCode)
        {
            LogManager.Shutdown();
            Thread.Sleep(TimeSpan.FromSeconds(5));
            Environment.Exit(exitCode);
        }

        private void StartAll()
        {
            _log.DebugNoPII($"This service appears to be on a system with {Environment.ProcessorCount} ProcessorCount.");
            foreach (AbstractServiceWorker worker in _workers) worker.Start();
            foreach (AbstractServiceWorkerGroup group in _groups) group.Start(group.Name);
        }

        private void StopAll()
        {
            if (Configuration.GetBooleanAppSetting("EnableFastShutdown", true))
            {
                _log.InfoNoPII("Stopping workers.");
                Parallel.ForEach(_workers, x => x.Stop());
                _log.InfoNoPII("Stopping groups.");
                Parallel.ForEach(_groups, x => x.Stop());
            }
            else
            {
                _log.InfoNoPII("Stopping workers.");
                foreach (AbstractServiceWorker worker in _workers) worker.Stop();
                _log.InfoNoPII("Stopping groups.");
                foreach (AbstractServiceWorkerGroup group in _groups) group.Stop();
            }
        }

        private void StartManager()
        {
            try
            {
                foreach (AbstractServiceWorker worker in _workers)
                {
                    if (worker is ThreadManagerWorker)
                    {
                        worker.Start();
                        return;
                    }
                }
                RegisterWorker(new ThreadManagerWorker(this));
            }
            catch (Exception e)
            {
                _log.ErrorNoPII($"Could not start {nameof(ThreadManagerWorker)}", e);
            }
        }

        private void StopManager()
        {
            _log.InfoNoPII("Stopping Manager.");
            try
            {
                foreach (AbstractServiceWorker worker in _workers)
                {
                    if (worker is ThreadManagerWorker)
                    {
                        worker.Stop();
                    }
                }
            }
            catch (Exception e)
            {
                _log.ErrorNoPII($"Could not stop {nameof(ThreadManagerWorker)}", e);
            }
        }

        private static void ForcedShutdown()
        {
            _log.ErrorNoPII("Forced shutdown triggered");
            Process currentProcess = Process.GetCurrentProcess();
            try
            {
                ProcessThreadCollection threads = currentProcess.Threads;
                foreach (ProcessThread thread in threads)
                {
                    if (!thread.ThreadState.HasFlag(ThreadState.Terminated))
                    {
                        _log.WarnNoPII($"Thread ID: {thread.Id}, State: {thread.ThreadState}");
                    }
                }
            }
            catch (Exception e)
            {
                _log.ErrorNoPII("Failed to get running threads", e);
            }
            currentProcess.Kill();
        }

        protected virtual bool ShouldAdjustWorkers(AbstractServiceWorkerGroup group)
        {
            return group.WorkerCount != group.GetDesiredWorkerCount();
        }

        private void BootstrapServices()
        {
            try
            {
                Bootstrapper.Bootstrap(GetServiceRegistries);
            }
            catch (Exception e)
            {
                _log.FatalNoPII("Failed to bootstrap", e);
                Exit(EXIT_FAIL_TO_BOOTSTRAP);
            }
        }

        /// <summary>
        /// Observes DiagnosticListeners for ADO.NET commands and instruments stored-procedure calls.
        /// </summary>
        private class DbDiagnosticListener : IObserver<DiagnosticListener>
        {
            public void OnCompleted() { }
            public void OnError(Exception error) { }
            public void OnNext(DiagnosticListener listener)
            {
                // Listen to both SqlClient and Microsoft.Data.SqlClient diagnostic sources
                if (listener.Name == "System.Data.SqlClient" ||
                    listener.Name == "Microsoft.Data.SqlClient")
                {
                    listener.Subscribe(new DbCommandObserver());
                }
            }
        }

        /// <summary>
        /// Observes command execution events and adds a "db.procedure" attribute when the command is a stored procedure.
        /// </summary>
        private class DbCommandObserver : IObserver<KeyValuePair<string, object>>
        {
            public void OnCompleted() { }
            public void OnError(Exception error) { }

            public void OnNext(KeyValuePair<string, object> kv)
            {
                // Event names differ by provider; these are the typical names
                if (kv.Key.EndsWith("Write.CommandExecuting") || kv.Key.EndsWith("WriteCommandBefore"))
                {
                    var cmdObj = kv.Value.GetType().GetProperty("Command")?.GetValue(kv.Value) as DbCommand;
                    if (cmdObj != null && cmdObj.CommandType == CommandType.StoredProcedure)
                    {
                        // If an Activity has been started by OpenTelemetry SQL instrumentation, decorate it
                        var current = Activity.Current;
                        if (current != null)
                        {
                            current.SetTag("db.procedure", cmdObj.CommandText);
                        }
                        else
                        {
                            // fallback: start a span around this command execution
                            var activity = DbActivitySource.StartActivity(cmdObj.CommandText, ActivityKind.Client);
                            if (activity != null)
                            {
                                activity.SetTag("db.system", "mssql");
                                activity.SetTag("db.procedure", cmdObj.CommandText);
                                // Note: the ended Activity will close on the corresponding Executed event
                            }
                        }
                    }
                }
                else if (kv.Key.EndsWith("Write.CommandExecuted") ||
                         kv.Key.EndsWith("WriteCommandAfter") ||
                         kv.Key.EndsWith("Write.CommandFailed"))
                {
                    // Close fallback activity if any
                    var current = Activity.Current;
                    if (current != null && current.Source.Name == DbActivitySource.Name)
                    {
                        current.Stop();
                    }
                }
            }
        }

        /// <summary>
        /// Internal worker used to keep track of the other workers and make sure no
        /// threads exit unexpectedly, and that worker groups have the correct
        /// number of workers.
        /// </summary>
        private class ThreadManagerWorker : AbstractServiceWorker
        {
            [EventSource("Dead Workers", "CLM.Service")]
            [Counter("Dead Workers", "CLM.Service",
                InstanceProperty = "Description",
                DisplayUnit = CounterUnit.__none,
                Ranges = new double[] { 1, 5, 10, 15, 20, 30, 50 },
                MeasureProperty = "Count")]
            private static readonly CountEventSource _deadWorkersCountEventSource = new CountEventSource();

            [EventSource("MissedHeartBeat Workers", "CLM.Service")]
            [Counter("MissedHeartBeat Workers", "CLM.Service",
                InstanceProperty = "Description",
                DisplayUnit = CounterUnit.__none,
                Ranges = new double[] { 1, 5, 10, 15, 20, 30, 50 },
                MeasureProperty = "Count")]
            private static readonly CountEventSource _noHeartBeatWorkersCountEventSource = new CountEventSource();

            public ThreadManagerWorker(ScmServicedComponent component)
                : base(component)
            {
                _scmServicedComponent = component;
            }

            private readonly ScmServicedComponent _scmServicedComponent = null;

            public override bool HasHeartBeat() => true;

            public override void Run()
            {
                _log.DebugNoPII($"Checking for unresponsive workers.");
                CheckWorkersHeartBeat();
                CheckForDeadWorkerThreads();
                AdjustWorkersIfNecessary();
            }

            private void CheckWorkersHeartBeat()
            {
                foreach (AbstractServiceWorker worker in _scmServicedComponent._workers)
                {
                    if (worker.MonitorHeartBeat && !worker.HasHeartBeat())
                    {
                        _noHeartBeatWorkersCountEventSource.Emit(1, worker.Name);
                        if (worker.TerminateOnHeartBeatMissing)
                        {
                            worker.AbortWorkerThread();
                        }
                    }
                }
                foreach (AbstractServiceWorkerGroup group in _scmServicedComponent._groups)
                {
                    int noBeatsCount = group.CheckWorkersHeartBeat();
                    if (noBeatsCount > 0)
                    {
                        _noHeartBeatWorkersCountEventSource.Emit(noBeatsCount, group.Name);
                    }
                }
            }

            private void CheckForDeadWorkerThreads()
            {
                foreach (AbstractServiceWorker worker in _scmServicedComponent._workers)
                {
                    if (worker.IsDead)
                    {
                        _log.WarnNoPII($"Found a dead worker: {worker.Name}. Restarting it.");
                        worker.Start();
                        _deadWorkersCountEventSource.Emit(1, worker.Name);
                    }
                }
                foreach (AbstractServiceWorkerGroup group in _scmServicedComponent._groups)
                {
                    int deadWorkers = group.RemoveDeadWorkers();
                    if (deadWorkers > 0)
                    {
                        _deadWorkersCountEventSource.Emit(deadWorkers, group.Name);
                    }
                }
            }

            private void AdjustWorkersIfNecessary()
            {
                foreach (AbstractServiceWorkerGroup group in _scmServicedComponent._groups)
                {
                    if (_scmServicedComponent.ShouldAdjustWorkers(group))
                    {
                        _log.WarnNoPII($"Group {group.Name} should have {group.GetDesiredWorkerCount()} workers, but has {group.WorkerCount}. Adjusting.");
                        group.AdjustWorkers();
                    }
                }
            }

            public override int SleepSeconds()
            {
                return Configuration.GetInt32AppSetting($"ClmService_{nameof(ThreadManagerWorker)}_SleepSeconds", 30);
            }
        }

        /// <summary>
        /// Clean up the diagnostic listener subscription.
        /// </summary>
        public void Dispose()
        {
            _diagListenerSubscription?.Dispose();
        }
    }
}

```

### Explanation

- Added a static `ActivitySource DbActivitySource` named `"CLM.Service.Database"` for fallback span creation around stored‐procedure calls.
- Subscribed in the constructor to `DiagnosticListener.AllListeners` with a private `DbDiagnosticListener` that listens for ADO.NET events from both `System.Data.SqlClient` and `Microsoft.Data.SqlClient`.
- Implemented `DbCommandObserver` to intercept `"Write.CommandExecuting"` (or legacy `"WriteCommandBefore"`) events, detect when `DbCommand.CommandType == StoredProcedure`, and then:
  - If an `Activity` is already in flight (e.g. via standard OpenTelemetry SQL instrumentation), decorates it with a `db.procedure` tag.
  - Otherwise, starts a new client‐kind `Activity`, sets `db.system` and `db.procedure`, and closes it on the corresponding `"Write.CommandExecuted"`/failure event.
- Ensured clean disposal of the listener subscription via `IDisposable`.
- Left the rest of the original service‐lifecycle and threading logic intact.