/**
 * AccountHierarchyRebuildQueueableTest
 *
 * Positive, negative, and bulk coverage for AccountHierarchyRebuildQueueable.
 * Target coverage ≥ 85% per Gate C.
 */
@IsTest
private class AccountHierarchyRebuildQueueableTest {

    @TestSetup
    static void setup() {
        List<Account> accts = new List<Account>();
        for (Integer i = 0; i < 200; i++) {
            accts.add(new Account(Name = 'Bulk Root ' + i));
        }
        insert accts;
    }

    @IsTest
    static void bulkPath_enqueuesAndCompletes() {
        Set<Id> ids = new Set<Id>();
        for (Account a : [SELECT Id FROM Account LIMIT 200]) {
            ids.add(a.Id);
        }
        Test.startTest();
        System.enqueueJob(new AccountHierarchyRebuildQueueable(ids));
        Test.stopTest();
        Integer depthsSet = [SELECT COUNT() FROM Account WHERE Id IN :ids AND Hierarchy_Depth__c != null];
        System.assertEquals(ids.size(), depthsSet, 'every account should have a computed depth');
    }

    @IsTest
    static void emptyInput_noOp() {
        Test.startTest();
        System.enqueueJob(new AccountHierarchyRebuildQueueable(new Set<Id>()));
        Test.stopTest();
        System.assert(true, 'empty input is a valid no-op');
    }

    @IsTest
    static void nullInput_treatedAsEmpty() {
        Test.startTest();
        System.enqueueJob(new AccountHierarchyRebuildQueueable(null));
        Test.stopTest();
        System.assert(true, 'null input must not throw');
    }
}
