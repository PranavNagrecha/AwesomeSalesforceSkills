# Validation Rule Documentation Template

Use one of these for each validation rule in your org. Store completed copies in your team's documentation system (Confluence, Notion, Google Docs).

---

## Rule: [Rule Name]

| Property | Value |
|----------|-------|
| **Object** | `<Object API name>` — e.g. Opportunity |
| **Rule API Name** | `<Object>_<Field_or_Concept>_<Action>` — e.g. `Opportunity_CloseDate_RequiredWhenClosed` |
| **Rule Label** | `<human-readable label>` — e.g. "Close Date Required When Closed" |
| **Status** | Active / Inactive |
| **Author** | `<name>` |
| **Deployment Date** | `<YYYY-MM-DD>` |
| **Last Reviewed** | `<YYYY-MM-DD>` |
| **Business Owner** | `<name or team>` |

---

## Business Justification

**Problem this solves:** what data-quality issue does this rule prevent? Be specific.

e.g. "Opportunities were being closed without a Close Date, which broke the revenue forecast report and the Mulesoft integration that uses CloseDate for contract generation."

**Business rule in plain English:** one sentence.

e.g. "Close Date is required whenever an Opportunity Stage is Closed Won or Closed Lost."

---

## Formula

```
// Paste the errorConditionFormula here, in the canonical order:
// bypass, then relevance gate, then business condition.
// Example:
AND(
  OR(
    ISPICKVAL(StageName, "Closed Won"),
    ISPICKVAL(StageName, "Closed Lost")
  ),
  ISBLANK(CloseDate),
  NOT($Permission.Bypass_Opportunity_Validation)
)
```

**Formula explanation:** what each clause does in plain English.

- Line 1-3: Checks if Stage is Closed Won or Closed Lost
- Line 4: Checks if Close Date is blank
- Line 5: Excludes users with the bypass Custom Permission

---

## Error Message

**Text:** the full message, 255 characters or fewer.

e.g. "Close Date is required when an Opportunity is Closed. Enter a Close Date to save this record."

**Placement:** ☐ Field-level — `errorDisplayField` = `<field API name>` / ☐ Page-level (top of page)

If field-level: confirm the field is on the page layout for every record type in scope. When it is not, `errorDisplayField` changes automatically to Top of Page.

---

## Scope

| Dimension | Value |
|-----------|-------|
| Record Types | ☐ All record types / ☐ Specific: `<RecordType.DeveloperName list>` |
| User scope | ☐ All users / ☐ Specific bypass: `<Custom Permission API name>` |
| Trigger condition | ☐ Insert and Edit / ☐ Insert only (uses ISNEW()) / ☐ Edit only |

---

## Bypass Mechanism

| Bypass Type | Implementation | Who Has It |
|-------------|---------------|------------|
| ☐ Custom Permission | Permission: `<API name>` — granted via Permission Set: `<API name>` | `<integration user, migration user, admin>` |
| ☐ Record Type exclusion | Record Types excluded: `<DeveloperName list>` | N/A |
| ☐ Profile check | Profile: `<name>` | N/A — not recommended; `$Profile.Name` breaks silently when the profile is renamed |
| ☐ No bypass | ⚠️ Flag: data migrations and integrations will be affected | — |

---

## Test Scenarios

| Scenario | Setup | Expected Result | Tested By | Date |
|----------|-------|----------------|-----------|------|
| Valid record — should save | `<describe the valid state>` | No error | `<tester>` | |
| Invalid record — should error | `<describe the invalid state>` | Error shown, attached to the `errorDisplayField` | `<tester>` | |
| Bypass user — should save | Assign the bypass Permission Set, set the invalid state | No error (bypass active) | `<tester>` | |
| Integration user | API call with invalid data + bypass PS | No error | `<tester>` | |
| Wrong Record Type | If scoped: save with an out-of-scope record type | No error (rule doesn't apply) | `<tester>` | |
| PRIORVALUE (if used) | Insert a new record | No unexpected error (`NOT(ISNEW())` guard holds) | `<tester>` | |
| Apex regression | `OpportunityValidationRuleTest` from `references/metadata-examples.md` | Both tests pass: rule fires, bypass suppresses | `<tester>` | |

---

## Dependencies and Related Rules

**Conflicts with:** rules with opposite conditions on the same fields. Evaluation order across rules is not guaranteed, so two rules must never depend on each other's outcome.

**Depends on:** automations that run before this rule in the order of execution — before-save flows (step 3) and before triggers (step 4) both write values this rule (step 5) will see. Note any workflow field update on these fields: validation rules are **not** re-run after a workflow field update re-saves the record.

**Affects integrations:** ☐ Yes — `<integration name>` | ☐ No

**Affects data loads:** ☐ Yes — bypass required | ☐ No

---

## Change History

| Date | Change | Author | Reason |
|------|--------|--------|--------|
| `<YYYY-MM-DD>` | Created | `<name>` | `<why now>` |

Any change to `errorMessage` is a translation-affecting change: update the matching `ValidationRuleTranslation` entry in the `CustomObjectTranslation` for every active language in the same deploy.
