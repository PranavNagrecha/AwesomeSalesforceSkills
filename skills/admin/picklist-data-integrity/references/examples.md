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

**What the reconciliation actually looks like.** Neither side of this
can be read off a single screen: describe returns only active values
(apexrefguide.txt:190848–190849) and the records return only what is
stored, so the finding is the difference between two result sets. Run
`references/metadata-examples.md` §1 and you get:

```text
=== Account.Region__c ===
restricted       : false
defined (active) : {AMER, APAC, EMEA}
stored           : {AMER=8102, EMEA=5330, APAC=2914, EMEA-North=1187, emea-north=0}

ORPHANED         : "EMEA-North" on 1187 record(s)
  sample Ids     : (0015g00001AbCdEAAV, 0015g00001AbCdFAAV, 0015g00001AbCdGAAV)
UNUSED           : none
```

Two details in that output do the diagnostic work. `restricted: false`
is why the write succeeded at all. And `emea-north` appearing with a
count of zero is the tell that the source system has been sending mixed
casing: the unrestricted write path creates an inactive picklist entry
and matches it case-insensitively
(object_reference.txt:2363–2367), so the second casing collapsed onto
the first rather than becoming a second population of records. See
`references/gotchas.md` § 10.

Whichever fix is chosen, it gets a governance record before it is
deployed — `references/metadata-examples.md` §6:

```yaml
id: PKL-2026-021
object: Account
field: Region__c
value: EMEA-North
action: add                 # promoting the phantom to a real value
reason: >
  Source CRM has used EMEA-North as a first-class region since the FY26
  territory split. Salesforce never adopted it, so 1187 accounts are
  invisible to every Region-filtered report.
affected_records: 1187
audit_environment: production
owner: pranav.nagrecha@example.com
date: 2026-09-04
```

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

The dashboard cannot answer "how many On Hold cases are left" once the
value is retired, because its filter is built from the values the
picklist currently offers. The count has to come from a query, which is
bound to the stored key and does not care whether the value is active:

```sql
-- Before the migration: the size of the problem.
SELECT Status, COUNT(Id)
FROM Case
GROUP BY Status
ORDER BY COUNT(Id) DESC
-- ... New 4021 / Working 890 / Escalated 233 / On Hold 30

-- After the migration, and again after the deploy: must be zero rows.
SELECT COUNT(Id) FROM Case WHERE Status = 'On Hold'
```

Run the second query a second time *after* the deactivation deploys. A
non-zero result there means something is still writing the retired value
— a scheduled job, an integration, a Flow — and the migration will need
repeating once that write path is closed.

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
