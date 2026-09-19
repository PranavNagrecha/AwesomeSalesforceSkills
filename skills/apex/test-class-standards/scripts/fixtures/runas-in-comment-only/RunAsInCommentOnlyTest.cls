/**
 * The only System.runAs(rep) in this class is in this comment. The test runs as the
 * deploying user, so the user-mode-test-without-runas ERROR must fire. Before the
 * 2026-09-19 fix the prose call satisfied the check and this class passed.
 */
@IsTest
private class RunAsInCommentOnlyTest {
    @IsTest
    static void loadsAsDeployingUser() {
        Opportunity o = new Opportunity(Name = 'x', StageName = 'Qualify', CloseDate = Date.today());
        insert o;
        Test.startTest();
        List<Opportunity> rows = OppService.load(new Set<Id>{ o.Id });
        Test.stopTest();
        Assert.areEqual(1, rows.size(), 'one row');
    }
}
