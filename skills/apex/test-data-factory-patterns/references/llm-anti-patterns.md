# LLM Anti-Patterns — Test Data Factory Patterns

## 1. Using @isTest(SeeAllData=true) Instead of Factory Methods

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

**Correct pattern:** Tests that read org data are fragile, environment-specific, and cannot run in scratch orgs. Use factory methods to create all test data. `SeeAllData=true` is a legacy pattern — avoid it in all new test classes.

**Detection hint:** `@isTest(SeeAllData=true)` on any test class.

---

## 2. Not Using System.runAs() for Portal User Creation

**What the LLM generates wrong:**
```apex
Account acc = new Account(Name='Portal Customer');
insert acc;
Contact con = new Contact(AccountId=acc.Id, LastName='Smith');
insert con;
User u = new User(ContactId=con.Id, ...);
insert u; // MIXED_DML_OPERATION exception at runtime
```

**Why it happens:** The LLM generates standard DML patterns without knowing the Mixed DML restriction.

**Correct pattern:**
```apex
// Non-setup objects first
Account acc = new Account(Name='Portal Customer');
insert acc;
Contact con = new Contact(AccountId=acc.Id, LastName='Smith');
insert con;
// User (setup object) inside System.runAs
System.runAs(new User(Id=UserInfo.getUserId())) {
  User u = new User(ContactId=con.Id, ...);
  insert u;
}
```

**Detection hint:** Any test that inserts a `User` record with a `ContactId` (portal user) in the same DML transaction as Account or Contact inserts.

---

## 3. Inserting Factory Records One at a Time in a Loop

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

## 4. Hardcoding Profile IDs or RecordType IDs

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

## 5. Missing @IsTest Annotation on the Factory Class

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
