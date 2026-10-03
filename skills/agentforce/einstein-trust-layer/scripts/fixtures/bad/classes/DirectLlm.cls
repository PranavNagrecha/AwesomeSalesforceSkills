public with sharing class DirectLlm {
    public static HttpResponse ask(String body) {
        HttpRequest req = new HttpRequest();
        req.setEndpoint('https://api.openai.com/v1/chat/completions');
        req.setMethod('POST');
        req.setBody(body);
        return new Http().send(req);
    }
}
