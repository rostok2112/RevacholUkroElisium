namespace Revachol.UkrainianCompanion.BepInExBridge
{
    internal static class MetadataProbe
    {
        public const bool RealTextCaptured = false;
        public const bool CurrentLineCaptureEnabled = false;
        public const bool UiProbeAttempted = false;
        public const bool SceneProbeAttempted = false;
        public const int DefaultSafeStatusEvents = 0;
        public const int DefaultSyntheticEvents = 0;
        public const int DefaultMetadataSnapshotCreatedCount = 1;

        public static MetadataProbeSnapshot BuildSnapshot(
            bool probeEnabled,
            bool pluginLoaded,
            bool companionHealthChecked,
            bool companionAvailable,
            bool syntheticEventSendConfigured
        )
        {
            return new MetadataProbeSnapshot(
                probeEnabled,
                probeEnabled,
                probeEnabled,
                pluginLoaded,
                companionHealthChecked,
                companionAvailable,
                syntheticEventSendConfigured,
                RealTextCaptured,
                CurrentLineCaptureEnabled,
                UiProbeAttempted,
                SceneProbeAttempted,
                DefaultSafeStatusEvents,
                DefaultSyntheticEvents,
                probeEnabled ? DefaultMetadataSnapshotCreatedCount : 0,
                CountWhen(companionHealthChecked),
                CountWhen(syntheticEventSendConfigured)
            );
        }

        private static int CountWhen(bool observed)
        {
            return observed ? 1 : 0;
        }
    }

    internal sealed class MetadataProbeSnapshot
    {
        public MetadataProbeSnapshot(
            bool probeEnabled,
            bool probeAttempted,
            bool probeCompleted,
            bool pluginLoaded,
            bool companionHealthChecked,
            bool companionAvailable,
            bool syntheticEventSendConfigured,
            bool realTextCaptured,
            bool currentLineCaptureEnabled,
            bool uiProbeAttempted,
            bool sceneProbeAttempted,
            int safeStatusEvents,
            int syntheticEvents,
            int metadataSnapshotCreatedCount,
            int healthCheckObservedCount,
            int syntheticSendConfiguredCount
        )
        {
            ProbeEnabled = probeEnabled;
            ProbeAttempted = probeAttempted;
            ProbeCompleted = probeCompleted;
            PluginLoaded = pluginLoaded;
            CompanionHealthChecked = companionHealthChecked;
            CompanionAvailable = companionAvailable;
            SyntheticEventSendConfigured = syntheticEventSendConfigured;
            RealTextCaptured = realTextCaptured;
            CurrentLineCaptureEnabled = currentLineCaptureEnabled;
            UiProbeAttempted = uiProbeAttempted;
            SceneProbeAttempted = sceneProbeAttempted;
            SafeStatusEvents = safeStatusEvents;
            SyntheticEvents = syntheticEvents;
            MetadataSnapshotCreatedCount = metadataSnapshotCreatedCount;
            HealthCheckObservedCount = healthCheckObservedCount;
            SyntheticSendConfiguredCount = syntheticSendConfiguredCount;
        }

        public bool ProbeEnabled { get; }
        public bool ProbeAttempted { get; }
        public bool ProbeCompleted { get; }
        public bool PluginLoaded { get; }
        public bool CompanionHealthChecked { get; }
        public bool CompanionAvailable { get; }
        public bool SyntheticEventSendConfigured { get; }
        public bool RealTextCaptured { get; }
        public bool CurrentLineCaptureEnabled { get; }
        public bool UiProbeAttempted { get; }
        public bool SceneProbeAttempted { get; }
        public int SafeStatusEvents { get; }
        public int SyntheticEvents { get; }
        public int MetadataSnapshotCreatedCount { get; }
        public int HealthCheckObservedCount { get; }
        public int SyntheticSendConfiguredCount { get; }

        public string ToLogLine()
        {
            return "Metadata probe snapshot: synthetic_manual=true"
                + ", probe_enabled="
                + Lower(ProbeEnabled)
                + ", probe_attempted="
                + Lower(ProbeAttempted)
                + ", probe_completed="
                + Lower(ProbeCompleted)
                + ", plugin_loaded="
                + Lower(PluginLoaded)
                + ", companion_health_checked="
                + Lower(CompanionHealthChecked)
                + ", companion_available="
                + Lower(CompanionAvailable)
                + ", synthetic_event_send_configured="
                + Lower(SyntheticEventSendConfigured)
                + ", real_text_captured="
                + Lower(RealTextCaptured)
                + ", current_line_capture_enabled="
                + Lower(CurrentLineCaptureEnabled)
                + ", ui_probe_attempted="
                + Lower(UiProbeAttempted)
                + ", scene_probe_attempted="
                + Lower(SceneProbeAttempted)
                + ", counters.safe_status_events="
                + SafeStatusEvents
                + ", counters.synthetic_events="
                + SyntheticEvents
                + ", counters.metadata_snapshot_created_count="
                + MetadataSnapshotCreatedCount
                + ", counters.health_check_observed_count="
                + HealthCheckObservedCount
                + ", counters.synthetic_send_configured_count="
                + SyntheticSendConfiguredCount
                + ".";
        }

        private static string Lower(bool value)
        {
            return value ? "true" : "false";
        }
    }
}
