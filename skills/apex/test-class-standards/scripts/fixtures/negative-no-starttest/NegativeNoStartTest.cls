/**
 * Plain helper test with no Test.startTest() anywhere — rule must stay silent
 * even though a permissioned runAs seeds with plain factory DML.
 */
@IsTest
private class NegativeNoStartTest {

    @IsTest
    static void helperInsertsInsideRunAs() {
        User agent = [SELECT Id FROM User WHERE Alias = 'agt1' LIMIT 1];

        System.runAs(agent) {
            insert createCases(1);
        }

        Assert.areEqual(1, [SELECT COUNT() FROM Case], 'helper seeded one Case');
    }

    private static List<Case> createCases(Integer count) {
        List<Case> out = new List<Case>();
        for (Integer i = 0; i < count; i++) {
            out.add(new Case(Subject = 'Helper ' + i, Origin = 'Web'));
        }
        return out;
    }
}
