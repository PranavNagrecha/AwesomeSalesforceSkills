# LLM Anti-Patterns — Flow Testing

Common mistakes AI coding assistants make when generating or advising on Salesforce Flow testing.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Relying only on manual debug runs instead of Flow Tests

**What the LLM generates:**

```
"Click Debug in Flow Builder, enter test values, and verify the output."
```

**Why it happens:** Debug runs are the most visible testing tool. LLMs default to them because they are quick and interactive. But debug runs are not repeatable, not automated, and not included in deployment pipelines.

**Correct pattern:**

Use Flow Tests (Setup > Flow Tests) for repeatable, automated validation:

```
Flow Test: "New Case creates escalation task"
  Trigger: Create Case with Priority = High
  Assertions:
    - Task.Subject contains "Escalation"
    - Task.OwnerId = Manager's User ID
```

Combine Flow Tests with debug runs: use debug for exploration, Flow Tests for regression.

**Detection hint:** Testing advice that mentions only "Debug" mode without referencing Flow Tests or automated assertions.

---

## Anti-Pattern 2: Not testing fault paths

**What the LLM generates:**

```
"Create a Flow Test for the happy path: when a Case is created with Priority = High,
verify that a Task is created."
```

**Why it happens:** LLMs focus on positive scenarios. Fault paths — what happens when DML fails, required fields are missing, or external callouts time out — are equally important and often untested.

**Correct pattern:**

Create separate Flow Tests for fault scenarios:

```
Flow Test: "DML failure logs error"
  Setup: Create a record that will fail validation rules
  Assertions:
    - Error_Log__c record created with FaultMessage populated
    - Original transaction handled gracefully
```

Test every fault connector path, not just the happy path.

**Detection hint:** Test plan that covers only success scenarios without any fault or error path tests.

---

## Anti-Pattern 3: Testing only with single records instead of bulk scenarios

**What the LLM generates:**

```
"Test by creating one record in the UI and checking that the flow ran correctly."
```

**Why it happens:** LLMs default to single-record testing because it is simpler. Record-triggered flows that work for one record often fail when a data loader inserts 200 records at once due to governor limits.

**Correct pattern:**

Test with realistic bulk volumes:
1. Use Data Loader or Apex test classes to insert 200+ records
2. Verify the flow completes without governor limit errors
3. Check that all records are processed correctly
4. Monitor for DML-in-loop issues that surface only at scale

```apex
@IsTest
static void testFlowBulk() {
    List<Case> cases = new List<Case>();
    for (Integer i = 0; i < 200; i++) {
        cases.add(new Case(Subject = 'Test ' + i, Priority = 'High'));
    }
    Test.startTest();
    insert cases;
    Test.stopTest();
    // Assert expected outcomes
}
```

**Detection hint:** Test plan that only mentions single-record creation without bulk testing.

---

## Anti-Pattern 4: Not testing Decision element branches

**What the LLM generates:**

```
"Test the flow by creating a record that matches the entry conditions."
```

**Why it happens:** LLMs test the primary branch. Decision elements with multiple outcomes create different execution paths that each need verification.

**Correct pattern:**

Create a test for each Decision branch:

```
Test 1: Priority = High    --> Verify escalation task created
Test 2: Priority = Medium  --> Verify standard routing
Test 3: Priority = Low     --> Verify no task created (default outcome)
```

Map the flow's Decision elements to test cases ensuring every branch is covered.

**Detection hint:** Test plan for a flow with Decision elements that only tests one outcome path.

---

## Anti-Pattern 5: Confusing Flow Tests with Apex Test classes

**What the LLM generates:**

```
"Write an Apex test that calls the flow using Flow.Interview
and asserts the output variables."
```

**Why it happens:** LLMs with Apex training data suggest Apex-based testing. While Apex tests can invoke flows, Flow Tests (the native testing framework in Setup) are purpose-built for flow testing and do not require code.

**Correct pattern:**

Use the right tool for each scenario:
- **Flow Tests**: for declarative flow path validation, accessible to admins
- **Apex Tests**: for testing flows invoked from Apex, or for complex data setup needs
- **Both**: for production deployments, ensure Flow Tests cover the declarative paths and Apex tests cover the integration points

**Detection hint:** Advice to use Apex Tests as the only testing mechanism for flows that have no Apex integration points.

---

## Anti-Pattern 6: Not testing with different user profiles and permission sets

**What the LLM generates:**

```
"Run the debug as yourself (admin) to verify the flow works."
```

**Why it happens:** LLMs test with the current user context. Admins have full access, so flows always work. Standard users may lack CRUD, FLS, or record access that the flow requires.

**Correct pattern:**

Test with representative user profiles:
1. Use "Run flow as another user" in Debug mode
2. Create Flow Tests that simulate non-admin contexts
3. Verify error handling when the user lacks permissions
4. For Experience Cloud flows, test with the Guest User profile

**Detection hint:** Testing advice that does not mention running as a non-admin user or checking profile-specific behavior.
