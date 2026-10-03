global class CalloutScheduler implements Schedulable {
    global void execute(SchedulableContext ctx) {
        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:ERP/ping');
        req.setMethod('GET');
        new Http().send(req);
    }
}
