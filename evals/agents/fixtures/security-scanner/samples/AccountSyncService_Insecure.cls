/**
 * AccountSyncService — synthetic sample for the security-scanner agent eval.
 * Intentionally insecure. Do not deploy.
 *
 * Carries five canonical findings the scanner should catch:
 *   1. no-sharing-keyword            (P1) — class lacks with/without/inherited sharing
 *   2. callout-without-named-credential (P0) — literal HTTPS endpoint
 *   3. hardcoded-secret              (P0) — API key inline as a string literal
 *   4. no-flsd-on-dml                (P1) — update without SecurityUtils
 *   5. soql-no-security              (P1) — SOQL without WITH SECURITY_ENFORCED / USER_MODE
 */
public class AccountSyncService {

    private static final String SYNC_API_KEY = 'sk_live_FIXTURE_REDACTED_NOT_A_REAL_KEY_DO_NOT_SCAN';

    @AuraEnabled
    public static void syncAccount(Id accountId, String newCountry) {
        List<Account> accts = [
            SELECT Id, BillingCountry, OwnerId, Industry
            FROM Account
            WHERE Id = :accountId
        ];
        if (accts.isEmpty()) {
            return;
        }
        Account a = accts[0];
        a.BillingCountry = newCountry;
        update a;

        Http http = new Http();
        HttpRequest req = new HttpRequest();
        req.setEndpoint('https://erp.example.com/api/sync');
        req.setMethod('POST');
        req.setHeader('Authorization', 'Bearer ' + SYNC_API_KEY);
        req.setBody(JSON.serialize(a));
        HttpResponse res = http.send(req);
        System.debug('ERP sync response: ' + res.getBody());
    }
}
