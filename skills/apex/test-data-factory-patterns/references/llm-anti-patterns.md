# LLM Anti-Patterns — Test Data Factory Patterns

## Anti-Pattern 1: Using @isTest(SeeAllData=true) Instead of Factory Methods

**What the LLM generates wrong:**
```apex
@isTest(SeeAllData=true)
public class MyTest {
  @isTest
  static void testSomething() {
    Account acc = [SELECT Id FROM Account LIMIT 1]; // Reads org data
  }
}
```

**Why it happens:** `SeeAllData=true` is a documented annotation. The LLM suggests it when a developer says "I need to access existing data in tests."

**Correct pattern:** Tests that read org data are fragile, environment-specific, and cannot run in scratch orgs. Use factory methods to create all test data. A single `SeeAllData=true` method also makes `@testSetup` unsupported for its whole class (Apex Developer Guide, Test Setup Method Considerations).

**Detection hint:** `@isTest(SeeAllData=true)` on any test class.

---

## Anti-Pattern 2: Blaming every user insert for mixed DML, or wrapping nothing

**What the LLM generates wrong:**
```apex
Account acc = new Account(Name = 'Portal Customer');
insert acc;
User owner = new User(UserRoleId = ceoRole.Id, /* other required fields */ LastName = 'Owner');
insert owner;                                   // setup object with a role
insert new PermissionSetAssignment(AssigneeId = owner.Id, PermissionSetId = ps.Id);
```

**Why it happens:** The model either does not know the mixed DML rule, or over-generalizes it to "users cannot be inserted with accounts". The Apex Developer Guide allows a `User` insert alongside other sObjects when `UserRoleId` is null; it is the role, the permission set assignment, the group membership, and the other listed setup objects that collide.

**Correct pattern:**
```apex
Account acc = new Account(Name = 'Portal Customer');
insert acc;
User owner;
System.runAs(new User(Id = UserInfo.getUserId())) {
  owner = TestDataFactory.newUser('Standard User');
  owner.UserRoleId = ceoRole.Id;
  insert owner;
  insert new PermissionSetAssignment(AssigneeId = owner.Id, PermissionSetId = ps.Id);
}
```

**Detection hint:** A test method that performs DML on Account, Contact, or Case and also inserts a `User` with `UserRoleId`, a `PermissionSetAssignment`, a `GroupMember`, or a `UserRole`, with none of it inside `System.runAs`.

---

## Anti-Pattern 3: Inserting Factory Records One at a Time in a Loop

**What the LLM generates wrong:**
```apex
public static void createCases(Id accountId, Integer count) {
  for (Integer i = 0; i < count; i++) {
    insert new Case(AccountId=accountId, Subject='Test ' + i);  // 150 DML limit
  }
}
```

**Why it happens:** Per-iteration DML is a natural loop pattern. The LLM does not always apply bulkification principles to test factory methods.

**Correct pattern:**
```apex
public static List<Case> createCases(Id accountId, Integer count, Boolean doInsert) {
  List<Case> cases = new List<Case>();
  for (Integer i = 0; i < count; i++) {
    cases.add(new Case(AccountId=accountId, Subject='Test ' + i));
  }
  if (doInsert) insert cases;
  return cases;
}
```

**Detection hint:** A loop body that contains an `insert` or `upsert` statement for a single record.

---

## Anti-Pattern 4: Hardcoding Profile IDs or RecordType IDs

**What the LLM generates wrong:**
```apex
User u = new User(ProfileId='00e50000000rFxy', ...); // Org-specific ID
```

**Why it happens:** The LLM often uses placeholder IDs from training examples.

**Correct pattern:**
```apex
Profile p = [SELECT Id FROM Profile WHERE Name='Standard User' LIMIT 1];
User u = new User(ProfileId=p.Id, ...);
```

**Detection hint:** Any hardcoded 15 or 18-character Salesforce ID (starting with `00e`, `012`, `00D`, etc.) inside a factory method.

---

## Anti-Pattern 5: Missing @IsTest Annotation on the Factory Class

**What the LLM generates wrong:**
```apex
public class TestDataFactory {  // Missing @IsTest
  public static Account createAccount() { ... }
}
```

**Why it happens:** The LLM treats factory classes as utility classes (public without annotations). It may not know that `@IsTest` on the class excludes it from org code size limits.

**Correct pattern:**
```apex
@IsTest
public class TestDataFactory {
  public static Account createAccount() { ... }
}
```

Without `@IsTest` at the class level, the factory's code counts against the org's 6 MB Apex code limit. For large orgs with comprehensive factories, this can consume significant code capacity.

**Detection hint:** Any `TestDataFactory` or `TestFactory` class that lacks `@IsTest` at the class level.

---

## Anti-Pattern 6: Caching setup Ids in static variables

**What the LLM generates wrong:**
```apex
@IsTest
private class InvoiceServiceTest {
  static Id accountId;
  @TestSetup
  static void setup() {
    Account a = TestDataFactory.createAccount('Acme', true);
    accountId = a.Id;   // lost before any test method runs
  }
  @IsTest
  static void createsInvoice() {
    InvoiceService.create(accountId); // accountId is null here
  }
}
```

**Why it happens:** The model treats the test class like a normal object whose fields persist. The Apex Developer Guide says every test method, including the setup method, runs as a separate transaction and the static context is reinitialized before each one.

**Correct pattern:**
```apex
@IsTest
static void createsInvoice() {
  Account a = [SELECT Id FROM Account WHERE Name = 'Acme' LIMIT 1];
  InvoiceService.create(a.Id);
}
```

**Detection hint:** A static field assigned inside a `@TestSetup` method and read inside an `@IsTest` method.

---

## Anti-Pattern 7: Hardcoding usernames and other unique values

**What the LLM generates wrong:**
```apex
User u = new User(Username = 'test@test.com', Alias = 'test', /* ... */ LastName = 'Test');
insert u;
```

**Why it happens:** Training examples use short literals. The Apex Developer Guide's own runAs example builds the username from `DateTime.now().getTime()` to keep it unique, and its isolation section notes that duplicate values on unique-constrained fields fail even in tests. UNVERIFIED (2026-10-03): the claim that usernames must be unique across every Salesforce org, not only within one org, is not stated in the fetched guide.

**Correct pattern:**
```apex
String unique = String.valueOf(DateTime.now().getTime()) + String.valueOf(Crypto.getRandomInteger());
User u = new User(Username = 'factory.' + unique + '@example.com', Alias = 'fact', /* ... */ LastName = 'Factory');
```

**Detection hint:** A `Username = '...'` string literal with no concatenated unique suffix inside a test or factory class.

