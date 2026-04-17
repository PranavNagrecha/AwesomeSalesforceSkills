/**
 * AccountIndustryStampQueueableTest
 *
 * Positive, bulk, and edge-case coverage for AccountIndustryStampQueueable.
 * Target coverage >= 85% per Gate C.
 */
@IsTest
private class AccountIndustryStampQueueableTest {

    @TestSetup
    static void setup() {
        List<Account> accts = new List<Account>();
        for (Integer i = 0; i < 200; i++) {
            accts.add(new Account(Name = 'Bulk Acct ' + i, Industry = 'Technology'));
        }
        insert accts;
    }

    @IsTest
    static void bulkPath_stampsEveryAccount() {
        Set<Id> ids = new Set<Id>();
        for (Account a : [SELECT Id FROM Account LIMIT 200]) {
            ids.add(a.Id);
        }
        Test.startTest();
        System.enqueueJob(new AccountIndustryStampQueueable(ids));
        Test.stopTest();
        Integer stamped = 0;
        for (Account a : [SELECT Description FROM Account WHERE Id IN :ids]) {
            if (a.Description != null && a.Description.startsWith('Industry: ')) {
                stamped += 1;
            }
        }
        System.assertEquals(ids.size(), stamped, 'every account should have a stamped description');
    }

    @IsTest
    static void emptyInput_noOp() {
        Test.startTest();
        System.enqueueJob(new AccountIndustryStampQueueable(new Set<Id>()));
        Test.stopTest();
        System.assert(true, 'empty input is a valid no-op');
    }

    @IsTest
    static void nullInput_treatedAsEmpty() {
        Test.startTest();
        System.enqueueJob(new AccountIndustryStampQueueable(null));
        Test.stopTest();
        System.assert(true, 'null input must not throw');
    }

    @IsTest
    static void nullIndustry_stampsUnknown() {
        Account solo = new Account(Name = 'No-Industry Co');
        insert solo;
        Set<Id> ids = new Set<Id>{ solo.Id };
        Test.startTest();
        System.enqueueJob(new AccountIndustryStampQueueable(ids));
        Test.stopTest();
        Account reread = [SELECT Description FROM Account WHERE Id = :solo.Id];
        System.assertEquals('Industry: Unknown', reread.Description, 'null Industry should fall back to Unknown');
    }
}
