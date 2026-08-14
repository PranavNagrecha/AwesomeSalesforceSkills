/**
 * AccountSyncService — synthetic sample for the security-scanner agent eval.
 * Intentionally insecure. Do not deploy.
 *
 * Carries five canonical findings the scanner should catch:
 *   1. no-sharing-keyword            (P1) — class lacks with/without/inherited sharing
 *   2. callout-without-named-credential (P0) — literal HTTPS endpoint
 *   3. hardcoded-secret              (P0) — API key inline as a string literal
 *   4. no-flsd-on-dml                (P1) — update without SecurityUtils
 *   5. soql-no-security              (P1) — SOQL that does not enforce FLS
 *
 * Findings 1 and 5 are BOTH version-dependent, and this file deliberately ships
 * without a .cls-meta.xml so a scanner has to notice that rather than assume.
 * At API 67.0+ a class with no sharing keyword defaults to `with sharing` and
 * SOQL already runs in user mode, so the correct scanner output is a stated
 * assumption about apiVersion, not a flat P1. The remedy for finding 5 is
 * `WITH USER_MODE` — never `WITH SECURITY_ENFORCED`, which was removed in 67.0
 * and does not compile there. See agents/_shared/AGENT_CONTRACT.md
 * "Apex security idiom by API version".
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
