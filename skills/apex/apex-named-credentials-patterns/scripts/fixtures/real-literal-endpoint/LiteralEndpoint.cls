public with sharing class LiteralEndpoint {
    public static void call() {
        HttpRequest req = new HttpRequest();
        req.setEndpoint('https://api.example.com/v1');
        new Http().send(req);
    }
}
