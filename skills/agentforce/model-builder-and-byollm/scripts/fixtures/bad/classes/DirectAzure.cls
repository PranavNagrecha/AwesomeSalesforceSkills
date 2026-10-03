public with sharing class DirectAzure {
    public static HttpResponse ask(String body) {
        HttpRequest req = new HttpRequest();
        req.setEndpoint('http://myres.openai.azure.com:8443/openai/deployments/gpt-4o/chat/completions');
        req.setHeader('api-key', 'abcdef0123456789abcdef');
        req.setBody(body);
        return new Http().send(req);
    }
}
