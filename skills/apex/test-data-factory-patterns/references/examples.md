# Examples — Test Data Factory Patterns

## Example 1: Account-Contact-Opportunity Hierarchy Factory

**Scenario:** A sales org's trigger suite tests require creating Account > Contact > Opportunity hierarchies across 40 test methods. Without a factory, each test method has 15–20 lines of setup code that duplicates field values.

**Problem:** An admin adds a required validation rule to Opportunity: `CloseDate must be a business day`. This breaks every test method that creates Opportunities with `Date.today()` on a weekend, producing 40 test failures simultaneously.

**Solution:** Centralize Opportunity creation in a factory with a business-day safe default:

```apex
@IsTest
public class TestDataFactory {
  public static Account createAccount(String name, Boolean doInsert) {
    Account a = new Account(Name = name, BillingCity = 'Chicago', BillingState = 'IL', BillingCountry = 'US');
    if (doInsert) insert a;
    return a;
  }

  public static Contact createContact(Id accountId, String firstName, String lastName, Boolean doInsert) {
    Contact c = new Contact(AccountId = accountId, FirstName = firstName, LastName = lastName,
                            Email = firstName.toLowerCase() + '.' + lastName.toLowerCase() + '@test.example.com');
    if (doInsert) insert c;
    return c;
  }

  public static Opportunity createOpportunity(Id accountId, String name, Boolean doInsert) {
    // next Monday as a safe business-day CloseDate
    Date closeDate = Date.today().addDays(7 - Math.mod(Date.today().dayOfWeek() - 2, 7));
    Opportunity o = new Opportunity(AccountId = accountId, Name = name, StageName = 'Prospecting', CloseDate = closeDate);
    if (doInsert) insert o;
    return o;
  }
}
```

When the validation rule is added, only `createOpportunity` needs updating — all 40 test methods pass again with one change.

**Why it works:** Centralization means one fix heals all tests. The `Boolean doInsert` parameter lets callers build object graphs in memory (doInsert=false) and insert in bulk at the end, staying within DML limits.

---

## Example 2: Portal User Factory with Mixed DML Workaround

**Scenario:** A B2B portal org's test suite needs to create portal users (Experience Cloud Customer Community users) linked to Contact records and test their data access. The original test keeps throwing `MIXED_DML_OPERATION`.

**Problem:**
```apex
// This fails with MIXED_DML_OPERATION
Account acc = new Account(Name = 'Portal Customer');
insert acc;
Contact con = new Contact(AccountId = acc.Id, LastName = 'Smith');
insert con;
Profile p = [SELECT Id FROM Profile WHERE Name = 'Customer Community User' LIMIT 1];
User portalUser = new User(ContactId = con.Id, ProfileId = p.Id, Username = 'test@example.com',
                           Alias = 'tuser', Email = 'test@example.com', EmailEncodingKey = 'UTF-8',
                           LastName = 'Smith', LanguageLocaleKey = 'en_US', LocaleSidKey = 'en_US',
                           TimeZoneSidKey = 'America/Chicago');
insert portalUser;  // MIXED_DML_OPERATION error here
```

**Solution:**

```apex
@IsTest
static void testPortalUserAccess() {
  // Non-setup objects first
  Account acc = TestDataFactory.createAccount('Portal Customer', true);
  Contact con = TestDataFactory.createContact(acc.Id, 'John', 'Smith', true);

  // Setup objects (User) inside System.runAs
  User portalUser;
  System.runAs(new User(Id = UserInfo.getUserId())) {
    Profile p = [SELECT Id FROM Profile WHERE Name = 'Customer Community User' LIMIT 1];
    portalUser = new User(
      ContactId = con.Id, ProfileId = p.Id,
      Username = 'portal.test.' + DateTime.now().getTime() + '@test.example.com',
      Alias = 'ptuser', Email = 'portal.test@example.com',
      EmailEncodingKey = 'UTF-8', LastName = 'Smith',
      LanguageLocaleKey = 'en_US', LocaleSidKey = 'en_US',
      TimeZoneSidKey = 'America/Chicago'
    );
    insert portalUser;
  }

  System.runAs(portalUser) {
    // Test portal user's data access here
    List<Account> visible = [SELECT Id FROM Account WHERE Id = :acc.Id WITH USER_MODE];
    System.assertEquals(1, visible.size(), 'Portal user should see their linked account');
  }
}
```

**Why it works:** `System.runAs()` creates a new transaction context for setup object DML, bypassing the Mixed DML restriction. The `DateTime.now().getTime()` suffix ensures the username is unique across test runs.
