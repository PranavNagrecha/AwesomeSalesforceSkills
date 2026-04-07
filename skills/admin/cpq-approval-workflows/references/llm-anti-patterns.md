# LLM Anti-Patterns — CPQ Approval Workflows

Common mistakes AI coding assistants make when generating or advising on CPQ Approval Workflows.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending a Standard Salesforce Approval Process for CPQ Line-Level Discount Approvals

**What the LLM generates:** Advice to create a standard `ApprovalProcess` on `SBQQ__Quote__c` with entry criteria that check a discount field, or instructions to create a formula field on the quote that attempts to roll up line-level discounts for use in a standard approval process condition.

**Why it happens:** Standard approval processes are the dominant paradigm in Salesforce training data. LLMs default to `ProcessDefinition` / `ApprovalProcess` metadata because it covers most Salesforce approval use cases, and the CPQ-specific Advanced Approvals package appears less frequently in training data. The LLM does not recognize that cross-line aggregation is architecturally impossible in standard processes.

**Correct pattern:**

```
Use SBAA__ApprovalVariable__c to aggregate across quote line items:
  Object:    SBQQ__QuoteLine__c
  Field:     SBQQ__Discount__c
  Operator:  Max

Reference this variable in SBAA__ApprovalCondition__c on SBAA__ApprovalRule__c.
Do NOT use ApprovalProcess metadata for line-level CPQ discount thresholds.
```

**Detection hint:** Any response mentioning `ApprovalProcess`, `ProcessDefinition`, or "standard approval process" in the context of CPQ discount-based approval is likely applying this anti-pattern. Watch for phrases like "add an approval process to SBQQ__Quote__c" or "create a formula field to roll up discounts."

---

## Anti-Pattern 2: Treating the SBAA__ Namespace as Part of the Base CPQ Package

**What the LLM generates:** Instructions to configure Advanced Approvals objects (`SBAA__ApprovalRule__c`, `SBAA__ApprovalVariable__c`) as though they are present in every CPQ org, without first verifying the Advanced Approvals package is installed.

**Why it happens:** LLMs often collapse Salesforce CPQ (SBQQ__) and CPQ Advanced Approvals (SBAA__) into a single conceptual package because they are frequently discussed together in documentation and community content. The LLM does not distinguish between what the base package provides and what requires a separate installation.

**Correct pattern:**

```
Before configuring any SBAA__ object:
1. Verify Setup > Installed Packages shows the CPQ Advanced Approvals package.
2. Verify the "CPQ Advanced Approvals" permission set exists.
If the package is not installed, SBAA__ objects do not exist and cannot be created.
Standard approval processes are not a fallback for cross-line discount logic.
```

**Detection hint:** Any response that jumps directly to creating `SBAA__ApprovalRule__c` records without first checking package installation is applying this anti-pattern. Also watch for responses that conflate the SBAA__ and SBQQ__ namespaces.

---

## Anti-Pattern 3: Configuring OR Logic Within a Single Approval Rule Using Multiple Conditions

**What the LLM generates:** Instructions to add multiple `SBAA__ApprovalCondition__c` records to a single `SBAA__ApprovalRule__c` with the explanation that either condition being true will trigger the approval (OR logic).

**Why it happens:** Many approval frameworks support per-condition logic operators (AND/OR). LLMs generalize this behavior to CPQ Advanced Approvals, where all conditions on a single rule are always ANDed. The generated configuration appears structurally valid but produces AND logic, silently failing to trigger when OR was intended.

**Correct pattern:**

```
For OR logic across two conditions, create two separate SBAA__ApprovalRule__c records:
  Rule A: condition "Max Line Discount > 30%"     -> Approver: Sales Manager
  Rule B: condition "Quote Total Revenue > $100K" -> Approver: Sales Manager

Both rules are evaluated independently on approval submission.
Do NOT add both conditions to a single rule expecting OR behavior.
```

**Detection hint:** Any response that adds two or more conditions to a single rule with language like "trigger approval if either condition is true" or "OR logic between conditions" is applying this anti-pattern. All conditions on one rule in SBAA__ are ANDed.

---

## Anti-Pattern 4: Assuming Smart Approvals Selectively Re-Approves Only the Affected Rule

**What the LLM generates:** An explanation that Smart Approvals will re-trigger only the specific approval rule whose conditions were affected by the changed field on a requote, while keeping other previously granted approvals intact.

**Why it happens:** "Smart" implies precision and selectivity. LLMs reason that re-approving only what changed is the "smart" behavior. The actual implementation re-approves all approvers across all rules when any approval-relevant field changes — it is a global reset, not a targeted one.

**Correct pattern:**

```
Smart Approvals behavior on requote:
- Non-relevant field changes (e.g., quote name, expiration date):
    All previous approvals are carried forward. No re-approval required.
- Any approval-relevant field changes (any field referenced in any active condition):
    ALL previous approvers across ALL rules must re-approve.
    There is no selective re-approval by rule or by approver.
```

**Detection hint:** Responses that say "only the affected approver will need to re-approve" or "Smart Approvals will keep the VP approval intact and only re-trigger the Sales Manager rule" are applying this anti-pattern.

---

## Anti-Pattern 5: Omitting the Permission Set Assignment Step for Advanced Approvals Users

**What the LLM generates:** Configuration instructions for `SBAA__ApprovalRule__c` and related objects that do not mention assigning the "CPQ Advanced Approvals" permission set, or that assume the base CPQ permission sets cover Advanced Approvals access.

**Why it happens:** LLMs frequently omit permission set steps because they are administrative prerequisites that appear separately from functional configuration. The CPQ permission set paradigm (multiple separate sets for different roles) is complex, and the Advanced Approvals set is a fourth distinct set that LLMs often miss.

**Correct pattern:**

```
Required permission sets for CPQ Advanced Approvals (assigned in addition to CPQ base sets):
  - "CPQ Advanced Approvals" — assign to: quote submitters, approvers, CPQ admins

Users without this permission set:
  - Cannot see the approval submission button on quote records
  - Cannot access SBAA__ object records (approval rules, variables, chains)
  - Receive no error message — features are simply hidden

Assignment steps:
  Setup > Users > [User] > Permission Set Assignments > Add "CPQ Advanced Approvals"
```

**Detection hint:** Any configuration guide for SBAA__ that does not include a permission set assignment step is likely applying this anti-pattern. Also watch for instructions that say "users with the Salesforce CPQ permission set can submit approvals" — this is incorrect for Advanced Approvals.

---

## Anti-Pattern 6: Configuring Escalation Without Verifying the Scheduled Apex Job

**What the LLM generates:** Instructions to set `SBAA__EscalationDays__c` and `SBAA__EscalationUser__c` on approval rules with no mention of the `SBAA.EscalateApprovals` scheduled Apex job that must be active for escalation to function.

**Why it happens:** LLMs treat field configuration as sufficient to activate a feature. The dependency on a background scheduled job is a platform implementation detail that does not appear prominently in field-level documentation and is absent from most configuration walkthroughs in training data.

**Correct pattern:**

```
Escalation configuration requires both:
1. Set on SBAA__ApprovalRule__c:
   - SBAA__EscalationDays__c: number of days before escalation
   - SBAA__EscalationUser__c: user to escalate to

2. Verify in Setup > Scheduled Jobs:
   - Job class: SBAA.EscalateApprovals
   - Status: Active / Scheduled
   If the job is missing: Setup > Apex Classes > Schedule Apex > Class: SBAA.EscalateApprovals

Without the scheduled job, no escalation ever fires regardless of rule configuration.
```

**Detection hint:** Any escalation configuration guidance that does not mention the `SBAA.EscalateApprovals` scheduled Apex job is applying this anti-pattern. Watch for responses that treat field-level configuration as the complete escalation setup.
