/**
 * ContactRollupService — synthetic sample for the soql-optimizer agent eval.
 * Intentionally inefficient. Do not deploy.
 *
 * Carries four canonical SOQL anti-patterns the optimizer should catch:
 *   1. query-in-loop          (P0) — inner SELECT inside a for-loop
 *   2. select-star            (P1) — many unused fields
 *   3. no-security            (P1) — no WITH SECURITY_ENFORCED / USER_MODE
 *   4. missing-limit          (P2) — top-level query has no LIMIT
 */
public class ContactRollupService {

    public Map<Id, Integer> countContactsPerAccount() {
        Map<Id, Integer> result = new Map<Id, Integer>();
        List<Account> accts = [
            SELECT Id, Name, BillingStreet, BillingCity, BillingState,
                   BillingPostalCode, BillingCountry, ShippingStreet,
                   ShippingCity, ShippingState, ShippingPostalCode,
                   ShippingCountry, Phone, Fax, Website, Industry,
                   AnnualRevenue, NumberOfEmployees, Description,
                   OwnerId, AccountSource, Type, ParentId,
                   Rating, CreatedDate, LastModifiedDate
            FROM Account
        ];
        for (Account a : accts) {
            List<Contact> kids = [
                SELECT Id, FirstName, LastName, Email, Phone, AccountId,
                       MailingCountry, Title, Department, LeadSource
                FROM Contact
                WHERE AccountId = :a.Id
            ];
            result.put(a.Id, kids.size());
        }
        return result;
    }
}
