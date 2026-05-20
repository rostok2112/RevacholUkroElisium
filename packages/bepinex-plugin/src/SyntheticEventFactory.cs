using System;
using System.Collections.Generic;
using System.Text;

namespace Revachol.UkrainianCompanion.BepInExBridge
{
    internal static class SyntheticEventFactory
    {
        public const string EventId = "synthetic.event.bepinex.4a.001";
        public const string SyntheticLineId = "synthetic.bepinex.4a.001";
        public const string Speaker = "Synthetic Clerk";
        public const string RawEnglishText =
            "The committee pinned a medal on the leaking pipe and called it infrastructure.";
        public const string SceneId = "synthetic.scene.bridge-lab";
        public const string ConversationId = "synthetic.conv.bridge";
        public const string Timestamp = "2026-05-06T10:00:00Z";

        public static string BuildProviderAnnotateRequestJson()
        {
            Dictionary<string, string> eventFields = new Dictionary<string, string>
            {
                { "event_id", EventId },
                { "synthetic_line_id", SyntheticLineId },
                { "speaker", Speaker },
                { "speaker_type", "npc" },
                { "raw_english_text", RawEnglishText },
                { "scene_id", SceneId },
                { "conversation_id", ConversationId },
                { "timestamp", Timestamp },
            };

            StringBuilder builder = new StringBuilder();
            builder.Append("{\"input_type\":\"fake_event\",\"event\":{");
            bool first = true;
            foreach (KeyValuePair<string, string> field in eventFields)
            {
                if (!first)
                {
                    builder.Append(",");
                }

                builder.Append("\"").Append(JsonEscape(field.Key)).Append("\":");
                builder.Append("\"").Append(JsonEscape(field.Value)).Append("\"");
                first = false;
            }

            builder.Append(",\"nearby_context\":[]");
            builder.Append("}}");
            return builder.ToString();
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
