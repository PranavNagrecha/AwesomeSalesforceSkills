@IsTest
private class OrderDispatchQueueableTest {

    @IsTest
    static void enqueuesOneJobAndCallsOut() {
        Test.setMock(HttpCalloutMock.class, new MockHttpResponseGenerator().withResponse(200, '{"ok":true}'));
        List<Order__c> orders = new List<Order__c>();
        for (Integer i = 0; i < 200; i++) {
            orders.add(new Order__c(External_Key__c = 'EXT-' + i, Status__c = 'Submitted'));
        }
        Test.startTest();
        insert orders;
        System.assertEquals(1, Limits.getQueueableJobs(), 'one job for the whole chunk');
        Test.stopTest(); // the queued job runs here

        System.assertEquals(1, [SELECT COUNT() FROM AsyncApexJob WHERE JobType = 'Queueable' AND Status = 'Completed']);
    }

    @IsTest
    static void failedCalloutMarksJobFailed() {
        Test.setMock(HttpCalloutMock.class, new MockHttpResponseGenerator().withResponse(503, ''));
        Order__c o = new Order__c(External_Key__c = 'EXT-X', Status__c = 'Submitted');
        insert o;
        Test.startTest();
        System.enqueueJob(new OrderDispatchQueueable(new Set<Id>{ o.Id }));
        try {
            Test.stopTest();
        } catch (OrderDispatchQueueable.OmsSyncException e) {
            System.assert(e.getMessage().contains('503'), 'status is reported');
        }
    }
}
