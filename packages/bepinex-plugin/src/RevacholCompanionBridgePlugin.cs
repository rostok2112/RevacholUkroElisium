using System;
using System.Threading.Tasks;
using BepInEx;
using BepInEx.Configuration;
using BepInEx.Unity.IL2CPP;

namespace Revachol.UkrainianCompanion.BepInExBridge
{
    [BepInPlugin(PluginGuid, PluginName, PluginVersion)]
    public sealed class RevacholCompanionBridgePlugin : BasePlugin
    {
        public const string PluginGuid = "local.revachol.ukrainian-companion.bridge";
        public const string PluginName = "Revachol Ukrainian Companion Bridge";
        public const string PluginVersion = "0.4.0-synthetic";

        public const string DefaultCompanionServerUrl = "http://127.0.0.1:8765";
        public const int DefaultRequestTimeoutMs = 3000;
        public const bool DefaultEnabled = true;
        public const bool DefaultSendSyntheticEventOnStart = false;
        public const bool DefaultMetadataProbeEnabled = false;
        public const bool DefaultMetadataProbeLogOnStart = false;
        public const bool DefaultCurrentLineEventEnabled = false;
        public const bool DefaultEmitSyntheticCurrentLineEventOnStart = false;
        public const bool DefaultRuntimeCurrentLineTransportEnabled = false;
        public const bool DefaultDebugConsoleEnabled = false;

        private ConfigEntry<bool>? _enabled;
        private ConfigEntry<string>? _companionServerUrl;
        private ConfigEntry<int>? _requestTimeoutMs;
        private ConfigEntry<bool>? _sendSyntheticEventOnStart;
        private ConfigEntry<bool>? _metadataProbeEnabled;
        private ConfigEntry<bool>? _metadataProbeLogOnStart;
        private ConfigEntry<bool>? _currentLineEventEnabled;
        private ConfigEntry<bool>? _emitSyntheticCurrentLineEventOnStart;
        private ConfigEntry<bool>? _runtimeCurrentLineTransportEnabled;
        private ConfigEntry<bool>? _debugConsoleEnabled;
        private CompanionHttpClient? _client;

        public override void Load()
        {
            BindConfig();

            Log.LogInfo($"{PluginName} {PluginVersion} loaded in synthetic/manual bridge mode.");

            if (_enabled == null || !_enabled.Value)
            {
                Log.LogInfo("Bridge disabled by config. No companion requests will be sent.");
                return;
            }

            _client = new CompanionHttpClient(
                _companionServerUrl == null ? DefaultCompanionServerUrl : _companionServerUrl.Value,
                _requestTimeoutMs == null ? DefaultRequestTimeoutMs : _requestTimeoutMs.Value
            );

            if (!_client.IsLocalhost)
            {
                Log.LogWarning(
                    "CompanionServerUrl is not localhost. Bridge requests are disabled for safety."
                );
                return;
            }

            _ = RunStartupChecksAsync();
        }

        public async Task SendSyntheticEventNowAsync()
        {
            if (_client == null)
            {
                Log.LogWarning("Synthetic send skipped because the companion client is unavailable.");
                return;
            }

            if (!_client.IsLocalhost)
            {
                Log.LogWarning("Synthetic send skipped because the companion URL is not localhost.");
                return;
            }

            string payload = SyntheticEventFactory.BuildProviderAnnotateRequestJson();
            BridgeHttpResult result = await _client.PostSyntheticProviderAnnotateAsync(payload);

            if (result.Success)
            {
                Log.LogInfo(
                    "Synthetic provider event sent: event_id="
                    + SyntheticEventFactory.EventId
                    + ", line_id="
                    + SyntheticEventFactory.SyntheticLineId
                    + ", status="
                    + result.StatusCode
                    + "."
                );
                return;
            }

            Log.LogWarning(
                "Synthetic provider event was not accepted: event_id="
                + SyntheticEventFactory.EventId
                + ", line_id="
                + SyntheticEventFactory.SyntheticLineId
                + ", status="
                + result.StatusCode
                + ". Game continues without companion data."
            );
        }

        public void EmitSyntheticCurrentLineEventNow()
        {
            if (_currentLineEventEnabled == null || !_currentLineEventEnabled.Value)
            {
                Log.LogInfo("Current-line event skipped because the feature is disabled.");
                return;
            }

            string eventJson = CurrentLineEventFactory.BuildSyntheticCurrentLineEventJson();
            Log.LogInfo(
                "Current-line event emitted: schema_version="
                + CurrentLineEventFactory.SchemaVersion
                + ", event_kind="
                + CurrentLineEventFactory.EventKind
                + ", line_id="
                + CurrentLineEventFactory.SyntheticLineId
                + ", source="
                + CurrentLineEventFactory.SourceSynthetic
                + ", raw_text_included=false, provider_called=false."
            );

            _ = eventJson.Length;
        }

        public async Task SendSyntheticRuntimeCurrentLineEventNowAsync()
        {
            if (_runtimeCurrentLineTransportEnabled == null || !_runtimeCurrentLineTransportEnabled.Value)
            {
                Log.LogInfo("Runtime current-line transport skipped because the feature is disabled.");
                return;
            }

            if (_client == null)
            {
                Log.LogWarning("Runtime current-line transport skipped because the companion client is unavailable.");
                return;
            }

            if (!_client.IsLocalhost)
            {
                Log.LogWarning("Runtime current-line transport skipped because the companion URL is not localhost.");
                return;
            }

            string payload = CurrentLineEventFactory.BuildSyntheticRuntimeCurrentLineEventJson();
            BridgeHttpResult result = await _client.PostRuntimeCurrentLineAsync(payload);
            if (result.Success)
            {
                Log.LogInfo(
                    "Synthetic runtime current-line event sent: line_id="
                    + CurrentLineEventFactory.SyntheticLineId
                    + ", status="
                    + result.StatusCode
                    + ", provider_called=false."
                );
                return;
            }

            Log.LogWarning(
                "Synthetic runtime current-line event was not accepted: line_id="
                + CurrentLineEventFactory.SyntheticLineId
                + ", status="
                + result.StatusCode
                + "."
            );
        }

        public string RunDebugCommand(string commandName)
        {
            if (_debugConsoleEnabled == null || !_debugConsoleEnabled.Value)
            {
                return DebugCommandHandler.BuildDisabledResult(commandName);
            }

            return DebugCommandHandler.BuildResult(
                commandName,
                bridgeEnabled: _enabled != null && _enabled.Value,
                companionLocalhost: _client != null && _client.IsLocalhost,
                syntheticSendConfigured: _sendSyntheticEventOnStart != null
                    && _sendSyntheticEventOnStart.Value,
                currentLineEventEnabled: _currentLineEventEnabled != null
                    && _currentLineEventEnabled.Value,
                matcherAvailable: true
            );
        }

        private void BindConfig()
        {
            _enabled = Config.Bind(
                "Bridge",
                "Enabled",
                DefaultEnabled,
                "Enable the synthetic/manual companion bridge skeleton."
            );
            _companionServerUrl = Config.Bind(
                "Bridge",
                "CompanionServerUrl",
                DefaultCompanionServerUrl,
                "Local companion server base URL. Only localhost URLs are used by this skeleton."
            );
            _requestTimeoutMs = Config.Bind(
                "Bridge",
                "RequestTimeoutMs",
                DefaultRequestTimeoutMs,
                "Timeout for companion health and synthetic event requests."
            );
            _sendSyntheticEventOnStart = Config.Bind(
                "Bridge",
                "SendSyntheticEventOnStart",
                DefaultSendSyntheticEventOnStart,
                "Send the built-in synthetic fake event after a successful startup health check."
            );
            _metadataProbeEnabled = Config.Bind(
                "MetadataProbe",
                "MetadataProbeEnabled",
                DefaultMetadataProbeEnabled,
                "Enable the disabled-by-default metadata-only probe snapshot."
            );
            _metadataProbeLogOnStart = Config.Bind(
                "MetadataProbe",
                "MetadataProbeLogOnStart",
                DefaultMetadataProbeLogOnStart,
                "Log one metadata-only startup snapshot when the metadata probe is enabled."
            );
            _currentLineEventEnabled = Config.Bind(
                "CurrentLineEvent",
                "CurrentLineEventEnabled",
                DefaultCurrentLineEventEnabled,
                "Enable the disabled-by-default redacted current-line metadata event."
            );
            _emitSyntheticCurrentLineEventOnStart = Config.Bind(
                "CurrentLineEvent",
                "EmitSyntheticCurrentLineEventOnStart",
                DefaultEmitSyntheticCurrentLineEventOnStart,
                "Emit the built-in redacted synthetic current-line metadata event after startup checks."
            );
            _runtimeCurrentLineTransportEnabled = Config.Bind(
                "CurrentLineEvent",
                "RuntimeCurrentLineTransportEnabled",
                DefaultRuntimeCurrentLineTransportEnabled,
                "Enable the disabled-by-default runtime current-line transport to localhost."
            );
            _debugConsoleEnabled = Config.Bind(
                "DebugConsole",
                "DebugConsoleEnabled",
                DefaultDebugConsoleEnabled,
                "Enable the disabled-by-default redacted bridge debug command surface."
            );
        }

        private async Task RunStartupChecksAsync()
        {
            if (_client == null)
            {
                return;
            }

            bool companionHealthChecked = false;
            bool companionAvailable = false;
            try
            {
                BridgeHttpResult health = await _client.CheckHealthAsync();
                companionHealthChecked = true;
                companionAvailable = health.Success;
                if (health.Success)
                {
                    Log.LogInfo("Companion health check passed: status=" + health.StatusCode + ".");
                }
                else
                {
                    Log.LogWarning(
                        "Companion health check failed: status="
                        + health.StatusCode
                        + ". Game continues without companion data."
                    );
                    LogMetadataProbeSnapshot(companionHealthChecked, companionAvailable);
                    return;
                }

                if (_sendSyntheticEventOnStart != null && _sendSyntheticEventOnStart.Value)
                {
                    await SendSyntheticEventNowAsync();
                }

                if (
                    _emitSyntheticCurrentLineEventOnStart != null
                    && _emitSyntheticCurrentLineEventOnStart.Value
                )
                {
                    EmitSyntheticCurrentLineEventNow();
                }

                LogMetadataProbeSnapshot(companionHealthChecked, companionAvailable);
            }
            catch (Exception exc)
            {
                Log.LogWarning(
                    "Companion unavailable during bridge startup. Game continues without companion data. "
                    + exc.GetType().Name
                    + ": "
                    + exc.Message
                );
                LogMetadataProbeSnapshot(companionHealthChecked, companionAvailable);
            }
        }

        private void LogMetadataProbeSnapshot(bool companionHealthChecked, bool companionAvailable)
        {
            if (_metadataProbeEnabled == null || !_metadataProbeEnabled.Value)
            {
                return;
            }

            if (_metadataProbeLogOnStart == null || !_metadataProbeLogOnStart.Value)
            {
                return;
            }

            MetadataProbeSnapshot snapshot = MetadataProbe.BuildSnapshot(
                probeEnabled: _metadataProbeEnabled.Value,
                pluginLoaded: true,
                companionHealthChecked: companionHealthChecked,
                companionAvailable: companionAvailable,
                syntheticEventSendConfigured: _sendSyntheticEventOnStart != null
                    && _sendSyntheticEventOnStart.Value
            );
            Log.LogInfo(snapshot.ToLogLine());
        }
    }
}
