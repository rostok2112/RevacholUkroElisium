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

        private ConfigEntry<bool>? _enabled;
        private ConfigEntry<string>? _companionServerUrl;
        private ConfigEntry<int>? _requestTimeoutMs;
        private ConfigEntry<bool>? _sendSyntheticEventOnStart;
        private ConfigEntry<bool>? _metadataProbeEnabled;
        private ConfigEntry<bool>? _metadataProbeLogOnStart;
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
