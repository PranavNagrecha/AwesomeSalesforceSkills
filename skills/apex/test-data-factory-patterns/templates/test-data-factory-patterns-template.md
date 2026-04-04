# Test Data Factory Patterns — Factory Class Template

Use this as the starting structure for a new Apex test data factory class.

```apex
/**
 * TestDataFactory - Centralized test data creation utility.
 *
 * @IsTest annotation: excludes this class from the org's 6 MB code size limit.
 * All methods are static for easy use in test classes.
 * Use Boolean doInsert = false to build object graphs in memory before bulk inserting.
 */
@IsTest
public class TestDataFactory {

    // ─── ACCOUNT ────────────────────────────────────────────────────────────────

    /**
     * Creates a minimal valid Account.
     * @param name      Account name (required)
     * @param doInsert  true = insert immediately; false = return unsaved record
     */
    public static Account createAccount(String name, Boolean doInsert) {
        Account a = new Account(
            Name            = name,
            BillingCity     = 'San Francisco',
            BillingState    = 'CA',
            BillingCountry  = 'US'
        );
        if (doInsert) insert a;
        return a;
    }

    /**
     * Bulk factory: creates count Accounts.
     */
    public static List<Account> createAccounts(Integer count, Boolean doInsert) {
        List<Account> accounts = new List<Account>();
        for (Integer i = 0; i < count; i++) {
            accounts.add(new Account(
                Name            = 'Test Account ' + i,
                BillingCity     = 'San Francisco',
                BillingState    = 'CA',
                BillingCountry  = 'US'
            ));
        }
        if (doInsert) insert accounts;
        return accounts;
    }

    // ─── CONTACT ────────────────────────────────────────────────────────────────

    public static Contact createContact(
            Id accountId, String firstName, String lastName, Boolean doInsert) {
        Contact c = new Contact(
            AccountId   = accountId,
            FirstName   = firstName,
            LastName    = lastName,
            Email       = firstName.toLowerCase() + '.' + lastName.toLowerCase()
                          + '@test.example.com'
        );
        if (doInsert) insert c;
        return c;
    }

    // ─── OPPORTUNITY ────────────────────────────────────────────────────────────

    public static Opportunity createOpportunity(
            Id accountId, String name, String stageName, Boolean doInsert) {
        Opportunity o = new Opportunity(
            AccountId   = accountId,
            Name        = name,
            StageName   = stageName != null ? stageName : 'Prospecting',
            CloseDate   = Date.today().addDays(30)
        );
        if (doInsert) insert o;
        return o;
    }

    // ─── CASE ───────────────────────────────────────────────────────────────────

    public static Case createCase(Id accountId, String subject, Boolean doInsert) {
        Case c = new Case(
            AccountId   = accountId,
            Subject     = subject,
            Status      = 'New',
            Origin      = 'Web'
        );
        if (doInsert) insert c;
        return c;
    }

    public static List<Case> createCases(Id accountId, Integer count, Boolean doInsert) {
        List<Case> cases = new List<Case>();
        for (Integer i = 0; i < count; i++) {
            cases.add(new Case(
                AccountId   = accountId,
                Subject     = 'Test Case ' + i,
                Status      = 'New',
                Origin      = 'Web'
            ));
        }
        // Single DML call — required for bulk trigger testing and DML limit compliance
        if (doInsert) insert cases;
        return cases;
    }

    // ─── USER (portal) ──────────────────────────────────────────────────────────
    // IMPORTANT: Always call this inside System.runAs() to avoid Mixed DML errors.
    // Non-setup objects (Account, Contact) must be created BEFORE calling this method.

    public static User createPortalUser(Id contactId, String profileName) {
        Profile p = [SELECT Id FROM Profile WHERE Name = :profileName LIMIT 1];
        return new User(
            ContactId           = contactId,
            ProfileId           = p.Id,
            Username            = 'portal.' + DateTime.now().getTime() + '@test.example.com',
            Alias               = 'puser',
            Email               = 'portal.test@test.example.com',
            EmailEncodingKey    = 'UTF-8',
            LastName            = 'TestPortal',
            LanguageLocaleKey   = 'en_US',
            LocaleSidKey        = 'en_US',
            TimeZoneSidKey      = 'America/Los_Angeles'
        );
        // Caller inserts inside System.runAs():
        // System.runAs(new User(Id = UserInfo.getUserId())) {
        //   User u = TestDataFactory.createPortalUser(con.Id, 'Customer Community User');
        //   insert u;
        // }
    }
}
```

---

## Usage Examples

### @testSetup with factory

```apex
@isTest
private class MyTriggerTest {

    @testSetup
    static void setup() {
        Account acc = TestDataFactory.createAccount('Shared Account', true);
        TestDataFactory.createCases(acc.Id, 200, true);
    }

    @isTest
    static void testBulkCaseCreation() {
        List<Case> cases = [SELECT Id, Status FROM Case];
        System.assertEquals(200, cases.size());
        // assertions...
    }
}
```

### Portal user factory

```apex
@isTest
static void testPortalUserAccess() {
    Account acc = TestDataFactory.createAccount('Portal Org', true);
    Contact con = TestDataFactory.createContact(acc.Id, 'Jane', 'Smith', true);

    User portalUser;
    System.runAs(new User(Id = UserInfo.getUserId())) {
        portalUser = TestDataFactory.createPortalUser(con.Id, 'Customer Community User');
        insert portalUser;
    }

    System.runAs(portalUser) {
        // test portal user data access
    }
}
```
