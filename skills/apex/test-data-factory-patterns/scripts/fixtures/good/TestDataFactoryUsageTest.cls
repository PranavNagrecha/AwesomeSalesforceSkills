@IsTest
private class TestDataFactoryUsageTest {
    @TestSetup
    static void setup() {
        TestDataFactory.createAccounts(200, true);
    }

    @IsTest
    static void bulkAccountsAreVisibleInEveryMethod() {
        Assert.areEqual(200, [SELECT COUNT() FROM Account WHERE Name LIKE 'Factory Account %'],
            'Setup records are available to each test method');
    }

    @IsTest
    static void deletionsRollBackBetweenMethods() {
        delete [SELECT Id FROM Account WHERE Name = 'Factory Account 0'];
        Assert.areEqual(199, [SELECT COUNT() FROM Account WHERE Name LIKE 'Factory Account %'],
            'The delete is local to this method; the other method still sees 200');
    }

    @IsTest
    static void createsUserWithRoleAfterNonSetupDml() {
        insert new Account(Name = 'Mixed DML Guard');
        User u = TestDataFactory.createUserWithAccess('Standard User', 'Factory Test Role', null);
        User reloaded = [SELECT Id, UserRoleId FROM User WHERE Id = :u.Id];
        Assert.isNotNull(reloaded.UserRoleId, 'Role assigned without a mixed DML error');
    }

    @IsTest
    static void contactsAreBuiltInOneStatement() {
        List<Account> parents = [SELECT Id FROM Account WHERE Name LIKE 'Factory Account %' LIMIT 50];
        Integer before = Limits.getDmlStatements();
        TestDataFactory.createContacts(parents, 2, true);
        Assert.areEqual(before + 1, Limits.getDmlStatements(), 'Bulk factory uses a single insert');
    }
}
