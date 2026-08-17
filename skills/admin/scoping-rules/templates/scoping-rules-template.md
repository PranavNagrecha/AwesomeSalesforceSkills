# Scoping Rule Design Record

Fill this in before building anything. Sections 1 and 2 decide whether the rest applies.

**Skill:** `admin/scoping-rules`
**Author:** [REPLACE: your name]
**Date:** [REPLACE: YYYY-MM-DD]
**Target org(s):** [REPLACE: sandbox name → production, or the promotion path]

---

## 1. Classification — focus or access

Answer this before opening Setup. It is the only question that can invalidate the whole design.

> If the affected user deliberately goes looking for an excluded record, is it acceptable that they find and open it?

- [ ] **YES** — focus requirement. Continue with this template.
- [ ] **NO** — access requirement. **Stop.** A scoping rule cannot satisfy this. Route to `admin/restriction-rules` (custom objects, external objects, Contract, Event, Quote, Task, TimeSheet, TimeSheetEntry) or to the sharing model via `admin/sharing-and-visibility`. Record the redirect below and close this document.

**Requirement as stated by the stakeholder:** [REPLACE: their words, verbatim]

**Classification and who confirmed it:** [REPLACE: name + date]

**Statement delivered to the stakeholder** (copy this, do not soften it):

> This sets the records you land on by default. It does not remove access. Any affected user can switch scope on a list view or report, and a direct link to an excluded record will still open normally. Global search is not scoped.

---

## 2. Feasibility gate

| Check | Value | Pass? |
|---|---|---|
| Target object | [REPLACE: object API name] | Must be a custom object, or Account, Case, Contact, Event, Lead, Opportunity, or Task |
| Org edition | [REPLACE: edition] | Performance, Unlimited, or Developer |
| Interface | — | Lightning Experience only |
| Acting identity holds **Manage Sharing** | [REPLACE: yes/no] | Required to create or manage |
| Reviewers hold **View Setup and Configuration** + **View Restriction and Scoping Rules** | [REPLACE: yes/no] | Required to view |
| Active scoping rules already on this object | [REPLACE: count] | Cap is 2 (Developer) / 5 (Performance, Unlimited) |
| Restriction rules already on this object | [REPLACE: count and their userCriteria] | One scoping *or* restriction rule per object per user |

If any row fails, stop and record why: [REPLACE: reason, or "all pass"]

---

## 3. Criteria design

**Record criteria (`recordFilter`)** — which records are "relevant":

```text
[REPLACE: e.g. Department=$User.Department]
```

**User criteria (`userCriteria`)** — which users the rule applies to:

```text
[REPLACE: e.g. $User.UserRoleId = '00Exxxxxxxxxxxx']
```

**Build path** — determined by the criteria, not by preference:

- [ ] A single EQUALS comparison → Object Manager is available (Setup → Object Manager → the object → Scoping Rules → New)
- [ ] Needs a `SOQL(...)` operator → **API only.** Object Manager cannot express this.

**Criteria validation:**

- [ ] Every referenced field is one of: boolean, date, dateTime, double, int, reference, string, time, single picklist value
- [ ] Exactly one EQUALS comparison — no `AND`, no `OR`, no `>`/`<`/`LIKE`/`!=` (they do not exist outside the SOQL operator)
- [ ] No `IsPersonAccount` field on Account (`PersonDepartment`, `PersonLeadSource`, …)
- [ ] No null or blank value anywhere in the criteria
- [ ] No lookup path deeper than one level
- [ ] Every owner reference is typed to User (`Owner:User`), never bare `Owner` and never a queue/group
- [ ] Any literal value containing a comma is double-quoted
- [ ] Not a rule on `Event.IsGroupEvent`

**If using the SOQL operator, additionally:**

- [ ] Every `SELECT`, including every nested `SELECT`, carries `USING SCOPE EVERYTHING` (the documented nested example omits it on the inner query — write the compliant superset and verify in a sandbox; see `gotchas.md` Gotcha 5)
- [ ] The subquery does not run `FROM` ActivityHistory, Attachment, Event, EventAttendee, Note, OpenActivity, a tag object, or Task — those are barred from the SOQL operator even when the target entity is scopeable
- [ ] No scope value other than `EVERYTHING` appears
- [ ] No `$User.` reference other than `$User.Id`
- [ ] The query object is not the same object as `targetEntity`
- [ ] The left operand is a single ID or reference field on the target entity
- [ ] The subquery was run standalone, as an affected user, at production scale, and timed: [REPLACE: ms]

---

## 4. Deployable artefact

```xml
<!-- force-app/main/default/restrictionRules/[REPLACE: Rule_API_Name].rule-meta.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<RestrictionRule xmlns="http://soap.sforce.com/2006/04/metadata">
    <active>false</active>
    <description>[REPLACE: documented as a required field — do not omit]</description>
    <enforcementType>Scoping</enforcementType>
    <masterLabel>[REPLACE: human-readable rule label]</masterLabel>
    <recordFilter>[REPLACE: record criteria from section 3]</recordFilter>
    <targetEntity>[REPLACE: object API name]</targetEntity>
    <userCriteria>[REPLACE: user criteria from section 3]</userCriteria>
    <version>1</version>
</RestrictionRule>
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
  <types>
    <members>*</members>
    <name>RestrictionRule</name>
  </types>
  <version>[REPLACE: API version, e.g. 67.0]</version>
</Package>
```

Directory layout for a Metadata API deploy:

```text
myPackage/package.xml
myPackage/restrictionRules/[REPLACE: Rule_API_Name].rule
```

Note `active` is `false` above. Deploy inactive, remap IDs (section 5), then activate.

---

## 5. Org-specific ID remap

Every role, profile, record type or user ID in the criteria is org-specific and will match nobody in the destination org if left unchanged.

| Placeholder in criteria | Meaning | Sandbox value | Production value |
|---|---|---|---|
| [REPLACE: e.g. `$User.UserRoleId`] | [REPLACE: e.g. Consulting Staff role] | [REPLACE] | [REPLACE] |

- [ ] No IDs in the criteria — nothing to remap
- [ ] All rows above completed and verified against the destination org

---

## 6. Surface wiring

**The rule changes nothing a user sees until this section is done.** List views and reports honour a scoping rule only when **Filter by scope** is selected.

| Surface | API name | Change | Done |
|---|---|---|---|
| List view | [REPLACE: ListView fullName] | `<filterScope>ScopingRule</filterScope>` | [ ] |
| Report | [REPLACE: Report fullName] | set the `scope` field | [ ] |

- [ ] Every list view the affected users start their day in is listed above
- [ ] This list is stored with the rule, because removal requires unwinding these **before** the rule is disabled — "after a scoping rule is disabled, the list views and reports aren't functional nor modifiable" — and no Setup page enumerates them

**User-switchable scope** (optional): if users need to move between scopes themselves, the documented approach is a Flow in the Lightning Utility Bar that writes the user-side attribute the `recordFilter` compares against.

- [ ] Not needed
- [ ] Flow: [REPLACE: flow API name] writing [REPLACE: User field]

---

## 7. Validation

Run every check. The Setup page looks identical whether the rule works or not, so none of these can be skipped.

- [ ] Deployed inactive, IDs remapped, then activated
- [ ] Logged in as a user matched by `userCriteria`: the wired list view returns the reduced set
- [ ] Logged in as a user matched by `userCriteria`: `SELECT COUNT() FROM [object]` returns the reduced count, and `SELECT COUNT() FROM [object] USING SCOPE everything` returns the full count — proving access is intact
- [ ] Logged in as a user **not** matched by `userCriteria`: nothing changed for them
- [ ] Confirmed no user is matched by two scoping or restriction rules on this object
- [ ] Duplicate rules on this object reviewed — scope narrows potential duplicates shown, even when *Bypass sharing rules* is on
- [ ] Performance measured in a full sandbox at production data volume, not a scratch org or developer sandbox
- [ ] Checker run: `python3 skills/admin/scoping-rules/scripts/check_scoping_rules.py --manifest-dir <metadata-dir>`

**Rollback plan** (reverse order — this is not optional):

1. Delete or re-point every list view and report in section 6 that has **Filter by scope** selected. Salesforce's instruction is *delete*, and this must happen while the rule is still enabled — afterwards they are neither functional nor modifiable
2. Then set `active` to `false` on the rule
3. Then delete the rule if it is not coming back

---

## 8. Notes

**Deviations from the standard pattern and why:** [REPLACE: or "none"]

**Open risks:** [REPLACE: e.g. rule may be disabled by Salesforce if the object grows past current volume — monitoring owner and check cadence]
