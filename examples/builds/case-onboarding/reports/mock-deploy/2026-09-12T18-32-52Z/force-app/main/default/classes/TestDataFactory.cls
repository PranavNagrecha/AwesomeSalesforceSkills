/**
 * TestDataFactory — canonical bulk-safe factory for common SObjects.
 *
 * Rules:
 *  - Every `createXxx(count, overrides)` returns `count` records and does NOT
 *    insert them. Callers insert when they need to.
 *  - Defaults are realistic (names, emails) so tests don't rely on generator
 *    randomness.
 *  - Overrides map supports any field — not a closed list.
 *  - Always bulk. Never call `createAccount()` inside a loop.
 *  - Lookup arguments (e.g. `accountId`) are assigned only when non-null: at
 *    API 67.0+ Apex runs in user context by default, so a test's plain
 *    `insert` checks FLS on every populated field, and a lookup assigned
 *    from a null argument still counts as populated.
 */
@IsTest
public class TestDataFactory {

    public static List<Account> createAccounts(Integer count, Map<String, Object> overrides) {
        List<Account> out = new List<Account>();
        for (Integer i = 0; i < count; i++) {
            Account a = new Account(Name = 'Test Account ' + i);
            applyOverrides(a, overrides);
            out.add(a);
        }
        return out;
    }

    public static List<Contact> createContacts(Integer count, Id accountId, Map<String, Object> overrides) {
        List<Contact> out = new List<Contact>();
        for (Integer i = 0; i < count; i++) {
            Contact c = new Contact(
                FirstName = 'Test',
                LastName  = 'Contact ' + i,
                Email     = 'test.contact.' + i + '@example.com'
            );
            if (accountId != null) {
                c.AccountId = accountId;
            }
            applyOverrides(c, overrides);
            out.add(c);
        }
        return out;
    }

    public static List<Opportunity> createOpportunities(Integer count, Id accountId, Map<String, Object> overrides) {
        List<Opportunity> out = new List<Opportunity>();
        Date closeDate = Date.today().addMonths(1);
        for (Integer i = 0; i < count; i++) {
            Opportunity o = new Opportunity(
                Name      = 'Test Opp ' + i,
                StageName = 'Prospecting',
                CloseDate = closeDate,
                Amount    = 1000
            );
            if (accountId != null) {
                o.AccountId = accountId;
            }
            applyOverrides(o, overrides);
            out.add(o);
        }
        return out;
    }

    public static List<Case> createCases(Integer count, Id accountId, Map<String, Object> overrides) {
        List<Case> out = new List<Case>();
        for (Integer i = 0; i < count; i++) {
            Case c = new Case(
                Subject = 'Test Case ' + i,
                Status  = 'New',
                Origin  = 'Email'
            );
            if (accountId != null) {
                c.AccountId = accountId;
            }
            applyOverrides(c, overrides);
            out.add(c);
        }
        return out;
    }

    public static List<Lead> createLeads(Integer count, Map<String, Object> overrides) {
        List<Lead> out = new List<Lead>();
        for (Integer i = 0; i < count; i++) {
            Lead l = new Lead(
                FirstName = 'Test',
                LastName  = 'Lead ' + i,
                Company   = 'Test Co ' + i,
                Email     = 'test.lead.' + i + '@example.com',
                Status    = 'Open - Not Contacted'
            );
            applyOverrides(l, overrides);
            out.add(l);
        }
        return out;
    }

    public static Map<String, Id> bulkInsertStandardSet(Integer perType) {
        List<Account> accounts = createAccounts(perType, null);
        insert accounts;
        List<Contact> contacts = new List<Contact>();
        List<Opportunity> opps = new List<Opportunity>();
        for (Account a : accounts) {
            contacts.addAll(createContacts(2, a.Id, null));
            opps.addAll(createOpportunities(1, a.Id, null));
        }
        insert contacts;
        insert opps;
        return new Map<String, Id>{
            'firstAccountId'    => accounts[0].Id,
            'firstContactId'    => contacts[0].Id,
            'firstOppId'        => opps[0].Id
        };
    }

    // Seed fixtures in system mode so FLS on fixture-only fields (e.g. an admin-set
    // lookup) never blocks setup; run only the action under test as the persona.
    public static Database.SaveResult[] insertAsSystem(List<SObject> records) {
        return Database.insert(records, AccessLevel.SYSTEM_MODE);
    }

    private static void applyOverrides(SObject record, Map<String, Object> overrides) {
        if (overrides == null || overrides.isEmpty()) { return; }
        for (String key : overrides.keySet()) {
            record.put(key, overrides.get(key));
        }
    }
}
