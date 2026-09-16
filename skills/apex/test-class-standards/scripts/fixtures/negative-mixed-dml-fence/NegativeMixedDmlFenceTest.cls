/**
 * Setup-object DML inside the mixed-DML self-user fence is not a permissioned
 * runAs — must not fire fixture-seeded-as-persona.
 */
@IsTest
private class NegativeMixedDmlFenceTest {

    @IsTest
    static void seedsSetupObjectsInsideSelfUserFence() {
        Profile p = [SELECT Id FROM Profile WHERE Name = 'Standard User' LIMIT 1];
        User agent;

        System.runAs(new User(Id = UserInfo.getUserId())) {
            agent = new User(
                Alias = 'agt2',
                Email = 'agt2@example.com',
                EmailEncodingKey = 'UTF-8',
                LastName = 'Agent',
                LanguageLocaleKey = 'en_US',
                LocaleSidKey = 'en_US',
                ProfileId = p.Id,
                TimeZoneSidKey = 'America/Los_Angeles',
                UserName = 'agt2' + DateTime.now().getTime() + '@example.com'
            );
            insert agent;
            insert new PermissionSetAssignment(
                AssigneeId = agent.Id,
                PermissionSetId = [SELECT Id FROM PermissionSet WHERE Name = 'Case_Agent_Core' LIMIT 1].Id
            );
        }

        Test.startTest();
        Assert.isNotNull(agent.Id, 'mixed-DML fence must insert the persona user');
        Test.stopTest();
    }
}
