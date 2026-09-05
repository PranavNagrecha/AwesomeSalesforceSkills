# Metadata Examples — Flow Cross-Object Updates

Two deployable record-triggered flows that write **across** a relationship in opposite
directions — child→parent and parent→child — plus the `CustomField` pair that decides how
much of this you have to build at all (MasterDetail vs Lookup, and the roll-up summary
that replaces the child→parent flow outright), the two `FlowTest` components, a
`package.xml`, the deploy order, and the debug-log line that proves the two flows are not
re-triggering each other.

Every element name, enum value and version floor below is cited by `grep -n` line into the
Metadata API Developer Guide text (`api_meta.txt`, Summer '26 / v62 extract of
<https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf>). Governor
numbers, save-order step numbers and debug-log event names come from the Apex Developer
Guide (`apexdev.txt`,
<https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf>).
Where a behaviour is documented only on help.salesforce.com, the claim carries an explicit
`UNVERIFIED (2026-09-05)` marker beside it, never in a footnote.

Canonical shapes this file deliberately does not re-invent:

- `templates/flow/RecordTriggered_Skeleton.flow-meta.xml` — the `<start>` block, the
  `<processType>AutoLaunchedFlow</processType>` / `<triggerType>` / `<filters>` shape, and
  `doesRequireRecordChangedToMeetCriteria`. Both flows below are that skeleton filled in.
- `templates/flow/FaultPath_Template.md` — what a fault path must *do* once you route to
  it. Every `faultConnector` below lands on that shape.
- `flow/flow-bulkification` owns **why** the Update sits outside the Loop and how the
  staging collection is built. Section 3 uses that pattern and does not re-argue it.
- `flow/flow-collection-processing` owns `FlowCollectionProcessor` and `FlowTransform` —
  the no-Loop way to Sum or Count a child collection. Section 4 routes aggregates there
  and to the declarative roll-up, not to a hand-built Loop.
- `flow/flow-record-save-order-interaction` owns re-entry into the save order; this file
  cites step numbers but does not re-derive them.
- `admin/lookup-and-relationship-design` owns the relationship choice itself. Section 5
  shows only the two consequences a *flow author* has to live with.

---

## 0. The org model these artifacts assume

A subscription billing org. One `Subscription__c` has many `Subscription_Line__c`. Lines
arrive from a provisioning integration in chunks; a subscription's `Region__c` is changed
by a human, rarely, and must reach every line.

| Component | Type | Why it is here |
|---|---|---|
| `Subscription__c` | Custom object | The parent. Written by flow 1, triggers flow 2 |
| `Subscription__c.Region__c` | Picklist (`NA`, `EMEA`, `APAC`) | The value that fans **down** to children |
| `Subscription__c.Line_Health__c` | Text(40) | The computed status stamped **up** from children by flow 1 |
| `Subscription__c.Active_Line_Count__c` | Roll-Up Summary (Count) | The declarative alternative to a counting flow — § 5.3 |
| `Subscription_Line__c` | Custom object | The child |
| `Subscription_Line__c.Subscription__c` | MasterDetail **or** Lookup → `Subscription__c` | The relationship under test — § 5.1 / § 5.2 |
| `Subscription_Line__c.Line_Status__c` | Picklist (`Draft`, `Active`, `Cancelled`) | Drives flow 1's computed parent status |
| `Subscription_Line__c.Region__c` | Picklist (`NA`, `EMEA`, `APAC`) | The value flow 2 fans down |
| `Application_Log__c` | Custom object; `Message__c`, `Source__c`, `Severity__c`, `Request_Id__c` | Fault-path landing (`templates/flow/FaultPath_Template.md`) |

The two flows below form a **write graph with a cycle in it**: flow 1 writes
`Subscription__c.Line_Health__c`, flow 2 triggers on `Subscription__c` and writes
`Subscription_Line__c.Region__c`, and any write to a `Subscription_Line__c` re-enters
flow 1. Everything in § 1–§ 3 is about making that cycle terminate on the first pass.

---

## 1. Child → parent: `Subscription_Line_AfterSave_Stamp_Health.flow-meta.xml`

One `Get`-free, one-DML stamp on the parent. Three things are load-bearing and all three
are visible in the XML:

- `<doesRequireRecordChangedToMeetCriteria>true</doesRequireRecordChangedToMeetCriteria>`
  in `<start>` — "conditions evaluate to true only if the record didn't meet the required
  conditions before the triggering update but now meets the conditions after the update"
  (`api_meta.txt` L72322–72326, API 50.0+). This is what stops flow 2's `Region__c` write
  on the child from waking flow 1 again: `Line_Status__c` did not transition, so the entry
  condition is not newly met.
- The `Parent_Present` Decision guarding on `IsNull` — see § 5.2 for when this branch is
  reachable.
- One `<recordUpdates>` at the end of the path, with **no `<loops>` anywhere in the file**.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>66.0</apiVersion>
    <description>Child to parent. Stamps a computed health string on Subscription__c when a line's status transitions. One DML, no Get, no Loop.</description>
    <decisions>
        <name>Parent_Present</name>
        <label>Parent Present</label>
        <locationX>176</locationX>
        <locationY>278</locationY>
        <defaultConnector>
            <targetReference>Classify_Health</targetReference>
        </defaultConnector>
        <defaultConnectorLabel>Parent Present</defaultConnectorLabel>
        <rules>
            <name>Orphan_Line</name>
            <label>Orphan Line</label>
            <conditionLogic>and</conditionLogic>
            <conditions>
                <leftValueReference>$Record.Subscription__c</leftValueReference>
                <operator>IsNull</operator>
                <rightValue>
                    <booleanValue>true</booleanValue>
                </rightValue>
            </conditions>
        </rules>
    </decisions>
    <decisions>
        <name>Classify_Health</name>
        <label>Classify Health</label>
        <locationX>176</locationX>
        <locationY>386</locationY>
        <defaultConnector>
            <targetReference>Stamp_Parent_Health</targetReference>
        </defaultConnector>
        <defaultConnectorLabel>Line Active</defaultConnectorLabel>
        <rules>
            <name>Line_Cancelled</name>
            <label>Line Cancelled</label>
            <conditionLogic>and</conditionLogic>
            <conditions>
                <leftValueReference>$Record.Line_Status__c</leftValueReference>
                <operator>EqualTo</operator>
                <rightValue>
                    <stringValue>Cancelled</stringValue>
                </rightValue>
            </conditions>
            <connector>
                <targetReference>Stamp_Parent_Attention</targetReference>
            </connector>
        </rules>
    </decisions>
    <environments>Default</environments>
    <interviewLabel>Subscription Line Stamp Health {!$Flow.CurrentDateTime}</interviewLabel>
    <label>Subscription Line After Save Stamp Health</label>
    <processType>AutoLaunchedFlow</processType>
    <recordCreates>
        <name>Log_Stamp_Fault</name>
        <label>Log Stamp Fault</label>
        <locationX>440</locationX>
        <locationY>494</locationY>
        <inputAssignments>
            <field>Message__c</field>
            <value>
                <elementReference>$Flow.FaultMessage</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Request_Id__c</field>
            <value>
                <elementReference>$Flow.InterviewGuid</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Severity__c</field>
            <value>
                <stringValue>Error</stringValue>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Source__c</field>
            <value>
                <stringValue>Subscription_Line_Stamp_Health</stringValue>
            </value>
        </inputAssignments>
        <object>Application_Log__c</object>
    </recordCreates>
    <recordUpdates>
        <name>Stamp_Parent_Health</name>
        <label>Stamp Parent Health</label>
        <locationX>176</locationX>
        <locationY>494</locationY>
        <faultConnector>
            <targetReference>Log_Stamp_Fault</targetReference>
        </faultConnector>
        <filterLogic>and</filterLogic>
        <filters>
            <field>Id</field>
            <operator>EqualTo</operator>
            <value>
                <elementReference>$Record.Subscription__c</elementReference>
            </value>
        </filters>
        <inputAssignments>
            <field>Line_Health__c</field>
            <value>
                <stringValue>All Lines Active</stringValue>
            </value>
        </inputAssignments>
        <object>Subscription__c</object>
    </recordUpdates>
    <recordUpdates>
        <name>Stamp_Parent_Attention</name>
        <label>Stamp Parent Attention</label>
        <locationX>308</locationX>
        <locationY>494</locationY>
        <faultConnector>
            <targetReference>Log_Stamp_Fault</targetReference>
        </faultConnector>
        <filterLogic>and</filterLogic>
        <filters>
            <field>Id</field>
            <operator>EqualTo</operator>
            <value>
                <elementReference>$Record.Subscription__c</elementReference>
            </value>
        </filters>
        <inputAssignments>
            <field>Line_Health__c</field>
            <value>
                <stringValue>Attention: Cancelled Line</stringValue>
            </value>
        </inputAssignments>
        <object>Subscription__c</object>
    </recordUpdates>
    <runInMode>DefaultMode</runInMode>
    <start>
        <locationX>50</locationX>
        <locationY>50</locationY>
        <connector>
            <targetReference>Parent_Present</targetReference>
        </connector>
        <doesRequireRecordChangedToMeetCriteria>true</doesRequireRecordChangedToMeetCriteria>
        <filterLogic>or</filterLogic>
        <filters>
            <field>Line_Status__c</field>
            <operator>EqualTo</operator>
            <value>
                <stringValue>Active</stringValue>
            </value>
        </filters>
        <filters>
            <field>Line_Status__c</field>
            <operator>EqualTo</operator>
            <value>
                <stringValue>Cancelled</stringValue>
            </value>
        </filters>
        <object>Subscription_Line__c</object>
        <recordTriggerType>CreateAndUpdate</recordTriggerType>
        <triggerType>RecordAfterSave</triggerType>
    </start>
    <status>Draft</status>
</Flow>
```

### How to read it

- **`<triggerType>RecordAfterSave</triggerType>`** (`api_meta.txt` L72524–72525, API 49.0+)
  is not optional for a cross-object write. `RecordBeforeSave` exists "to make more updates
  to *that* record before it's saved to the database" (L72536–72540) — the guide scopes it
  to the triggering record. UNVERIFIED (2026-09-05): the stronger claim that a before-save
  flow *cannot host* a Create/Update/Delete element at all appears only in Flow Builder's
  UI and on help.salesforce.com; the Metadata API guide states the scope, not the
  prohibition.
- **`<recordTriggerType>CreateAndUpdate</recordTriggerType>`** — values at L72448–72461.
  UNVERIFIED (2026-09-05): that field table says "Available only when `triggerType` is
  `RecordBeforeSave` or `DataCloudDataChange`", yet every after-save flow Flow Builder
  emits carries it. Treat the guide sentence as an omission and keep the element; a
  retrieve from your own org is the cheapest confirmation.
- **Two `<recordUpdates>`, one per Decision outcome, not one Update fed by a formula.**
  Both target `Subscription__c`; only one executes per interview. This keeps the field
  value literal and greppable, which is what makes the checker's ping-pong rule work.
- **Filter mode, not `inputReference`.** `FlowRecordUpdate` documents exactly two ways to
  say *which* record (`api_meta.txt` L71264–71292):

  | Mode | Elements present | Reads as |
  |---|---|---|
  | Filter | `object` + `filters` (+ `filterLogic`) + `inputAssignments` | "find the records matching this and set these fields" |
  | Reference | `inputReference` (+ `object`) | "use the record variable's own Id and field values" |

  `object` is **Required** in both (L71292). Filter mode is used here because the fields
  being set (`Line_Health__c`) are not on any variable the flow holds.
- **The `inputReference` variant** for the same stamp writes the parent through the
  relationship rather than through a filter:

  ```xml
  <recordUpdates>
      <name>Stamp_Parent_Via_Reference</name>
      <label>Stamp Parent Via Reference</label>
      <locationX>176</locationX>
      <locationY>494</locationY>
      <inputAssignments>
          <field>Line_Health__c</field>
          <value>
              <stringValue>All Lines Active</stringValue>
          </value>
      </inputAssignments>
      <inputReference>$Record.Subscription__r</inputReference>
      <object>Subscription__c</object>
  </recordUpdates>
  ```

  UNVERIFIED (2026-09-05): `api_meta.txt` documents `inputReference` and
  `inputAssignments` as independent fields of `FlowRecordUpdate` but ships no sample
  combining them, and no sample of a `$Record.<Relationship>__r` value in an
  `inputReference`. The dotted-parent traversal *syntax* on `$Record` is grounded —
  `$Record.Account.SLA__c` and `$Record.Product2.Name` appear in the guide's own
  RecommendationStrategy sample at L102276–102289 — but that is an expression context,
  not a `FlowRecordUpdate` target. Prefer filter mode until you have retrieved the
  reference form from your own org.
- **No `<loops>` element exists in this file.** A child→parent stamp never needs one: the
  flow already holds the one child that triggered it, and the parent Id is a field on that
  child. If you find yourself adding a Loop here, you have started building an aggregate —
  go to § 4.

---

## 2. Grandparent traversal in the entry condition

The same flow, entry-criteria block only, when the decision depends on a field two hops up
(`Subscription_Line__c` → `Subscription__c` → `Account`):

```xml
<start>
    <locationX>50</locationX>
    <locationY>50</locationY>
    <connector>
        <targetReference>Parent_Present</targetReference>
    </connector>
    <doesRequireRecordChangedToMeetCriteria>true</doesRequireRecordChangedToMeetCriteria>
    <filterFormula>AND(
  NOT(ISBLANK({!$Record.Subscription__c})),
  TEXT({!$Record.Line_Status__c}) = "Cancelled",
  TEXT({!$Record.Subscription__r.Account__r.Segment__c}) = "Enterprise"
)</filterFormula>
    <object>Subscription_Line__c</object>
    <recordTriggerType>CreateAndUpdate</recordTriggerType>
    <triggerType>RecordAfterSave</triggerType>
</start>
```

`filterFormula` is "a formula that's used to filter what records execute the flow during a
save. Available only in record-triggered flows" (`api_meta.txt` L72390–72393, API 55.0+).
It replaces `<filters>`; do not ship both.

Two things to know before you write a traversal that long:

- **The null guard has to be inside the formula, not after it.** `NOT(ISBLANK(...))` is the
  first conjunct for a reason — a traversal through an empty lookup yields no value, and
  the Decision element in § 1 runs *after* the entry criteria have already been evaluated.
- **Depth.** UNVERIFIED (2026-09-05): the "five levels" figure people quote for Flow
  traversal is a SOQL limit, not a documented Flow limit. What is grounded is the SOQL
  rule — "In each specified relationship, no more than five levels can be specified in a
  child-to-parent relationship. For example, `Contact.Account.Owner.FirstName` (three
  levels)" (`salesforce_app_limits_cheatsheet.txt` L1143–1146). Whether Flow's `$Record`
  traversal is subject to the same ceiling is stated only on help.salesforce.com. Two hops
  as shown here is comfortably inside any reading of it.

---

## 3. Parent → child: `Subscription_AfterSave_Fan_Region.flow-meta.xml`

One `Get Records` for the whole related list, a Loop that only stages, one `Update Records`
after the loop. The Get's second filter — `Region__c NotEqualTo $Record.Region__c` — is the
part specific to *cross-object* work: it removes from the working set every child that is
already correct, so the Update writes nothing on a re-run and therefore wakes nothing.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>66.0</apiVersion>
    <assignments>
        <name>Stage_Line_Region</name>
        <label>Stage Line Region</label>
        <locationX>308</locationX>
        <locationY>386</locationY>
        <assignmentItems>
            <assignToReference>Loop_Lines.Region__c</assignToReference>
            <operator>Assign</operator>
            <value>
                <elementReference>$Record.Region__c</elementReference>
            </value>
        </assignmentItems>
        <assignmentItems>
            <assignToReference>linesToUpdate</assignToReference>
            <operator>Add</operator>
            <value>
                <elementReference>Loop_Lines</elementReference>
            </value>
        </assignmentItems>
        <connector>
            <targetReference>Loop_Lines</targetReference>
        </connector>
    </assignments>
    <decisions>
        <name>Any_Lines_Staged</name>
        <label>Any Lines Staged</label>
        <locationX>176</locationX>
        <locationY>494</locationY>
        <defaultConnectorLabel>Nothing To Write</defaultConnectorLabel>
        <rules>
            <name>Has_Lines</name>
            <label>Has Lines</label>
            <conditionLogic>and</conditionLogic>
            <conditions>
                <leftValueReference>linesToUpdate</leftValueReference>
                <operator>IsEmpty</operator>
                <rightValue>
                    <booleanValue>false</booleanValue>
                </rightValue>
            </conditions>
            <connector>
                <targetReference>Update_Line_Regions</targetReference>
            </connector>
        </rules>
    </decisions>
    <description>Parent to child. Fans a changed Region to every line that does not already carry it. One Get, one Update, both outside the Loop.</description>
    <environments>Default</environments>
    <interviewLabel>Subscription Fan Region {!$Flow.CurrentDateTime}</interviewLabel>
    <label>Subscription After Save Fan Region</label>
    <loops>
        <name>Loop_Lines</name>
        <label>Loop Lines</label>
        <locationX>176</locationX>
        <locationY>386</locationY>
        <collectionReference>Get_Stale_Lines</collectionReference>
        <iterationOrder>Asc</iterationOrder>
        <nextValueConnector>
            <targetReference>Stage_Line_Region</targetReference>
        </nextValueConnector>
        <noMoreValuesConnector>
            <targetReference>Any_Lines_Staged</targetReference>
        </noMoreValuesConnector>
    </loops>
    <processType>AutoLaunchedFlow</processType>
    <recordCreates>
        <name>Log_Fan_Fault</name>
        <label>Log Fan Fault</label>
        <locationX>440</locationX>
        <locationY>602</locationY>
        <inputAssignments>
            <field>Message__c</field>
            <value>
                <elementReference>$Flow.FaultMessage</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Request_Id__c</field>
            <value>
                <elementReference>$Flow.InterviewGuid</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Severity__c</field>
            <value>
                <stringValue>Error</stringValue>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Source__c</field>
            <value>
                <stringValue>Subscription_Fan_Region</stringValue>
            </value>
        </inputAssignments>
        <object>Application_Log__c</object>
    </recordCreates>
    <recordLookups>
        <name>Get_Stale_Lines</name>
        <label>Get Stale Lines</label>
        <locationX>176</locationX>
        <locationY>278</locationY>
        <assignNullValuesIfNoRecordsFound>false</assignNullValuesIfNoRecordsFound>
        <connector>
            <targetReference>Loop_Lines</targetReference>
        </connector>
        <faultConnector>
            <targetReference>Log_Fan_Fault</targetReference>
        </faultConnector>
        <filterLogic>and</filterLogic>
        <filters>
            <field>Subscription__c</field>
            <operator>EqualTo</operator>
            <value>
                <elementReference>$Record.Id</elementReference>
            </value>
        </filters>
        <filters>
            <field>Region__c</field>
            <operator>NotEqualTo</operator>
            <value>
                <elementReference>$Record.Region__c</elementReference>
            </value>
        </filters>
        <getFirstRecordOnly>false</getFirstRecordOnly>
        <limit>
            <numberValue>2000.0</numberValue>
        </limit>
        <object>Subscription_Line__c</object>
        <queriedFields>Id</queriedFields>
        <queriedFields>Region__c</queriedFields>
        <queriedFields>Subscription__c</queriedFields>
        <storeOutputAutomatically>true</storeOutputAutomatically>
    </recordLookups>
    <recordUpdates>
        <name>Update_Line_Regions</name>
        <label>Update Line Regions</label>
        <locationX>176</locationX>
        <locationY>602</locationY>
        <faultConnector>
            <targetReference>Log_Fan_Fault</targetReference>
        </faultConnector>
        <inputReference>linesToUpdate</inputReference>
        <object>Subscription_Line__c</object>
    </recordUpdates>
    <runInMode>DefaultMode</runInMode>
    <start>
        <locationX>50</locationX>
        <locationY>50</locationY>
        <connector>
            <targetReference>Get_Stale_Lines</targetReference>
        </connector>
        <doesRequireRecordChangedToMeetCriteria>true</doesRequireRecordChangedToMeetCriteria>
        <filterFormula>ISCHANGED({!$Record.Region__c})</filterFormula>
        <object>Subscription__c</object>
        <recordTriggerType>Update</recordTriggerType>
        <triggerType>RecordAfterSave</triggerType>
    </start>
    <status>Draft</status>
    <variables>
        <name>linesToUpdate</name>
        <dataType>SObject</dataType>
        <isCollection>true</isCollection>
        <isInput>false</isInput>
        <isOutput>false</isOutput>
        <objectType>Subscription_Line__c</objectType>
    </variables>
</Flow>
```

### How to read it

- **`<recordTriggerType>Update</recordTriggerType>`, not `CreateAndUpdate`.** A brand-new
  `Subscription__c` has no children yet, so a create-triggered fan-out is a guaranteed
  zero-row `Get` on every insert. Values at `api_meta.txt` L72448–72461.
- **`<queriedFields>`** names the three fields the Loop and the Update actually touch
  (`api_meta.txt` L71202–71204). It is not decoration: `storeOutputAutomatically` plus an
  unrestricted field set is how a fan-out flow ends up carrying every field of every child
  in heap.
- **`<limit>`** — "the maximum number of records to store. Valid values are between 2 and
  20,000. Supported only when `getFirstRecordOnly` is false" (`api_meta.txt`
  L71176–71182, API 63.0+). It caps *this* flow, not the transaction; the transaction cap
  is 10,000 rows across all DML (`apexdev.txt` L19556). A `<limit>` above 10,000 on a
  collection you intend to update is arithmetic that cannot succeed.
- **The Loop's `<nextValueConnector>` targets an `<assignments>` element and nothing
  else.** Every element reachable from that connector runs once per iteration. The checker
  in `scripts/check_flow_cross_object_updates.py` walks that path; `flow/flow-bulkification`
  owns the reasoning and the 150-DML arithmetic (`apexdev.txt` L19550).
- **`<inputReference>linesToUpdate</inputReference>` on the Update.** The collection
  variable carries Ids and field values, so no `filters` block is present and no
  `inputAssignments` are needed — the second of the two modes in § 1.
- **The `Any_Lines_Staged` Decision before the Update.** `IsEmpty` is "an empty collection"
  (`api_meta.txt` L70097–70098, API 61.0+). Without it, an update-nothing path still issues
  a DML statement against an empty collection on every `Region__c` edit.

---

## 4. When neither flow should exist: aggregates

The single most common cross-object flow is a hand-built count or sum over children. Three
options, in the order to try them:

| Want | Use | Why |
|---|---|---|
| Count / Sum / Min / Max of a **master-detail** child field on the parent | `CustomField` roll-up summary — § 5.3 | Platform-maintained; no flow, no interview, no recursion surface |
| Same, but the relationship is a **Lookup** | `FlowCollectionProcessor` / `FlowTransform` — see `flow/flow-collection-processing` | Still no Loop; the aggregate is computed in one element |
| A derived *string* or multi-condition status, like `Line_Health__c` in § 1 | The flow in § 1 | Not expressible as a roll-up operation |

`summaryOperation` valid values are `Count`, `Min`, `Max`, `Sum` (`api_meta.txt`
L43651–43666), and `summarizedField` "can't be null unless the `summaryOperation` value is
`count`" (L43636–43638). The relationship requirement is stated in the field table itself:
`summaryForeignKey` "represents the **master-detail** field on the child that defines the
relationship between the parent and the child" (L43648–43650). That single sentence is why
a Lookup relationship gets a flow and a MasterDetail one does not.

A Loop + `Assignment` with the `Add` operator over a Number is the shape to reach for
last. The operator does work — "when the `assignToReference` field is a variable of type
number or currency, this operator adds the value to the variable" (`api_meta.txt`
L69773–69774) — but it buys you a per-interview iteration to compute something the
platform will maintain for free when the relationship is master-detail. The checker flags
exactly that combination as ADVISORY.

---

## 5. The `CustomField` pair that decides how much flow you write

### 5.1 MasterDetail

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Subscription__c</fullName>
    <label>Subscription</label>
    <referenceTo>Subscription__c</referenceTo>
    <relationshipLabel>Subscription Lines</relationshipLabel>
    <relationshipName>Subscription_Lines</relationshipName>
    <relationshipOrder>0</relationshipOrder>
    <reparentableMasterDetail>false</reparentableMasterDetail>
    <trackHistory>false</trackHistory>
    <type>MasterDetail</type>
    <writeRequiresMasterRead>false</writeRequiresMasterRead>
</CustomField>
```

- `relationshipOrder` — "valid for all master-detail relationships, but the value is only
  non-zero for junction objects… 0 or 1 are the only valid values, and 0 is always the
  value for objects that aren't junction objects" (`api_meta.txt` L43582–43592). Ship `0`.
- `reparentableMasterDetail` "indicates whether the child records in a master-detail
  relationship on a custom object can be reparented to different parent records. The
  default value is `false`" (L43593–43597, API 25.0+). Leaving it `false` means a
  cross-object flow can never be handed a line whose parent changed — which removes an
  entire class of "stamp went to the wrong subscription" bug, and removes the need for a
  flow that re-stamps the old parent.
- `writeRequiresMasterRead` "sets the minimum sharing access level required on the primary
  record to create, edit, or delete child records… `false` — allows users with Read/Write
  access to the primary record permission to create, edit, or delete child records. This
  setting is more restrictive than `true`, and is the default value" (L43724–43734). This
  is the one that bites a *user-context* flow: the running user needs Read/Write on
  `Subscription__c` before flow 3's write to `Subscription_Line__c` is allowed.

### 5.2 Lookup

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Subscription__c</fullName>
    <deleteConstraint>SetNull</deleteConstraint>
    <label>Subscription</label>
    <referenceTo>Subscription__c</referenceTo>
    <relationshipLabel>Subscription Lines</relationshipLabel>
    <relationshipName>Subscription_Lines</relationshipName>
    <required>false</required>
    <trackHistory>false</trackHistory>
    <type>Lookup</type>
</CustomField>
```

`deleteConstraint` values (`api_meta.txt` L43347–43357, and the `DeleteConstraint` field
type at L45707–45711):

| Value | Behaviour per the guide | What a cross-object flow must then handle |
|---|---|---|
| `SetNull` | **The default.** "If the lookup record is deleted, the lookup field is cleared" | Orphan children exist. § 1's `Parent_Present` Decision is load-bearing, and any flow that traverses `$Record.Subscription__r` returns nothing |
| `Restrict` | "Prevents the record from being deleted if it's in a lookup relationship" | No orphans; the guard is defensive only. Parent deletes now fail loudly, which is a Setup decision, not a flow decision |
| `Cascade` | "Deletes the lookup record as well as associated lookup fields" | Children disappear with the parent, so a child-triggered flow may fire during the delete cascade |

The pairing that produces the § 1 guard is `Lookup` + `SetNull` + `required false`. Under
the § 5.1 MasterDetail definition the same Decision branch is far harder to reach, because
a detail record has to reference a master — the guide states this obliquely, in the deploy
rules: converting "a Lookup field relationship to a Master-Detail relationship" requires
that "detail records must reference a master record or be soft-deleted… for the deployment
to succeed" (`api_meta.txt` L4207–4213). Keep the guard in both variants: it costs one
Decision and it is the difference between a flow that survives a relationship change and
one that starts failing the day someone converts the field.

### 5.3 The roll-up summary that replaces a flow

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Active_Line_Count__c</fullName>
    <label>Active Line Count</label>
    <summaryFilterItems>
        <field>Subscription_Line__c.Line_Status__c</field>
        <operation>equals</operation>
        <value>Active</value>
    </summaryFilterItems>
    <summaryForeignKey>Subscription_Line__c.Subscription__c</summaryForeignKey>
    <summaryOperation>count</summaryOperation>
    <type>Summary</type>
</CustomField>
```

`summaryFilterItems` "represents the set of filter conditions for this field if it's a
summary field. This field is summed on the child if the filter conditions are met"
(`api_meta.txt` L43644–43647). `summarizedField` is absent because the operation is
`count` (L43636–43638). Requires the § 5.1 MasterDetail definition; it will not deploy
against § 5.2.

**Where this lands in the transaction.** Roll-ups are step 16 of the save order — "if the
record contains a roll-up summary field or is part of a cross-object workflow, performs
calculations and updates the roll-up summary field in the parent record. Parent record
goes through save procedure" — and step 17 does the same for the grandparent
(`apexdev.txt` L15471–15477). Two consequences a flow author has to hold:

1. The parent's own after-save flows run again when the roll-up updates it. That is not a
   bug; it is step 16's "parent record goes through save procedure".
2. "During a recursive save, Salesforce skips steps 9 (assignment rules) through 17
   (roll-up summary field in the grandparent record)" (`apexdev.txt` L15414–15415). A flow
   that fires *inside* a recursive save therefore cannot rely on a roll-up having been
   recomputed. `flow/flow-record-save-order-interaction` owns the rest of this.

---

## 6. `FlowTest` for the child → parent stamp

`FlowTest` components have the suffix `.flowtest`, live in the `flowtests` folder, and are
available in API version 55.0 and later (`api_meta.txt` L73976, L73980). `testType` is
Required as of API 66.0 with the value `WithAssertion` (L74041–74050).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<FlowTest xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Line transitions to Cancelled; parent Line_Health__c must carry the attention string.</description>
    <flowApiName>Subscription_Line_AfterSave_Stamp_Health</flowApiName>
    <label>Line Cancelled Stamps Parent Attention</label>
    <testPoints>
        <elementApiName>Start</elementApiName>
        <parameters>
            <leftValueReference>$Record</leftValueReference>
            <type>InputTriggeringRecordInitial</type>
            <value>
                <sobjectValue>{"Line_Status__c":"Active"}</sobjectValue>
            </value>
        </parameters>
        <parameters>
            <leftValueReference>$Record</leftValueReference>
            <type>InputTriggeringRecordUpdated</type>
            <value>
                <sobjectValue>{"Line_Status__c":"Cancelled"}</sobjectValue>
            </value>
        </parameters>
    </testPoints>
    <testPoints>
        <assertions>
            <conditions>
                <leftValueReference>$Record.Line_Status__c</leftValueReference>
                <operator>EqualTo</operator>
                <rightValue>
                    <stringValue>Cancelled</stringValue>
                </rightValue>
            </conditions>
            <errorMessage>Cancelled path did not run.</errorMessage>
        </assertions>
        <elementApiName>Finish</elementApiName>
    </testPoints>
    <testType>WithAssertion</testType>
</FlowTest>
```

The `InputTriggeringRecordInitial` / `InputTriggeringRecordUpdated` pair is what exercises
`doesRequireRecordChangedToMeetCriteria`: the initial record must *not* meet the criteria
and the updated one must. Both parameters use `$Record` as `leftValueReference`, which the
guide requires for these two types (`api_meta.txt` L74303–74308).

**What a `FlowTest` cannot assert here.** Assertions read flow resources, and `$Record` is
the *child*. The parent's `Line_Health__c` is written by a DML the test cannot see. So this
test proves the branch was taken; § 8's SOQL proves the parent was written. Do not write an
assertion against `$Record.Subscription__r.Line_Health__c` and believe it.
UNVERIFIED (2026-09-05): whether a `FlowTest` assertion may traverse a relationship at all
is not stated in the `FlowTestCondition` field table (`api_meta.txt` L74157–74195).

---

## 7. `FlowTest` for the parent → child fan-out

```xml
<?xml version="1.0" encoding="UTF-8"?>
<FlowTest xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Region changes NA to EMEA; the entry formula must admit the record and the fan-out must run.</description>
    <flowApiName>Subscription_AfterSave_Fan_Region</flowApiName>
    <label>Region Change Fans To Lines</label>
    <testPoints>
        <elementApiName>Start</elementApiName>
        <parameters>
            <leftValueReference>$Record</leftValueReference>
            <type>InputTriggeringRecordInitial</type>
            <value>
                <sobjectValue>{"Region__c":"NA"}</sobjectValue>
            </value>
        </parameters>
        <parameters>
            <leftValueReference>$Record</leftValueReference>
            <type>InputTriggeringRecordUpdated</type>
            <value>
                <sobjectValue>{"Region__c":"EMEA"}</sobjectValue>
            </value>
        </parameters>
    </testPoints>
    <testPoints>
        <assertions>
            <conditions>
                <leftValueReference>$Record.Region__c</leftValueReference>
                <operator>EqualTo</operator>
                <rightValue>
                    <stringValue>EMEA</stringValue>
                </rightValue>
            </conditions>
            <errorMessage>Region change did not reach the flow.</errorMessage>
        </assertions>
        <elementApiName>Finish</elementApiName>
    </testPoints>
    <testType>WithAssertion</testType>
</FlowTest>
```

A `FlowTest` starts one interview. It does not prove the flow is bulk-safe and it does not
prove the child rows changed — for the first, see `flow/flow-bulkification`; for the
second, § 8. Isolated test data (`flowTestDataSources` with an Apex factory class,
`isolatedObjectExternalKeys`) is available in API 66.0 and later
(`api_meta.txt` L74003–74005, L74026–74029) and is how you give this test real children to
fan to.

---

## 8. `package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Subscription_Line_AfterSave_Stamp_Health</members>
        <members>Subscription_AfterSave_Fan_Region</members>
        <name>Flow</name>
    </types>
    <types>
        <members>Line_Cancelled_Stamps_Parent_Attention</members>
        <members>Region_Change_Fans_To_Lines</members>
        <name>FlowTest</name>
    </types>
    <types>
        <members>Subscription__c</members>
        <members>Subscription_Line__c</members>
        <members>Application_Log__c</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>Subscription__c.Region__c</members>
        <members>Subscription__c.Line_Health__c</members>
        <members>Subscription__c.Active_Line_Count__c</members>
        <members>Subscription_Line__c.Subscription__c</members>
        <members>Subscription_Line__c.Line_Status__c</members>
        <members>Subscription_Line__c.Region__c</members>
        <name>CustomField</name>
    </types>
    <version>66.0</version>
</Package>
```

Only **one** of § 5.1 and § 5.2 can be in the tree for `Subscription_Line__c.Subscription__c`
— they are two definitions of the same field. `Active_Line_Count__c` is listed only if you
took the MasterDetail branch.

---

## 9. Deploy order

```bash
# 0. lint the source tree first. The ping-pong rule needs BOTH flows present to fire,
#    so run it after the flows are in the tree and before anything reaches an org
python3 skills/flow/flow-cross-object-updates/scripts/check_flow_cross_object_updates.py \
  --manifest-dir force-app/main/default --strict

# 1. objects and fields, relationship field included. A flow that references
#    Subscription_Line__c.Region__c before the field exists fails here, cheaply
sf project deploy start \
  --metadata CustomObject:Subscription__c \
  --metadata CustomObject:Subscription_Line__c \
  --metadata CustomObject:Application_Log__c \
  --target-org uat

# 2. check-only validation of the whole manifest. NOTE: if this deploy changes the
#    relationship field between MasterDetail and Lookup, skip this step -- that change
#    "isn't supported when using the checkOnly option" (api_meta.txt L4177-4183).
#    Do a full deploy to a scratch org or a second sandbox instead
sf project deploy validate --manifest manifest/package.xml --target-org uat

# 3. both flows, still <status>Draft</status>. Draft flows deploy and do not run
sf project deploy start \
  --metadata Flow:Subscription_Line_AfterSave_Stamp_Health \
  --metadata Flow:Subscription_AfterSave_Fan_Region \
  --target-org uat

# 4. the flow tests, then run them from Setup > Flows > <flow> > View Tests
sf project deploy start \
  --metadata FlowTest:Line_Cancelled_Stamps_Parent_Attention \
  --metadata FlowTest:Region_Change_Fans_To_Lines \
  --target-org uat

# 5. activate ONE side first and exercise it. Activating both flows in the same
#    deploy is how a ping-pong reaches production untested
sf project retrieve start --metadata Flow:Subscription_Line_AfterSave_Stamp_Health --target-org uat
# edit <status> to Active, redeploy, exercise, read the log (section 10), then repeat for the second flow
```

Step 2's caveat is the one that catches teams: a MasterDetail↔Lookup conversion also
"deletes all detail records in the Recycle Bin" and, for a Lookup→MasterDetail conversion,
"a successful deployment permanently deletes any detail records in the Recycle Bin"
(`api_meta.txt` L4190–4213). That is data loss inside a metadata deploy.

---

## 10. Verification

**Did the parent actually get written?** The `FlowTest` cannot see it; SOQL can.

```sql
SELECT Id, Name, Line_Health__c, Active_Line_Count__c,
       (SELECT Id, Line_Status__c, Region__c FROM Subscription_Lines ORDER BY CreatedDate DESC LIMIT 5)
FROM Subscription__c
WHERE LastModifiedDate = TODAY
ORDER BY LastModifiedDate DESC
LIMIT 20
```

The subquery uses `Subscription_Lines` — the `relationshipName` from § 5.1/§ 5.2, not the
field name. A parent row whose `Line_Health__c` says `Attention: Cancelled Line` while no
child in the subquery is `Cancelled` means the stamp is stale, which means flow 1's entry
criteria are narrower than the states it stamps.

**Did anything ping-pong?** Set the Workflow debug-log category to `FINE` or better, edit
one `Subscription__c.Region__c`, and count interview starts per flow definition:

| Debug-log event | Field it logs | What you want to see |
|---|---|---|
| `FLOW_CREATE_INTERVIEW_BEGIN` | "Organization ID, definition ID, and version ID" (`apexdev.txt` L38759–38761, Workflow INFO+) | The `Subscription_Line__c` flow's definition ID appears **zero** times. Flow 2 wrote only `Region__c`, and flow 1's entry criteria watch `Line_Status__c` |
| `FLOW_START_INTERVIEWS_BEGIN` / `_END` | "Requests" (`apexdev.txt` L38856–38861) | One `_BEGIN` per flow per DML, whatever the batch size — the interviews start as a set |
| `FLOW_ELEMENT_BEGIN` | "Interview ID, element type, and element name" (`apexdev.txt` L38768–38770, Workflow FINE+) | `Get_Stale_Lines` once, `Stage_Line_Region` once per stale child, `Update_Line_Regions` once |

A second `FLOW_CREATE_INTERVIEW_BEGIN` carrying the child flow's definition ID is the
signature of the ping-pong. It means one of the two entry conditions is wider than the
field the other side writes — fix the condition, not the DML.

**Did the transaction stay inside budget?** `LIMIT_USAGE_FOR_NS` at the end of the log
(`apexdev.txt` L38275) against the synchronous ceilings: 100 SOQL, 150 DML, 10,000 rows
processed by DML, 10,000 ms CPU, and stack depth 16 for recursive trigger firing
(`apexdev.txt` L19542–19559, L19579). SOQL and DML counts must be flat across a 1-record
and a 200-record load; row count is the one that scales, and it is the one bounded by
§ 3's `<limit>`.
