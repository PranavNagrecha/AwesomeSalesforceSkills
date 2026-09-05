# Gotchas — Standard Object Quirks

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

Ordered by how badly the common belief is wrong: gotchas 1–3 correct claims that most
practitioners (and most LLMs) state backwards; 4–12 are behaviours that are simply
unknown until they bite. Line references are into the Summer '26 / v62 PDFs — the Apex
Developer Guide (`apexdev.txt`), the Object Reference (`object_reference.txt`), the
Metadata API Developer Guide (`api_meta.txt`) and the Salesforce App Limits cheat sheet.

## Gotcha 1: Person-Account DML Fires Account Triggers, Not Contact Triggers

**What happens:** Inserting, updating or deleting a person account runs your **Account**
triggers only. The Apex Developer Guide states it as a note inside "Operations That Don't
Invoke Triggers": "Inserts, updates, and deletes on person accounts fire Account triggers,
not Contact triggers" (apexdev.txt L15521). Logic written on Contact — including the
defensive `IsPersonAccount` guard that circulates widely — never executes for these records.
Two failures follow: the intended behaviour is missing, and the guard code creates false
confidence that the case was handled.

**When it occurs:** Every person-account DML operation, in every org with person accounts
enabled. It is invisible in a Contact-only sandbox and appears the day the org turns person
accounts on.

**How to avoid:** Put the logic in an Account trigger handler and branch on
`IsPersonAccount` (read-only; `Defaulted on create, Filter, Group, Sort` —
object_reference.txt L13116–L13122). Treat any `IsPersonAccount` guard found inside a
Contact trigger as evidence that the real requirement was never implemented, and go looking
for the Account-side code that should exist.

```apex
// AccountTriggerHandler — the branch belongs here, not in a Contact trigger.
protected override void beforeInsert() {
    for (Account a : (List<Account>) Trigger.new) {
        if (a.IsPersonAccount) {
            // person-account path: FirstName/LastName, PersonEmail, PersonMailingCity
        } else {
            // business-account path: Name, Phone, BillingCity
        }
    }
}
```

---

## Gotcha 2: Event Requires *Either* DurationInMinutes *or* EndDateTime, Not EndDateTime Specifically

**What happens:** The API contract is an either/or, not a hard requirement on `EndDateTime`.
The Object Reference gives the same sentence twice, once under each field: "If
`IsAllDayEvent` is false, a value must be supplied for either `DurationInMinutes` or
`EndDateTime`. Supplying values in both fields is allowed if the values add up to the same
amount of time" (object_reference.txt L111593–L111597 and L111637–L111641). `EndDateTime`
was mandatory only in API 12.0 and earlier; from 13.0 onward it is optional under that rule
(object_reference.txt L111589–L111592). An insert that sets neither field fails; an insert
that sets only `DurationInMinutes` succeeds.

**When it occurs:** Whenever an integration, Flow or Apex path supplies neither field —
typically because the mapping assumes the UI's implicit duration default. It also occurs as
a *reported* error on the wrong field: for API 38.0 and earlier the error always surfaces on
`DurationInMinutes`, and from 39.0 the error location depends on which field was left empty
(object_reference.txt L111642–L111646). That version split is why the same defect produces
different error text in two orgs.

**How to avoid:** Require exactly one of the two in the field mapping and validate it before
DML. If both are populated — a common outcome when a calendar system sends both — assert
that they agree, because disagreement is what the guide explicitly disallows. Do not add
`EndDateTime` "because the API needs it" when the payload already carries a duration.

---

## Gotcha 3: Task.CompletedDateTime Tracks the Closed Status *Category*, Not the Value "Completed"

**What happens:** The field is "the date and time the task was saved with a **Closed**
status" (object_reference.txt L277989–L277994). On insert it is set if the task is saved
with a Closed status and null if saved Open; on update it is reset when saved with a *new*
Closed status, reset to **null** when saved with a non-closed status, and left alone when
saved with the same closed status unchanged (object_reference.txt L278003–L278009). An org
with `Closed - No Action` alongside `Completed` populates the field for both, so a report
filtered on `Status = 'Completed'` undercounts, while one filtered on
`CompletedDateTime != null` does not.

**When it occurs:** Any org that has added a second closed status — which is most orgs with
a mature service or sales process. The bug is invisible in a default org where `Completed`
happens to be the only closed value.

**How to avoid:** Filter on `CompletedDateTime != null`, or read the closed values out of the
`TaskStatus` standard value set rather than hard-coding a string (see
`references/metadata-examples.md` § 5). Note also that the status picklist is a dynamic enum:
"If the Closed mapping is changed it won't cause an update of existing tasks. Only new
insert/update operations are affected" (object_reference.txt L278012–L278013) — so flipping
`closed` on a value leaves historical rows inconsistent with the new definition.

Related: `ActivityDate` is the due date, labelled "Due Date" (object_reference.txt L277934),
never the completion date. And the Properties line on `CompletedDateTime` reads `Filter,
Nillable, Sort` — no Create, no Update (object_reference.txt L277991–L277992) — so you cannot
backfill it during a migration. Historical completion dates need a custom field.

---

## Gotcha 4: Lead-Conversion Triggers Are Opt-In at the Org Level

**What happens:** The before triggers on insert of accounts, contacts and opportunities, and
on update of accounts and contacts, "fire during lead conversion **only if** validation and
triggers for lead conversion are enabled in the organization" (apexdev.txt L15548–L15551).
With the setting off — the default state most orgs are in — a before-insert Contact trigger
written to normalise or validate conversion output simply does not run for converted records,
while running perfectly for every other Contact insert. The result is a data-quality rule
that holds everywhere except on exactly the records conversion produces.

**When it occurs:** Every conversion in an org where the setting has not been turned on. It
surfaces as "the validation works when I create the contact manually" — which is true, and
is the reason the defect survives triage.

**How to avoid:** Confirm the org setting before designing any conversion-time guard. If it
is off and cannot be turned on, move the logic out of the trigger: capture the values before
`Database.convertLead` and write them after using the Ids on `Database.LeadConvertResult`.
Turning the setting on is itself a behaviour change — every existing before trigger starts
firing during conversion — so it belongs in a release, not a hotfix.

---

## Gotcha 5: Lead Conversion Only Fills Empty Fields on Existing Targets

**What happens:** When conversion merges into an *existing* account or contact, "only empty
fields in the target object are overwritten—existing data (including IDs) are not
overwritten", with `setOverwriteLeadSource` on the `LeadConvert` object as the only
documented exception, and that exception covers `LeadSource` alone (apexdev.txt
L8356–L8360). Separately, the system maps standard lead fields automatically but custom lead
fields only where an admin configured the mapping (apexdev.txt L8353–L8355). So a
better-quality value on the Lead loses to a stale value already sitting on the Contact.

**When it occurs:** Any conversion that matches an existing Contact or Account — the normal
case in an org with duplicate management, and the case that "reconvert to fix the data" is
expected to solve. It does not.

**How to avoid:** Treat conversion as create-or-fill, never as update. If the Lead's value
must win, do an explicit update after conversion against `LeadConvertResult.getContactId()`.
For custom fields, keep a test that enumerates Lead custom fields and asserts each has either
a mapping or an explicit post-conversion copy — new fields are unmapped by default, so the
gap reopens with every schema change.

UNVERIFIED (2026-09-05): the widely repeated framing that unmapped values are lost with "no
warning, no error, and no audit log entry" is not stated in either guide; apexdev.txt L8355
defers to Salesforce Help for mapping details. The mapping requirement above is grounded; the
silence is inference. Confirm the audit behaviour in your own org before quoting it.

---

## Gotcha 6: Record-Type Conversion Between Business and Person Account Fires No Account Trigger

**What happens:** "Update account triggers don't fire before or after a business account
record type changes to person account. They also don't fire before or after a person account
record type changes to business account" (apexdev.txt L15545–L15546). Both directions are
silent. Roll-ups, audit trails, external syncs and field-derivation logic all skip the single
most consequential change that can happen to an account record.

**When it occurs:** Data migrations that convert account types in bulk, and admin cleanup of
records created against the wrong record type. It is easy to miss because ordinary field
updates on the same records *do* fire triggers, so the automation looks healthy.

**How to avoid:** Detect the conversion outside the trigger path — a scheduled job comparing
`RecordTypeId` (or `IsPersonAccount`) against a stored snapshot, or a field-history / event
feed comparison. Do not expect `Trigger.old` to show you the transition; you will never be
called. Where the conversion is a known project step, run the compensating job as a
documented part of the runbook rather than trusting automation to notice.

---

## Gotcha 7: PersonAccount `Name` Cannot Be Written by DML, and Schema Field Tokens Throw

**What happens:** Two separate rules bite Apex that treats a person account as an ordinary
Account. First: "If an Account record has a record type of Person Account, the `Name` field
can't be modified with DML operations" (apexdev.txt L9029) — the name is composed from the
child person contact's `FirstName` / `LastName`. Second: "Field tokens aren't available for
person accounts. If you access `Schema.Account.fieldname`, you get an exception error.
Instead, specify the field name as a string" (apexdev.txt L10866–L10867). Generic code that
builds field lists from `Schema.Account.<field>` tokens throws, and generic code that assigns
`Name` fails on DML.

**When it occurs:** Reusable utilities — field-mapping engines, dynamic SOQL builders,
data-loading frameworks — that were written and tested against business accounts. Both
failures appear only once a person account enters the data set.

**How to avoid:** Assign `FirstName` and `LastName` on person accounts and let the platform
compose `Name`. Reach fields through `Schema.getGlobalDescribe().get('Account')
.getDescribe().fields.getMap().get('PersonEmail')` — string keys — rather than dotted tokens.
A related trap sits nearby: once the `IsPersonAccount` fields hold non-null values you can't
set `IsPersonAccount` back to false without an error (object_reference.txt L14042), so the
conversion is one-way for those records.

---

## Gotcha 8: A CaseComment Is Effectively Write-Once Without Modify All

**What happens:** "In the API, CaseComment records can't be modified after insertion unless
the user has the 'Modify All Records' object-level permission for Cases or the 'Modify All
Data' permission. If not, users can only update the `IsPublished` field, and can't delete
CaseComment" (object_reference.txt L63045–L63049). An edit-comment feature therefore either
requires one of the two broadest permissions in the platform, or does not exist. Note the
asymmetry: all users can *create* and *view* comments, so the design looks viable right up to
the first update.

**When it occurs:** Any redaction, correction or moderation flow built on CaseComment, and
any data-fix script run as an integration user without Modify All Data.

**How to avoid:** Design for append-only: insert a superseding comment rather than editing.
Where a genuine correction path is required, decide explicitly whether granting Modify All
Records on Cases to a small permission set is acceptable, and record that decision — it also
grants read and edit of every case in the org. `CommentBody` is capped at 4,000 bytes
(object_reference.txt L62929), so long corrections need chunking regardless.

---

## Gotcha 9: CaseComment.IsNotificationSelected Always Reads Null

**What happens:** The field is `Create, Defaulted on create, Update` — writable — but "when
this field is queried, it always returns null" (object_reference.txt L62994–L63000). It is a
write-only control that instructs the platform to email the case contact; it is not a stored
flag you can read back. Code that queries it to decide whether a notification was already
sent gets null every time and, if the logic is "notify when null", sends a duplicate email on
every run.

**When it occurs:** Idempotency checks, replay logic, and reconciliation reports over
CaseComment. It is also a silent trap in test assertions: asserting the field is null after
setting it true passes, and proves nothing.

**How to avoid:** Never read it. Track notification state in your own field or in the audit
trail of the sending system. Also note the field only functions when Enable Case Comment
Notification to Contacts is enabled in Support Settings (object_reference.txt L63001–L63004),
so setting it true in an org without that setting is a no-op that reads null either way —
indistinguishable from success.

---

## Gotcha 10: Merge Takes Three Records Total and Fires One Delete Plus One Update

**What happens:** "Only leads, contacts, cases, and accounts can be merged" and "you can pass
a main record and up to two additional sObject records to a single merge method" (apexdev.txt
L8201–L8202); the App Limits cheat sheet repeats the cap from the API side — "up to three
records can be merged in a single request, including the master record… To merge more than 3
records, do a successive merge" — and adds that external Id fields can't be used with
`merge()` (salesforce_app_limits_cheatsheet.txt L977–L982). Trigger behaviour is equally
compressed: a merge fires **one** delete event covering all losing records and **one** update
event for the winner only, and "any child records that are reparented as a result of the
merge operation do not fire triggers" (apexdev.txt L15354–L15366). `MasterRecordId` on the
deleted rows is set only in **after delete** — never before (apexdev.txt L15358–L15359).

The field-survival rule is the one that loses data: "field values on the main record,
including null and empty field values, always supersede the corresponding field values on the
records to be merged" (apexdev.txt L8203–L8207). A blank on the winner stays blank even when
the loser held a good value.

**When it occurs:** Every dedupe run. The record-count cap bites in bulk cleanup; the trigger
compression bites when downstream logic expects per-record events; the null-supersedes rule
bites when the "best" record was chosen by recency rather than completeness.

**How to avoid:** Merge in successive batches of three, most-complete record as master. Copy
any field you want preserved onto the master *before* merging. Detect merge-caused deletes by
reading `MasterRecordId` from `Trigger.old` in an **after delete** trigger, and do not rely on
child-record triggers to fire for reparenting. Worked code is in
`references/metadata-examples.md` § 3.

---

## Gotcha 11: The Two Guides Disagree on Whether Case Supports merge()

**What happens:** The Apex Developer Guide lists cases among the mergeable objects
(apexdev.txt L8201). The Object Reference's Case entry does not: its Supported Calls line
reads `create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(),
query(), retrieve(), search(), undelete(), update(), upsert()` — no `merge()`
(object_reference.txt L62206–L62207). Account, Contact and Lead all list `merge()` explicitly
in the same guide (object_reference.txt L12740–L12741, L71309–L71310, L163052–L163053), so
the omission on Case is specific rather than a formatting artefact.

**When it occurs:** When planning case deduplication, or when an LLM cites one guide to
justify a design the other does not support.

**How to avoid:** State both sources when the question comes up, and settle it empirically in
a scratch org before committing to a case-merge design — `Database.merge` against two Cases
either compiles and runs or it does not, and that test costs minutes. Do not present either
guide alone as settled. Where case merge turns out to be unavailable, the fallback is a
close-and-link pattern using `Case.ParentId`.

---

## Gotcha 12: Cascading Delete Is Real for Case Children and Absent for Account→Contact

**What happens:** The delete operation supports cascading deletions: "if you delete a case
record, Apex automatically deletes any CaseComment, CaseHistory, and CaseSolution records
associated with that case. However, if a particular child record is not deletable or is
currently being used, then the delete operation on the parent case record fails" (apexdev.txt
L8236–L8240). So a Case delete can be blocked by an undeletable child — including a
CaseComment the running user lacks permission to delete (gotcha 8). Deleted records sit in the
Recycle Bin for 15 days (apexdev.txt L8212, L8260).

**When it occurs:** Bulk case purges run as a user without Modify All Data, where the delete
fails on the comment rather than on the case, producing an error that names the wrong object.

**How to avoid:** Run purges as a user who can delete every child type, and expect partial
failure otherwise. For the Account→Contact direction, the guides describe cascade as a
parent/child behaviour and document `Contact.AccountId` as `Nillable` (object_reference.txt
L71327–L71336) — consistent with a lookup that survives parent deletion — but do not state
the null-out mechanism.

UNVERIFIED (2026-09-05): the specific claim that deleting an Account sets `Contact.AccountId`
to null and leaves the Contact in place is not stated in the Object Reference or the Apex
Developer Guide (`grep -n -i "orphan"` returns nothing relevant in either). It is a
Salesforce Help topic that could not be fetched. Test the behaviour in a sandbox before
relying on it; the deletable-children rule above is what is actually documented.
