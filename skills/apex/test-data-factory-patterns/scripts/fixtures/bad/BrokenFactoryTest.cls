@IsTest(SeeAllData=true)
private class BrokenFactoryTest {
    static Id accountId;

    @TestSetup
    static void setup() {
        Account a = new Account(Name = 'Acme');
        insert a;
        accountId = a.Id;
    }

    @IsTest
    static void mixesSetupAndNonSetupDml() {
        insert new Account(Name = 'Other');
        UserRole r = new UserRole(Name = 'Ops');
        insert r;
        User u = new User(Username = 'test@test.com', UserRoleId = r.Id, ProfileId = '00e000000000001AAA',
            Alias = 'tst', Email = 'test@test.com', EmailEncodingKey = 'UTF-8', LastName = 'T',
            LanguageLocaleKey = 'en_US', LocaleSidKey = 'en_US', TimeZoneSidKey = 'America/Los_Angeles');
        insert u;
        for (Integer i = 0; i < 200; i++) {
            insert new Case(Subject = 'Case ' + i);
        }
        System.assertNotEquals(null, accountId);
    }
}
