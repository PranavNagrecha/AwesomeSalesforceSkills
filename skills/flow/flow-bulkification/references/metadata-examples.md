# Metadata Examples — Flow Bulkification

The same requirement built four ways: **the anti-pattern** (Get and Update inside a Loop),
**the corrected flow** (one Get, a Loop that only stages, one Update), **a Collection
Filter + Sort variant** that removes work before the Loop ever runs, and **a scheduled
batch flow** that bounds its own working set. Plus a `FlowTest` that pins the bulk shape,
a `package.xml`, a deploy order, and the two places you verify bulkification actually
happened.

Element names, enum values, version floors and limits come from the Metadata API
Developer Guide (`api_meta.txt`), cited by `grep -n` line. Governor numbers and save-order
positions come from the Apex Developer Guide (`apexdev.txt`). The
Salesforce App Limits Cheat Sheet contains **no Flow or flow-interview limits at all** —
four hits for "flow", all of them the word "workflow" in unrelated rows — so nothing here
is sourced from it.

Canonical shapes this file deliberately does not re-invent:

- `templates/flow/RecordTriggered_Skeleton.flow-meta.xml` — the `<start>` block and
  entry-criteria shape. Flows 1–3 are that skeleton filled in.
- `templates/flow/FaultPath_Template.md` — what a fault path must *do* once you route to
  it. Every `faultConnector` below lands on that shape.
- `flow/record-triggered-flow-patterns` `references/metadata-examples.md` owns
  before-save / after-save / before-delete selection, `triggerOrder`, and scheduled paths
  on an Opportunity model. `flow/fault-handling` owns the fault-path interior on an
  Invoice/Payment model. `flow/subflows-and-reusability` owns the parent/child contract on
  a Case model. Nothing here repeats those objects or those scenarios.
- `flow/flow-loop-element-patterns` owns the Loop element itself — iteration-variable
  aliasing, the retired 2,000-element ceiling, empty-collection behaviour. This file owns
  only the *bulk* consequence of where elements sit relative to the Loop.

---

## Assumed org model

One carrier integration bulk-upserts `Shipment__c` in chunks of 200. When a shipment's
`Status__c` becomes `Delivered`, every related `Shipment_Line__c` must be stamped.

| Component | Type | Used by |
|---|---|---|
| `Shipment__c` | Custom object; `Status__c` (Picklist: `In_Transit`, `Delivered`, `Exception`), `Carrier__c` (Text) | the triggering object, flows 1–3 |
| `Shipment_Line__c` | Custom object; `Shipment__c` (Master-Detail → `Shipment__c`), `Line_Status__c` (Picklist), `Quantity__c` (Number), `Exception_Flag__c` (Checkbox), `Synced_On__c` (DateTime) | the related records written in bulk |
| `Application_Log__c` | Custom object; `Source__c`, `Severity__c`, `Message__c`, `Request_Id__c` | every fault path (`templates/flow/FaultPath_Template.md`) |

The cardinality is what makes this a bulkification problem rather than a Flow problem: a
200-shipment chunk with 12 lines each is 2,400 child records, reached through 200 flow
interviews that share one transaction budget.

---

## 1. The anti-pattern — `Shipment_AfterSave_SyncLines_ANTIPATTERN.flow-meta.xml`

**DO NOT DEPLOY THIS.** It is here because it deploys cleanly, passes a one-record sandbox
test, and fails on the first real integration run. Keep it in a fixture directory and run
the checker against it; it is the negative test case for
`scripts/check_flow_bulkification.py`.

Two elements sit on the Loop's `nextValueConnector` path: a `recordLookups` and a
`recordUpdates`. Both therefore execute once per iteration.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>66.0</apiVersion>
    <description>ANTI-PATTERN FIXTURE. Get Records and Update Records both sit inside the loop body. Do not deploy.</description>
    <environments>Default</environments>
    <interviewLabel>Shipment Line Sync (BAD) {!$Flow.CurrentDateTime}</interviewLabel>
    <label>Shipment Line Sync ANTI-PATTERN</label>
    <loops>
        <name>Loop_Lines</name>
        <label>Loop Lines</label>
        <locationX>176</locationX>
        <locationY>350</locationY>
        <collectionReference>Get_Shipment_Lines</collectionReference>
        <iterationOrder>Asc</iterationOrder>
        <nextValueConnector>
            <targetReference>Get_Parent_Shipment</targetReference>
        </nextValueConnector>
    </loops>
    <processType>AutoLaunchedFlow</processType>
    <recordLookups>
        <name>Get_Parent_Shipment</name>
        <label>Get Parent Shipment</label>
        <locationX>176</locationX>
        <locationY>458</locationY>
        <assignNullValuesIfNoRecordsFound>false</assignNullValuesIfNoRecordsFound>
        <connector>
            <targetReference>Update_One_Line</targetReference>
        </connector>
        <filterLogic>and</filterLogic>
        <filters>
            <field>Id</field>
            <operator>EqualTo</operator>
            <value>
                <elementReference>Loop_Lines.Shipment__c</elementReference>
            </value>
        </filters>
        <getFirstRecordOnly>true</getFirstRecordOnly>
        <object>Shipment__c</object>
        <storeOutputAutomatically>true</storeOutputAutomatically>
    </recordLookups>
    <recordLookups>
        <name>Get_Shipment_Lines</name>
        <label>Get Shipment Lines</label>
        <locationX>176</locationX>
        <locationY>242</locationY>
        <assignNullValuesIfNoRecordsFound>false</assignNullValuesIfNoRecordsFound>
        <connector>
            <targetReference>Loop_Lines</targetReference>
        </connector>
        <filterLogic>and</filterLogic>
        <filters>
            <field>Shipment__c</field>
            <operator>EqualTo</operator>
            <value>
                <elementReference>$Record.Id</elementReference>
            </value>
        </filters>
        <getFirstRecordOnly>false</getFirstRecordOnly>
        <object>Shipment_Line__c</object>
        <storeOutputAutomatically>true</storeOutputAutomatically>
    </recordLookups>
    <recordUpdates>
        <name>Update_One_Line</name>
        <label>Update One Line</label>
        <locationX>176</locationX>
        <locationY>566</locationY>
        <connector>
            <targetReference>Loop_Lines</targetReference>
        </connector>
        <filterLogic>and</filterLogic>
        <filters>
            <field>Id</field>
            <operator>EqualTo</operator>
            <value>
                <elementReference>Loop_Lines.Id</elementReference>
            </value>
        </filters>
        <inputAssignments>
            <field>Line_Status__c</field>
            <value>
                <stringValue>Delivered</stringValue>
            </value>
        </inputAssignments>
        <object>Shipment_Line__c</object>
    </recordUpdates>
    <runInMode>DefaultMode</runInMode>
    <start>
        <locationX>50</locationX>
        <locationY>50</locationY>
        <connector>
            <targetReference>Get_Shipment_Lines</targetReference>
        </connector>
        <doesRequireRecordChangedToMeetCriteria>true</doesRequireRecordChangedToMeetCriteria>
        <filterLogic>and</filterLogic>
        <filters>
            <field>Status__c</field>
            <operator>EqualTo</operator>
            <value>
                <stringValue>Delivered</stringValue>
            </value>
        </filters>
        <object>Shipment__c</object>
        <recordTriggerType>CreateAndUpdate</recordTriggerType>
        <triggerType>RecordAfterSave</triggerType>
    </start>
    <status>Draft</status>
</Flow>
```

### Why it fails — the arithmetic, not the opinion

Read the two connectors. `Loop_Lines` hands control to `Get_Parent_Shipment` through
`<nextValueConnector>` — "A reference to the next element in the collection"
(`api_meta.txt` L70714) — and `Update_One_Line` hands control back to `Loop_Lines`. Every
element on that cycle runs once per line.

| Per interview | Elements | 12 lines | 200-record chunk |
|---|---|---|---|
| SOQL | `Get_Shipment_Lines` (1) + `Get_Parent_Shipment` (1 × lines) | 13 | 2,600 |
| DML statements | `Update_One_Line` (1 × lines) | 12 | 2,400 |

The synchronous budget is **100 SOQL queries and 150 DML statements per transaction**
(`apexdev.txt` L19544, L19554; restated as "one transaction can issue up to 100 SOQL
queries and up to 150 DML statements", L20172–20173). A 200-record Bulk API chunk is one
transaction — "if a Bulk API request causes a trigger to fire multiple times for chunks of
200 records, governor limits are reset between these trigger invocations for the same HTTP
request" (`apexdev.txt` L14904–14907), so the reset is *per chunk*, not per record. This
flow exhausts SOQL somewhere inside the eighth shipment and rolls the whole chunk back.

Three details in the XML that make it worse and are easy to miss:

- `Get_Parent_Shipment` re-reads the record the flow already has. `$Record` is the
  triggering record; the in-loop Get buys nothing at all. In-loop Gets that fetch data the
  interview already holds are the most common form of this bug.
- Neither the `recordLookups` nor the `recordUpdates` has a `<faultConnector>`, though
  both accept one (`api_meta.txt` L71283 for update; the lookup's is documented in the
  same table). When the limit is hit the interview simply stops.
- `Update_One_Line` uses `<filters>` rather than `<inputReference>` — it re-queries the
  row it is about to write. That is a second read charged against the same budget on top
  of the DML statement.

---

## 2. The corrected flow — `Shipment_AfterSave_SyncLines.flow-meta.xml`

Same requirement. One `recordLookups`, one `loops` whose body contains **only** an
`assignments` element, one `recordUpdates` on the `noMoreValuesConnector`. Per interview:
1 SOQL, 1 DML, regardless of how many lines the shipment has.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>66.0</apiVersion>
    <assignments>
        <name>Stage_Line</name>
        <label>Stage Line</label>
        <locationX>176</locationX>
        <locationY>458</locationY>
        <assignmentItems>
            <assignToReference>Loop_Lines.Line_Status__c</assignToReference>
            <operator>Assign</operator>
            <value>
                <stringValue>Delivered</stringValue>
            </value>
        </assignmentItems>
        <assignmentItems>
            <assignToReference>Loop_Lines.Synced_On__c</assignToReference>
            <operator>Assign</operator>
            <value>
                <elementReference>$Flow.CurrentDateTime</elementReference>
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
    <description>Stamps every Shipment_Line__c of a delivered shipment. One Get, one DML, whatever the line count.</description>
    <environments>Default</environments>
    <interviewLabel>Shipment Line Sync {!$Flow.CurrentDateTime}</interviewLabel>
    <label>Shipment Line Sync</label>
    <loops>
        <name>Loop_Lines</name>
        <label>Loop Lines</label>
        <locationX>176</locationX>
        <locationY>350</locationY>
        <collectionReference>Get_Shipment_Lines</collectionReference>
        <iterationOrder>Asc</iterationOrder>
        <nextValueConnector>
            <targetReference>Stage_Line</targetReference>
        </nextValueConnector>
        <noMoreValuesConnector>
            <targetReference>Update_Shipment_Lines</targetReference>
        </noMoreValuesConnector>
    </loops>
    <processType>AutoLaunchedFlow</processType>
    <recordCreates>
        <name>Log_Line_Sync_Fault</name>
        <label>Log Line Sync Fault</label>
        <locationX>440</locationX>
        <locationY>566</locationY>
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
                <stringValue>Shipment_Line_Sync</stringValue>
            </value>
        </inputAssignments>
        <object>Application_Log__c</object>
    </recordCreates>
    <recordLookups>
        <name>Get_Shipment_Lines</name>
        <label>Get Shipment Lines</label>
        <locationX>176</locationX>
        <locationY>242</locationY>
        <assignNullValuesIfNoRecordsFound>false</assignNullValuesIfNoRecordsFound>
        <connector>
            <targetReference>Loop_Lines</targetReference>
        </connector>
        <faultConnector>
            <targetReference>Log_Line_Sync_Fault</targetReference>
        </faultConnector>
        <filterLogic>and</filterLogic>
        <filters>
            <field>Shipment__c</field>
            <operator>EqualTo</operator>
            <value>
                <elementReference>$Record.Id</elementReference>
            </value>
        </filters>
        <getFirstRecordOnly>false</getFirstRecordOnly>
        <object>Shipment_Line__c</object>
        <queriedFields>Id</queriedFields>
        <queriedFields>Line_Status__c</queriedFields>
        <queriedFields>Synced_On__c</queriedFields>
        <storeOutputAutomatically>true</storeOutputAutomatically>
    </recordLookups>
    <recordUpdates>
        <name>Update_Shipment_Lines</name>
        <label>Update Shipment Lines</label>
        <locationX>176</locationX>
        <locationY>566</locationY>
        <faultConnector>
            <targetReference>Log_Line_Sync_Fault</targetReference>
        </faultConnector>
        <inputReference>linesToUpdate</inputReference>
        <object>Shipment_Line__c</object>
    </recordUpdates>
    <runInMode>DefaultMode</runInMode>
    <start>
        <locationX>50</locationX>
        <locationY>50</locationY>
        <connector>
            <targetReference>Get_Shipment_Lines</targetReference>
        </connector>
        <doesRequireRecordChangedToMeetCriteria>true</doesRequireRecordChangedToMeetCriteria>
        <filterLogic>and</filterLogic>
        <filters>
            <field>Status__c</field>
            <operator>EqualTo</operator>
            <value>
                <stringValue>Delivered</stringValue>
            </value>
        </filters>
        <object>Shipment__c</object>
        <recordTriggerType>CreateAndUpdate</recordTriggerType>
        <triggerType>RecordAfterSave</triggerType>
    </start>
    <status>Draft</status>
    <triggerOrder>10</triggerOrder>
    <variables>
        <name>linesToUpdate</name>
        <dataType>SObject</dataType>
        <isCollection>true</isCollection>
        <isInput>false</isInput>
        <isOutput>false</isOutput>
        <objectType>Shipment_Line__c</objectType>
    </variables>
</Flow>
```

### How to read it

- **The loop body is exactly one element.** `<nextValueConnector>` targets `Stage_Line`
  and `Stage_Line`'s `<connector>` targets `Loop_Lines` again. That two-element cycle is
  the whole bulkification rule expressed in XML: nothing that touches the database may sit
  on it.
- **`<noMoreValuesConnector>`** — "The element to navigate to when all entries in the
  collection have been iterated through" (`api_meta.txt` L70716–70717). This is where the
  single DML goes. A loop with no `noMoreValuesConnector` (like flow 1 above) silently
  discards whatever the loop staged; the checker treats that as a finding.
- **`<operator>Add</operator>` on a collection variable** — "When the
  `assignToReference` field is a collection variable, this operator appends the value to
  the end of the collection" (`api_meta.txt` L69786–69787). Note the restriction two lines
  down: passing *another collection* as the value is "available in API version 43.0 and
  later, but only via Metadata API. From Flow Builder, you can't save an Assignment element
  that contains a collection variable in the Value column for the Add operator"
  (L69787–69790). Here the value is a single record (`Loop_Lines`), so this element
  round-trips through Flow Builder unchanged.
- **`<inputReference>linesToUpdate</inputReference>`** — "Specifies the record variable
  whose field values are used to update the record's fields" (`api_meta.txt` L71292). This
  is the collection form. The alternative is `<filters>` + `<inputAssignments>`
  (L71286, L71289), which is what flow 1 used — that form re-queries and cannot take a
  staged collection. **If you take one XML-level rule from this file: bulk-safe
  `recordUpdates` carry `inputReference`; per-record `recordUpdates` carry `filters`.**
- **`<storeOutputAutomatically>true</storeOutputAutomatically>`** — the returned records'
  values "are automatically available in the flow without creating any variables … the
  flow can reference a field by specifying the name of the Get Records element and the
  record field", API 47.0+, "Supported only when `processType` is `Flow` or
  `AutoLaunchedFlow`" (`api_meta.txt` L71237–71249). That is why the Loop's
  `<collectionReference>` is the *element name* `Get_Shipment_Lines` rather than a
  declared variable, and why there is no `<outputReference>` — `outputReference` is
  "Supported only when `storeOutputAutomatically` is false" (L71195–71200).
- **`<getFirstRecordOnly>false</getFirstRecordOnly>`** — "Indicates whether to store field
  values for only one record, even when multiple records meet the filter criteria.
  Supported only when `storeOutputAutomatically` is true" (`api_meta.txt`
  L71153–71160). Setting it `true` here would return one line and the flow would stamp one
  row per shipment while looking correct in Flow Builder. Flow 1 sets it `true` on the
  in-loop Get, which is right for that Get and wrong for this one — the value is per
  element, and reviewing it per element is the point.
- **`<queriedFields>`** — "An array that specifies which fields from the selected record
  are saved to the specified record variable" (`api_meta.txt` L71202–71204). Three fields
  rather than the whole row. Heap is 6 MB synchronous / 12 MB asynchronous
  (`apexdev.txt` L19577), and a collection variable is what fills it.
- **`$Flow.FaultMessage` / `$Flow.InterviewGuid`** in `Log_Line_Sync_Fault` follow
  `templates/flow/FaultPath_Template.md`. Both database elements route their
  `faultConnector` to it; the log create is itself a fault target, so it takes no fault
  path of its own.
- Element ordering inside `<Flow>` is alphabetical, matching the guide's own sample
  definition (`api_meta.txt` L73739–73838: `apiVersion`, `assignments`, `environments`,
  `interviewLabel`, `label`, `loops`, `processType`, `recordLookups`, `runInMode`,
  `start`, `status`, `variables`).

---

## 3. Collection Filter and Sort variant — `Shipment_AfterSave_SyncLines_Filtered.flow-meta.xml`

An **alternative implementation of flow 2** — deploy one or the other, not both, or give
them distinct `<triggerOrder>` values (`flow/record-triggered-flow-patterns`
`references/gotchas.md` § `triggerOrder` ties). It shrinks the collection *before* the
Loop instead of testing each item inside it: lines already marked `Delivered` never enter
the iteration, and the sort plus `<limit>` bound what a single interview can carry.

`collectionProcessors` is "An array of nodes that process collections", API 50.0+
(`api_meta.txt` L68092–68093).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>66.0</apiVersion>
    <assignments>
        <name>Stage_Pending_Line</name>
        <label>Stage Pending Line</label>
        <locationX>176</locationX>
        <locationY>674</locationY>
        <assignmentItems>
            <assignToReference>Loop_Pending.Line_Status__c</assignToReference>
            <operator>Assign</operator>
            <value>
                <stringValue>Delivered</stringValue>
            </value>
        </assignmentItems>
        <assignmentItems>
            <assignToReference>Loop_Pending.Synced_On__c</assignToReference>
            <operator>Assign</operator>
            <value>
                <elementReference>$Flow.CurrentDateTime</elementReference>
            </value>
        </assignmentItems>
        <assignmentItems>
            <assignToReference>linesToUpdate</assignToReference>
            <operator>Add</operator>
            <value>
                <elementReference>Loop_Pending</elementReference>
            </value>
        </assignmentItems>
        <connector>
            <targetReference>Loop_Pending</targetReference>
        </connector>
    </assignments>
    <collectionProcessors>
        <name>Filter_Pending_Lines</name>
        <label>Filter Pending Lines</label>
        <elementSubtype>FilterCollectionProcessor</elementSubtype>
        <locationX>176</locationX>
        <locationY>350</locationY>
        <assignNextValueToReference>currentItem_Filter_Pending_Lines</assignNextValueToReference>
        <collectionProcessorType>FilterCollectionProcessor</collectionProcessorType>
        <collectionReference>Get_Shipment_Lines</collectionReference>
        <conditionLogic>and</conditionLogic>
        <conditions>
            <leftValueReference>currentItem_Filter_Pending_Lines.Line_Status__c</leftValueReference>
            <operator>NotEqualTo</operator>
            <rightValue>
                <stringValue>Delivered</stringValue>
            </rightValue>
        </conditions>
        <connector>
            <targetReference>Sort_By_Quantity</targetReference>
        </connector>
    </collectionProcessors>
    <collectionProcessors>
        <name>Sort_By_Quantity</name>
        <label>Sort By Quantity</label>
        <elementSubtype>SortCollectionProcessor</elementSubtype>
        <locationX>176</locationX>
        <locationY>458</locationY>
        <collectionProcessorType>SortCollectionProcessor</collectionProcessorType>
        <collectionReference>Filter_Pending_Lines</collectionReference>
        <connector>
            <targetReference>Loop_Pending</targetReference>
        </connector>
        <limit>200</limit>
        <sortOptions>
            <doesPutEmptyStringAndNullFirst>false</doesPutEmptyStringAndNullFirst>
            <sortField>Quantity__c</sortField>
            <sortOrder>Desc</sortOrder>
        </sortOptions>
    </collectionProcessors>
    <description>Flow 2 with the per-item test moved out of the loop into a Collection Filter, and a bounded Sort.</description>
    <environments>Default</environments>
    <interviewLabel>Shipment Line Sync Filtered {!$Flow.CurrentDateTime}</interviewLabel>
    <label>Shipment Line Sync Filtered</label>
    <loops>
        <name>Loop_Pending</name>
        <label>Loop Pending</label>
        <locationX>176</locationX>
        <locationY>566</locationY>
        <collectionReference>Sort_By_Quantity</collectionReference>
        <iterationOrder>Asc</iterationOrder>
        <nextValueConnector>
            <targetReference>Stage_Pending_Line</targetReference>
        </nextValueConnector>
        <noMoreValuesConnector>
            <targetReference>Update_Pending_Lines</targetReference>
        </noMoreValuesConnector>
    </loops>
    <processType>AutoLaunchedFlow</processType>
    <recordCreates>
        <name>Log_Pending_Sync_Fault</name>
        <label>Log Pending Sync Fault</label>
        <locationX>440</locationX>
        <locationY>674</locationY>
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
                <stringValue>Shipment_Line_Sync_Filtered</stringValue>
            </value>
        </inputAssignments>
        <object>Application_Log__c</object>
    </recordCreates>
    <recordLookups>
        <name>Get_Shipment_Lines</name>
        <label>Get Shipment Lines</label>
        <locationX>176</locationX>
        <locationY>242</locationY>
        <assignNullValuesIfNoRecordsFound>false</assignNullValuesIfNoRecordsFound>
        <connector>
            <targetReference>Filter_Pending_Lines</targetReference>
        </connector>
        <faultConnector>
            <targetReference>Log_Pending_Sync_Fault</targetReference>
        </faultConnector>
        <filterLogic>and</filterLogic>
        <filters>
            <field>Shipment__c</field>
            <operator>EqualTo</operator>
            <value>
                <elementReference>$Record.Id</elementReference>
            </value>
        </filters>
        <getFirstRecordOnly>false</getFirstRecordOnly>
        <limit>
            <numberValue>2000.0</numberValue>
        </limit>
        <object>Shipment_Line__c</object>
        <queriedFields>Id</queriedFields>
        <queriedFields>Line_Status__c</queriedFields>
        <queriedFields>Quantity__c</queriedFields>
        <queriedFields>Synced_On__c</queriedFields>
        <storeOutputAutomatically>true</storeOutputAutomatically>
    </recordLookups>
    <recordUpdates>
        <name>Update_Pending_Lines</name>
        <label>Update Pending Lines</label>
        <locationX>176</locationX>
        <locationY>782</locationY>
        <faultConnector>
            <targetReference>Log_Pending_Sync_Fault</targetReference>
        </faultConnector>
        <inputReference>linesToUpdate</inputReference>
        <object>Shipment_Line__c</object>
    </recordUpdates>
    <runInMode>DefaultMode</runInMode>
    <start>
        <locationX>50</locationX>
        <locationY>50</locationY>
        <connector>
            <targetReference>Get_Shipment_Lines</targetReference>
        </connector>
        <doesRequireRecordChangedToMeetCriteria>true</doesRequireRecordChangedToMeetCriteria>
        <filterLogic>and</filterLogic>
        <filters>
            <field>Status__c</field>
            <operator>EqualTo</operator>
            <value>
                <stringValue>Delivered</stringValue>
            </value>
        </filters>
        <object>Shipment__c</object>
        <recordTriggerType>CreateAndUpdate</recordTriggerType>
        <triggerType>RecordAfterSave</triggerType>
    </start>
    <status>Draft</status>
    <triggerOrder>20</triggerOrder>
    <variables>
        <name>currentItem_Filter_Pending_Lines</name>
        <dataType>SObject</dataType>
        <isCollection>false</isCollection>
        <isInput>false</isInput>
        <isOutput>false</isOutput>
        <objectType>Shipment_Line__c</objectType>
    </variables>
    <variables>
        <name>linesToUpdate</name>
        <dataType>SObject</dataType>
        <isCollection>true</isCollection>
        <isInput>false</isInput>
        <isOutput>false</isOutput>
        <objectType>Shipment_Line__c</objectType>
    </variables>
</Flow>
```

### How to read it

- `<collectionProcessorType>` takes exactly three values:
  `SortCollectionProcessor` (API 50.0+), `RecommendationMapCollectionProcessor`
  (53.0+), and `FilterCollectionProcessor` (53.0+) (`api_meta.txt` L69934–69941).
  There is no "map to a different sObject" processor in that list; the Map element in
  Flow Builder is the recommendation variant, and `<outputSObjectType>` /
  `<mapItems>` (L69977–69979) belong to it.
- `<collectionReference>` on a processor is "The collection being sorted, filtered, or
  assigned to recommendations" (`api_meta.txt` L69942–69943). It chains: the Sort reads
  `Filter_Pending_Lines`, the Loop reads `Sort_By_Quantity`. Each processor produces a new
  collection referenced by element name, exactly like `storeOutputAutomatically` on a Get.
- `<limit>` on the Sort — "The maximum number of records to include in the generated
  collection. There's no default value. All items of the collection are kept if it's
  greater than the size of the collection. If `sortField` and `sortOrder` are also
  specified, the records are sorted before the limit takes effect", API 51.0+
  (`api_meta.txt` L69961–69967). Sort-then-limit is the ordering that makes "top 200 by
  quantity" mean something.
- `<limit>` on the Get is a different field with a different shape — a
  `FlowElementReferenceOrValue`, "Valid values are between 2 and 20,000. Supported only
  when `getFirstRecordOnly` is false", API 63.0+ (`api_meta.txt` L71177–71183). Hence
  `<numberValue>2000.0</numberValue>` on the lookup and a bare integer on the processor.
- `<sortOptions>` carries `sortField`, `sortOrder` (`Asc` / `Desc`) and
  `doesPutEmptyStringAndNullFirst` (`api_meta.txt` L69986–70004). `sortField` is
  "Required for record collections and collections of Apex-defined variables" and "If the
  collection is a primitive data type … `sortField` isn't supported" (L69994–69998).
- **UNVERIFIED (2026-09-05):** the guide documents `assignNextValueToReference` on
  `FlowCollectionProcessor` as "The name of the variable that's assigned to the next value
  of the collection" (`api_meta.txt` L69931–69932) but gives **no sample XML for a
  `FilterCollectionProcessor`**, so the exact form of a filter condition's
  `leftValueReference` — the `currentItem_…` variable plus a field, as written above — is
  inferred from that field's description, not read from a documented example. Retrieve one
  Collection Filter built in Flow Builder from a sandbox and diff it before hand-writing
  another. `<elementSubtype>` is documented "Reserved for internal use" (L70745) yet Flow
  Builder emits it on these nodes; it is included here for round-trip fidelity, not
  because the guide requires it.
- The `Filter_Pending_Lines` node has no `<faultConnector>` and needs none — a collection
  processor works in memory and does not reach the database.

---

## 4. Scheduled batch flow — `Shipment_Nightly_Line_Reconcile.flow-meta.xml`

The catch-up job for lines the record-triggered path missed. It is the same collection
discipline with one extra requirement: a scheduled flow chooses its own working set, so it
must bound it.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>66.0</apiVersion>
    <assignments>
        <name>Stage_Reconciled_Line</name>
        <label>Stage Reconciled Line</label>
        <locationX>176</locationX>
        <locationY>566</locationY>
        <assignmentItems>
            <assignToReference>Loop_Stale.Exception_Flag__c</assignToReference>
            <operator>Assign</operator>
            <value>
                <booleanValue>false</booleanValue>
            </value>
        </assignmentItems>
        <assignmentItems>
            <assignToReference>Loop_Stale.Synced_On__c</assignToReference>
            <operator>Assign</operator>
            <value>
                <elementReference>$Flow.CurrentDateTime</elementReference>
            </value>
        </assignmentItems>
        <assignmentItems>
            <assignToReference>reconciledLines</assignToReference>
            <operator>Add</operator>
            <value>
                <elementReference>Loop_Stale</elementReference>
            </value>
        </assignmentItems>
        <connector>
            <targetReference>Loop_Stale</targetReference>
        </connector>
    </assignments>
    <collectionProcessors>
        <name>Oldest_Stale_Lines_First</name>
        <label>Oldest Stale Lines First</label>
        <elementSubtype>SortCollectionProcessor</elementSubtype>
        <locationX>176</locationX>
        <locationY>350</locationY>
        <collectionProcessorType>SortCollectionProcessor</collectionProcessorType>
        <collectionReference>Get_Stale_Lines</collectionReference>
        <connector>
            <targetReference>Loop_Stale</targetReference>
        </connector>
        <limit>500</limit>
        <sortOptions>
            <doesPutEmptyStringAndNullFirst>true</doesPutEmptyStringAndNullFirst>
            <sortField>Synced_On__c</sortField>
            <sortOrder>Asc</sortOrder>
        </sortOptions>
    </collectionProcessors>
    <description>Nightly catch-up for Shipment_Line__c rows the record-triggered path missed. Bounded Get, bounded Sort, one DML.</description>
    <environments>Default</environments>
    <interviewLabel>Shipment Line Reconcile {!$Flow.CurrentDateTime}</interviewLabel>
    <label>Shipment Nightly Line Reconcile</label>
    <loops>
        <name>Loop_Stale</name>
        <label>Loop Stale</label>
        <locationX>176</locationX>
        <locationY>458</locationY>
        <collectionReference>Oldest_Stale_Lines_First</collectionReference>
        <iterationOrder>Asc</iterationOrder>
        <nextValueConnector>
            <targetReference>Stage_Reconciled_Line</targetReference>
        </nextValueConnector>
        <noMoreValuesConnector>
            <targetReference>Update_Reconciled_Lines</targetReference>
        </noMoreValuesConnector>
    </loops>
    <processType>AutoLaunchedFlow</processType>
    <recordCreates>
        <name>Log_Reconcile_Fault</name>
        <label>Log Reconcile Fault</label>
        <locationX>440</locationX>
        <locationY>566</locationY>
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
                <stringValue>Shipment_Line_Reconcile</stringValue>
            </value>
        </inputAssignments>
        <object>Application_Log__c</object>
    </recordCreates>
    <recordLookups>
        <name>Get_Stale_Lines</name>
        <label>Get Stale Lines</label>
        <locationX>176</locationX>
        <locationY>242</locationY>
        <assignNullValuesIfNoRecordsFound>false</assignNullValuesIfNoRecordsFound>
        <connector>
            <targetReference>Oldest_Stale_Lines_First</targetReference>
        </connector>
        <faultConnector>
            <targetReference>Log_Reconcile_Fault</targetReference>
        </faultConnector>
        <filterLogic>and</filterLogic>
        <filters>
            <field>Exception_Flag__c</field>
            <operator>EqualTo</operator>
            <value>
                <booleanValue>true</booleanValue>
            </value>
        </filters>
        <getFirstRecordOnly>false</getFirstRecordOnly>
        <limit>
            <numberValue>2000.0</numberValue>
        </limit>
        <object>Shipment_Line__c</object>
        <queriedFields>Id</queriedFields>
        <queriedFields>Exception_Flag__c</queriedFields>
        <queriedFields>Synced_On__c</queriedFields>
        <sortField>Synced_On__c</sortField>
        <sortOrder>Asc</sortOrder>
        <storeOutputAutomatically>true</storeOutputAutomatically>
    </recordLookups>
    <recordUpdates>
        <name>Update_Reconciled_Lines</name>
        <label>Update Reconciled Lines</label>
        <locationX>176</locationX>
        <locationY>674</locationY>
        <faultConnector>
            <targetReference>Log_Reconcile_Fault</targetReference>
        </faultConnector>
        <inputReference>reconciledLines</inputReference>
        <object>Shipment_Line__c</object>
    </recordUpdates>
    <runInMode>SystemModeWithSharing</runInMode>
    <start>
        <locationX>50</locationX>
        <locationY>50</locationY>
        <connector>
            <targetReference>Get_Stale_Lines</targetReference>
        </connector>
        <schedule>
            <frequency>Daily</frequency>
            <startDate>2026-09-06</startDate>
            <startTime>02:00:00.000Z</startTime>
        </schedule>
        <triggerType>Scheduled</triggerType>
    </start>
    <status>Draft</status>
    <variables>
        <name>reconciledLines</name>
        <dataType>SObject</dataType>
        <isCollection>true</isCollection>
        <isInput>false</isInput>
        <isOutput>false</isOutput>
        <objectType>Shipment_Line__c</objectType>
    </variables>
</Flow>
```

### How to read it — and the one decision that defines a scheduled flow

- **There is no `<object>` on `<start>`, and that is the whole design.** When a scheduled
  flow's Start *does* carry `<object>`, "The object whose records you want to retrieve from
  the database. **A flow interview starts for each record that meets the filter
  conditions**" (`api_meta.txt` L72424–72428). One interview per matching record: 40,000
  stale lines is 40,000 interviews, and the flow author controls neither the batch size nor
  the transaction boundary — `FlowSchedule` has `frequency`, `startDate`, `startTime`,
  `dayOfMonthToRun`, `daysOfWeekToRun`, `endDate`, `endTime`, `frequencyNumber`
  (`api_meta.txt` L71335–71386) and **no batch-size field**. The only documented
  batch-size control anywhere in the Flow metadata is `FlowScheduledPath.maxBatchSize`,
  "from 1 to 200. Default is 200" (L71397–71398), which applies to scheduled *paths* on
  record-triggered flows — a different feature (see
  `flow/record-triggered-flow-patterns` `references/gotchas.md` § scheduled path batching).
  Omitting `<object>` starts one interview that reads a bounded collection instead, which
  is the shape you can reason about.
- `<triggerType>Scheduled</triggerType>` — "The flow starts at the scheduled time", API
  47.0+ (`api_meta.txt` L72543–72544), and is "Available only when `processType` is
  `AutoLaunchedFlow` or `PromptFlow`" (L72551–72553). `<schedule>` is "Required when
  `triggerType` is `Scheduled`" (L72462–72463).
- `<recordTriggerType>` is deliberately absent: the guide restricts it to "Available only
  when `triggerType` is `RecordBeforeSave` or `DataCloudDataChange`" (`api_meta.txt`
  L72458–72460).
- **Two limits, deliberately different.** The Get caps at 2,000 rows; the Sort caps at 500.
  The Get bound protects heap and query rows; the Sort bound is what one interview
  actually commits. Raise the Sort limit only after you have measured, because everything
  it passes to the Loop ends up in `reconciledLines` and then in one DML statement — DML
  rows cap at 10,000 per transaction (`apexdev.txt` L19556–19557).
- `<runInMode>SystemModeWithSharing</runInMode>` — "The flow respects org-wide default
  settings, role hierarchies, sharing rules, manual sharing, teams, and territories. The
  flow doesn't respect object permissions, field-level access, or other permissions of the
  running user" (`api_meta.txt` L68379–68386). A scheduled flow has no interactive user, so
  leaving `DefaultMode` makes the running context a question rather than a decision.
- **UNVERIFIED (2026-09-05):** whether a schedule-triggered flow's interview runs against
  the *synchronous* (100 SOQL / 6 MB heap / 10,000 ms CPU) or *asynchronous* (200 SOQL /
  12 MB / 60,000 ms) limits is not stated in `api_meta.txt` or `apexdev.txt`. Size the two
  `<limit>` values against the synchronous column until you have measured a real run with
  `FLOW_INTERVIEW_FINISHED_LIMIT_USAGE` in the debug log (see § 8).

---

## 5. The bulk regression test — `Shipment_AfterSave_SyncLines_Delivered.flowtest-meta.xml`

`FlowTest` exists so you can check the shape before activation: "Before you activate a
record-triggered, autolaunched, or Data Cloud-triggered flow, you can test it to verify
its expected results and identify flow run-time failures" (`api_meta.txt` L73961–73963).
Components have the suffix `.flowtest` and live in the `flowtests` folder (L73976); in
SFDX source format that is `.flowtest-meta.xml`. Available API 55.0+ (L73980).

A flow test runs one interview, so it cannot prove behaviour across a 200-record chunk.
What it *can* pin is the two structural facts that make the bulk shape work: the loop
staged something into the collection, and the single DML after the loop did not fault.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<FlowTest xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Shipment moves to Delivered. Asserts the loop staged lines into the collection and the single bulk update did not fault.</description>
    <flowApiName>Shipment_AfterSave_SyncLines</flowApiName>
    <label>Delivered shipment stages and commits its lines once</label>
    <testPoints>
        <elementApiName>Start</elementApiName>
        <parameters>
            <leftValueReference>$Record</leftValueReference>
            <type>InputTriggeringRecordInitial</type>
            <value>
                <sobjectValue>{&quot;Name&quot;:&quot;SHP-88120&quot;,&quot;Status__c&quot;:&quot;In_Transit&quot;,&quot;Carrier__c&quot;:&quot;Northwind Freight&quot;}</sobjectValue>
            </value>
        </parameters>
        <parameters>
            <leftValueReference>$Record</leftValueReference>
            <type>InputTriggeringRecordUpdated</type>
            <value>
                <sobjectValue>{&quot;Name&quot;:&quot;SHP-88120&quot;,&quot;Status__c&quot;:&quot;Delivered&quot;,&quot;Carrier__c&quot;:&quot;Northwind Freight&quot;}</sobjectValue>
            </value>
        </parameters>
    </testPoints>
    <testPoints>
        <assertions>
            <conditions>
                <leftValueReference>linesToUpdate</leftValueReference>
                <operator>IsEmpty</operator>
                <rightValue>
                    <booleanValue>false</booleanValue>
                </rightValue>
            </conditions>
            <errorMessage>The loop staged nothing: linesToUpdate is empty, so the single Update Records had no work and the lines were never stamped.</errorMessage>
        </assertions>
        <assertions>
            <conditions>
                <leftValueReference>Update_Shipment_Lines</leftValueReference>
                <operator>HasError</operator>
                <rightValue>
                    <booleanValue>false</booleanValue>
                </rightValue>
            </conditions>
            <errorMessage>The bulk Update Records faulted. Flow has no partial-success mode on recordUpdates: one bad row fails the whole collection.</errorMessage>
        </assertions>
        <elementApiName>Finish</elementApiName>
    </testPoints>
    <testType>WithAssertion</testType>
</FlowTest>
```

### How to read it

- `<elementApiName>` accepts only `Start` and `Finish` — "The element API names for the
  start of the flow and the end of the flow" (`api_meta.txt` L74143–74147). You cannot
  assert on the Loop itself, which is precisely why the assertions target the *collection
  variable* and the *DML element* instead: those are the two observable ends of the loop.
- `IsEmpty` is a documented `FlowComparisonOperator`, API 61.0+ (`api_meta.txt` L74217),
  and `HasError` is one, API 64.0+ (L74203). `HasError` against a `recordUpdates` element is
  the closest a flow test gets to asserting on DML success.
- `<testType>WithAssertion</testType>` is documented Required but available only in API
  version 66.0 and later (`api_meta.txt` L74041–74048); the guide's own first sample omits
  it. Drop it if your manifest targets an earlier version.
- The sObject payload is XML-escaped JSON inside `<sobjectValue>`, matching the guide's own
  sample (`api_meta.txt` L74344–74396).
- **What this test cannot do.** It runs one interview. To prove the flow survives a chunk
  you need the 200-record load in § 8 — a flow test that passes is a necessary condition
  for activation, never a sufficient one for a bulk path.

---

## 6. `package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Shipment_AfterSave_SyncLines</members>
        <members>Shipment_Nightly_Line_Reconcile</members>
        <name>Flow</name>
    </types>
    <types>
        <members>Shipment_AfterSave_SyncLines_Delivered</members>
        <name>FlowTest</name>
    </types>
    <types>
        <members>Shipment__c</members>
        <members>Shipment_Line__c</members>
        <members>Application_Log__c</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>Shipment__c.Status__c</members>
        <members>Shipment__c.Carrier__c</members>
        <members>Shipment_Line__c.Shipment__c</members>
        <members>Shipment_Line__c.Line_Status__c</members>
        <members>Shipment_Line__c.Quantity__c</members>
        <members>Shipment_Line__c.Exception_Flag__c</members>
        <members>Shipment_Line__c.Synced_On__c</members>
        <name>CustomField</name>
    </types>
    <version>66.0</version>
</Package>
```

Only two flows are listed. The anti-pattern (§ 1) belongs in a fixture directory the
checker scans, never in a deploy manifest; the Collection Filter variant (§ 3) is an
alternative to `Shipment_AfterSave_SyncLines`, so shipping both means giving them distinct
`<triggerOrder>` values and accepting two after-save passes over the same object. Flow and
FlowTest are listed by member rather than by `*` so the manifest states exactly what is in
scope.

---

## 7. Deploy order

```bash
# 0. lint the source tree, including the anti-pattern fixture — it must FAIL
python3 skills/flow/flow-bulkification/scripts/check_flow_bulkification.py \
  --manifest-dir force-app/main/default

# 1. check-only validation. Nothing commits; the flows are still Draft in the source
sf project deploy validate \
  --manifest manifest/package.xml \
  --target-org uat

# 2. objects and fields first. A flow that references Shipment_Line__c.Synced_On__c
#    before the field exists fails at deploy, which is the cheap failure
sf project deploy start \
  --metadata CustomObject:Shipment__c \
  --metadata CustomObject:Shipment_Line__c \
  --metadata CustomObject:Application_Log__c \
  --target-org uat

# 3. both flows, still Draft
sf project deploy start \
  --metadata Flow:Shipment_AfterSave_SyncLines \
  --metadata Flow:Shipment_Nightly_Line_Reconcile \
  --target-org uat

# 4. the flow test, then run it from Setup > Flows > Shipment Line Sync > View Tests
sf project deploy start \
  --metadata FlowTest:Shipment_AfterSave_SyncLines_Delivered \
  --target-org uat

# 5. load 200 shipments with lines BEFORE activating anything in production,
#    and read the limit usage out of the debug log (section 8)
sf data import bulk --sobject Shipment__c --file data/shipments-200.csv --target-org uat
sf data import bulk --sobject Shipment_Line__c --file data/lines-2400.csv --target-org uat

# 6. only now flip <status> to Active and redeploy
sf project deploy start --metadata Flow:Shipment_AfterSave_SyncLines --target-org uat

# 7. retrieve the pair back to see what actually landed, version numbers included
sf project retrieve start --manifest manifest/package.xml --target-org uat
```

Step 5 is the step teams skip, and it is the only one that exercises the thing this skill
is about. A flow that has never seen 200 records in one transaction has not been tested.

---

## 8. Verification

**The debug log is the only place bulkification is directly observable.** Set the
`Workflow` category to `FINER` on the integration user, run the 200-record load from step
5, and read for three event types (all from the Apex Developer Guide's debug event table):

| Event | What it tells you | Source |
|---|---|---|
| `FLOW_START_INTERVIEWS_BEGIN` / `_END` | logs "Requests" — the interviews started as a set, not one at a time | `apexdev.txt` L38856–38860 |
| `FLOW_BULK_ELEMENT_BEGIN` / `_DETAIL` / `_END` | "Interview ID, element type, element name, **number of records**, and execution time" — one entry per *element*, carrying the record count it processed | `apexdev.txt` L38721–38729 |
| `FLOW_BULK_ELEMENT_LIMIT_USAGE` | "Incremented usage toward a limit for this bulk element", itemised across SOQL queries, SOQL query rows, DML statements, DML rows, CPU time, heap size | `apexdev.txt` L38730–38744 |
| `FLOW_INTERVIEW_FINISHED_LIMIT_USAGE` | the same limit list, "when the interview finishes" | `apexdev.txt` L38821–38835 |
| `FLOW_LOOP_DETAIL` | "Interview ID, index, and value. The index is the position in the collection variable for the item that the loop is operating on" — one entry **per iteration** | `apexdev.txt` L38843–38846 |
| `FLOW_BULK_ELEMENT_NOT_SUPPORTED` | "Operation, element name, and entity name that doesn't support bulk operations" — the platform naming, at runtime, exactly what it did **not** bulkify | `apexdev.txt` L38746–38747 |

Read those two shapes against each other. A healthy run of flow 2 shows one
`FLOW_BULK_ELEMENT_*` group for `Get_Shipment_Lines` and one for
`Update_Shipment_Lines` with a large record count, and many `FLOW_LOOP_DETAIL` lines in
between with no bulk-element group among them. A run of flow 1 shows a
`FLOW_BULK_ELEMENT_*` group for `Get_Parent_Shipment` and `Update_One_Line` repeating
between loop details, with `FLOW_BULK_ELEMENT_LIMIT_USAGE` climbing on each — that
climbing SOQL count is the failure, visible before the exception.

**SOQL.** Confirm the write actually covered the whole chunk rather than the first few
shipments:

```sql
SELECT Shipment__r.Status__c, Line_Status__c, COUNT(Id) lineCount
FROM Shipment_Line__c
WHERE Shipment__r.LastModifiedDate = TODAY
GROUP BY Shipment__r.Status__c, Line_Status__c
ORDER BY COUNT(Id) DESC
```

Every row where `Shipment__r.Status__c = 'Delivered'` and `Line_Status__c != 'Delivered'`
is a line the flow was supposed to stamp and did not. On a rolled-back chunk that count is
the whole chunk; on a partially-processed load it is the tail.

**Fault channel.** Anything that failed left a row, because every database element in
flows 2–4 routes its `faultConnector` to `Application_Log__c`:

```sql
SELECT Source__c, Severity__c, Message__c, Request_Id__c, CreatedDate
FROM Application_Log__c
WHERE Source__c IN ('Shipment_Line_Sync', 'Shipment_Line_Sync_Filtered', 'Shipment_Line_Reconcile')
  AND CreatedDate = TODAY
ORDER BY CreatedDate DESC
```

A `Message__c` containing `Too many SOQL queries: 101` or `Too many DML statements: 151`
is the in-loop pattern, not a data problem. An empty log **and** missing stamps is worse:
it means the interview never reached a fault-capable element — check whether a loop is
missing its `noMoreValuesConnector` and the staged collection was simply discarded.
