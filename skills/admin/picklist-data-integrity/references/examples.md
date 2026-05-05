# Examples — Picklist Data Integrity

## Example 1 — Phantom values from unrestricted picklist + API write

**Context.** Account has a `Region__c` picklist (Unrestricted) with
values `AMER, EMEA, APAC`. An integration syncs from the source CRM
which has a value `EMEA-North` not in the picklist definition. The
integration writes successfully (Unrestricted permits any string).
Reports filtered by Region show only AMER / EMEA / APAC; a chunk of
records are missing from the report — the EMEA-North accounts.

**Wrong cause assumed.** "The integration is dropping records."

**Actual cause.** Records have `Region__c = "EMEA-North"`, which the
picklist filter doesn't recognize. Records exist; they just don't
match the filter.

**Right answer.** Either:

- **Add `EMEA-North` to the picklist** so the filter recognizes it
  (and reports surface the records).
- **Switch to Restricted** to force the integration to send only
  known values, and surface the EMEA-North case as an integration
  error to be handled upstream.

The wrong choice is leaving the phantom values silently invisible
to reports.

---

## Example 2 — Deactivated value persists on existing records

**Context.** Admin deactivates `Status = "On Hold"` because the
business no longer uses that status. A month later, sales-ops
reports "the case dashboard shows zero On Hold cases" but support
manager says "I have 30 cases sitting at On Hold from before".

**What's happening.** The 30 cases still have `Status = "On Hold"`.
The dashboard's filter is built from the current picklist values,
which doesn't include "On Hold" — so the filter doesn't surface the
30 records, but they exist in the database.

**Right answer.** Pattern C migration. Mass-update the 30 records
to a different active status (`Closed`, `In Progress`,
business-decided). Then verify zero records have the deactivated
value. Then optionally use Setup → field → Value → Replace to catch
any stragglers.

---

## Example 3 — Dependent picklist migration before controller deactivation

**Context.** Country/State dependent picklist. Business decides to
deprecate `Country = "United Kingdom"` in favor of separating
`Country = "England"`, `Country = "Scotland"`, etc. Admin
deactivates `United Kingdom` first.

**What goes wrong.** Records with `Country = United Kingdom AND
State = London` still exist. The State field's edit UI no longer
shows London (because no controlling value path leads there).
Admins editing these records get confused — the State field shows
London but offers no values; trying to clear it sticks the record
in an unsavable state.

**Right answer.** Reverse the order:

1. Mass-update records FIRST: `Country = United Kingdom AND State =
   London` → `Country = England AND State = London`. Both fields
   updated atomically (same DML).
2. Verify zero records have `Country = United Kingdom`.
3. THEN deactivate the controller value.

Always migrate dependents before deactivating controllers.

---

## Example 4 — Global Value Set rename ripples across 6 fields

**Context.** Global Value Set `Industry_Codes` is used on 6
picklist fields across Account, Lead, Contact, Opportunity. Admin
renames `Tech` → `Technology`. Two days later, a Sales Ops report
shows "Tech" disappeared from the dashboards' picklist filters and
many records show "Technology" while a few still show "Tech".

**What's happening.** Renaming the **label** in the global value set
changed the displayed label everywhere. But records don't store the
label; they store the **API name**. If the API name was also
changed, that's a value migration that needs records updated. If
only the label was renamed, all records "say" Technology even though
their stored API name is unchanged.

**Right answer.** Be deliberate about label-vs-API-name renames.
Renaming label only: ripple is automatic, no record migration. API
name change: treat as a value retirement + new value addition.

---

## Anti-Pattern: Validation rule duplicating picklist restriction

```
Restricted picklist with values: [New, In Progress, Closed]
PLUS validation rule: ISPICKVAL(Status, "New") || ISPICKVAL(Status, "In Progress") || ISPICKVAL(Status, "Closed")
```

**What goes wrong.** The validation rule duplicates what the
restricted picklist already enforces. Both layers reject the same
invalid values. Adding a new picklist value also requires updating
the validation rule (often forgotten). Validation rule errors
accumulate noise.

**Correct.** Restricted picklist is sufficient for value-membership
validation. Use validation rules for cross-field constraints
("Status = Closed requires Closed_Date populated") that the
picklist alone can't express.
