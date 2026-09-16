/**
 * Persona editing an existing record between startTest/stopTest is the action
 * under test — not fixture seeding.
 */
@IsTest
private class NegativeActionInsideBoundaryTest {

    @IsTest
    static void updatesExistingRecordInsideBoundary() {
        User agent = [SELECT Id FROM User WHERE Alias = 'agt1' LIMIT 1];
        Case row = [SELECT Id, Subject FROM Case LIMIT 1];

        System.runAs(agent) {
            Test.startTest();
            row.Subject = 'Persona edit';
            update row;
            Test.stopTest();
        }

        Assert.areEqual('Persona edit', [SELECT Subject FROM Case WHERE Id = :row.Id].Subject);
    }
}
