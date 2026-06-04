using System;
using System.Collections.Generic;
using System.Text;

namespace Revachol.UkrainianCompanion.BepInExBridge
{
    internal static class DebugCommandHandler
    {
        public const string SchemaVersion = "m3-debug-console-command-result.v1";
        public const string BridgeStatus = "bridge_status";
        public const string SyntheticSend = "synthetic_send";
        public const string CurrentLineEventStatus = "current_line_event_status";
        public const string MatcherStatus = "matcher_status";

        private static readonly HashSet<string> AllowedCommands = new HashSet<string>
        {
            BridgeStatus,
            SyntheticSend,
            CurrentLineEventStatus,
            MatcherStatus,
        };

        public static string BuildDisabledResult(string commandName)
        {
            return BuildResult(
                commandName,
                bridgeEnabled: false,
                companionLocalhost: false,
                syntheticSendConfigured: false,
                currentLineEventEnabled: false,
                matcherAvailable: false,
                debugConsoleEnabled: false
            );
        }

        public static string BuildResult(
            string commandName,
            bool bridgeEnabled,
            bool companionLocalhost,
            bool syntheticSendConfigured,
            bool currentLineEventEnabled,
            bool matcherAvailable,
            bool debugConsoleEnabled = true
        )
        {
            string normalizedCommand = NormalizeCommand(commandName);
            bool commandAllowed = AllowedCommands.Contains(normalizedCommand);
            StringBuilder builder = new StringBuilder();
            builder.Append("{");
            AppendStringField(builder, "schema_version", SchemaVersion, first: true);
            AppendStringField(builder, "command", commandAllowed ? normalizedCommand : "unsupported");
            AppendBoolField(builder, "command_allowed", commandAllowed);
            AppendBoolField(builder, "debug_console_enabled", debugConsoleEnabled);
            AppendBoolField(builder, "bridge_enabled", bridgeEnabled);
            AppendBoolField(builder, "companion_localhost", companionLocalhost);
            AppendBoolField(builder, "synthetic_send_configured", syntheticSendConfigured);
            AppendBoolField(builder, "synthetic_send_performed", false);
            AppendBoolField(builder, "current_line_event_enabled", currentLineEventEnabled);
            AppendBoolField(builder, "matcher_available", matcherAvailable);
            AppendBoolField(builder, "raw_text_included", false);
            AppendBoolField(builder, "payload_dump_included", false);
            AppendBoolField(builder, "private_paths_included", false);
            AppendBoolField(builder, "provider_called", false);
            builder.Append("}");
            return builder.ToString();
        }

        private static string NormalizeCommand(string commandName)
        {
            return string.IsNullOrWhiteSpace(commandName)
                ? string.Empty
                : commandName.Trim().ToLowerInvariant().Replace("-", "_");
        }

        private static void AppendStringField(
            StringBuilder builder,
            string key,
            string value,
            bool first = false
        )
        {
            if (!first)
            {
                builder.Append(",");
            }

            builder.Append("\"").Append(JsonEscape(key)).Append("\":");
            builder.Append("\"").Append(JsonEscape(value)).Append("\"");
        }

        private static void AppendBoolField(StringBuilder builder, string key, bool value)
        {
            builder.Append(",");
            builder.Append("\"").Append(JsonEscape(key)).Append("\":");
            builder.Append(value ? "true" : "false");
        }

        private static string JsonEscape(string value)
        {
            StringBuilder builder = new StringBuilder(value.Length + 8);
            foreach (char character in value)
            {
                switch (character)
                {
                    case '\\':
                        builder.Append("\\\\");
                        break;
                    case '"':
                        builder.Append("\\\"");
                        break;
                    case '\b':
                        builder.Append("\\b");
                        break;
                    case '\f':
                        builder.Append("\\f");
                        break;
                    case '\n':
                        builder.Append("\\n");
                        break;
                    case '\r':
                        builder.Append("\\r");
                        break;
                    case '\t':
                        builder.Append("\\t");
                        break;
                    default:
                        if (character < 32)
                        {
                            builder.Append("\\u").Append(((int)character).ToString("x4"));
                        }
                        else
                        {
                            builder.Append(character);
                        }
                        break;
                }
            }
            return builder.ToString();
        }
    }
}
