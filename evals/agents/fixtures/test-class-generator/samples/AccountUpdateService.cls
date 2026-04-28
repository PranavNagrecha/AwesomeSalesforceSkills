/**
 * AccountUpdateService — synthetic sample for test-class-generator eval.
 *
 * Exercises the scenario matrix the agent must hit:
 *   - DML on Account (insert + update)         -> bulk + happy-path
 *   - SOQL on Account                          -> bulk + happy-path
 *   - HTTP callout to a Named Credential       -> MockHttpResponseGenerator
 *   - `with sharing` keyword                   -> System.runAs(standardUser)
 *   - Custom exception thrown on bad input     -> negative path
 */
public with sharing class AccountUpdateService {

    public class AccountUpdateException extends Exception {}

    public static List<Account> refreshTier(Set<Id> accountIds) {
        if (accountIds == null || accountIds.isEmpty()) {
            throw new AccountUpdateException('accountIds is required');
        }

        List<Account> targets = [
            SELECT Id, Name, AnnualRevenue, Tier__c
            FROM Account
            WHERE Id IN :accountIds
            WITH SECURITY_ENFORCED
        ];

        for (Account a : targets) {
            a.Tier__c = a.AnnualRevenue != null && a.AnnualRevenue >= 1000000 ? 'Enterprise' : 'SMB';
        }
        update targets;
        return targets;
    }

    public static String fetchExternalScore(Id accountId) {
        if (accountId == null) {
            throw new AccountUpdateException('accountId is required');
        }
        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:Risk_Scoring_API/v1/score?id=' + accountId);
        req.setMethod('GET');
        Http http = new Http();
        HttpResponse res = http.send(req);
        if (res.getStatusCode() != 200) {
            throw new AccountUpdateException('Risk API returned ' + res.getStatusCode());
        }
        return res.getBody();
    }
}
