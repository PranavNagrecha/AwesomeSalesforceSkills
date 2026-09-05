# Examples - Flow Testing

## Example 1: Record-Triggered Flow Test Matrix

**Context:** An opportunity renewal flow branches by amount and partner status, then creates tasks only for high-risk renewals.

**Problem:** The team has only clicked Debug once with a happy-path record and assumes the flow is sufficiently covered.

**Solution:**

Create a path matrix before authoring Flow Tests.

```text
Flow: Opportunity_AfterSave_SetRenewalRisk

Scenario 1:
- Amount = 5000
- Partner = false
- Expected result: Risk = Low, no task created

Scenario 2:
- Amount = 150000
- Partner = true
- Expected result: Risk = High, renewal task created

Scenario 3:
- Missing required contract field
- Expected result: Flow fault path or validation branch taken
```

**Why it works:** The test strategy now covers business outcomes instead of one generic successful save.

---

## Example 2: Screen Flow Needs Both Flow And Component Tests

**Context:** A shipping address wizard uses a custom LWC screen component for postal-code validation.

**Problem:** The team adds a Flow Test but never tests whether the component's validation methods behave correctly.

**Solution:**

Split the test surface:

```text
Flow-level coverage:
- User can complete the wizard with valid inputs
- Invalid data blocks finish at the correct screen
- Final confirmation performs the expected update

Component-level coverage:
- `validate()` returns invalid for blank postal code
- `setCustomValidity()` stores external errors
- `reportValidity()` displays the message on the input
```

**Why it works:** The flow and the custom runtime component each get the type of test that matches the behavior they own.

---

## Example 3: Turning A Deploy Result Into A Coverage Worklist

**Context:** A release manager wants a "flow coverage" number for the go/no-go call. There
isn't one — but there is something better in the deploy result nobody was reading.

**Problem:** The team was about to invent a threshold, pick 75% by analogy with Apex, and
gate on a figure that no Salesforce guide states for flows.

**Solution:**

`DeployResult.flowCoverage` is a `FlowCoverageResult[]`, available from API version 44.0
(`api_meta.txt` L7600–7606). Each entry names the elements that no test executed
(`api_meta.txt` L7714–7736):

```xml
<flowCoverage>
    <flowName>Warranty_Claim_AfterSave_TierApproval</flowName>
    <processType>AutoLaunchedFlow</processType>
    <numElements>6</numElements>
    <numElementsNotCovered>2</numElementsNotCovered>
    <elementsNotCovered>Assign_Standard_Tier,Log_Tier_Failure</elementsNotCovered>
</flowCoverage>
```

Read as a ratio that is 67% and means nothing. Read as a list it is a two-line worklist:

| Uncovered element | What it means | Action |
|---|---|---|
| `Assign_Standard_Tier` | The Decision's default outcome has never run. Only the escalation branch is proven. | Add the negative-path `FlowTest` — `references/metadata-examples.md` §3. |
| `Log_Tier_Failure` | The fault route has never run. Expected, and not fixable by a `FlowTest`. | Accept, and record why: no `FlowTest` field can force a DML failure (`isUseMockOuput` is reserved, `api_meta.txt` L74152). Cover it with an Apex test that inserts a record violating a validation rule. |

**Why it works:** The uncovered-element list distinguishes a real gap (a branch nobody
tested) from a structural one (a route no declarative test can reach). A percentage
collapses both into the same number and hides which is which.

---

## Anti-Pattern: Happy-Path Debug Only

**What practitioners do:** They run the flow once in Debug mode and take the green result as proof of quality.

**What goes wrong:** Branches, failures, and future regressions remain untested. The next change breaks production behavior that was never actually covered.

**Correct approach:** Treat Debug as investigation support, then capture important behavior in repeatable tests and explicit path coverage.
