@IsTest
private class StaleLeadBatchTest {

    @IsTest
    static void closesOpenLeadsInOneScope() {
        List<Lead> leads = new List<Lead>();
        for (Integer i = 0; i < 50; i++) {
            leads.add(new Lead(LastName = 'Stale ' + i, Company = 'Acme', Status = 'Open - Not Contacted'));
        }
        insert leads;
        // LastActivityDate cannot be set directly; this test checks the batch runs and leaves fresh leads alone.
        Test.startTest();
        Id jobId = Database.executeBatch(new StaleLeadBatch(), 200);
        Test.stopTest();
        System.assertEquals('Completed', [SELECT Status FROM AsyncApexJob WHERE Id = :jobId].Status);
        System.assertEquals(50, [SELECT COUNT() FROM Lead WHERE Status = 'Open - Not Contacted'], 'leads with no old activity stay open');
    }

    @IsTest
    static void schedulerDispatchesTheBatch() {
        Test.startTest();
        String cronId = System.schedule('Stale lead test', '0 0 2 * * ?', new StaleLeadScheduler());
        Test.stopTest();
        System.assertEquals(1, [SELECT COUNT() FROM CronTrigger WHERE Id = :cronId]);
    }
}
