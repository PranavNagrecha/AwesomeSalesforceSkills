@IsTest
private class AccountDashboardControllerTest {

    @TestSetup
    static void setup() {
        List<Account> accounts = new List<Account>{
            new Account(Name = 'Wrapper Alpha'),
            new Account(Name = 'Wrapper Beta')
        };
        insert accounts;
        List<Opportunity> opps = new List<Opportunity>();
        for (Integer i = 0; i < 3; i++) {
            opps.add(new Opportunity(Name = 'Beta Open ' + i, AccountId = accounts[1].Id,
                StageName = 'Prospecting', CloseDate = Date.today().addDays(30)));
        }
        opps.add(new Opportunity(Name = 'Alpha Open', AccountId = accounts[0].Id,
            StageName = 'Prospecting', CloseDate = Date.today().addDays(30)));
        opps.add(new Opportunity(Name = 'Alpha Won', AccountId = accounts[0].Id,
            StageName = 'Closed Won', CloseDate = Date.today()));
        insert opps;
    }

    @IsTest
    static void sortsByOpenCountDescending() {
        Test.startTest();
        List<AccountRow> rows = AccountDashboardController.getAccountRows('openCount');
        Test.stopTest();
        System.assertEquals('Wrapper Beta', rows[0].accountName, 'most open opportunities first');
        System.assertEquals(3, rows[0].openOpportunityCount);
        System.assertEquals(1, rows[1].openOpportunityCount, 'closed opportunity not counted');
    }

    @IsTest
    static void sortsByNameByDefault() {
        List<AccountRow> rows = AccountDashboardController.getAccountRows(null);
        System.assertEquals('Wrapper Alpha', rows[0].accountName);
    }

    @IsTest
    static void comparatorsHandleNulls() {
        AccountRow blankName = new AccountRow();
        blankName.openOpportunityCount = null;
        AccountRow named = new AccountRow(new Account(Name = 'Zeta'), 5);

        List<AccountRow> byCount = new List<AccountRow>{ blankName, null, named };
        byCount.sort(new AccountRowComparators.ByOpenCountDesc());
        System.assertEquals(named, byCount[0], 'highest count first');
        System.assertEquals(null, byCount[2], 'null row last');

        List<AccountRow> byName = new List<AccountRow>{ blankName, named };
        byName.sort();
        System.assertEquals('Zeta', byName[0].accountName, 'null name sorts last');
    }
}
