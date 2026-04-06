# LLM Anti-Patterns — UAT and Acceptance Criteria

Common mistakes AI coding assistants make when generating or advising on Salesforce UAT planning and acceptance criteria.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Writing acceptance criteria without Salesforce-specific validation steps

**What the LLM generates:** "Acceptance criteria: User can create a new record. User can edit the record. User can delete the record."

**Why it happens:** LLMs produce generic CRUD acceptance criteria that could apply to any system. Salesforce-specific acceptance criteria must test platform behaviors: FLS visibility per profile, validation rule enforcement, Flow execution, page layout correctness, picklist value availability per record type, and sharing rule behavior.

**Correct pattern:**

```
Salesforce-specific acceptance criteria:
Given: user with Sales Rep profile and B2B record type access
When: user creates a new Opportunity on Account "Acme Corp"
Then:
- Record type selector shows "B2B Sales Process" as default.
- Stage picklist shows only B2B-specific values.
- Amount field is visible and editable (FLS check).
- Close Date is required (validation rule fires if blank).
- After save, the Before-Save Flow sets Region__c from Account.Region__c.
- The Opportunity appears in "My Open Opportunities" list view.
- Manager (one role above) can see the Opportunity in their report.
- A user with Service Agent profile CANNOT see the Opportunity (sharing check).
```

**Detection hint:** If acceptance criteria mention only "create/read/update/delete" without Salesforce-specific behaviors (FLS, validation rules, Flow, sharing), the criteria are too generic. Search for Salesforce terms: `profile`, `FLS`, `validation rule`, `Flow`, `record type`.

---

## Anti-Pattern 2: Testing with only one user profile

**What the LLM generates:** "Log in as the admin and run through all test cases."

**Why it happens:** LLMs default to the System Administrator profile for testing. System Administrators bypass most security: they see all records, all fields, and all page layouts. Testing as admin does not reveal FLS gaps, sharing issues, record type restrictions, or permission set problems that regular users experience.

**Correct pattern:**

```
Multi-profile UAT test matrix:
| Test Case              | Admin | Sales Rep | Service Agent | Read-Only |
|------------------------|-------|-----------|---------------|-----------|
| Create Opportunity     | Pass  | Must test | Must NOT work | Must NOT  |
| Edit Case Status       | Pass  | Must NOT  | Must test     | Must NOT  |
| View Salary field      | Pass  | Must NOT  | Must NOT      | Must NOT  |
| Run Pipeline report    | Pass  | Must test | Filtered view | Must test |

Test with at LEAST:
1. System Administrator (baseline).
2. Each distinct user profile that will use the feature.
3. One profile that should NOT have access (negative test).
```

**Detection hint:** If the test plan uses only the "admin" or "System Administrator" profile, non-admin behaviors are untested. Search for multiple profile names in the test plan.

---

## Anti-Pattern 3: Generating test scripts without test data setup instructions

**What the LLM generates:** "Test Step 1: Open the Account record. Test Step 2: Click the 'Escalate' button."

**Why it happens:** LLMs write test steps assuming test data already exists. UAT in a sandbox may have no data (Developer sandbox) or stale data (Full sandbox). Test scripts must include data setup prerequisites: create the Account, create the Contact, set the record type, set the owner, and configure the record to the state needed for the test.

**Correct pattern:**

```
Test script with data prerequisites:
Prerequisites:
1. Create Account: Name = "UAT Test Account", Type = "Customer".
2. Create Contact: Name = "Test Contact", linked to UAT Test Account.
3. Create Case: Subject = "UAT Escalation Test", Status = "New",
   Priority = "High", Contact = Test Contact.
4. Ensure logged-in user has Service Agent profile.

Test Steps:
1. Navigate to Case "UAT Escalation Test."
2. Click the "Escalate" quick action button.
3. Verify the escalation form appears with pre-filled fields.
4. Select Escalation Reason = "Customer Impact."
5. Click Save.

Expected Result:
- Case Status changes to "Escalated."
- IsEscalated checkbox is TRUE.
- Manager receives an email alert.
```

**Detection hint:** If test scripts start with "open the record" without data setup prerequisites, the tester may not have the right data. Search for `Prerequisites` or `Test Data Setup` at the beginning of the test script.

---

## Anti-Pattern 4: Not including negative test cases

**What the LLM generates:** "Test that the user can create the record, edit the fields, and save successfully."

**Why it happens:** LLMs focus on the happy path. UAT must also verify that unauthorized actions are blocked: users without permission cannot see the button, validation rules fire when invalid data is entered, sharing prevents unauthorized record access, and required fields enforce data quality.

**Correct pattern:**

```
Test case types for complete UAT:
1. Positive tests (happy path): authorized user performs the action successfully.
2. Negative tests (security/validation):
   - User without permission clicks the action button → button is NOT visible
     or access denied.
   - User enters invalid data → validation rule fires with correct error message.
   - User without sharing access searches for the record → record not found.
3. Boundary tests:
   - Enter maximum-length text in a field → saves correctly.
   - Enter minimum values for required fields → saves correctly.
   - Leave optional fields blank → saves correctly.
4. Regression tests:
   - Existing features still work after the new feature is deployed.
```

**Detection hint:** If the test plan has only positive test cases (all "user can do X"), negative tests are missing. Search for `cannot`, `NOT visible`, `denied`, or `error message` in the test steps.

---

## Anti-Pattern 5: Classifying all defects as the same severity

**What the LLM generates:** "Log the defect as a bug. The team will fix it."

**Why it happens:** LLMs do not apply a severity classification model. UAT defects range from cosmetic (label typo) to blocking (data loss, security breach). Without severity classification, teams waste time on cosmetic issues while critical defects delay go-live.

**Correct pattern:**

```
Salesforce UAT defect severity model:
| Severity    | Definition                                    | Example                           | Action          |
|-------------|-----------------------------------------------|-----------------------------------|-----------------|
| S1 Critical | Data loss, security breach, system crash       | Sharing rule exposes PII          | Block go-live   |
| S2 High     | Major feature broken, no workaround            | Flow fails on save, records lost  | Fix before go-live|
| S3 Medium   | Feature degraded but workaround exists          | Button misaligned, extra click    | Fix in next sprint|
| S4 Low      | Cosmetic, minor UX issue                       | Typo in field label, wrong icon   | Backlog         |

Defect log format:
| ID | Summary | Severity | Steps to Reproduce | Expected | Actual | Status |
```

**Detection hint:** If the defect log has no severity column or classifies all defects the same way, the prioritization model is missing. Search for `severity`, `S1`, `S2`, `Critical`, or `priority` in the defect log.
