using System;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;

namespace Revachol.UkrainianCompanion.BepInExBridge
{
    internal sealed class CompanionHttpClient : IDisposable
    {
        private readonly Uri _baseUri;
        private readonly HttpClient _httpClient;

        public CompanionHttpClient(string baseUrl, int timeoutMs)
        {
            if (!Uri.TryCreate(baseUrl, UriKind.Absolute, out Uri? parsed))
            {
                parsed = new Uri(RevacholCompanionBridgePlugin.DefaultCompanionServerUrl);
            }

            _baseUri = EnsureTrailingSlash(parsed);
            IsLocalhost = IsLoopbackHost(_baseUri.Host);
            _httpClient = new HttpClient
            {
                Timeout = TimeSpan.FromMilliseconds(Math.Max(250, timeoutMs)),
            };
        }

        public bool IsLocalhost { get; }

        public Task<BridgeHttpResult> CheckHealthAsync()
        {
            return SendAsync(HttpMethod.Get, "health", null);
        }

        public Task<BridgeHttpResult> PostSyntheticProviderAnnotateAsync(string jsonPayload)
        {
            return SendAsync(HttpMethod.Post, "synthetic/provider-annotate", jsonPayload);
        }

        public Task<BridgeHttpResult> PostRuntimeCurrentLineAsync(string jsonPayload)
        {
            return SendAsync(HttpMethod.Post, "runtime/current-line", jsonPayload);
        }

        public void Dispose()
        {
            _httpClient.Dispose();
        }

        private async Task<BridgeHttpResult> SendAsync(
            HttpMethod method,
            string relativePath,
            string? jsonPayload
        )
        {
            if (!IsLocalhost)
            {
                return BridgeHttpResult.Skipped();
            }

            using (HttpRequestMessage request = new HttpRequestMessage(
                method,
                new Uri(_baseUri, relativePath)
            ))
            {
                if (jsonPayload != null)
                {
                    request.Content = new StringContent(jsonPayload, Encoding.UTF8, "application/json");
                }

                using (HttpResponseMessage response = await _httpClient
                    .SendAsync(request)
                    .ConfigureAwait(false))
                {
                    return new BridgeHttpResult((int)response.StatusCode, response.IsSuccessStatusCode);
                }
            }
        }

        private static Uri EnsureTrailingSlash(Uri uri)
        {
            string rendered = uri.ToString();
            if (!rendered.EndsWith("/", StringComparison.Ordinal))
            {
                rendered += "/";
            }
            return new Uri(rendered);
        }

        private static bool IsLoopbackHost(string host)
        {
            return string.Equals(host, "127.0.0.1", StringComparison.OrdinalIgnoreCase)
                || string.Equals(host, "localhost", StringComparison.OrdinalIgnoreCase)
                || string.Equals(host, "::1", StringComparison.OrdinalIgnoreCase);
        }
    }

    internal readonly struct BridgeHttpResult
    {
        public BridgeHttpResult(int statusCode, bool success)
        {
            StatusCode = statusCode;
            Success = success;
        }

        public int StatusCode { get; }
        public bool Success { get; }

        public static BridgeHttpResult Skipped()
        {
            return new BridgeHttpResult(0, false);
        }
    }
}
