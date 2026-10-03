public with sharing class OrderReporting {
    public static List<AggregateResult> totals() {
        return [SELECT Status__c, SUM(Amount__c) total FROM SalesOrder__x GROUP BY Status__c];
    }
    public static List<SalesOrder__x> search(String term) {
        String pattern = term + '%';
        return [SELECT Id FROM SalesOrder__x WHERE Status__c LIKE :pattern WITH USER_MODE];
    }
    public static Integer openCount() {
        return [SELECT COUNT() FROM SalesOrder__x WHERE Status__c = 'Open'];
    }
    public static void create() {
        insert new SalesOrder__x(Status__c = 'Submitted');
        List<Id> customerIds = new List<Id>();
        for (Id cid : customerIds) {
            List<SalesOrder__x> rows = [SELECT Id FROM SalesOrder__x WHERE CustomerNumber__c = :cid];
        }
    }
}
