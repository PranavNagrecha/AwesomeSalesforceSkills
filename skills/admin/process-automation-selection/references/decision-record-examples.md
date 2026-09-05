# Process Automation Selection — Decision Record Examples

This is this skill's metadata-examples file. The artifact this skill produces is not a
metadata type — it is a **decision record** plus the skeleton the decision hands off to.
The record is what makes a tool choice re-openable eighteen months later; the skeleton is
what stops the build from freestyling once the choice is made.

---

## The Record Shape

Store one record per requirement, as YAML front matter in a markdown file so it is both
greppable and readable. Every field below is required — the checker script rejects a record
that omits one.

```yaml
---
record_id: ADR-AUTO-0007
requirement: >
  When an Opportunity is set to Closed Won, create one Onboarding__c record per
  Opportunity Product and stamp the Account's Onboarding_Status__c.
trigger: record_change            # record_change | user_action | clock | inbound_call | event
volume:
  per_transaction: 200            # records in the largest single save (bulk load / API batch)
  per_day: 50000                  # peak, measured — not the sandbox number
cross_object: true                # does it write anything other than the triggering record?
timing: after_save                # before_save | after_save | scheduled | screen | async | n/a
chosen_mechanism: apex_trigger_handler
tree_steps_cited:
  - "automation-selection.md Q1 — a record change, so route to Q2"
  - "automation-selection.md Q2 — writes related records, so not before-save"
  - "automation-selection.md Q3 — needs savepoint rollback across two objects"
rejected:
  - alternative: after_save_flow
    reason: >
      Q3 asks for rollback on a specific error class; a fault path cannot roll back the
      Onboarding__c inserts already committed earlier in the same interview.
  - alternative: flow_plus_invocable
    reason: >
      Q6 keeps orchestration in Flow only when it is simple; this one branches on product
      family, contract term and territory before the first DML.
owner: rev-ops-platform-team
review_date: 2027-03-01
---
```

### How to read it

- **`tree_steps_cited` is the load-bearing field.** Each entry must name a real question in
  `standards/decision-trees/automation-selection.md` (or `flow-pattern-selector.md` /
  `async-selection.md`) in the form `automation-selection.md Q3`. A record whose reasoning
  cannot be traced to a numbered step is an opinion wearing a template.
- **`rejected` must carry reasons, not names.** The alternative that was not chosen is the
  half of the record a future reader actually needs; a bare list of names tells them nothing.
- **`volume.per_transaction` is the number the governor limits are spent against**, and
  `volume.per_day` is the number that decides scheduled Flow vs Batch Apex
  (`automation-selection.md` Q10). Record both; they answer different questions.
- **`timing` is a position in the save procedure**, not a preference — see `references/gotchas.md`
  gotcha 1 for the step numbers.
- **`review_date` is not decoration.** Volume changes and a correct decision expires; the
  date is when someone re-runs the tree with the current numbers.
- **`chosen_mechanism` names the skeleton**, which is what step 5 of the Recommended Workflow
  scaffolds from.

---

## Worked Decision 1 — Same-Record Field Default → Before-Save Flow

**Requirement:** Every Lead created without a `LeadSource` gets `Web`, and `Company` is
trimmed of leading and trailing whitespace before it is saved.

```yaml
---
record_id: ADR-AUTO-0001
requirement: >
  Default Lead.LeadSource to 'Web' when blank on create, and trim Lead.Company.
trigger: record_change
volume:
  per_transaction: 200
  per_day: 12000
cross_object: false
timing: before_save
chosen_mechanism: before_save_record_triggered_flow
tree_steps_cited:
  - "automation-selection.md Q1 — a record change, route to Q2"
  - "automation-selection.md Q2 — under ~10s and touches only fields on the record itself, so before-save record-triggered Flow"
  - "flow-pattern-selector.md Q3 — no DML, no Action, no email beyond the triggering record, so before-save is confirmed rather than assumed"
rejected:
  - alternative: apex_before_insert_trigger
    reason: >
      automation-selection.md 'Do NOT graduate to Apex because' — none of the Q3
      conditions apply, and a trigger buys nothing here that an admin cannot maintain.
  - alternative: after_save_record_triggered_flow
    reason: >
      An after-save flow would issue a second save for work the first save already pays
      for, and after-trigger records are read-only (references/gotchas.md gotcha 9).
  - alternative: workflow_rule_field_update
    reason: >
      End of support 31 Dec 2025 per automation-selection.md Strategic defaults, and a
      workflow field update re-fires update triggers one extra time (gotcha 5).
owner: marketing-ops
review_date: 2027-09-04
---
```

**Skeleton it hands off to:** `templates/flow/RecordTriggered_Skeleton.flow-meta.xml`.
Change `<object>` to `Lead`, keep `<triggerType>RecordBeforeSave</triggerType>`, and set
`<recordTriggerType>` to `Create`. The valid `recordTriggerType` values are `Create`,
`CreateAndUpdate`, `Delete`, `None` and `Update`, and the field is available only when
`triggerType` is `RecordBeforeSave` or `DataCloudDataChange` (Metadata API Developer Guide,
`FlowStart`, api_meta.txt L72448–L72460).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <label>Lead Before Save Defaults</label>
    <processType>AutoLaunchedFlow</processType>
    <status>Active</status>
    <start>
        <object>Lead</object>
        <recordTriggerType>Create</recordTriggerType>
        <triggerType>RecordBeforeSave</triggerType>
    </start>
</Flow>
```

---

## Worked Decision 2 — After-Insert Cross-Object Create at 50k/day → Apex Trigger Handler

**Requirement:** Every Closed Won Opportunity creates one `Onboarding__c` per Opportunity
Product, inside the same transaction, with a rollback if any child insert fails. Peak load is
a nightly integration batch of 50,000 Opportunities per day, 200 per API call.

```yaml
---
record_id: ADR-AUTO-0007
requirement: >
  On Opportunity close, create one Onboarding__c per Opportunity Product and roll the
  whole set back if any child insert fails.
trigger: record_change
volume:
  per_transaction: 200
  per_day: 50000
cross_object: true
timing: after_save
chosen_mechanism: apex_trigger_handler
tree_steps_cited:
  - "automation-selection.md Q1 — a record change, route to Q2"
  - "automation-selection.md Q2 — no, it writes related records"
  - "automation-selection.md Q3 — yes: complex exception handling with rollback (savepoints), so Apex (trigger + handler + service layer)"
rejected:
  - alternative: after_save_record_triggered_flow
    reason: >
      Q3's rollback condition is met. A Flow fault path routes the interview to an error
      handler; it does not undo DML already performed earlier in the same interview.
  - alternative: flow_plus_invocable
    reason: >
      Q6 applies only when the orchestration is still simple. Branching on product family,
      contract term and territory before the first DML is not that.
  - alternative: queueable_from_flow
    reason: >
      async-selection.md Q1 — 200 records and well under 60s, so nothing here needs to
      leave the synchronous transaction; deferring it would only lose the rollback.
owner: rev-ops-platform-team
review_date: 2027-03-01
---
```

**Skeleton it hands off to:** `templates/apex/TriggerHandler.cls`, subclassed. Ten lines of
the canonical base, showing the entry point and the recursion guard the handler inherits:

```apex
// excerpt — full class: templates/apex/TriggerHandler.cls
public virtual class TriggerHandler {
    @TestVisible private static Map<String, Integer> depthByHandler = new Map<String, Integer>();
    @TestVisible private static Set<String> skipOnceHandlers = new Set<String>();
    private static final Integer MAX_DEPTH = 10;

    public void run() {
        if (!Trigger.isExecuting && !Test.isRunningTest()) { return; }
        String handlerName = String.valueOf(this).split(':')[0];
        String sObjectName = inferSObjectName();
        if (!TriggerControl.isActive(sObjectName, handlerName)) { return; }
```

The handler's own recursion guard (`MAX_DEPTH = 10`) sits below the platform's own ceiling:
total stack depth for any Apex invocation that recursively fires triggers via insert, update
or delete is **16**, synchronous and asynchronous alike (Salesforce Developer Limits and
Allocations Quick Reference, salesforce_app_limits_cheatsheet.txt L69).

---

## Worked Decision 3 — Nightly Reconciliation → Scheduled Flow vs Batch Apex

**Requirement:** Every night, find Accounts whose `Last_Sync__c` is older than 24 hours and
re-stamp a status field. Two candidate populations were measured: 8,000 rows in the
low-volume org, 900,000 rows in the enterprise org.

```yaml
---
record_id: ADR-AUTO-0014
requirement: >
  Nightly reconciliation of Account.Sync_Status__c against Last_Sync__c.
trigger: clock
volume:
  per_transaction: 200
  per_day: 900000
cross_object: false
timing: scheduled
chosen_mechanism: batch_apex
tree_steps_cited:
  - "automation-selection.md Q1 — a scheduled clock, route to Q10"
  - "automation-selection.md Q10 — > 50k records per run, so Batch Apex"
  - "flow-pattern-selector.md Q6 — the ~50k line is this repo's routing opinion and must stay in step with automation-selection.md Q10; 900k is far above it"
  - "async-selection.md Q1 — > 50k OR > 5 min routes to Q8 (Batch Apex)"
  - "async-selection.md Q8 — light per-record work, no callouts, so scope=200 (the default)"
rejected:
  - alternative: schedule_triggered_flow
    reason: >
      A schedule-triggered flow starts one interview per record returned by its query
      (Metadata API FlowStart.object, api_meta.txt L72425-L72426), so 900k rows means 900k
      interviews in one nightly window — see the interview-allocation note below.
  - alternative: queueable_chain
    reason: >
      async-selection.md Q1 puts 2k-50k in Queueable territory; 900k is an order of
      magnitude past it and gives up Batch's QueryLocator and Bulk API monitoring.
owner: integrations-team
review_date: 2027-01-15
---
```

**The same requirement in the 8,000-row org flips the answer.** At `per_day: 8000`,
`automation-selection.md` Q10 resolves to schedule-triggered Flow, and `chosen_mechanism`
becomes `schedule_triggered_flow`. That is the point of recording volume as a number: the
requirement did not change, the org did, and the record shows exactly which line was crossed.

The scheduled-Flow half of that choice rests on three grounded metadata facts:

| Fact | Where it comes from |
|---|---|
| A flow interview starts for each record that meets the `FlowStart` filter conditions | Metadata API Developer Guide, `FlowStart.object` (api_meta.txt L72425–L72426) |
| `FlowSchedule.frequency` valid values for a non-segment scheduled flow are `Once`, `Daily`, `Weekly` (`OnActivate`, `Hourly`, `Monthly`, `Weekdays`, `Yearly` are segment-triggered flows only) | Metadata API Developer Guide, `FlowSchedule` (api_meta.txt L71352–L71366) |
| `FlowScheduledPath.maxBatchSize` is the maximum scheduled-path interviews executed in a single batch, from 1 to 200, default 200 | Metadata API Developer Guide, `FlowScheduledPath` (api_meta.txt L71397–L71399) |

UNVERIFIED (2026-09-04): the org-wide cap of 250,000 schedule-triggered flow interviews per
24 hours (or user licenses × 200, whichever is greater) does not appear in the extracted
Metadata API, Apex Developer, Object Reference or App Limits Cheat Sheet text. It is sourced
in `standards/decision-trees/flow-pattern-selector.md` to Salesforce Help
`platform.flow_considerations_trigger_schedule`, which cannot be fetched here. Cite the tree,
not a remembered number, and confirm against the current Help page before quoting it to a
customer.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <label>Nightly Account Sync Reconciliation</label>
    <processType>AutoLaunchedFlow</processType>
    <status>Active</status>
    <start>
        <object>Account</object>
        <schedule>
            <frequency>Daily</frequency>
            <startDate>2026-09-05</startDate>
            <startTime>02:00:00.000Z</startTime>
        </schedule>
        <triggerType>Scheduled</triggerType>
    </start>
</Flow>
```

`schedule` is required when `triggerType` is `Scheduled` (Metadata API Developer Guide,
`FlowStart.schedule`, api_meta.txt L72462–L72463); `startTime` is the time of day the flow
runs, based on the org's default time zone (`FlowSchedule.startTime`, api_meta.txt L71378–L71379).

---

## One Object, One Order — The Automation Inventory

Run this before proposing anything new. The point is not the count; it is that a rule already
living on the object is a rejected alternative you have not written down yet.

| Surface | How to list it | Object filter field |
|---|---|---|
| Record-triggered and scheduled flows | SOQL on `FlowDefinitionView` (`describeSObjects()`, `query()`; API 46.0+) | `TriggerObjectOrEventLabel` (API 53.0+) |
| Apex triggers | SOQL on `ApexTrigger` (`query()` supported) | `TableEnumOrId` |
| Workflow Rules | Metadata API retrieve of `Workflow` — see the note below | n/a (per-object file) |

```sql
-- Every flow attached to Account, with the fields that decide ownership and order.
SELECT ApiName, Label, ProcessType, TriggerType, RecordTriggerType,
       TriggerOrder, IsActive, IsOutOfDate, TriggerObjectOrEventLabel,
       NamespacePrefix, ManageableState
FROM   FlowDefinitionView
WHERE  TriggerObjectOrEventLabel = 'Account'
ORDER  BY TriggerType, TriggerOrder NULLS LAST
```

```sql
-- Every trigger on Account, with which contexts it claims.
SELECT Name, Status, ApiVersion, TableEnumOrId, NamespacePrefix,
       UsageBeforeInsert, UsageBeforeUpdate, UsageBeforeDelete,
       UsageAfterInsert,  UsageAfterUpdate,  UsageAfterDelete, UsageAfterUndelete
FROM   ApexTrigger
WHERE  TableEnumOrId = 'Account'
ORDER  BY Name
```

Field grounding, all from the Object Reference (object_reference.txt):

| Field | Meaning | Line |
|---|---|---|
| `FlowDefinitionView.IsActive` | Whether the latest version of the flow definition is the active version (API 47.0+) | L139397–L139403 |
| `FlowDefinitionView.IsOutOfDate` | Whether the active version is the latest version — a `true` here means someone edited and did not activate | L139405–L139411 |
| `FlowDefinitionView.ProcessType` | Restricted picklist of flow type; `AutoLaunchedFlow` is the record-triggered/scheduled value | L139544–L139549 |
| `FlowDefinitionView.TriggerType` | Restricted picklist including `RecordBeforeSave` (API 48.0+), `RecordAfterSave` (49.0+), `RecordBeforeDelete` (50.0+), `PlatformEvent` (49.0+) | L139772–L139828 |
| `FlowDefinitionView.RecordTriggerType` | `Create`, `CreateAndUpdate`, `Delete`, `None`, `Update`; available only when `triggerType` is `RecordBeforeSave` (API 54.0+) | L139689–L139703 |
| `FlowDefinitionView.TriggerOrder` | Run order of a record-triggered flow, from 1 to 2,000 (API 54.0+) | L139763–L139770 |
| `FlowDefinitionView.TriggerObjectOrEventLabel` | Label of the object or platform event that triggers the flow (API 53.0+) | L139755–L139761 |
| `ApexTrigger.TableEnumOrId` | The object associated with the trigger, such as Account or Contact | L33036–L33044 |
| `ApexTrigger.Status` | `Active`, `Inactive`, `Deleted` — an `Inactive` trigger is still deployed metadata | L33022–L33034 |
| `ApexTrigger.UsageBeforeInsert` … `UsageAfterUndelete` | Which trigger contexts the trigger declares | L33055–L33103 |

UNVERIFIED (2026-09-04): `FlowDefinitionView` has no field in the Object Reference that
reports which *version* of a flow is deployed alongside a given trigger, and no field that
records whether two flows on the same object have been ordered relative to each other beyond
`TriggerOrder` itself. The Object Reference states the `TriggerOrder` range and availability;
it does not state what the platform does when two record-triggered flows on the same object
and timing both leave `TriggerOrder` null. Treat unset `TriggerOrder` as unordered and set it
explicitly rather than inferring a default.

**Workflow Rules are not queryable this way.** `WorkflowRule` is a Metadata API type, not a
standard object with `query()` support, so retrieve it instead:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Account</members>
        <members>Opportunity</members>
        <name>Workflow</name>
    </types>
    <types>
        <members>*</members>
        <name>Flow</name>
    </types>
    <types>
        <members>*</members>
        <name>ApexTrigger</name>
    </types>
    <version>62.0</version>
</Package>
```

```bash
# Retrieve the inventory into a scratch directory (never into the project source dir).
sf project retrieve start --manifest package.xml --target-org <alias> --output-dir ./automation-inventory

# Audit what came back: legacy files, workflow-processType flows, Flow+trigger overlap.
python3 scripts/check_process_automation_selection.py --manifest-dir ./automation-inventory

# Lint the decision record you wrote from it.
python3 scripts/check_process_automation_selection.py --decision-record docs/adr/ADR-AUTO-0007.md
```

Once the decision is made and a skeleton is chosen, deploy only the skeleton:

```bash
sf project deploy start --source-dir force-app/main/default/flows/Lead_Before_Save_Defaults.flow-meta.xml \
  --target-org <alias> --test-level RunLocalTests
```

### Verification step

After deploying, confirm the object's automation is in the order the record claims:

```sql
SELECT ApiName, TriggerType, TriggerOrder, IsActive
FROM   FlowDefinitionView
WHERE  TriggerObjectOrEventLabel = 'Lead' AND IsActive = true
ORDER  BY TriggerType, TriggerOrder NULLS LAST
```

Every active row must appear in the decision record's inventory table, and no row may have a
null `TriggerOrder` where a sibling row on the same `TriggerType` has one. In Setup, the same
check is **Setup → Process Automation → Flow Trigger Explorer**, filtered to the object.

---

## Hand-Off

| Decision lands on | Hand the record to |
|---|---|
| Before-save or after-save record-triggered Flow | `skills/flow/record-triggered-flow-patterns` |
| Schedule-triggered Flow | `skills/flow/scheduled-flows` |
| Apex trigger + handler | `skills/apex/trigger-framework` |
| Batch Apex | `skills/apex/batch-apex-patterns` |
| A legacy Workflow Rule or Process Builder that now has to be converted | `skills/flow/process-builder-to-flow-migration`, or the `agents/automation-migration-router/AGENT.md` run-time agent for an inventory + parallel-run + rollback plan on one object |
| Ownership routing on create rather than a tool boundary | `skills/admin/assignment-rules`, `references/routing-selector.md` |
| A human approval chain | `skills/admin/approval-processes` |
