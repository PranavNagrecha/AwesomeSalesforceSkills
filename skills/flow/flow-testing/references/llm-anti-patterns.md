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

Ship a `FlowTest` component — source-controlled, deployable, runnable from CI. It has the
suffix `.flowtest`, lives in the `flowtests` folder, and is available from API version
55.0 (`api_meta.txt` L73976-73980). A complete pair is in
`references/metadata-examples.md` §2 and §3.

```xml
<testPoints>
    <assertions>
        <conditions>
            <leftValueReference>assignedTier</leftValueReference>
            <operator>EqualTo</operator>
            <rightValue>
                <stringValue>Escalated</stringValue>
            </rightValue>
        </conditions>
        <errorMessage>Check_Claim_Amount routed to the default outcome.</errorMessage>
    </assertions>
    <elementApiName>Finish</elementApiName>
</testPoints>
```

Combine Flow Tests with debug runs: use debug for exploration, Flow Tests for regression.
**UNVERIFIED (2026-09-05):** the Flow Builder / Setup navigation for creating and running
a flow test by hand is documented only on help.salesforce.com, which is not in the
grounding corpus. The metadata shape above is grounded; the click path is not.

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

**Why it happens:** LLMs with Apex training data reach for the familiar idiom. The advice is not merely stylistically wrong — for a record-triggered flow it does not run. `Flow.Interview.start()` "can be used only with flows that have one of these types: • Autolaunched Flow • User Provisioning Flow" (`apexrefguide.txt` L158164-158177). A record-triggered flow shares the `AutoLaunchedFlow` process type but carries a `triggerType`, and a flow with a trigger "starts only when" that trigger fires, not when an app launches it (`api_meta.txt` L72496-72499).

**Correct pattern:**

Match the driver to the flow type:
- **`FlowTest` component**: record-triggered, autolaunched and Data Cloud-triggered flows (`api_meta.txt` L73961-73962). No code, source-controlled, runs before activation.
- **Apex + `Flow.Interview`**: genuinely autolaunched flows, where you need `Map<String, Object>` inputs, `getVariableValue` on the outputs, and `System.runAs` for user context. See `references/metadata-examples.md` §5.
- **Apex + DML**: the only way to exercise a record-triggered flow from Apex — insert or update the records and query the result.
- **Neither**: screen flows. `FlowTest` does not cover them and `start()` does not accept them.

**Detection hint:** Generated Apex containing `Flow.Interview.<Name>` where `<Name>` is a record-triggered flow, or any claim that an Apex test "invokes" a record-triggered flow directly.

---

## Anti-Pattern 6: Not testing with different user profiles and permission sets

**What the LLM generates:**

```
"Run the debug as yourself (admin) to verify the flow works."
```

**Why it happens:** LLMs test with the current user context. Admins have full access, so flows always work. Standard users may lack CRUD, FLS, or record access that the flow requires.

**Correct pattern:**

Test with representative user profiles:
1. In Apex, wrap the interview in `System.runAs(standardUser)`. To have the flow honour that user's record access, the launching class must be declared `with sharing` and run on API version 62.0 or later; then "data access is restricted to the sharing rules of the user that executed the Apex class" (`apexrefguide.txt` L157958-157963).
2. Set the flow's own `runInMode` deliberately. `DefaultMode` means "how the flow is launched determines whether the flow runs in user context or in system context" (`api_meta.txt` L68374-68380) — a flow tested only through an admin-launched path has never exercised the user-context branch of that sentence.
3. Verify error handling when the user lacks permissions.
4. For Experience Cloud flows, test with the Guest User profile.

**UNVERIFIED (2026-09-05):** the Flow Builder Debug window's "Run as another user" option, and its rollback / "do not commit" toggle, are documented only on help.salesforce.com. Neither `api_meta.txt` nor `apexdev.txt` describes the Debug window at all. The `System.runAs` and `runInMode` mechanisms above are grounded; the Debug-window options are not.

**Detection hint:** Testing advice that does not mention running as a non-admin user or checking profile-specific behavior.


---

## Anti-Pattern 7: Packing several conditions into one assertion

**What the LLM generates:**

```xml
<assertions>
    <conditions>
        <leftValueReference>$Record.Approval_Tier__c</leftValueReference>
        <operator>EqualTo</operator>
        <rightValue><stringValue>Escalated</stringValue></rightValue>
    </conditions>
    <conditions>
        <leftValueReference>assignedTier</leftValueReference>
        <operator>EqualTo</operator>
        <rightValue><stringValue>Escalated</stringValue></rightValue>
    </conditions>
    <errorMessage>Escalation did not work</errorMessage>
</assertions>
```

**Why it happens:** `FlowTestAssertion.conditions` is an array, so grouping reads as
economical. It destroys the diagnostic. "If one condition evaluates to false, the
assertion fails" (`api_meta.txt` L74181-74183) and `errorMessage` is a single string per
assertion — the run tells you the group failed, never which condition, and the generic
message tells you nothing further.

**Correct pattern:**

One condition per assertion, each with an `errorMessage` naming the element or resource
that must be wrong for that specific condition to fail. Multiple `assertions` blocks are
allowed inside one test point; `references/metadata-examples.md` §2 uses three.

**Detection hint:** A `FlowTestAssertion` with more than one `conditions` child, or an
`errorMessage` that restates the condition ("Tier was not Escalated") instead of naming
the suspect element.

---

## Anti-Pattern 8: Quoting a required flow-test coverage percentage

**What the LLM generates:**

```
"Salesforce requires 75% test coverage before you can deploy an active flow to production."
```

**Why it happens:** The 75% figure is heavily represented in Apex training data —
"unit tests must cover at least 75% of your **Apex code**" (`apexdev.txt` L728, L773,
L35283) — and the model transfers it to flows because both are "automation".

**Correct pattern:**

State what the guides actually document, and state the gap honestly. `DeployResult`
carries `flowCoverage` and `flowCoverageWarnings` from API version 44.0 (`api_meta.txt`
L7600-7606), and `FlowCoverageResult` reports `numElements`, `numElementsNotCovered` and
`elementsNotCovered` — a list of element names, not a ratio (`api_meta.txt` L7714-7736).
`FlowCoverageWarning.flowName` "is null" when "the warning applies to the overall test
coverage of flows within your org" (`api_meta.txt` L7750-7753), so an org-level notion of
flow coverage exists. **No required percentage for flows appears anywhere in
`api_meta.txt`, `apexdev.txt` or `apexrefguide.txt`.** Review `elementsNotCovered` per
element instead of chasing a number.

**Detection hint:** Any percentage attached to flow coverage, or the phrase "flows require
75%".
