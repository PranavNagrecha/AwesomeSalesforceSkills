/**
 * Pre-repair Gotcha 15 shape: plain factory insert inside a permissioned runAs,
 * ahead of Test.startTest(). Expect fixture-seeded-as-persona WARN.
 */
@IsTest
private class PositivePlainInsertInRunAsTest {

    @IsTest
    static void seedsInsideRunAsThenActs() {
        User agent = [SELECT Id FROM User WHERE Alias = 'agt1' LIMIT 1];

        System.runAs(agent) {
            insert TestDataFactory.createCases(1, null, null);

            Test.startTest();
            List<Case> rows = [SELECT Id FROM Case LIMIT 1];
            Assert.areEqual(1, rows.size(), 'seeded Case must be visible to the persona');
            Test.stopTest();
        }
    }
}
