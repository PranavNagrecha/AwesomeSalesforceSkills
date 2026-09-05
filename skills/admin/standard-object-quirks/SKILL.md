---
name: standard-object-quirks
description: "Guidance on non-obvious runtime behaviors of Salesforce standard objects — polymorphic lookups, lead conversion field loss, PersonAccount dual-nature, CaseComment trigger isolation, and Activity date fields. Also covers which trigger actually fires for a person account, the either/or Event duration contract, the Closed status category behind Task.CompletedDateTime, the 3-record merge cap and its single delete + single update trigger events, and the CaseComment post-insert write lock. Trigger keywords: person account trigger not firing, Contact trigger person account, Event required field EndDateTime, DurationInMinutes, CompletedDateTime null, merge MasterRecordId, CaseComment cannot be edited, IsNotificationSelected null, lead conversion triggers disabled. NOT for the Activity object model — use admin/activity-and-task-patterns. NOT for writing TYPEOF queries — use apex/apex-polymorphic-soql."
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
  - "contact trigger is not firing when a person account is inserted"
  - "insert event fails with required fields are missing EndDateTime"
  - "task CompletedDateTime is null even though the status looks closed"
  - "merge only fired one delete trigger for three duplicate accounts"
  - "case comment cannot be edited or deleted after it is saved"
  - "why did my account trigger not fire when the record type changed to person account"
tags:
  - standard-object-quirks
  - polymorphic-lookups
  - lead-conversion
  - person-accounts
  - activity-objects
  - case-comments
  - record-merge
inputs:
  - "The standard object(s) involved and the specific behavior that is unexpected"
  - "Whether the org uses PersonAccounts, Lead conversion, or Activity-based automation"
  - "The Apex trigger inventory for the objects in play, so the real firing object can be confirmed"
  - "Whether 'validation and triggers for lead conversion' is enabled in the org"
outputs:
  - "Explanation of the platform behavior causing the issue with official-source grounding"
  - "Corrected code, query, or configuration pattern that accounts for the quirk"
  - "Deployable Apex handler / test class / value-set metadata that encodes the corrected behaviour"
  - "SOQL probes that prove the quirk is present in this specific org"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

# Standard Object Quirks

This skill activates when a practitioner encounters unexpected runtime behavior from Salesforce standard objects — situations where the platform does something that contradicts reasonable assumptions drawn from the UI or general database experience. It provides doc-grounded explanations and corrective patterns for polymorphic lookup behavior, lead conversion field mapping gaps, PersonAccount dual-nature pitfalls, CaseComment trigger isolation, record merge, and Activity date-field confusion.

Two of the most widely repeated "quirks" in this space are backwards. Person-account DML fires **Account** triggers, not Contact triggers. Event does **not** require `EndDateTime` — it requires *either* `EndDateTime` *or* `DurationInMinutes`. Both corrections are sourced below, and both are the reason this skill exists: the folklore is more confident than the documentation.

---

## Before Starting

Gather this context before working on anything in this domain:

- Which standard objects are involved? Confirm whether the org uses PersonAccounts (check `Account.IsPersonAccount` field availability — it is read-only, `Defaulted on create, Filter, Group, Sort`, object_reference.txt L13116–L13122), and whether Lead conversion or Activity automation is in scope.
- The most common wrong assumption is that standard objects behave like custom objects. They do not: standard objects have hard-coded platform behaviors (cascade rules, polymorphic fields, dual-nature records) that cannot be overridden by configuration.
- **Confirm which trigger actually fires before you debug the one you wrote.** The Apex Developer Guide's "Operations That Don't Invoke Triggers" list is the authority for this whole domain (apexdev.txt L15515–L15560) and it contradicts several widely repeated assumptions.
- Key limits: polymorphic fields cannot be traversed in a single SOQL relationship query; Lead conversion field mapping only transfers mapped fields; PersonAccount records share a single Id across Account and Contact but expose different field sets depending on SOQL target; a merge takes a main record plus **at most two** others (apexdev.txt L8202).

## Questions to Ask Before Configuring

Ask these before writing the trigger, the query, or the load file. Each one maps to a gotcha in `references/gotchas.md`, and every one of them is a question an LLM will skip.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Are person accounts enabled, and which object do you believe your logic runs on?" | Person-account inserts, updates and deletes fire Account triggers, not Contact triggers (apexdev.txt L15521). A Contact-side design is simply dead code | The correct handler object, and whether an existing Contact trigger is quietly never running for these records |
| "Does any process convert records between business account and person account record types?" | Update account triggers don't fire in either direction across that conversion (apexdev.txt L15545–L15546), so audit, sync and roll-up logic silently skips those records | A named compensating job, or an accepted gap written down |
| "Is 'validation and triggers for lead conversion' switched on in this org?" | The before triggers on account, contact and opportunity insert (and account/contact update) fire during conversion **only** when it is (apexdev.txt L15548–L15551) | Whether conversion-time validation is a design you can rely on or one you must replace |
| "Which Task statuses are flagged as closed, and are there more than one?" | `CompletedDateTime` follows the **Closed status category**, not the literal value `Completed` (object_reference.txt L277993–L278013). Orgs routinely add `Closed - No Action` | The real status list to filter on, and whether reporting queries are undercounting |
| "For Events, do the source systems send an end time, a duration, or neither?" | Either field satisfies the API; only sending *neither* fails (object_reference.txt L111593–L111597) | Which field the integration maps, and whether both are sent with values that agree |
| "How many duplicates per merge, and what has to survive?" | Three records per call including the master (cheat sheet L977–L982), and the main record's field values — including empty ones — always win (apexdev.txt L8203–L8207) | A successive-merge plan and a pre-merge field-preservation step |
| "Who needs to edit case comments after they are saved?" | In the API, CaseComment can't be modified after insertion without **Modify All Records** on Cases or **Modify All Data**; other users can only update `IsPublished` and can't delete (object_reference.txt L63045–L63049) | Either a permission decision or a design that never edits a comment |

What a proper configuration adds over just doing it: the automation fires on the object the platform actually fires on, the closed-status and duration contracts are read from the org's own metadata instead of a hard-coded string, and the merge and conversion paths have an explicit story for the data the platform is documented to drop.

---

## Core Concepts

### Polymorphic Lookups (WhoId / WhatId)

Task and Event use polymorphic lookup fields: `WhoId` points to either a Contact or a Lead (object_reference.txt L278448, "The WhoId represents a human such as a lead or a contact. WhoIds are polymorphic."), while `WhatId` points to a nonhuman record — the guide's own `Refers To` list names roughly eighty standard types (Account, Asset, Campaign, CareProgram, Opportunity, Product2, …) plus custom objects (object_reference.txt L278390–L278393 description, L278398–L278444 `Refers To`). You cannot traverse both sides of a polymorphic relationship in a single SOQL query using dot notation for type-specific fields; use `TYPEOF` in SOQL or query each target type separately.

UNVERIFIED (2026-09-05): the exact compile error text for dot-notation on a polymorphic field (`No such column 'Email' on entity 'Name'`) and the `TYPEOF` syntax itself are SOQL/SOSL Reference Guide topics — `grep -n "TYPEOF" object_reference.txt apexdev.txt` returns zero hits in both. The polymorphism itself is grounded above; the sibling skill `admin/activity-and-task-patterns` carries the same grounding from the Object Reference. Confirm error strings against your own org.

### Lead Conversion Field Mapping

When a Lead is converted, Salesforce creates or updates a Contact, optionally an Account, and optionally an Opportunity. Standard lead fields are mapped automatically; custom lead fields map only where an admin has configured it (apexdev.txt L8353–L8355). Unmapped custom fields do not arrive on the target records.

Two behaviours compound this. **Merged fields:** where data lands on an *existing* account or contact, only empty target fields are overwritten — existing data, including Ids, survives, with `setOverwriteLeadSource` the single documented exception (apexdev.txt L8356–L8360). **Triggers:** the before triggers on account/contact/opportunity insert and account/contact update fire during conversion only if validation and triggers for lead conversion are enabled in the org (apexdev.txt L15548–L15551). A conversion-time guard written as a before trigger is therefore off by default from Apex's point of view.

UNVERIFIED (2026-09-05): the Setup path for lead field mapping and the claim that unmapped values are lost with "no warning, no error, no audit log entry" are not in the Apex Developer Guide or Object Reference — apexdev.txt L8355 defers explicitly to Salesforce Help. The mapping requirement is grounded; the silence framing is inference.

### PersonAccount Dual-Nature

A person account is an Account whose record type is Person Account, backed by a child person contact record. The Object Reference states it plainly: the `IsPersonAccount Fields` "are the subset of person account fields that are contained in the child person contact record of each person account"; when `IsPersonAccount` is false those fields are null and cannot be modified (object_reference.txt L13677–L13683). Person account fields are exposed on Account with a `Person` prefix — `PersonEmail` carries the UI label "Email", which is exactly why developers reach for a bare `Email` field that does not exist on Account (object_reference.txt L13770).

Three hard platform rules follow, and all three cut against intuition:

| Rule | Source |
|---|---|
| Inserts, updates and deletes on person accounts fire **Account** triggers, **not** Contact triggers | apexdev.txt L15521 |
| Update account triggers don't fire before or after a business↔person account record-type change, in either direction | apexdev.txt L15545–L15546 |
| For a person account, `Name` can't be modified with DML operations | apexdev.txt L9029 |

A fourth catches Apex that introspects schema: field tokens aren't available for person accounts, and `Schema.Account.fieldname` throws — the field name must be passed as a string (apexdev.txt L10866–L10867). Once `IsPersonAccount Fields` hold non-null values you can't set `IsPersonAccount` back to false without an error (object_reference.txt L14042).

### CaseComment, Task and Event Date Contracts

CaseComment has its own trigger context — DML on CaseComment does not fire Case triggers, because Apex triggers are scoped per sObject and CaseComment is one of the standard child objects that carries its own trigger context (apexdev.txt L14849–L14850, L14861–L14863). This is ordinary trigger scoping rather than a CaseComment-specific carve-out, but the *unordinary* parts are the ones that break builds: a CaseComment can't be modified after insertion unless the user holds Modify All Records on Cases or Modify All Data — others can only update `IsPublished`, and can't delete at all (object_reference.txt L63045–L63049) — and `IsNotificationSelected` always returns null when queried (object_reference.txt L62994–L63000). Deleting the parent Case does cascade: "if you delete a case record, Apex automatically deletes any CaseComment, CaseHistory, and CaseSolution records associated with that case" (apexdev.txt L8236–L8240).

On Task, `ActivityDate` is the due date (object_reference.txt L277934). `CompletedDateTime` is "the date and time the task was saved with a **Closed** status", set on insert when the status is Closed, reset on update to a new Closed status, and reset to null on a save with a non-closed status (object_reference.txt L277993–L278009). Status is a dynamic enum: changing the Closed mapping does not update existing tasks (object_reference.txt L278012–L278013). The field is **not** tied to the literal string `Completed`.

For Event, when `IsAllDayEvent` is false, "a value must be supplied for either `DurationInMinutes` or `EndDateTime`. Supplying values in both fields is allowed if the values add up to the same amount of time" (object_reference.txt L111593–L111597, repeated verbatim at L111637–L111641). `EndDateTime` was required only in API 12.0 and earlier; from 13.0 it is optional under that either/or rule (object_reference.txt L111589–L111592).

### Record Merge

Only leads, contacts, cases and accounts can be merged, and a single merge call takes a main record plus **up to two** additional records (apexdev.txt L8201–L8202); the App Limits cheat sheet gives the same cap from the API side and prescribes successive merges beyond three (salesforce_app_limits_cheatsheet.txt L977–L982). The main record's field values always supersede the others *including nulls and empty values*, so a blank on the winner stays blank (apexdev.txt L8203–L8207), and external Id fields can't be used with merge (apexdev.txt L8208).

Merge fires no merge-specific trigger event. It fires one delete event covering every losing record and one update event for the winner only; reparented children fire nothing at all, and `MasterRecordId` on the deleted rows is populated only in **after delete** (apexdev.txt L15354–L15366).

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

### Person-Account-Aware Account Handler Pattern

**When to use:** Any org with person accounts, where logic must distinguish a business account from a person account — and especially when someone has already written the logic on Contact.

**How it works:**

1. Put the logic in an **Account** trigger handler. Person-account DML never reaches a Contact trigger (apexdev.txt L15521), so a Contact-side implementation is unreachable for these records.
2. Branch on `IsPersonAccount` inside the handler rather than filtering records out of a Contact handler.
3. Never assign to `Name` on a person-account record; write `FirstName` / `LastName` instead (apexdev.txt L9029).
4. Where the code introspects schema, use `Schema.getGlobalDescribe()` / `getMap().get('PersonEmail')` with a **string** field name — `Schema.Account.PersonEmail` throws for person accounts (apexdev.txt L10866–L10867).
5. Add a compensating job for record-type conversions, which fire no update account trigger in either direction (apexdev.txt L15545–L15546).

The deployable handler, its bulk-safe test class, and the person/business fixture data are in `references/metadata-examples.md` § 1–2.

**Why not the alternative:** guarding a Contact trigger against person accounts (the pattern this skill previously recommended) protects against something that does not happen, while leaving the real code path — Account — unwritten.

### Lead Conversion Field Preservation Pattern

**When to use:** Custom fields on Lead must survive conversion without relying on per-field manual mapping.

**How it works:**

1. Read the Lead's custom fields into memory **before** calling `Database.convertLead`, since the API gives you no post-hoc access to what was dropped.
2. Convert, then write the captured values onto the Ids returned by `Database.LeadConvertResult`.
3. Do not put this in a before trigger on the target objects unless you have confirmed the org has validation and triggers for lead conversion enabled — they do not fire otherwise (apexdev.txt L15548–L15551).
4. Expect existing target records to keep their data: only empty fields are overwritten (apexdev.txt L8356–L8360), so an update after conversion is the only way to force a value onto an existing Contact.

**Why not the alternative:** Relying solely on Lead Field Mapping requires manual setup per field and is easy to miss when new custom fields are added. Relying on a conversion-time trigger fails silently in the default org configuration.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need Contact/Lead fields from Task | Use TYPEOF in SOQL | Polymorphic lookups cannot use standard dot-notation for type-specific fields |
| PersonAccount email in reports or queries | Query `PersonEmail` on Account | Account has no bare `Email` field; `PersonEmail`'s label is "Email" (object_reference.txt L13770) |
| Logic must run when a person account changes | Account trigger handler, branching on `IsPersonAccount` | Person-account DML fires Account triggers, not Contact triggers (apexdev.txt L15521) |
| Logic must run when a record type flips business↔person | Scheduled or platform-event compensator, not a trigger | Update account triggers don't fire across that conversion (apexdev.txt L15545–L15546) |
| Case automation on comment addition | CaseComment trigger that updates parent Case | Triggers are scoped per sObject; CaseComment DML never enters a Case trigger |
| Editing a CaseComment after save | Redesign to insert a new comment, or grant Modify All Records on Cases | The API blocks post-insert modification without that permission (object_reference.txt L63045–L63049) |
| Preserving custom Lead fields through conversion | Capture before `convertLead`, write after using `LeadConvertResult` Ids | Unmapped custom fields do not transfer; conversion triggers are opt-in |
| Creating Events via Apex or an integration | Set **either** `EndDateTime` **or** `DurationInMinutes`; if both, make them agree | Either field satisfies the API when `IsAllDayEvent` is false (object_reference.txt L111593–L111597) |
| Detecting completed Tasks | Filter on `CompletedDateTime != null`, or on the org's closed status values | The field tracks the Closed status *category*, not the value `Completed` |
| Deduplicating more than three records | Successive merges of three, largest survivor first | Three per request including the master (cheat sheet L977–L982) |

---

## Recommended Workflow

1. **Establish which object the platform fires on.** List the triggers on every object in play, then check them against "Operations That Don't Invoke Triggers" (apexdev.txt L15515–L15560). If person accounts or lead conversion are involved, do this before reading any of your own code — the answer is frequently "the trigger you are debugging never runs."
2. **Reproduce with a probe, not a theory.** Run the matching SOQL probe from `references/metadata-examples.md` § 7 (person-account field exposure, Task closed-status spread, Event duration/end-time population, CaseComment notification nulls, merge survivors via `MasterRecordId`). Each probe returns org-specific evidence rather than a restatement of the doc.
3. **Match the symptom to a gotcha.** Work `references/gotchas.md` top to bottom; it is ordered by how often the folklore is inverted rather than merely incomplete. Read `references/llm-anti-patterns.md` if the code under review was AI-generated — anti-patterns 6–8 cover exactly the claims this skill had to correct.
4. **Deploy the corrected shape from `references/metadata-examples.md`.** The Account handler + test class (§ 1–2), the `Database.merge` result handling (§ 3), the two valid Event insert forms (§ 4), the `TaskStatus` value set with its `closed` flags (§ 5), and the package.xml and `sf project deploy` commands (§ 8).
5. **Run the checker.** `python3 scripts/check_standard_object_quirks.py --manifest-dir force-app/main/default` flags Contact triggers that assume person-account events, Event DML with neither duration form, merge calls exceeding three records, `TaskStatus` value sets with no `closed` value, and polymorphic dot-notation. It is stdlib-only and reads source, not an org.
6. **Prove it with tests that cover both branches.** The test class in § 2 asserts the Account handler runs for a person account and that no Contact trigger was involved; extend it with a business-account case and a `MasterRecordId` assertion for merge.
7. **Record the org-specific answers in `templates/standard-object-quirks-template.md`** — closed status values, whether conversion triggers are enabled, and which permission set carries Modify All Records on Cases. These are org facts, not platform facts, and they change.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] All SOQL queries on Task/Event use TYPEOF or explicit type checks for WhoId/WhatId
- [ ] PersonAccount queries use Person-prefixed fields (PersonEmail, PersonMailingCity) not standard Contact fields on Account
- [ ] Person-account logic lives in an **Account** trigger handler, not a Contact one
- [ ] No code assigns `Account.Name` on a person-account record
- [ ] Schema introspection on Account uses string field names, not `Schema.Account.<field>` tokens
- [ ] Record-type conversion between business and person account has a non-trigger compensator
- [ ] Lead conversion logic captures unmapped custom fields **before** `convertLead` and writes them after
- [ ] Conversion-time before-trigger logic is only relied on if the org setting is confirmed enabled
- [ ] CaseComment-driven automation uses a CaseComment trigger, and never attempts to edit a saved comment
- [ ] Event creation sets either `EndDateTime` or `DurationInMinutes`, and both agree if both are set
- [ ] Task completion filters use `CompletedDateTime` or the org's real closed status list, not the literal `'Completed'`
- [ ] Merge calls pass at most three records and read `MasterRecordId` in an **after delete** context
- [ ] `python3 scripts/check_standard_object_quirks.py --manifest-dir <src>` reports no issues
- [ ] Code comments explain the non-obvious platform behavior at each quirk site

---

## Salesforce-Specific Gotchas

The full set, each with **What happens / When it occurs / How to avoid** and its source line, is in `references/gotchas.md`. The three that most often survive code review because everyone agrees on the wrong answer:

1. **Contact triggers do not fire for person accounts.** Guarding a Contact trigger against person accounts defends against an event the platform never raises.
2. **Event has no single required date field.** Either `DurationInMinutes` or `EndDateTime` satisfies the API; only omitting both fails.
3. **`Task.CompletedDateTime` follows the Closed status category.** An org with a second closed status populates it for statuses that are not spelled `Completed`.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Corrected SOQL query or Apex snippet | Revised code that accounts for the identified standard-object quirk |
| Account trigger handler + test class | Person-account-aware dispatch, deployable, in `references/metadata-examples.md` § 1–2 |
| `TaskStatus` standard value set | Closed-status flags that drive `CompletedDateTime` and `IsClosed`, § 5 |
| SOQL probe set | Org-specific evidence that a quirk is present, § 7 |
| Quirk documentation comment | Inline code comment explaining the non-obvious behavior for future maintainers |
| Checker run output | `scripts/check_standard_object_quirks.py` findings across the source tree |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | Building the deployable artefacts — person-account-aware Account handler and test class, `Database.merge` with result handling, both valid Event insert forms, the `TaskStatus` value set, the CaseComment permission note, SOQL probes, and package.xml plus CLI commands |
| `references/gotchas.md` | Before writing or reviewing any automation on Account, Contact, Lead, Task, Event, Case or CaseComment — and first when a trigger "isn't firing" |
| `references/examples.md` | Three worked scenarios end to end: a polymorphic Task query, a person-account field query, and CaseComment-driven Case activity |
| `references/llm-anti-patterns.md` | Reviewing AI-generated Apex or SOQL that touches these objects; anti-patterns 6–8 are the inverted-folklore ones |
| `references/well-architected.md` | Weighing explicit quirk handling against complexity, and citing the source behind any claim in this skill |

---

## Related Skills

- `admin/activity-and-task-patterns` — the Activity object model itself: `ActivitiesSettings`, shared Task/Event fields, `TaskStatus`, Shared Activities
- `apex/apex-polymorphic-soql` — `TYPEOF`, `What.Type` and `instanceof` in depth, including the syntax this skill deliberately leaves UNVERIFIED
- `apex/trigger-framework` — where person-account-aware logic belongs in a handler, and the base class the § 1 example extends
- `admin/lead-management-and-conversion` — designing the conversion process, lead field mapping, and converted-status configuration
- `admin/duplicate-management` — matching and duplicate rules that feed the merge path this skill's merge gotchas govern
- `admin/case-management-setup` — Case and CaseComment configuration, support settings, and case feed behaviour
- `admin/data-model-documentation` — documenting the overall schema rather than diagnosing a runtime behavioral quirk
- `admin/validation-rules` — when the fix for a quirk is a validation rule enforcing data integrity
- `admin/sharing-and-visibility` — when the quirk involves record access, OWD, or sharing rule behavior on standard objects
