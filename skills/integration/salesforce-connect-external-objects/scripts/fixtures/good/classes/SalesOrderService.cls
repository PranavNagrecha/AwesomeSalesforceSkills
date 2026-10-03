public with sharing class SalesOrderService {
    public static List<SalesOrder__x> openOrdersFor(String customerNumber) {
        // WITH clauses are not supported on external objects, so user mode is
        // passed as the AccessLevel argument instead of WITH USER_MODE.
        Map<String, Object> binds = new Map<String, Object>{ 'customer' => customerNumber };
        return Database.queryWithBinds(
            'SELECT Id, ExternalId, Status__c, Amount__c FROM SalesOrder__x '
                + 'WHERE CustomerNumber__c = :customer AND Status__c = \'Open\' LIMIT 200',
            binds,
            AccessLevel.USER_MODE
        );
    }

    // External objects do not accept plain insert; the write is queued.
    public static String submit(String customerNumber, Decimal amount) {
        SalesOrder__x order = new SalesOrder__x(
            CustomerNumber__c = customerNumber,
            Amount__c = amount,
            Status__c = 'Submitted'
        );
        Database.SaveResult sr = Database.insertAsync(order);
        return Database.getAsyncLocator(sr);
    }
}
