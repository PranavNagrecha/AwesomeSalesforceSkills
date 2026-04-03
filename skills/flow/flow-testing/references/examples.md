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

## Anti-Pattern: Happy-Path Debug Only

**What practitioners do:** They run the flow once in Debug mode and take the green result as proof of quality.

**What goes wrong:** Branches, failures, and future regressions remain untested. The next change breaks production behavior that was never actually covered.

**Correct approach:** Treat Debug as investigation support, then capture important behavior in repeatable tests and explicit path coverage.
