public with sharing class NoCalloutMarkerQueueable implements Queueable {
    public void execute(QueueableContext ctx) {
        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:ERP/orders');
        new Http().send(req);
        System.enqueueJob(new NoCalloutMarkerQueueable());
        System.enqueueJob(new NoCalloutMarkerQueueable());
    }
}
