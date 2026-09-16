/**
 * Gotcha 15 repair: seed via AccessLevel.SYSTEM_MODE / insertAsSystem outside runAs;
 * only the action under test sits inside the permissioned block.
 */
@IsTest
private class NegativeSystemModeSeedTest {

    @TestSetup
    static void seed() {
        List<Case> cases = TestDataFactory.createCases(1, null, null);
        Database.insert(cases, AccessLevel.SYSTEM_MODE);
    }

    @IsTest
    static void actsAsPersona() {
        User agent = [SELECT Id FROM User WHERE Alias = 'agt1' LIMIT 1];
        Case row = [SELECT Id, Subject FROM Case LIMIT 1];

        System.runAs(agent) {
            Test.startTest();
            row.Subject = 'Updated';
            update row;
            Test.stopTest();
        }

        Assert.areEqual('Updated', [SELECT Subject FROM Case WHERE Id = :row.Id].Subject);
    }
}
