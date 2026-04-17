@IsTest
private class SummarizeAccountCasesActionTest {

    @IsTest
    static void happyPath_returnsSummary() {
        Account a = new Account(Name = 'Acme');
        insert a;
        insert new Case(AccountId = a.Id, Subject = 'Test case 1');
        insert new Case(AccountId = a.Id, Subject = 'Test case 2');

        SummarizeAccountCasesAction.Request req = new SummarizeAccountCasesAction.Request();
        req.accountId = a.Id;

        Test.startTest();
        List<SummarizeAccountCasesAction.Response> res =
            SummarizeAccountCasesAction.run(new List<SummarizeAccountCasesAction.Request>{ req });
        Test.stopTest();

        System.assertEquals(1, res.size(), 'one response per request');
        System.assertEquals(true, res[0].success, 'happy path should succeed');
        System.assert(res[0].summary != null && res[0].summary.contains('Acme'),
            'summary should name the account');
        System.assert(res[0].summary.contains('2 case'), 'summary should count cases');
    }

    @IsTest
    static void missingAccountId_reportsError() {
        SummarizeAccountCasesAction.Request req = new SummarizeAccountCasesAction.Request();
        req.accountId = null;

        List<SummarizeAccountCasesAction.Response> res =
            SummarizeAccountCasesAction.run(new List<SummarizeAccountCasesAction.Request>{ req });

        System.assertEquals(1, res.size());
        System.assertEquals(false, res[0].success);
        System.assertNotEquals(null, res[0].errorMessage, 'error message populated');
    }

    @IsTest
    static void unknownAccount_reportsNotFound() {
        Id fakeId = '001000000000000AAA';
        SummarizeAccountCasesAction.Request req = new SummarizeAccountCasesAction.Request();
        req.accountId = fakeId;

        List<SummarizeAccountCasesAction.Response> res =
            SummarizeAccountCasesAction.run(new List<SummarizeAccountCasesAction.Request>{ req });

        System.assertEquals(false, res[0].success);
        System.assert(res[0].errorMessage != null);
    }

    @IsTest
    static void bulkPath_noLimitsBreached() {
        List<Account> accs = new List<Account>();
        for (Integer i = 0; i < 20; i++) {
            accs.add(new Account(Name = 'Bulk ' + i));
        }
        insert accs;

        List<SummarizeAccountCasesAction.Request> reqs =
            new List<SummarizeAccountCasesAction.Request>();
        for (Account a : accs) {
            SummarizeAccountCasesAction.Request r = new SummarizeAccountCasesAction.Request();
            r.accountId = a.Id;
            reqs.add(r);
        }

        Test.startTest();
        List<SummarizeAccountCasesAction.Response> res = SummarizeAccountCasesAction.run(reqs);
        Test.stopTest();

        System.assertEquals(20, res.size());
        for (SummarizeAccountCasesAction.Response r : res) {
            System.assertEquals(true, r.success);
        }
    }

    @IsTest
    static void emptyInput_returnsEmpty() {
        List<SummarizeAccountCasesAction.Response> res =
            SummarizeAccountCasesAction.run(new List<SummarizeAccountCasesAction.Request>());
        System.assertEquals(0, res.size());
    }
}
