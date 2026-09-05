# Gotchas: Flow for Admins

---

## Fault Connectors Are Not Optional on DML and Callout Elements

**What happens:** A Record-Triggered Flow creates a child record. The parent record is deleted between the trigger firing and the DML executing (race condition in a concurrent environment). The Flow fails with an unhandled exception. The triggering record's save is rolled back. The user gets a generic error. No one gets notified. The admin finds out three days later when a user says "I've been getting a weird error."

**When it bites you:** Every time a Flow performs DML or makes a callout without a fault connector. Common in: high-concurrency environments, records that users frequently delete, integrations that update records simultaneously.

**How to avoid it:**
- Every Get Records, Create Records, Update Records, Delete Records, and callout element gets a fault connector. No exceptions.
- The fault path minimum: Send an email to the org admin with `{!$Flow.FaultMessage}` and the record ID
- Better: Create a record in an Error_Log__c custom object so errors are queryable
- Best for Screen Flows: Show the user a human-readable error screen so they know what happened

---

## Record-Triggered Flows Run Once Per Record in the Batch — Not Once Per Bulk Operation

**What happens:** An admin writes a Record-Triggered Flow that includes a Get Records element to query related Cases. The flow works fine in testing (one record at a time). In production, a data migration updates 200 Accounts simultaneously. The flow runs 200 times, executing 200 Get Records queries. The SOQL limit is 100 per transaction. The 101st Account fails.

**When it bites you:** Any bulk operation on an object with a Record-Triggered Flow that includes Get Records — data migrations, mass updates via reports, API batch operations.

**How to avoid it:**
- Don't use Get Records inside a Loop element in a Record-Triggered Flow
- Use Flow formulas to reference the triggering record's fields directly — no additional SOQL needed
- For truly complex cross-object logic in bulk contexts, consider Apex (which can batch queries efficiently) rather than Flow

---

## Before-Save Flows Cannot Make DML Calls

**What happens:** An admin builds a Before-Save Record-Triggered Flow. Partway through, they add a "Create Records" element to create a related Task. The flow activates. First time it runs, it throws: `CANNOT_INSERT_UPDATE_ACTIVATE_ENTITY`. The error is confusing. The admin spends an hour investigating.

**When it bites you:** Every time someone adds a DML element to a Before-Save flow without realising the restriction.

**How to avoid it:**
- Before-Save flows: field updates on the triggering record ONLY (using "Update Triggering Record" element)
- Any DML on other records → change to After-Save
- The distinction to remember: Before-Save = "change this record before it's written." After-Save = "do things after the record exists."

---

## Screen Flows Don't Support Bulk — and That's Okay

**What happens:** An admin tries to use a Screen Flow to process multiple records. The Screen Flow processes one user session at a time — it's not designed for bulk operations. The admin tries to call it from a trigger or a batch process and gets unexpected behaviour.

**When it bites you:** When someone tries to use a Screen Flow as automation logic rather than user interface.

**How to avoid it:**
- Screen Flows are for user-guided processes — one user, one session, one interaction
- For bulk processing: use Record-Triggered Flows, Scheduled Flows, or Batch Apex
- A Screen Flow invoked from a list view Quick Action runs once per selected record — it is NOT truly bulk; the user clicks through multiple times

---

## Flow Interviews Consume Governor Limits in the Calling Transaction

**What happens:** An Apex trigger calls a Flow via `Flow.Interview`. The Apex trigger processes 200 records. The Flow has 2 Get Records elements each. That's 400 Flow SOQL calls, plus the Apex trigger's own queries. Total exceeds 100 SOQL limit. Transaction fails. Data is rolled back.

**When it bites you:** Apex-invoked Flows in triggers, especially in bulk contexts.

**How to avoid it:**
- When calling Flows from Apex, design the Flow to be SOQL-minimal
- Pass data INTO the Flow as input variables (Apex queries once, passes results) rather than having the Flow query
- Or: Avoid calling Flows from Apex triggers altogether for complex logic — keep the logic in Apex where you control the query pattern

---

## A Deployed Flow Lands as Draft in Production Even When the XML Says `<status>Active</status>`

**What happens:** You test in a sandbox, `<status>Active</status>` deploys and the flow is live. You promote the identical file to production. The deploy succeeds — green, no warnings, no errors — and nothing runs. In Setup the flow shows a new version whose status is Inactive. Users report that "the automation stopped working" days later, and the deploy log gives you no reason to suspect it because nothing failed.

**When it bites you:** Every first deploy of an active flow into a production org where nobody has switched on **Deploy processes and flows as active**. The Metadata API guide states the rule directly: "You can deploy changes to an active flow if in a non-production org, such as a scratch or sandbox org. To deploy changes in a production org, you must enable the Deploy processes and flows as active preference" (api_meta.txt:68037–68040). The setting itself is `FlowSettings.enableFlowDeployAsActiveEnabled`: "When the value is `false`, all processes and flows are deployed as inactive… The default value is `false` for production orgs and is `true` for non-production orgs" (api_meta.txt:116877–116886). Sandbox and production therefore behave differently *by default*, which is why this never reproduces where you tested.

**How to avoid it:**
- Retrieve `Settings:Flow` from the target org and read `enableFlowDeployAsActiveEnabled` before you plan the release, not after the deploy.
- If it is `false`, the release plan needs a manual activation step in production with a named owner and a time.
- If you turn it on, understand the second half of the same sentence: "deploying an active process or flow in a production org causes your Apex tests to run. If Apex tests don't launch your org's required percentage of active processes and autolaunched flows, the deployment is rolled back." Turning the preference on converts a silent-inactive failure into a rolled-back deploy gated on Apex coverage of your *flows*.
- Verify every deploy with `SELECT ApiName, IsActive, IsOutOfDate FROM FlowDefinitionView` (`references/metadata-examples.md`). `IsOutOfDate = true` is the fingerprint: the version deployed but an older one is still the one running.

---

## `doesRequireRecordChangedToMeetCriteria` Is a Transition Gate, Not a "Field Changed" Gate

**What happens:** An admin sets the entry filter to `Status Equals Closed` and ticks the "only when a record is updated to meet the condition requirements" box, expecting "fire when Status changes". Someone edits the Description on a Case that was closed last week. The flow does not fire — correct. Then an integration writes `Status = Closed` onto a Case that was *already* Closed, as part of a full-record upsert. The flow does not fire either, and the admin spends an afternoon deciding whether the integration is broken.

**When it bites you:** Whenever the design says "when the field changes" but the criteria are written as "when the field equals X". The Metadata API definition is about the *criteria block as a whole*, not about any one field: "If set to `true`, conditions evaluate to `true` only if the record didn't meet the required conditions before the triggering update but now meets the conditions after the update" (api_meta.txt:72322–72325). A record already meeting the criteria is a record that did not transition, no matter which fields the update touched.

**How to avoid it:**
- Say the criteria out loud as "the record has just entered this state". If that is what you want, the flag is correct.
- If you want "this specific field changed to anything", the flag is the wrong tool — use `ISCHANGED()` in a `filterFormula` instead, which is a formula on the record and evaluates per field.
- The flag lives on `start`, alongside `filters` and `filterLogic`. There is no per-row version of it, so a multi-row criteria block gets one transition test covering all rows.
- It also exists on `FlowRule` (api_meta.txt:71320–71322), so the same semantics apply if you push the check down into a Decision element rather than the entry criteria.

---

## Workflow Field Updates Re-Fire Apex Triggers but Do Not Re-Fire Flows

**What happens:** A record-triggered flow computes a value from `Amount`. A legacy workflow rule field update overwrites `Amount` during the same save. The flow's value is now stale — computed against the pre-workflow number — and no amount of re-testing in Flow Debug reproduces it, because Debug does not run the workflow rule chain the same way. Meanwhile the Apex trigger on the same object *does* see the new value, so the flow and the trigger disagree about the same record in the same transaction.

**When it bites you:** Any object that still has a workflow rule with a field update alongside a record-triggered flow. The Apex Developer Guide's order of execution is explicit at step 11: when there are workflow field updates, the platform "Updates the record again", "Runs system validations again", and executes "before update triggers and after update triggers, regardless of the record operation (insert or update), one more time (and only one more time)" — but "Custom validation rules, flows, duplicate rules, processes built with Process Builder, and escalation rules aren't run again" (apexdev.txt:15453–15458). Triggers get a second pass. Flows do not.

**How to avoid it:**
- Inventory workflow field updates on any object before you build a flow that reads the fields they write. This is the specific reason migrating the last workflow rules off an object is worth doing before, not after, the flow work.
- If a value must reflect the post-workflow state, compute it in an after-save flow reading the committed record, or move the field-update logic into the flow itself.
- Do not reach for a second flow to "fix up" the value — it re-enters the save procedure (step 13 note: "When a process or flow executes a DML operation, the affected record goes through the save procedure", apexdev.txt:15468) and you have built a loop.

---

## A Before-Save Flow Runs Before Validation Rules and Before Duplicate Rules — So It Can Get the Save Blocked

**What happens:** A before-save flow normalises a phone number, or defaults a required picklist, or copies an account's region onto the record. A validation rule that has been quiet for two years starts firing on records nobody edited by hand. Or a duplicate rule with the block action starts rejecting API inserts. The error message names the validation or duplicate rule, so the investigation goes to that rule and not to the flow that changed the data underneath it.

**When it bites you:** Every time a before-save flow writes to a field that any validation rule or matching rule reads. The order of execution puts before-save flows at step 3, before triggers at step 4, "most system validation steps again… and any custom validation rules" at step 5, and duplicate rules at step 6 — and if a duplicate rule blocks, "the record isn't saved and no further steps, such as after triggers and workflow rules, are taken" (apexdev.txt:15440–15446). The flow's write is an input to both gates.

**How to avoid it:**
- List the validation rules and matching rules that read each field a before-save flow writes. That list is the flow's real test plan.
- The failure surfaces as `FIELD_CUSTOM_VALIDATION_EXCEPTION` on a save the user thought was innocent; when triaging one, check whether a before-save flow touched the field in the same transaction before assuming the user typed bad data.
- The same ordering is what makes before-save the right place to populate a field a validation rule *requires* — the gate runs after you, so you can satisfy it. Use it deliberately in that direction.

---

## Flow Versions Accumulate and Cannot Always Be Deleted

**What happens:** Two years of iteration leaves a flow with 40 versions. An admin tries to tidy up and finds that some versions will not delete. The error mentions paused interviews. Nobody knows which interviews, or who paused them, and the cleanup stalls.

**When it bites you:** Any flow that has a Pause element, a Wait, or a scheduled path — those create interviews that outlive the transaction. The Metadata API guide states the rule: "You can delete a flow version if it isn't active and doesn't have any paused interviews. If the flow version has paused interviews, wait for those interviews to resume and finish, or delete them" (api_meta.txt:68041–68042). Versions also survive deactivation of the flow; deactivating changes `status`, it does not remove anything.

**How to avoid it:**
- Query `FlowVersionView` before a cleanup to see exactly what exists and in what status — but remember the constraint in its own Usage note: "A query must be filtered by `DurableId` or `FlowDefinitionViewId` to get results" (object_reference.txt:145295–145296). An unfiltered query returns an empty result, not an error, which reads as "no versions" if you are not expecting it.
- Query `FlowInterview` for the paused interviews and resolve them deliberately (they are deletable with the Manage Flow permission, object_reference.txt:139869–139871) rather than waiting and hoping.
- Prune on a cadence tied to releases, so the list never reaches the size where nobody dares touch it. Depth on version policy is in `flow/flow-versioning-strategy`.

---

## `InvalidDraft` Displays as "Draft" in Setup, So a Broken Flow Looks Merely Unfinished

**What happens:** A field the flow references is deleted, or a referenced Apex action is removed, or a dependent object is retired. The flow's status becomes `InvalidDraft`. In Setup that status renders as **Draft** — the same word the UI shows for an ordinary work-in-progress version. An admin scanning the flow list sees "Draft" next to a flow they believe is live and moves on. The automation has been dead since the dependency went away.

**When it bites you:** After any metadata deletion that a flow depended on, and after installing or uninstalling a package. The `FlowVersionStatus` enum distinguishes five states — `Active`, `Draft` ("In the UI, this status appears as Inactive"), `Obsolete` ("In the UI, this status appears as Inactive"), `InvalidDraft` ("In the UI, this status appears as Draft"), and `UnderReview` (api_meta.txt:68416–68423) — but the UI collapses them into two words. UNVERIFIED (2026-09-04): the Metadata API guide defines the `InvalidDraft` status and its UI rendering but does not enumerate what causes a version to become invalid; the deleted-field and removed-action causes above are the common ones in practice, not a documented list.

**How to avoid it:**
- Query the metadata status, never read it off the Setup list: `SELECT ApiName, Status FROM FlowVersionView WHERE FlowDefinitionViewId = '…'` returns the real value.
- Add that query to the field-deletion checklist. `admin/analyze-field-impact` and the `/analyze-field-impact` agent exist for the blast-radius question; the flow-status check is the confirmation afterwards.
- On a deploy, an `InvalidDraft` version in the source is a file that will not activate. Catch it in the source with `scripts/check_flow_metadata.py` rather than in the org.
