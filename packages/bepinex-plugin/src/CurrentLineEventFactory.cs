using System;
using System.Collections.Generic;
using System.Text;

namespace Revachol.UkrainianCompanion.BepInExBridge
{
    internal static class CurrentLineEventFactory
    {
        public const string SchemaVersion = "m3-current-line-event.v1";
        public const string EventKind = "current_line";
        public const string BridgeSource = "bepinex";
        public const string SourceSynthetic = "synthetic";
        public const string SourceSyntheticRuntime = "synthetic_runtime";
        public const string SyntheticLineId = SyntheticEventFactory.SyntheticLineId;
        public const string SyntheticConversationId = SyntheticEventFactory.ConversationId;
        public const string SyntheticRuntimeSourceText = "Invented runtime bridge smoke line.";
        public const string SyntheticRuntimeSpeaker = "Synthetic Speaker";

        public static string BuildSyntheticCurrentLineEventJson()
        {
            Dictionary<string, string> stringFields = new Dictionary<string, string>
            {
                { "schema_version", SchemaVersion },
                { "event_kind", EventKind },
                { "bridge_source", BridgeSource },
                { "line_id", SyntheticLineId },
                { "conversation_id", SyntheticConversationId },
                { "source", SourceSynthetic },
            };

            StringBuilder builder = new StringBuilder();
            builder.Append("{");
            bool first = true;
            foreach (KeyValuePair<string, string> field in stringFields)
            {
                AppendComma(builder, ref first);
                AppendStringField(builder, field.Key, field.Value);
            }

            AppendComma(builder, ref first);
            builder.Append("\"emitted_at_unix_ms\":").Append(CurrentUnixTimeMilliseconds());
            AppendComma(builder, ref first);
            builder.Append("\"capture_enabled\":false");
            AppendComma(builder, ref first);
            builder.Append("\"raw_text_included\":false");
            AppendComma(builder, ref first);
            builder.Append("\"private_paths_included\":false");
            AppendComma(builder, ref first);
            builder.Append("\"provider_called\":false");
            builder.Append("}");
            return builder.ToString();
        }

        public static string BuildSyntheticRuntimeCurrentLineEventJson()
        {
            return BuildRuntimeCurrentLineEventJson(
                SyntheticLineId,
                SyntheticRuntimeSourceText,
                SyntheticRuntimeSpeaker,
                SyntheticConversationId,
                SourceSyntheticRuntime
            );
        }

        public static string BuildRuntimeCurrentLineEventJson(
            string lineId,
            string sourceText,
            string speaker,
            string conversationId,
            string source
        )
        {
            Dictionary<string, string> stringFields = new Dictionary<string, string>
            {
                { "schema_version", "runtime-current-line-event.v1" },
                { "event_kind", EventKind },
                { "line_id", lineId ?? string.Empty },
                { "source_text", sourceText ?? string.Empty },
                { "speaker", speaker ?? string.Empty },
                { "conversation_id", conversationId ?? string.Empty },
                { "source", source ?? "bepinex_runtime" },
            };

            StringBuilder builder = new StringBuilder();
            builder.Append("{");
            bool first = true;
            foreach (KeyValuePair<string, string> field in stringFields)
            {
                AppendComma(builder, ref first);
                AppendStringField(builder, field.Key, field.Value);
            }

            AppendComma(builder, ref first);
            builder.Append("\"provider_called\":false");
            AppendComma(builder, ref first);
            builder.Append("\"game_file_read\":false");
            AppendComma(builder, ref first);
            builder.Append("\"screenshot_included\":false");
            AppendComma(builder, ref first);
            builder.Append("\"bepinex_log_read\":false");
            AppendComma(builder, ref first);
            builder.Append("\"private_path_included\":false");
            builder.Append("}");
            return builder.ToString();
        }

        private static long CurrentUnixTimeMilliseconds()
        {
            return DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
        }

        private static void AppendComma(StringBuilder builder, ref bool first)
        {
            if (!first)
            {
                builder.Append(",");
            }

            first = false;
        }

        private static void AppendStringField(StringBuilder builder, string key, string value)
        {
            builder.Append("\"").Append(JsonEscape(key)).Append("\":");
            builder.Append("\"").Append(JsonEscape(value)).Append("\"");
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
