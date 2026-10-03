public with sharing class OrderDispatchQueueable implements Queueable, Database.AllowsCallouts {

    public class OmsSyncException extends Exception {}

    private final Set<Id> orderIds;

    public OrderDispatchQueueable(Set<Id> orderIds) {
        this.orderIds = orderIds;
    }

    public void execute(QueueableContext context) {
        // Re-query: the job runs later, so read current values.
        List<Order__c> orders = [
            SELECT Id, External_Key__c, Status__c
            FROM Order__c
            WHERE Id IN :orderIds
            WITH USER_MODE
        ];
        if (orders.isEmpty()) {
            return;
        }
        HttpRequest request = new HttpRequest();
        request.setEndpoint('callout:OMS_NC/orders/sync');
        request.setMethod('POST');
        request.setHeader('Content-Type', 'application/json');
        request.setTimeout(10000);
        request.setBody(JSON.serialize(orders));

        HttpResponse response = new Http().send(request);
        if (response.getStatusCode() >= 300) {
            // Surface the failure on the AsyncApexJob record; a Finalizer can pick it up for retry.
            throw new OmsSyncException('OMS sync failed with status ' + response.getStatusCode());
        }
    }
}
