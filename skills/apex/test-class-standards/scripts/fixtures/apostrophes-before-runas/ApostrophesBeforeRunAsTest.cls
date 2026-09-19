/**
 * Comments carry possessive apostrophes: the rep's manager's approval, the owner's
 * record, the org's default, the team's quota. Each one used to open a phantom string literal in the
 * runAs scan and blank the real System.runAs below. Expect no ERROR.
 */
@IsTest
private class ApostrophesBeforeRunAsTest {
    @IsTest
    static void loadsAsPersona() {
        // the rep's fixtures are seeded in system mode, outside the persona's block
        Opportunity o = new Opportunity(Name = 'x', StageName = 'Qualify', CloseDate = Date.today());
        Database.insert(new List<Opportunity>{ o }, AccessLevel.SYSTEM_MODE); // reason: seed, not the action under test
        User rep = [SELECT Id FROM User WHERE Alias = 'rep1' LIMIT 1];
        System.runAs(rep) {
            Test.startTest();
            List<Opportunity> rows = OppService.load(new Set<Id>{ o.Id });
            Test.stopTest();
            Assert.areEqual(1, rows.size(), 'the persona row'); 
        }
    }
}
