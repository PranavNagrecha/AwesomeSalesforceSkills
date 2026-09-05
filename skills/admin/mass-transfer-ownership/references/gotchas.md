# Gotchas — Mass Transfer Ownership

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: User deactivation blocks while records remain

**What happens:** Admin clicks Deactivate; Salesforce returns "User is currently the default owner of records." Deactivation refuses.

**When it occurs:** The departing user owns at least one active record, or is configured as a default queue/case-owner anywhere in Setup.

**How to avoid:** Always reassign first, then deactivate. Build a pre-deactivation checklist that queries each owned-record source — and add a team-membership pass to it, because the Object Reference's `Deactivate Users` section states that "the user interface provides options to auto-remove a user from teams, but the removal isn't supported in API." A scripted offboarding therefore leaves the departing user on every account and opportunity team unless you delete those rows explicitly.

UNVERIFIED (2026-09-04): the specific message and the claim that deactivation is *refused* while records remain could not be confirmed in the v62 Object Reference, Metadata API, Apex, Data Loader, Bulk API or App Limits PDFs — that behaviour is documented in Salesforce Help, which cannot be fetched here. The transfer-first sequence is correct either way; treat the exact error text as unconfirmed.

---

## Gotcha 2: Sharing recalc continues after the apparent success

**What happens:** Data Loader returns "Operation finished successfully" in 8 minutes. Forty-five minutes later, users still can't see records they own. Help desk lights up.

**When it occurs:** Whenever the org-wide default for the transferred object is Private and the volume exceeds tens of thousands of records.

**How to avoid:** Communicate the recalc lag to stakeholders. Use deferred sharing calculations above roughly 100k rows — UNVERIFIED (2026-09-04): that threshold is a practitioner heuristic, not a published limit; no Salesforce document names a volume at which deferral becomes necessary, and the real trigger is the org's sharing rule count and role depth, which you can only measure in a full sandbox. Monitor Setup → Background Jobs for "Sharing Rule Recalculation" to drain before declaring done, and confirm with a `UserRecordAccess` sample that the new owner reads `HasReadAccess = true`.

---

## Gotcha 3: Data Loader updates do not cascade

**What happens:** Account.OwnerId is updated for 5,000 Accounts. Child Cases retain the old owner. Reports filtered by Case.Owner show wrong attribution.

**When it occurs:** Whenever a parent OwnerId change is done via Data Loader or API rather than the Mass Transfer Records UI.

**How to avoid:** Plan child-object passes explicitly. Build a checklist per parent that lists every child object whose OwnerId should follow.

---

## Gotcha 4: Triggers and assignment rules fire on transfer

**What happens:** A Lead reassignment triggers the Lead assignment rule, which immediately reroutes the Leads back via round-robin. Effective transfer: zero.

**When it occurs:** Any DML update where `AssignmentRuleHeader` is set (default in Data Loader UI for Lead/Case).

**How to avoid:** Uncheck "Use Assignment Rule" in Data Loader, or omit `AssignmentRuleHeader` in Apex. For triggers, gate them on a custom-setting flag your team toggles during migrations.

---

## Gotcha 5: Queue OwnerId requires the object to support queues

**What happens:** Setting `OwnerId = '00G...'` on a custom object returns `INVALID_OWNER`.

**When it occurs:** The object's "Allow Queues" setting is off in Setup.

**How to avoid:** Check the object's `OwnerId` field table in the Object Reference before you build the file. `Case.OwnerId` is documented as a polymorphic relationship field that **Refers To: Group, User**; `Account.OwnerId` is documented as **Refers To: User** — no Group, no queue, ever. For custom objects, verify Setup → Object Manager → \[Object\] → Allow Queues is enabled before targeting `00G` IDs.

---

## Gotcha 6: "Keep Account Team" does not keep team members added by a group-access user

**What happens:** The Account transfer runs with Keep Account Team on. Afterwards a subset of
account team members is simply gone. Not all of them — a subset, which is what makes it look
like a data glitch rather than a documented rule.

**When it occurs:** Whenever a team member was added by a user whose own access to the account
came from a group rather than from ownership or the role hierarchy. The Object Reference states
it without qualification: "If team members are added by a user with group-based access, those
members are removed after an account's owner is changed. This applies even if the Keep account
team option is selected." The team members that survive are the ones added by a Salesforce
admin, a user with Modify All Data, the account owner, or "a user higher than the account owner
in the owner's direct role hierarchy chain (**not a parallel branch**)."

**How to avoid:** Snapshot `AccountTeamMember` for every in-scope account before the transfer
and diff it afterwards — that snapshot is the only way to re-add what vanished. If the teams
matter more than the transfer speed, have an admin re-add the members after the move rather than
trying to preserve them through it.

---

## Gotcha 7: The previous Opportunity owner's access after transfer differs between API and UI

**What happens:** A rep is transferred out of 400 Opportunities through Data Loader and still
sees every one of them in their list views. The admin re-runs the transfer, assuming it failed.

**When it occurs:** On every API-driven Opportunity owner change. Two documented behaviours
combine. First, `Opportunity.OwnerId`: "If you update this field, the previous owner's access
becomes Read Only or the access specified in your organization-wide default for opportunities,
whichever is greater" — so the old owner keeps read access by design. Second, if opportunity
teams are enabled, "For API version 12.0 and later, sharing records are kept, as they are for
all objects. (All previous opportunity team members are kept on the opportunity team.)" The
`OpportunityTeamMember` usage note names the UI/API split directly: "when you change the owner
of an opportunity using the API, the previous owner's access becomes Read Only or the access
specified in your organization-wide default for opportunities, whichever is greater. However,
performing this same action in the user interface allows you to select the access level for the
previous owner when the previous owner is on an opportunity team."

**How to avoid:** If the point of the transfer is to *revoke* the departing rep's visibility,
the `OwnerId` update alone will not do it. Plan a separate `OpportunityTeamMember` delete pass,
or do the small-volume cases through the UI where the access level is selectable. State which
one you chose in the runbook, because "they can still see them" is otherwise reported as a bug.

---

## Gotcha 8: Transferring a child record fails when the new owner can't read the parent Account

**What happens:** An Opportunity or Case transfer returns insufficient-access errors on a
scattered subset of rows. The new owner has the Transfer Record permission and full object
CRUD, so the error reads as nonsense.

**When it occurs:** When the new owner has no read access to the *parent Account*. Salesforce's
Insufficient Access event type documents the scenario: "The user can't change ownership of a
case, contact, or opportunity because the user doesn't have permission to share the parent
account or the new owner doesn't currently have read access to the parent account." The trap is
the next sentence: "Insufficient access errors resulting from bulk operations involving two or
more records aren't logged." Your 40,000-row Bulk job produces exactly zero diagnostic events.

**How to avoid:** Transfer parents before children, always, and sample-check the new owner's
access to the parent set with `UserRecordAccess` (200 ids per query) before the child job runs.
When parents legitimately stay put, grant the new owner read on them first.

---

## Gotcha 9: The Data Loader assignment-rule setting silently overrides your OwnerId column

**What happens:** A Case transfer completes with zero errors and every success row reports a
new owner that is not the one in the CSV.

**When it occurs:** When an assignment rule id is set in Data Loader's Settings dialog. The
guide describes the field as taking "the ID of the assignment rule to use for inserts, updates,
and upserts … on cases and leads" and then states the consequence outright: "The assignment rule
overrides Owner values in your CSV file." The setting persists between sessions, so it is
usually left over from an unrelated load weeks earlier.

**How to avoid:** Open Settings and clear the assignment-rule field before every Case or Lead
transfer, and verify against the `success.csv`, not the row count. On the Bulk API 2.0 path the
equivalent is `assignmentRuleId` in the *Create a Job* body — an optional property, so simply
omitting it is correct. In Apex, leave `assignmentRuleHeader` unset; note that
"`Database.DMLOptions` object supports assignment rules for cases and leads, but not for
accounts."

---

## Gotcha 10: Keep Account Teams fails the whole file if the owners aren't uniform

**What happens:** A territory realignment run with `process.keepAccountTeam=true` fails
outright. No accounts are updated at all — not a partial success, a full stop.

**When it occurs:** When the CSV holds more than one old owner or more than one new owner. The
Data Loader Guide's constraint is exact: "the uploaded .csv file must have the same value for
all Current Account owner records. Likewise, the New Account Owner records must all have the
same value. Otherwise, the operation fails and the Account Owners are not updated." The setting
also requires Data Loader 56.0.3 or later, `sfdc.useBulkApi=false`, and edits made with Data
Loader **closed** — which quietly forces the slower SOAP path on a job you sized for Bulk.

**How to avoid:** Treat Keep Account Teams as a one-pair-per-file operation: split a
many-to-many remap into one file and one run per old-owner/new-owner pair, and budget for SOAP
throughput rather than Bulk. If the pair count is large, keeping the teams is not worth it —
snapshot `AccountTeamMember` instead (Gotcha 6) and re-add.

---

## Gotcha 11: Transfer Record permission is not enough — you also need read on the target User

**What happens:** An integration user or a delegated admin with "Transfer Record" gets access
errors on a transfer they are explicitly permissioned for.

**When it occurs:** When the running user cannot read the *new owner's* User record — common in
orgs where the User object's org-wide default is Private, or where the operator is an external
or restricted-visibility user. The Object Reference is explicit: "To change ownership of a record
by updating its `OwnerId` field, you must have both the Transfer Record permission and Read
access to the User record of the new record owner." On Account specifically, "For API version
16.0 and later, users must have the 'Transfer Record' permission in order to update (transfer)
account ownership using this field."

**How to avoid:** Verify both halves before the run. Query `UserRecordAccess` for
`HasTransferAccess` on a 200-record sample, and separately confirm the operator can `SELECT Id,
Name FROM User WHERE Id = :newOwnerId` in the same session.

---

## Gotcha 12: Every transferred row re-enters the full save order, twice over

**What happens:** A 40,000-record transfer trips validation rules, creates 40,000 tasks from a
record-triggered flow, fires escalation, and re-routes a slice of the file through assignment
rules — none of which the runbook mentioned because the runbook treated `OwnerId` as a field
update rather than a record save.

**When it occurs:** On every owner change, through every tool. The Apex Developer Guide's order
of execution lists what runs on save, and an `OwnerId` update is a save: before-save
record-triggered flows (3), before triggers (4), custom validation rules (5), duplicate rules (6),
after triggers (8), assignment rules (9), auto-response rules (10), workflow rules (11),
escalation rules (12), after-save record-triggered flows (14), entitlement rules (15), roll-up
recalculation into parent and grandparent (16, 17), and **Criteria Based Sharing evaluation
(18)** — before the commit at step 19.

**How to avoid:** Enumerate the automation on each in-scope object against that numbered list
before choosing a batch size, and rehearse in a full sandbox to measure the real per-record cost.
Step 18 is the one that surprises people: criteria-based sharing is re-evaluated inside the same
transaction, so a Private object with several criteria-sharing rules makes each row several times
more expensive than the raw DML suggests.

---

## Gotcha 13: Deferred sharing calculation is off by default, and the two flags are ordered

**What happens:** The runbook says "defer sharing calculations before the transfer." The admin
opens Setup the night before and finds no such option, or deploys `deferSharingRules` and it has
no effect.

**When it occurs:** Two separate causes. First, availability: "The defer sharing calculation
feature isn't enabled by default. To enable it for your Salesforce org, contact Salesforce
Customer Support" — a support case with lead time, not a checkbox. Second, ordering: "If the
`deferGroupMembership` field is set to true, you can't change the value of `deferSharingRules`.
Sharing rule calculations are suspended regardless of the value of `deferSharingRules`." Both
flags are `SharingSettings` fields available in API version 49.0 and later, and using the type
at all needs the Manage Sharing permission.

**How to avoid:** Raise the support case weeks ahead. Suspend group membership last and resume
it first. And plan the window around the *resume*, not the transfer: "When you change the value
of this field from true to false, sharing rules are automatically recalculated. Depending on
your org, this recalculation can take a significant amount of time to complete."

---

## Gotcha 14: Bulk API job results expire in seven days

**What happens:** Three weeks after a transfer, an audit asks which 62 records failed. The job
id is in the runbook; the results are gone.

**When it occurs:** Always. "You can retrieve the ingest job's results (success, failed, and
unprocessed records) within 7 days of job completion, unless the job has been deleted
explicitly." The same window applies to job records themselves: "Jobs in a terminal state
(completed, aborted, or failed) that are older than seven days are deleted."

**How to avoid:** Pull `successfulResults`, `failedResults`, and `unprocessedRecords` on the day
of the run and store them alongside the rollback CSV. The job id in a runbook is a reference to
something that will not exist by the time anyone asks about it.
