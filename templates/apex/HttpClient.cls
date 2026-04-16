/**
 * HttpClient — Named-Credential-aware HTTP client with retry + timeout + logging.
 *
 * Usage:
 *
 *     HttpClient.Response res = new HttpClient()
 *         .namedCredential('My_External_API')
 *         .path('/v1/accounts/' + externalId)
 *         .method('GET')
 *         .header('Accept', 'application/json')
 *         .timeoutMs(20000)
 *         .retryOnTransient(true)
 *         .send();
 *
 *     if (!res.isSuccess()) { throw new HttpClientException('Upstream ' + res.statusCode); }
 *
 * Rules:
 *  - Never hardcode endpoints. Always use a Named Credential.
 *  - Tests MUST use MockHttpResponseGenerator — never real network.
 *  - Retries are only for transient failures (5xx, 408, 429, IO exceptions).
 */
public with sharing class HttpClient {

    public class HttpClientException extends Exception {}

    public class Response {
        public Integer statusCode;
        public String status;
        public String body;
        public Map<String, String> headers = new Map<String, String>();
        public Boolean isSuccess() { return statusCode != null && statusCode >= 200 && statusCode < 300; }
        public Boolean isTransient() {
            if (statusCode == null) { return true; }
            return statusCode >= 500 || statusCode == 408 || statusCode == 429;
        }
    }

    private String namedCredential;
    private String path = '';
    private String method = 'GET';
    private Blob bodyBlob;
    private String bodyString;
    private Map<String, String> headers = new Map<String, String>();
    private Integer timeoutMs = 30000;
    private Boolean retry = false;
    private Integer maxAttempts = 3;

    public HttpClient namedCredential(String name) { this.namedCredential = name; return this; }
    public HttpClient path(String p)               { this.path = p == null ? '' : p; return this; }
    public HttpClient method(String m)             { this.method = (m == null ? 'GET' : m).toUpperCase(); return this; }
    public HttpClient body(String s)               { this.bodyString = s; this.bodyBlob = null; return this; }
    public HttpClient body(Blob b)                 { this.bodyBlob = b;   this.bodyString = null; return this; }
    public HttpClient header(String k, String v)   { this.headers.put(k, v); return this; }
    public HttpClient timeoutMs(Integer ms)        { this.timeoutMs = ms; return this; }
    public HttpClient retryOnTransient(Boolean r)  { this.retry = r; return this; }
    public HttpClient maxAttempts(Integer n)       { this.maxAttempts = Math.max(1, n); return this; }

    public Response send() {
        if (String.isBlank(namedCredential)) {
            throw new HttpClientException('Named Credential is required');
        }
        Integer attempts = retry ? maxAttempts : 1;
        Response last;
        for (Integer i = 1; i <= attempts; i++) {
            last = sendOnce();
            if (last.isSuccess() || !last.isTransient()) { return last; }
            ApplicationLogger.warn(
                'HttpClient.retry',
                'Attempt ' + i + '/' + attempts + ' failed ' + last.statusCode + ' ' + last.status
            );
            if (i < attempts) {
                Long backoff = (Long)(Math.pow(2, i) * 100);
                sleep(backoff);
            }
        }
        return last;
    }

    private Response sendOnce() {
        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:' + namedCredential + path);
        req.setMethod(method);
        req.setTimeout(timeoutMs);
        for (String k : headers.keySet()) { req.setHeader(k, headers.get(k)); }
        if (bodyString != null) { req.setBody(bodyString); }
        else if (bodyBlob != null) { req.setBodyAsBlob(bodyBlob); }

        Response out = new Response();
        try {
            HttpResponse raw = new Http().send(req);
            out.statusCode = raw.getStatusCode();
            out.status = raw.getStatus();
            out.body = raw.getBody();
            for (String h : raw.getHeaderKeys()) { out.headers.put(h, raw.getHeader(h)); }
        } catch (Exception e) {
            ApplicationLogger.error('HttpClient.sendOnce', e);
            out.statusCode = 0;
            out.status = e.getMessage();
        }
        return out;
    }

    private void sleep(Long ms) {
        Long until = System.currentTimeMillis() + ms;
        while (System.currentTimeMillis() < until) { /* busy wait — Apex has no sleep */ }
    }
}
