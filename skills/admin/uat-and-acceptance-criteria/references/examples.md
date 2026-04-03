# Examples — UAT and Acceptance Criteria

## Example 1: Writing a UAT Test Script for a Case Auto-Assignment Flow

**Context:** A service team built a Record-Triggered Flow that automatically assigns new Cases to a queue based on the Case Origin field. The story has two acceptance criteria:
- "If a Case is created with Origin = 'Web', then the Case is assigned to the Web Support Queue."
- "If a Case is created with Origin = 'Phone', then the Case is assigned to the Phone Support Queue."

**Problem:** The tester creates a Case and checks the assigned queue. The Case ends up in the default case queue rather than the Web Support Queue. Without a structured test script, the tester writes "broken" and moves on. The defect is reported as "auto-assignment doesn't work" — which is too vague for the admin to reproduce or fix.

**Solution:**

A properly structured test case for TC-001 looks like this:

```
Test Case ID: TC-001
User Story ID: US-042
Test Scenario: Case auto-assigned to Web Support Queue when Origin = Web
Preconditions:
  - Logged in as: Service Agent (service_agent@uat-sandbox.org)
  - Sandbox: UAT1 (Full Sandbox, refreshed 2026-03-15)
  - No existing cases with this subject

Test Steps:
  1. Click App Launcher and select Service Console.
  2. Click New in the Cases tab.
  3. Select Origin = Web.
  4. Enter Subject = "Test UAT TC-001 Web Assignment".
  5. Leave all other fields at default.
  6. Click Save.
  7. On the Case record, locate the Case Owner field.

Expected Result:
  Case Owner = Web Support Queue

Actual Result:
  [Tester records here]

Pass / Fail: [P/F]
Defect ID: [if Fail]
Tester: Jane Smith
Date: 2026-04-03
```

**Why it works:** The click-level detail means the tester cannot deviate from the intended path. The precondition records the sandbox and user context, which is essential for reproducing a defect. The expected result is verbatim from the acceptance criterion — it is either exactly matched or it is not. The admin can reproduce the exact failure condition from the steps and expected result without guessing.

---

## Example 2: Defect Classification for a Security Finding

**Context:** During UAT for a new Account field "Customer Tier" (visible to Sales Managers, read-only to Sales Reps), a tester logged in as a Sales Rep discovers the field is editable.

**Problem:** The tester records: "Field is editable when it should not be." This is correct but incomplete. Without severity and component classification, this defect sits in a general backlog and is prioritized arbitrarily.

**Solution:**

```
Defect ID: DEF-017
Test Case ID: TC-023
User Story ID: US-051
Severity: P1 — Critical (security exposure: Sales Reps can modify a restricted field)
Component Type: Security — Field-Level Security
Description:
  Customer Tier field on Account is editable by users with Sales Rep profile.
  Expected: Read-only per FLS configuration.
  Actual: Editable — user can save changes to Customer Tier.
Steps to Reproduce:
  1. Log in as Sales Rep (salesrep_uat@sandbox.org).
  2. Open any Account record.
  3. Click Edit on the Customer Tier field.
  4. Observe field is editable and changes can be saved.
Expected Result: Field is read-only; no Edit pencil icon is visible.
Actual Result: Field is editable. Changes persist after Save.
Assignee: Admin — FLS configuration
Status: Open
```

**Why it works:** Severity P1 immediately signals this blocks release — a Sales Rep writing to a restricted field is a data integrity and security issue. Component type "Security — FLS" routes this instantly to the admin who manages field-level security, not to a developer or data team member. The steps to reproduce are complete enough that the admin can verify the fix by executing the same steps after the FLS update.

---

## Anti-Pattern: Testing Only the Happy Path

**What practitioners do:** The UAT test script covers only the success scenario for each feature. Tests create records with all required fields populated, all automation conditions met, and no edge cases.

**What goes wrong:** Validation rules, FLS restrictions, and sharing limits are specifically designed to trigger on edge conditions — the exact conditions the happy-path test skips. A validation rule that fires when a field is left blank will never be tested if every test populates that field. A sharing rule that restricts visibility to a specific role will never be tested if all testers use an admin profile.

**Correct approach:** For every acceptance criterion, write at least two test cases:
1. The positive case: the condition is met, the expected behavior fires.
2. The negative case: the condition is NOT met, the system prevents or restricts the action as designed.

For security-related criteria, test from every profile/permission set that is explicitly scoped in the story.
