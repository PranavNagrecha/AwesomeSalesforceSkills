# Validation Rule Documentation Template

Use one of these for each validation rule in your org. Store completed copies in your team's documentation system (Confluence, Notion, Google Docs).

---

## Rule: [Rule Name]

| Property | Value |
|----------|-------|
| **Object** | TODO: e.g. Opportunity |
| **Rule API Name** | TODO: e.g. `Opportunity_CloseDate_RequiredWhenClosed` |
| **Rule Label** | TODO: e.g. "Close Date Required When Closed" |
| **Status** | Active / Inactive |
| **Author** | TODO |
| **Deployment Date** | TODO: YYYY-MM-DD |
| **Last Reviewed** | TODO: YYYY-MM-DD |
| **Business Owner** | TODO: Name / Team |

---

## Business Justification

**Problem this solves:**
TODO: What data quality issue does this rule prevent? Be specific.
e.g. "Opportunities were being closed without a Close Date, which broke the revenue forecast report and the Mulesoft integration that uses CloseDate for contract generation."

**Business rule in plain English:**
TODO: One sentence. e.g. "Close Date is required whenever an Opportunity Stage is Closed Won or Closed Lost."

---

## Formula

```
TODO: Paste formula here

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

**Formula explanation:**
TODO: Describe what each clause does in plain English.
- Line 1-3: Checks if Stage is Closed Won or Closed Lost
- Line 4: Checks if Close Date is blank
- Line 5: Excludes users with the bypass Custom Permission

---

## Error Message

**Text:**
TODO: Full error message text
e.g. "Close Date is required when an Opportunity is Closed. Enter a Close Date to save this record."

**Placement:** ☐ Field-level (on: TODO field name) / ☐ Page-level (top of page)

---

## Scope

| Dimension | Value |
|-----------|-------|
| Record Types | ☐ All record types / ☐ Specific: TODO |
| User scope | ☐ All users / ☐ Specific bypass: TODO Custom Permission name |
| Trigger condition | ☐ Insert and Edit / ☐ Insert only (uses ISNEW()) / ☐ Edit only |

---

## Bypass Mechanism

| Bypass Type | Implementation | Who Has It |
|-------------|---------------|------------|
| ☐ Custom Permission | Permission: `TODO` — granted via Permission Set: `TODO` | TODO: Integration user, Admin |
| ☐ Record Type exclusion | Record Types excluded: TODO | N/A |
| ☐ Profile check | Profile: TODO | N/A — not recommended, document if used |
| ☐ No bypass | ⚠️ Flag: data migrations and integrations will be affected | — |

---

## Test Scenarios

| Scenario | Setup | Expected Result | Tested By | Date |
|----------|-------|----------------|-----------|------|
| Valid record — should save | TODO: Describe valid state | ✅ No error | TODO | |
| Invalid record — should error | TODO: Describe invalid state | ✅ Error shown: "[error message]" | TODO | |
| Bypass user — should save | Assign bypass perm set, set invalid state | ✅ No error (bypass active) | TODO | |
| Integration user | API call with invalid data + bypass PS | ✅ No error | TODO | |
| Wrong Record Type | If scoped: test with out-of-scope RT | ✅ No error (rule doesn't apply) | TODO | |
| PRIORVALUE (if used) | Test on new record (insert) | ✅ No unexpected error | TODO | |

---

## Dependencies and Related Rules

**Conflicts with:** TODO: List any rules that might conflict (opposite conditions on same fields)

**Depends on:** TODO: List any rules or automations that must run before/after this rule

**Affects integrations:** ☐ Yes — TODO: name of integration | ☐ No

**Affects data loads:** ☐ Yes — bypass required | ☐ No

---

## Change History

| Date | Change | Author | Reason |
|------|--------|--------|--------|
| TODO | Created | TODO | TODO |
