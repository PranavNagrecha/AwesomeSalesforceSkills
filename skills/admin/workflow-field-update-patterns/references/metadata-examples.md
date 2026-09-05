# Metadata Examples — Workflow Field Update Patterns

The migration this skill owns is a **two-component swap**: a `Workflow` component loses a field
update, and a `Flow` component gains the equivalent write. Both sides are shown here as deployable
XML so the diff between "what the org does today" and "what the org will do after cutover" is
readable before anything is deployed.

## Where the metadata lives

| Component | Metadata API location | Salesforce CLI (DX) path |
|---|---|---|
| `Workflow` | "Workflow files have the suffix `.workflow`. There's one file per standard or custom object that has workflow. These files are stored in the `workflows` directory of the corresponding package." (api_meta.txt:139896–139898) | `force-app/main/default/workflows/<Object>.workflow-meta.xml` |
| `Flow` | Stored in the flow directory of the package; the DX form appends `-meta.xml` | `force-app/main/default/flows/<FlowApiName>.flow-meta.xml` |

One `.workflow-meta.xml` file per object holds **every** workflow component for that object —
`alerts`, `fieldUpdates`, `flowActions`, `knowledgePublishes`, `outboundMessages`, `rules`, `tasks`
(api_meta.txt:139905–139943). A field update is therefore never a standalone file: retrieving one
retrieves the object's whole workflow surface, and deploying the file replaces that whole surface.
This is the single biggest practical difference from Flow, where one automation is one file.

## `WorkflowFieldUpdate` — the fields that decide what the update does

Source: Metadata API Developer Guide, *WorkflowFieldUpdate*, api_meta.txt:140118–140245.

| Element | Required | What it does |
|---|---|---|
| `field` | yes | "The field on the object for the workflow to be updated." |
| `name` | yes | Label. `fullName` is the API name. |
| `notifyAssignee` | yes | "Notify the assignee when the field is updated." |
| `operation` | yes | `Formula` \| `Literal` \| `LookupValue` \| `NextValue` \| `Null` \| `PreviousValue` |
| `formula` | when `operation` = `Formula` | "the formula used to compute the new field value" |
| `literalValue` | when `operation` = `Literal` | "the literal value for the field" |
| `lookupValue` | when `operation` = `LookupValue` | the referenced record. "Only User is supported in the current API" (api_meta.txt:140172) |
| `lookupValueType` | with `lookupValue` | `Queue` \| `RecordType` \| `User` |
| `protected` | yes | Managed-package protection flag |
| `reevaluateOnChange` | no | Re-evaluates **all** workflow rules on the object if the value changed; the cascade "can happen up to 5 times after the initial field update that started it" (api_meta.txt:140192–140194) |
| `targetObject` | no | "Object set if the change is detected on a child record… the object points to the foreign key reference on the child object that points to the parent" — this is the cross-object field update |

`NextValue` and `PreviousValue` are "Only allowed when the field update references a picklist"
(api_meta.txt:140175, 140178).

---

## Example 1 — the legacy `Workflow` file being retired

One active rule with two field updates: a `Formula` update that stamps an audit note, and a
`Literal` update that sets a picklist and asks the platform to re-evaluate afterwards. This is the
shape you will actually retrieve out of a long-lived org.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Workflow xmlns="http://soap.sforce.com/2006/04/metadata">
    <fieldUpdates>
        <fullName>Stamp_Review_Note</fullName>
        <description>Audit breadcrumb written when a high-value Opportunity first qualifies.</description>
        <field>Review_Note__c</field>
        <formula>&quot;Flagged high-value at &quot; &amp; TEXT(TODAY()) &amp; &quot; by &quot; &amp; $User.Username</formula>
        <name>Stamp Review Note</name>
        <notifyAssignee>false</notifyAssignee>
        <operation>Formula</operation>
        <protected>false</protected>
        <reevaluateOnChange>false</reevaluateOnChange>
    </fieldUpdates>
    <fieldUpdates>
        <fullName>Set_Review_Priority_High</fullName>
        <description>Sets Review_Priority__c so the routing rule below can pick the record up.</description>
        <field>Review_Priority__c</field>
        <literalValue>High</literalValue>
        <name>Set Review Priority High</name>
        <notifyAssignee>false</notifyAssignee>
        <operation>Literal</operation>
        <protected>false</protected>
        <reevaluateOnChange>true</reevaluateOnChange>
    </fieldUpdates>
    <rules>
        <fullName>High_Value_Opportunity_Review</fullName>
        <actions>
            <name>Stamp_Review_Note</name>
            <type>FieldUpdate</type>
        </actions>
        <actions>
            <name>Set_Review_Priority_High</name>
            <type>FieldUpdate</type>
        </actions>
        <active>true</active>
        <criteriaItems>
            <field>Opportunity.Amount</field>
            <operation>greaterThan</operation>
            <value>100000</value>
        </criteriaItems>
        <criteriaItems>
            <field>Opportunity.StageName</field>
            <operation>notEqual</operation>
            <value>Closed Lost</value>
        </criteriaItems>
        <description>Flags high-value Opportunities for deal-desk review.</description>
        <triggerType>onCreateOrTriggeringUpdate</triggerType>
    </rules>
</Workflow>
```

How to read it:

- **`fieldUpdates` and `rules` are siblings, not nested.** A rule points at an update by name through
  `actions/name` + `actions/type` = `FieldUpdate` (`WorkflowActionReference`, api_meta.txt:140060–140080).
  Deleting a `fieldUpdates` block without removing the matching `actions` reference makes the file
  undeployable — this is the most common hand-edit failure on this component.
- **`formula` content is XML-escaped, not CDATA.** `"` becomes `&quot;` and `&` becomes `&amp;`, exactly
  as in the guide's own sample (`Name &amp; &quot;Updated&quot;`, api_meta.txt:140598). A retrieved file
  round-trips this correctly; a hand-typed one usually does not.
- **`reevaluateOnChange` on the `Literal` update is the live wire.** "if the field update changes the
  field's value, all workflow rules on the associated object are reevaluated… This cascade of workflow
  rule reevaluation and triggering can happen up to 5 times after the initial field update that started
  it" (api_meta.txt:140186–140194). Flow has no equivalent switch, so this element has to be read before
  migrating — see Example 2's mapping note and `references/gotchas.md` § 11.
- **`triggerType` is `onCreateOrTriggeringUpdate`**, one of `onAllChanges` / `onCreateOnly` /
  `onCreateOrTriggeringUpdate` (api_meta.txt:140420–140432). It maps to a *pair* of Flow settings, not
  to one.
- **No `<active>` element on the file itself.** `active` lives on each rule. Deactivating "the workflow"
  means flipping `rules/active` to `false` and deploying the whole file.

---

## Example 2 — the before-save Flow that replaces it

Same-record writes only, so this is `RecordBeforeSave` and the writes are **Assignments to `$Record`**,
not `recordUpdates` elements. `flow-pattern-selector.md` Q2 → Q3 ("only set fields on the SAME record"
→ "nothing beyond field assignment") lands here.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>62.0</apiVersion>
    <assignments>
        <name>Stamp_Review_Fields</name>
        <label>Stamp Review Fields</label>
        <locationX>176</locationX>
        <locationY>287</locationY>
        <assignmentItems>
            <assignToReference>$Record.Review_Priority__c</assignToReference>
            <operator>Assign</operator>
            <value>
                <stringValue>High</stringValue>
            </value>
        </assignmentItems>
        <assignmentItems>
            <assignToReference>$Record.Review_Note__c</assignToReference>
            <operator>Assign</operator>
            <value>
                <elementReference>Review_Note_Text</elementReference>
            </value>
        </assignmentItems>
    </assignments>
    <description>Replaces Workflow rule High_Value_Opportunity_Review and its two field updates. Same-record writes only — do not add a Create/Update Records element here.</description>
    <environments>Default</environments>
    <formulas>
        <name>Review_Note_Text</name>
        <dataType>String</dataType>
        <expression>"Flagged high-value at " &amp; TEXT(TODAY()) &amp; " by " &amp; {!$User.Username}</expression>
    </formulas>
    <interviewLabel>High Value Opportunity Review {!$Flow.CurrentDateTime}</interviewLabel>
    <label>High Value Opportunity Review</label>
    <processType>AutoLaunchedFlow</processType>
    <runInMode>DefaultMode</runInMode>
    <start>
        <locationX>50</locationX>
        <locationY>0</locationY>
        <connector>
            <targetReference>Stamp_Review_Fields</targetReference>
        </connector>
        <doesRequireRecordChangedToMeetCriteria>true</doesRequireRecordChangedToMeetCriteria>
        <filterLogic>and</filterLogic>
        <filters>
            <field>Amount</field>
            <operator>GreaterThan</operator>
            <value>
                <numberValue>100000.0</numberValue>
            </value>
        </filters>
        <filters>
            <field>StageName</field>
            <operator>NotEqualTo</operator>
            <value>
                <stringValue>Closed Lost</stringValue>
            </value>
        </filters>
        <object>Opportunity</object>
        <recordTriggerType>CreateAndUpdate</recordTriggerType>
        <triggerType>RecordBeforeSave</triggerType>
    </start>
    <status>Active</status>
</Flow>
```

**The mapping, element by element.** Every row is a decision the migration has to make explicitly;
the Migrate to Flow tool makes them for you, and this table is how you check its work.

| Workflow element | Flow element | Why |
|---|---|---|
| `rules/criteriaItems` (+ `booleanFilter`) | `start/filters` (+ `start/filterLogic`) | Same gate, evaluated before an interview starts. `criteriaItems/field` is qualified (`Opportunity.Amount`); `filters/field` is not (`Amount`) |
| `rules/formula` | `start/filterFormula` | Use when the rule used a formula condition instead of criteria items |
| `triggerType` `onCreateOrTriggeringUpdate` | `recordTriggerType` `CreateAndUpdate` **plus** `doesRequireRecordChangedToMeetCriteria` `true` | The Flow flag means "conditions evaluate to true only if the record didn't meet the required conditions before the triggering update but now meets the conditions after the update" (api_meta.txt:72322–72326) — that *is* the definition of a triggering update |
| `triggerType` `onCreateOnly` | `recordTriggerType` `Create` | — |
| `triggerType` `onAllChanges` | `recordTriggerType` `CreateAndUpdate` **plus** `doesRequireRecordChangedToMeetCriteria` `false` | Dropping the flag is what makes it fire on every qualifying save, matching the workflow semantics |
| `fieldUpdates` `operation` `Literal` | `assignmentItems` with a `stringValue` / `numberValue` / `booleanValue` | — |
| `fieldUpdates` `operation` `Formula` | `formulas` resource + `assignmentItems` `elementReference` | Flow formula syntax differs: field merges are `{!$Record.Field__c}`, and the escaping rules of the `.workflow` file do not apply |
| `fieldUpdates` `operation` `Null` | `assignmentItems` with `<value><stringValue></stringValue></value>` or the Assign operator against an empty variable | No dedicated "set to null" operator exists |
| `fieldUpdates` `operation` `NextValue` / `PreviousValue` | *no equivalent* — a Decision with one outcome per adjacent picklist pair | See `references/gotchas.md` § 12 |
| `fieldUpdates` `reevaluateOnChange` `true` | *no equivalent switch* | See `references/gotchas.md` § 11 |
| `fieldUpdates` `targetObject` | after-save Flow with a `recordUpdates` element (Example 3) | A cross-object field update cannot be before-save |
| `workflowTimeTriggers` | `start/scheduledPaths` on an **after-save** Flow | Before-save Flows have no scheduled paths; see `flow/flow-time-based-patterns` |

Reading the Flow side:

- `processType` is `AutoLaunchedFlow`. There is no "record-triggered" process type; `start/triggerType`
  is what makes it record-triggered (`RecordBeforeSave` = "Creating and/or updating a record triggers an
  autolaunched flow to make more updates to that record before it's saved to the database",
  api_meta.txt:72539–72542).
- The write is an **Assignment**, because in a before-save Flow the triggering record is still in memory.
  There is no DML and therefore no `recordUpdates` element in this file — and there must not be one.
- `status` is `Active` here for illustration. Deploy the replacement as `Draft` first if you intend to
  activate it manually after the parity test; "Any flow without a `status` value is deployed or retrieved
  with a `status` value of `Draft`" (api_meta.txt:73187–73188).

---

## Example 3 — the after-save variant, for a `targetObject` (cross-object) field update

When the legacy field update carried `targetObject` — "Object set if the change is detected on a child
record. If set, the object points to the foreign key reference on the child object that points to the
parent" (api_meta.txt:140237–140245) — the write lands on a *different* record. Before-save cannot do
that. This is `RecordAfterSave` with a real `recordUpdates` element and a fault path.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>62.0</apiVersion>
    <description>Replaces the cross-object field update on OpportunityLineItem that stamped the parent Opportunity.</description>
    <environments>Default</environments>
    <interviewLabel>Line Item Rolls Up To Opportunity {!$Flow.CurrentDateTime}</interviewLabel>
    <label>Line Item Rolls Up To Opportunity</label>
    <processType>AutoLaunchedFlow</processType>
    <recordUpdates>
        <name>Stamp_Parent_Opportunity</name>
        <label>Stamp Parent Opportunity</label>
        <locationX>176</locationX>
        <locationY>287</locationY>
        <faultConnector>
            <targetReference>Capture_Fault</targetReference>
        </faultConnector>
        <filterLogic>and</filterLogic>
        <filters>
            <field>Id</field>
            <operator>EqualTo</operator>
            <value>
                <elementReference>$Record.OpportunityId</elementReference>
            </value>
        </filters>
        <inputAssignments>
            <field>Review_Priority__c</field>
            <value>
                <stringValue>High</stringValue>
            </value>
        </inputAssignments>
        <object>Opportunity</object>
    </recordUpdates>
    <assignments>
        <name>Capture_Fault</name>
        <label>Capture Fault</label>
        <locationX>440</locationX>
        <locationY>287</locationY>
        <assignmentItems>
            <assignToReference>faultDetail</assignToReference>
            <operator>Assign</operator>
            <value>
                <elementReference>$Flow.FaultMessage</elementReference>
            </value>
        </assignmentItems>
    </assignments>
    <runInMode>DefaultMode</runInMode>
    <start>
        <locationX>50</locationX>
        <locationY>0</locationY>
        <connector>
            <targetReference>Stamp_Parent_Opportunity</targetReference>
        </connector>
        <doesRequireRecordChangedToMeetCriteria>true</doesRequireRecordChangedToMeetCriteria>
        <filterLogic>and</filterLogic>
        <filters>
            <field>TotalPrice</field>
            <operator>GreaterThan</operator>
            <value>
                <numberValue>100000.0</numberValue>
            </value>
        </filters>
        <object>OpportunityLineItem</object>
        <recordTriggerType>CreateAndUpdate</recordTriggerType>
        <triggerType>RecordAfterSave</triggerType>
    </start>
    <status>Active</status>
    <variables>
        <name>faultDetail</name>
        <dataType>String</dataType>
        <isCollection>false</isCollection>
        <isInput>false</isInput>
        <isOutput>false</isOutput>
    </variables>
</Flow>
```

How to read it:

- `recordUpdates` is `FlowRecordUpdate`: `object` (required), `filters` to select the record,
  `inputAssignments` to set field values, `faultConnector` for the DML error path
  (api_meta.txt:71264–71296). The cross-object write costs a DML statement; the before-save
  Assignment in Example 2 does not.
- **This variant re-enters the save procedure.** The parent Opportunity update goes through the whole
  order of execution again, and during that recursive save "Salesforce skips steps 9 (assignment rules)
  through 17 (roll-up summary field in the grandparent record)" (apexdev.txt:15414–15415). Automation on
  Opportunity that lives in that range will not run. `admin/process-automation-selection` § 6 owns this
  behaviour in full.
- `automation-selection.md` Q4 ("Does the logic need to cross objects?" → Yes) → Q5 ("linear with 1–2
  decisions?" → Yes) is the branch that authorises after-save Flow here rather than Apex.

---

## Example 4 — the Apex variant, for the cases the tree routes to code

`automation-selection.md` Q3 sends a field update to Apex when it needs a callout with retry, a
savepoint rollback, recursive DML on the same object, or logic Flow cannot express. The write itself
is a plain assignment in `beforeUpdate()`; the handler is the canonical one.

```apex
// Excerpt — subclass of templates/apex/TriggerHandler.cls. Not a complete file:
// TriggerHandler.run() and TriggerControl.isActive() live in the template.
public class OpportunityTriggerHandler extends TriggerHandler {

    protected override void beforeUpdate() {
        for (Opportunity opp : (List<Opportunity>) Trigger.new) {
            Opportunity prior = (Opportunity) Trigger.oldMap.get(opp.Id);
            Boolean nowQualifies = opp.Amount > 100000 && opp.StageName != 'Closed Lost';
            Boolean didQualify   = prior.Amount > 100000 && prior.StageName != 'Closed Lost';
            if (nowQualifies && !didQualify) {          // == doesRequireRecordChangedToMeetCriteria
                opp.Review_Priority__c = 'High';        // == a Literal field update
            }
        }
    }
}
```

```apex
trigger OpportunityTrigger on Opportunity (before update) {
    new OpportunityTriggerHandler().run();
}
```

How to read it:

- `beforeUpdate()` is one of the seven virtual methods the template dispatches to
  (`templates/apex/TriggerHandler.cls`). The template already carries a per-handler depth counter and a
  `skipOnce()` hook, so no ad-hoc `static Boolean hasRun` is needed.
- Assigning to `Trigger.new` in a **before** context is the write. No DML, no recursion — the same
  economics as the before-save Flow, which is why Apex is only justified by the Q3 conditions and not by
  the field update itself.
- Some fields cannot be written here at all. "Some field values are set during the system save operation,
  which occurs after before triggers have fired. As a result, these fields cannot be modified or
  accurately detected in before insert or before update triggers" — the list includes `Opportunity.Amount`
  (unless the Opportunity has no line items), `Opportunity.ForecastCategory`, `Opportunity.IsWon`,
  `Opportunity.IsClosed`, `Case.IsClosed`, `Task.IsClosed`, `Contract.ActivatedDate`, `Id` and
  `CreatedDate` (apexdev.txt:15593–15612). A workflow field update at step 11 *can* set some of these
  because it runs after the save — see `references/gotchas.md` § 13.

---

## `package.xml`

`Workflow` retrieves per object; `Flow` retrieves per flow API name.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Opportunity</members>
        <members>OpportunityLineItem</members>
        <name>Workflow</name>
    </types>
    <types>
        <members>High_Value_Opportunity_Review</members>
        <members>Line_Item_Rolls_Up_To_Opportunity</members>
        <name>Flow</name>
    </types>
    <version>62.0</version>
</Package>
```

The guide's own inventory manifest for this component is the wildcard form — "When using a manifest
file, retrieve all workflow components using this code" (api_meta.txt:139885–139889):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>*</members>
        <name>Workflow</name>
    </types>
    <version>62.0</version>
</Package>
```

Use the wildcard for the **inventory** pass (you need every object's workflow file to know what you are
migrating) and the named form for the **cutover** deploy (you want a small, reviewable diff).

---

## Retrieve and deploy

```bash
# 1. Inventory: pull every workflow component in the org.
sf project retrieve start --manifest manifest/workflow-inventory.xml --target-org prod-ro

# 2. Count what you are actually migrating, per object.
python3 skills/admin/workflow-field-update-patterns/scripts/check_workflow_field_update_patterns.py \
  --manifest-dir force-app/main/default

# 3. Retrieve the one object you are cutting over, plus its replacement flow.
sf project retrieve start \
  --metadata Workflow:Opportunity \
  --metadata Flow:High_Value_Opportunity_Review \
  --target-org uat

# 4. Validate-only against production before the real deploy.
sf project deploy validate \
  --manifest manifest/cutover.xml \
  --test-level RunLocalTests \
  --target-org prod

# 5. Deploy the flow activation and the rule deactivation together (see cutover below).
sf project deploy start --manifest manifest/cutover.xml --target-org prod
```

`--manifest-dir` on the checker is the root the checker walks for `*.workflow-meta.xml` and
`*.flow-meta.xml`; point it at the retrieved tree, not at a single file.

---

## Cutover: deactivate old and activate new in one deploy

The gap between "workflow off" and "flow on" is the failure mode. Both directions of the gap are bad:
deactivate first and records saved in the window go unstamped; activate first and both writers run
until you get back to it. Ship them as one deployment.

Set `rules/active` to `false` in the retrieved workflow file — this is the whole deactivation, and it
must ship in the same `package.xml` as the `Active` flow:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- Excerpt from workflows/Opportunity.workflow-meta.xml: the single element that changes at cutover.
     The full file (Example 1) must still be deployed intact — Workflow deploys whole-file. -->
<Workflow xmlns="http://soap.sforce.com/2006/04/metadata">
    <rules>
        <fullName>High_Value_Opportunity_Review</fullName>
        <active>false</active>
    </rules>
</Workflow>
```

Sequence:

1. Retrieve `Workflow:<Object>` and record which rules are `active` and which `fieldUpdates` they
   reference. Check `failedMigrationToolVersion` on each rule before estimating effort — a populated
   value means the Migrate to Flow tool already failed on it once (api_meta.txt:140402–140406, and
   `admin/process-automation-selection` § 10).
2. Build the replacement Flow. Deploy it as `Draft` to the sandbox that mirrors production.
3. **Parity test in the sandbox with both writers live** (table below). Identical outcomes mean the
   mapping is right.
4. Deactivate the workflow rule in the sandbox; re-run the parity table. Outcomes must not change.
5. Deploy to production as one `package.xml`: flow `status` = `Active`, rule `active` = `false`.
6. Verify (below), then delete the orphaned `fieldUpdates` blocks in a later, separate deploy —
   never in the cutover deploy, so rollback stays a one-line revert.

### Verification

Field history is the honest post-deploy check: it records that the field was still written after the
workflow rule stopped running, which is exactly the claim you need to confirm.

```sql
SELECT Field, OldValue, NewValue, CreatedDate
FROM   OpportunityFieldHistory
WHERE  OpportunityId = '006XXXXXXXXXXXXXXX'
AND    Field IN ('Review_Priority__c', 'Review_Note__c')
ORDER  BY CreatedDate DESC
LIMIT  20
```

**UNVERIFIED (2026-09-04)** — `CreatedDate`. The Object Reference's field table for
`OpportunityFieldHistory` (object_reference.txt:193415–193482) lists `DataType`, `Field`, `IsDeleted`,
`OpportunityId`, `NewValue` and `OldValue`, and does not itself enumerate the system audit fields. If
the query rejects the column, drop it and order by `Id DESC` instead.

Save a qualifying Opportunity after the deploy and re-run the query. A new row for each field, with
the values Example 2 writes, proves the Flow took over. **Zero new rows** means the Flow's entry
criteria are narrower than the rule's criteria were — almost always the
`doesRequireRecordChangedToMeetCriteria` flag set to `true` when the source rule was `onAllChanges`.

Field history must be enabled on both fields for this to return anything; a Setup check of
**Object Manager → Opportunity → Fields & Relationships → Set History Tracking** is the fallback when
it does not.

### Parity test table

Run each row against the sandbox with the rule live, then again with it deactivated. The two runs must
produce identical values in the last two columns.

| # | Setup | Action | Expected `Review_Priority__c` | Expected `Review_Note__c` |
|---|---|---|---|---|
| 1 | New Opportunity, Amount 250,000, Stage Prospecting | Insert | `High` | stamped |
| 2 | New Opportunity, Amount 50,000 | Insert | unchanged | unchanged |
| 3 | Existing Opp, Amount 50,000 → 250,000 | Update | `High` | stamped |
| 4 | Existing Opp already at Amount 250,000, `Review_Priority__c` = `High` | Update Description only | `High` (not rewritten) | not rewritten |
| 5 | Existing Opp, Amount 250,000, Stage → `Closed Lost` | Update | unchanged | unchanged |
| 6 | Existing Opp, Amount 250,000 → 300,000 | Update | `High` (already met before **and** after) | see note |
| 7 | 200 Opportunities crossing the threshold | Data Loader update | all `High` | all stamped |

Row 4 and row 6 are the rows that catch a mis-set
`doesRequireRecordChangedToMeetCriteria`: with the flag `true` neither re-fires, because the record
already met the conditions before the update. If the source rule was `onAllChanges`, both **should**
re-fire and the flag must be `false`. Row 7 is the one that catches a
`recordUpdates`-in-a-loop mistake in the after-save variant.

---

## Related reading

- `references/gotchas.md` — the platform behaviours these examples are shaped around.
- `admin/flow-for-admins` — the Flow XML surface in general (element ordering, `filterFormula` vs
  `filters`, `status` handling).
- `flow/workflow-rule-to-flow-migration` — the migration at whole-rule scope, including alerts, tasks
  and outbound messages, which this skill's field-update slice deliberately ignores.
