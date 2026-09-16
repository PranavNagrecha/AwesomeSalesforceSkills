public with sharing class AuthInSource {
    public static void call() {
        HttpRequest req = new HttpRequest();
        req.setEndpoint('https://api.example.com/v1');
        req.setHeader('Authorization', 'Bearer x');
        new Http().send(req);
    }
}
