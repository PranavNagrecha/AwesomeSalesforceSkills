---
name: standard-object-quirks
description: "Guidance on non-obvious runtime behaviors of Salesforce standard objects — polymorphic lookups, lead conversion field loss, PersonAccount dual-nature, CaseComment trigger isolation, and Activity date fields. NOT for schema documentation or data modeling; NOT for custom object design; NOT for field-level security configuration."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Security
  - Operational Excellence
triggers:
  - "WhoId or WhatId polymorphic lookup not returning expected records in SOQL"
  - "Lead conversion losing custom field values or creating duplicate records"
  - "PersonAccount queries returning null for Email field instead of PersonEmail"
tags:
  - standard-object-quirks
  - polymorphic-lookups
  - lead-conversion
  - person-accounts
  - activity-objects
  - case-comments
inputs:
  - "The standard object(s) involved and the specific behavior that is unexpected"
  - "Whether the org uses PersonAccounts, Lead conversion, or Activity-based automation"
outputs:
  - "Explanation of the platform behavior causing the issue with official-source grounding"
  - "Corrected code, query, or configuration pattern that accounts for the quirk"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-05
---

# Standard Object Quirks

This skill activates when a practitioner encounters unexpected runtime behavior from Salesforce standard objects — situations where the platform does something that contradicts reasonable assumptions drawn from the UI or general database experience. It provides doc-grounded explanations and corrective patterns for polymorphic lookup behavior, lead conversion field mapping gaps, PersonAccount dual-nature pitfalls, CaseComment trigger isolation, and Activity date-field confusion.

---

## Before Starting

Gather this context before working on anything in this domain:

- Which standard objects are involved? Confirm whether the org uses PersonAccounts (check `Account.IsPersonAccount` field availability), and whether Lead conversion or Activity automation is in scope.
- The most common wrong assumption is that standard objects behave like custom objects. They do not: standard objects have hard-coded platform behaviors (cascade rules, polymorphic fields, dual-nature records) that cannot be overridden by configuration.
- Key limits: polymorphic fields cannot be traversed in a single SOQL relationship query; Lead conversion field mapping only transfers mapped fields; PersonAccount records share a single Id across Account and Contact but expose different field sets depending on SOQL target.

---

## Core Concepts

### Polymorphic Lookups (WhoId / WhatId)

Task and Event use polymorphic lookup fields: `WhoId` points to either a Contact or a Lead, while `WhatId` points to Account, Opportunity, Case, or any of 20+ standard and custom objects. You cannot traverse both sides of a polymorphic relationship in a single SOQL query using dot notation. Instead, you must use `TYPEOF` in SOQL or query each target type separately. Attempting `SELECT Who.Name FROM Task` works, but `SELECT Who.Email FROM Task` fails because the runtime does not know which sObject type `Who` resolves to at compile time.

### Lead Conversion Field Mapping

When a Lead is converted, Salesforce creates or updates a Contact, optionally an Account, and optionally an Opportunity. Only fields that are explicitly mapped in Lead Field Mapping (Setup > Object Manager > Lead > Fields & Relationships > Map Lead Fields) are transferred. Unmapped custom fields on the Lead are silently lost. Standard field mappings are pre-configured but custom fields require manual mapping. If a Lead has a value in an unmapped custom field, that data is permanently lost after conversion unless captured by a before-conversion trigger.

### PersonAccount Dual-Nature

A PersonAccount is simultaneously an Account record and a Contact record sharing a single Salesforce Id. In SOQL, PersonAccount-specific fields use the `Person` prefix on the Account object (e.g., `PersonEmail`, `PersonMailingCity`). Querying the `Email` field on Account returns null for PersonAccounts — you must use `PersonEmail`. The Contact record associated with a PersonAccount has its own Id but is not independently deletable. Apex triggers on Account fire for PersonAccount changes, but triggers on Contact also fire for the implicit Contact side of the PersonAccount.

### CaseComment Trigger Isolation and Activity Date Fields

CaseComment is a child of Case, but DML operations on CaseComment do not fire Case triggers. If you need Case-level automation when a comment is added, you must write a trigger on CaseComment that explicitly updates the parent Case. Separately, on the Task object, `ActivityDate` is the due date, not the completion date. The completion date is `CompletedDateTime` (available only when Status is Completed). For Event, `EndDateTime` is required when creating records via API or Apex even though the UI allows specifying only a duration.

---

## Common Patterns

### Safe Polymorphic Query Pattern

**When to use:** You need to query Tasks and get related Contact or Lead fields.

**How it works:**

```apex
List<Task> tasks = [
    SELECT Id, Subject,
        TYPEOF Who
            WHEN Contact THEN FirstName, LastName, Email
            WHEN Lead THEN FirstName, LastName, Company
        END
    FROM Task
    WHERE OwnerId = :UserInfo.getUserId()
];

for (Task t : tasks) {
    if (t.Who instanceof Contact) {
        Contact c = (Contact) t.Who;
        System.debug('Contact email: ' + c.Email);
    } else if (t.Who instanceof Lead) {
        Lead l = (Lead) t.Who;
        System.debug('Lead company: ' + l.Company);
    }
}
```

**Why not the alternative:** Using `Who.Name` alone works but gives you no type-specific fields. Attempting dot-notation on a polymorphic field for type-specific fields causes a compile-time error.

### Lead Conversion Field Preservation Pattern

**When to use:** Custom fields on Lead must survive conversion without manual field mapping.

**How it works:**

1. Create a before-trigger on Lead that fires on the `convertLead` operation.
2. In the trigger, copy custom field values to a staging custom object or to the target Contact/Account via a lookup established pre-conversion.
3. Alternatively, build a Flow that runs on Lead conversion to capture and transfer unmapped values.
4. Post-conversion, verify the target records contain the expected data.

**Why not the alternative:** Relying solely on Lead Field Mapping requires manual setup per field and is easy to miss when new custom fields are added. The trigger-based approach is self-maintaining.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need Contact/Lead fields from Task | Use TYPEOF in SOQL | Polymorphic lookups cannot use standard dot-notation for type-specific fields |
| PersonAccount email in reports or queries | Query `PersonEmail` on Account | `Email` field on Account is null for PersonAccounts |
| Case automation on comment addition | CaseComment trigger that updates parent Case | CaseComment DML does not fire Case triggers |
| Preserving custom Lead fields through conversion | Before-conversion trigger or post-conversion Flow | Unmapped custom fields are silently dropped |
| Creating Events via Apex | Always set EndDateTime explicitly | API requires it even though UI derives it from Duration |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner diagnosing a standard object quirk:

1. **Identify the standard object** — Confirm exactly which standard object is exhibiting unexpected behavior. Check if PersonAccounts are enabled (`SELECT IsPersonAccount FROM Account LIMIT 1`).
2. **Reproduce the behavior** — Write a minimal SOQL query or Apex snippet that demonstrates the unexpected result. Compare the API behavior against what the UI shows.
3. **Check known quirks** — Review this skill's Core Concepts and Gotchas sections. Most standard-object surprises fall into one of five categories: polymorphic lookups, lead conversion, PersonAccounts, CaseComment isolation, or Activity date fields.
4. **Apply the corrective pattern** — Use the matching pattern from Common Patterns. If the issue is a polymorphic query, switch to TYPEOF. If it is PersonAccount, switch to Person-prefixed fields. If it is CaseComment, add a dedicated trigger.
5. **Validate with unit tests** — Write an Apex test that asserts the corrected behavior. For polymorphic queries, test with both Contact and Lead WhoId values. For PersonAccounts, test with both Business and Person account types.
6. **Document the quirk locally** — Add a comment in the code explaining the platform behavior, so future maintainers do not revert to the naive pattern.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] All SOQL queries on Task/Event use TYPEOF or explicit type checks for WhoId/WhatId
- [ ] PersonAccount queries use Person-prefixed fields (PersonEmail, PersonMailingCity) not standard Contact fields on Account
- [ ] Lead conversion logic accounts for unmapped custom fields with explicit mapping or trigger-based preservation
- [ ] CaseComment-driven automation uses a CaseComment trigger, not a Case trigger
- [ ] Event creation via Apex sets EndDateTime explicitly
- [ ] Unit tests cover both sides of polymorphic lookups (Contact and Lead for WhoId)
- [ ] Code comments explain the non-obvious platform behavior at each quirk site

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Account deletion does not cascade-delete Contacts** — Deleting an Account does not delete its child Contacts. Instead, Contacts are unlinked (AccountId set to null) if they have no other master-detail relationships. This contradicts the assumption that parent deletion removes children.
2. **Task CompletedDateTime vs ActivityDate** — `ActivityDate` on Task is the due date, not the completion date. The actual completion timestamp is `CompletedDateTime`, which is only populated when the Task Status equals "Completed." Automation that checks `ActivityDate` to detect completed tasks will produce wrong results.
3. **PersonAccount Contact triggers fire unexpectedly** — When a PersonAccount is updated, triggers on both Account and Contact execute because the platform maintains an implicit Contact record. Trigger logic that assumes Contact triggers only fire for standalone Contact records will run on PersonAccount updates too, potentially causing errors or double-processing.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Corrected SOQL query or Apex snippet | Revised code that accounts for the identified standard-object quirk |
| Quirk documentation comment | Inline code comment explaining the non-obvious behavior for future maintainers |
| Unit test class | Test coverage proving the corrected behavior under both normal and edge-case scenarios |

---

## Related Skills

- data-model-documentation — Use when you need to document the overall schema design rather than diagnose a runtime behavioral quirk
- validation-rules — Use when the fix for a standard object quirk involves adding a validation rule to enforce data integrity
- sharing-and-visibility — Use when the quirk involves record access, OWD, or sharing rule behavior on standard objects
