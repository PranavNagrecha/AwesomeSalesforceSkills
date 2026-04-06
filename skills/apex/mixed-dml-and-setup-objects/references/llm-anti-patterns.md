# LLM Anti-Patterns — Mixed DML and Setup Objects

Common mistakes AI coding assistants make when generating or advising on mixed DML and setup objects.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Inserting User and Business Records in the Same Test Method Without Isolation

**What the LLM generates:**

```apex
@IsTest
static void testSomething() {
    Account acc = new Account(Name = 'Test');
    insert acc;
    User u = new User(/* fields */);
    insert u;
    // test logic
}
```

**Why it happens:** LLMs generate sequential DML as the simplest approach. Training data often contains older test patterns that predate the mixed DML enforcement or run in orgs where the error was not triggered due to test isolation settings.

**Correct pattern:**

```apex
@IsTest
static void testSomething() {
    Account acc = new Account(Name = 'Test');
    insert acc;
    User u;
    System.runAs(new User(Id = UserInfo.getUserId())) {
        u = new User(/* fields */);
        insert u;
    }
    // test logic using u
}
```

**Detection hint:** Look for `insert` of User, UserRole, Group, GroupMember, PermissionSet, or PermissionSetAssignment in the same method as non-setup object DML without an enclosing `System.runAs()`.

---

## Anti-Pattern 2: Using System.runAs() in Production Code to Avoid Mixed DML

**What the LLM generates:**

```apex
public class AccountService {
    public static void createAccountAndUser(String name, String email) {
        Account acc = new Account(Name = name);
        insert acc;
        System.runAs(new User(Id = UserInfo.getUserId())) {
            User u = new User(/* fields */);
            insert u;
        }
    }
}
```

**Why it happens:** LLMs learn `System.runAs()` as the mixed DML fix from test examples and incorrectly generalize it to production code. The training data rarely distinguishes between test-only and production-valid patterns.

**Correct pattern:**

```apex
public class AccountService {
    public static void createAccountAndUser(String name, String email) {
        Account acc = new Account(Name = name);
        insert acc;
        UserCreationService.createUserAsync(acc.Id, email);
    }
}

public class UserCreationService {
    @future
    public static void createUserAsync(Id accountId, String email) {
        User u = new User(/* fields */);
        insert u;
    }
}
```

**Detection hint:** `System.runAs` appearing in a class that is not annotated with `@IsTest` and not inside a test method.

---

## Anti-Pattern 3: Wrapping Non-Setup DML in System.runAs() Instead of Setup DML

**What the LLM generates:**

```apex
@IsTest
static void testMixed() {
    User u = new User(/* fields */);
    insert u;
    System.runAs(u) {
        Account acc = new Account(Name = 'Test');
        insert acc; // Error: setup DML already happened outside runAs
    }
}
```

**Why it happens:** LLMs confuse "run the test as a specific user" with "isolate DML contexts." They place `System.runAs()` around the business logic instead of around the setup-object creation.

**Correct pattern:**

```apex
@IsTest
static void testMixed() {
    Account acc = new Account(Name = 'Test');
    insert acc;
    User u;
    System.runAs(new User(Id = UserInfo.getUserId())) {
        u = new User(/* fields */);
        insert u;
    }
    System.runAs(u) {
        // Business logic assertions here
    }
}
```

**Detection hint:** Setup-object DML (User insert) appearing before and outside the `System.runAs()` block, with non-setup DML inside it.

---

## Anti-Pattern 4: Forgetting That PermissionSetAssignment Is a Setup Object

**What the LLM generates:**

```apex
@IsTest
static void testWithPermSet() {
    Account acc = new Account(Name = 'Test');
    insert acc;
    User u = [SELECT Id FROM User WHERE Username = 'test@example.com' LIMIT 1];
    PermissionSet ps = [SELECT Id FROM PermissionSet WHERE Name = 'My_Perm' LIMIT 1];
    insert new PermissionSetAssignment(AssigneeId = u.Id, PermissionSetId = ps.Id);
    // MIXED_DML_OPERATION thrown
}
```

**Why it happens:** LLMs frequently treat only `User` as a setup object. `PermissionSetAssignment`, `GroupMember`, and `QueueSObject` are less commonly discussed in training data.

**Correct pattern:**

```apex
@IsTest
static void testWithPermSet() {
    Account acc = new Account(Name = 'Test');
    insert acc;
    User u = [SELECT Id FROM User WHERE Username = 'test@example.com' LIMIT 1];
    System.runAs(new User(Id = UserInfo.getUserId())) {
        PermissionSet ps = [SELECT Id FROM PermissionSet WHERE Name = 'My_Perm' LIMIT 1];
        insert new PermissionSetAssignment(AssigneeId = u.Id, PermissionSetId = ps.Id);
    }
}
```

**Detection hint:** `PermissionSetAssignment`, `GroupMember`, or `QueueSObject` DML outside a `System.runAs()` block in a method that also performs non-setup DML.

---

## Anti-Pattern 5: Using Try/Catch to Swallow the Mixed DML Exception

**What the LLM generates:**

```apex
try {
    insert acc;
    insert user;
} catch (DmlException e) {
    if (e.getMessage().contains('MIXED_DML_OPERATION')) {
        // Silently ignore
    }
}
```

**Why it happens:** LLMs sometimes default to exception handling as a universal fix. They treat the error as recoverable when it is actually a transaction design problem. The DML that threw the exception did not commit.

**Correct pattern:**

Separate the DML into compliant transaction boundaries using `System.runAs()` (tests) or `@future` (production). Never catch and swallow `MIXED_DML_OPERATION`.

**Detection hint:** `catch` block referencing `MIXED_DML_OPERATION` string with no re-throw or meaningful recovery logic.

---

## Anti-Pattern 6: Assuming Queueable Solves Mixed DML in the Same Transaction

**What the LLM generates:**

```apex
public class MyTriggerHandler {
    public void afterInsert(List<Account> accounts) {
        // Setup DML here -- WRONG
        User u = new User(/* fields */);
        insert u;
        System.enqueueJob(new SomeQueueable(accounts));
    }
}
```

**Why it happens:** LLMs know Queueable is async and assume it creates a separate transaction for all surrounding DML. But the setup DML before the enqueue call is still in the current transaction.

**Correct pattern:**

Move the setup-object DML into the Queueable's `execute()` method so it runs in the new transaction:

```apex
public class UserCreationQueueable implements Queueable {
    private List<Id> accountIds;
    public UserCreationQueueable(List<Id> ids) { this.accountIds = ids; }
    public void execute(QueueableContext ctx) {
        // Setup DML here -- runs in separate transaction
        User u = new User(/* fields */);
        insert u;
    }
}
```

**Detection hint:** Setup-object DML appearing in the same method as `System.enqueueJob()`, before the enqueue call.
