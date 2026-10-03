public with sharing class OrderStatusEventHandler {

    public static void apply(List<Order_Status__e> events) {
        // 1. Collect keys; the last event per key wins.
        Map<String, String> statusByKey = new Map<String, String>();
        for (Order_Status__e e : events) {
            if (String.isNotBlank(e.Order_Key__c)) {
                statusByKey.put(e.Order_Key__c, e.Status__c);
            }
        }
        if (statusByKey.isEmpty()) {
            return;
        }
        // 2. One query for up to 2,000 keys (well under 50,000 rows).
        List<Order__c> toUpdate = new List<Order__c>();
        for (Order__c o : [
            SELECT Id, External_Key__c, Status__c
            FROM Order__c
            WHERE External_Key__c IN :statusByKey.keySet()
            WITH USER_MODE
        ]) {
            String status = statusByKey.get(o.External_Key__c);
            if (o.Status__c != status) {
                o.Status__c = status;
                toUpdate.add(o);
            }
        }
        // 3. One DML statement; partial success so one bad row doesn't fail the batch.
        Database.update(toUpdate, false);
    }
}
