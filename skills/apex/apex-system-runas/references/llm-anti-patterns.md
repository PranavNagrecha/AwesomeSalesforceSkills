# LLM Anti-Patterns — Apex System.runAs

Common mistakes AI coding assistants make with `System.runAs` in tests.

## Anti-Pattern 1: Using runAs to "test FLS"

**What the LLM generates:**

```
System.runAs(lowPrivUser) {
    Account a = [SELECT Hidden__c FROM Account LIMIT 1];
    // expects an exception; gets a value
}
```

**Why it happens:** Model assumes user-context extends to FLS.

**Correct pattern:**

```
runAs enforces sharing and profile-level CRUD, NOT field-level
security. For FLS coverage, use one of:

1. SELECT ... WITH USER_MODE
2. Security.stripInaccessible(AccessType.READABLE, records)
3. Schema.describeSObjectResult().fields.getMap().get('X').getDescribe().isAccessible()

The runAs test will silently pass while the production code
exposes fields the user shouldn't see.
```

**Detection hint:** FLS-related assertions inside `System.runAs` without `WITH USER_MODE` or `stripInaccessible`.

---

## Anti-Pattern 2: Forgetting the mixed-DML guard in @TestSetup

**What the LLM generates:**

```
@TestSetup
static void setup() {
    User u = new User(...);
    insert u;
    insert new Account(OwnerId = u.Id);  // MIXED_DML_OPERATION
}
```

**Why it happens:** Model doesn't remember setup-object classification.

**Correct pattern:**

```
@TestSetup
static void setup() {
    User u;
    System.runAs(new User(Id = UserInfo.getUserId())) {
        u = new User(...);
        insert u;
    }
    insert new Account(OwnerId = u.Id);
}

The no-op runAs wraps the setup-object DML in its own DML context,
then the outer transaction can insert the sObject normally.
```

**Detection hint:** Test or setup method inserting `User`/`Group`/`UserRole` alongside sObject DML without `System.runAs`.

---

## Anti-Pattern 3: runAs outside test context

**What the LLM generates:**

```
public class AdminService {
    public void doThing(User u) {
        System.runAs(u) { /* ... */ }  // ERROR: only legal in tests
    }
}
```

**Why it happens:** Model confuses runAs with a general impersonation API.

**Correct pattern:**

```
runAs is test-only. In production code, there is no user switching.
If your use case is:

- Running queries with a specific profile's permissions: use
  WITH USER_MODE or Database.query with AccessLevel.
- Executing DML as system: @future or @InvocableMethod with
  proper auth context.
- True user impersonation: Connected App OAuth with refresh token.
```

**Detection hint:** `System.runAs` in a non-test `.cls` file (no `@IsTest` anywhere).

---

## Anti-Pattern 4: runAs won't "elevate" admin to non-admin

**What the LLM generates:** Expects runAs to restrict a modify-all-data running test user.

**Why it happens:** Model assumes runAs fully adopts target user privileges.

**Correct pattern:**

```
If the OUTER test user has "View All Data" / "Modify All Data",
runAs only narrows in some dimensions. For sharing tests, the
TARGET user's lack of those perms is what gives you a meaningful
result — make sure the User you impersonate genuinely has limited
privileges and is on a profile without admin flags.

Also: runAs doesn't bypass setup-object permission checks — you
cannot runAs a user lacking "Manage Users" and then insert a User.
```

**Detection hint:** Sharing test seemingly passes because the outer test user is admin — the inner assertions don't exercise the intended limits.

---

## Anti-Pattern 5: Querying User by profile name in multi-org code

**What the LLM generates:**

```
User u = [SELECT Id FROM User WHERE Profile.Name = 'Standard User' LIMIT 1];
System.runAs(u) { ... }
```

**Why it happens:** Model picks the first user available.

**Correct pattern:**

```
Profile names differ across orgs (renamed, translated, or custom).
The first "Standard User" may be a system integration account or
an already-deactivated user. Create a dedicated test user:

User u = new User(
    ProfileId = [SELECT Id FROM Profile WHERE Name = 'Standard User'].Id,
    Username = 'test.user.' + DateTime.now().getTime() + '@example.com',
    Email = 'test@example.com',
    Alias = 'tstu',
    TimeZoneSidKey = 'America/Los_Angeles',
    LocaleSidKey = 'en_US',
    EmailEncodingKey = 'UTF-8',
    LanguageLocaleKey = 'en_US',
    LastName = 'Tester'
);
insert u;
// assign permsets
// now runAs(u)

Put this in a TestUserFactory so every test uses a controlled fixture.
```

**Detection hint:** Test method queries `User WHERE Profile.Name = '...' LIMIT 1` and relies on finding one.
