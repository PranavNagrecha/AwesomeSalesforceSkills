# Metadata Examples — Flow Loop Element Patterns

Deployable `*.flow-meta.xml` for the Loop element itself: **the anti-pattern** (a nested
loop that matches two collections and mutates the loop variable with nothing staged),
**the corrected flow** (Sort + `limit` before the Loop, one Assignment that mutates the
loop variable *and* stages it, one post-loop DML on a fault path), and **a
collection-processor flow** that replaces the inner matching loop with a
`FilterCollectionProcessor` and builds a new record collection with a Map processor.
Plus a `FlowTest`, a `package.xml`, a deploy order, and two places you verify the loop
behaved.

Every element name, enum value, version floor and limit below is cited to the Metadata
API Developer Guide (`api_meta.txt`) or the Apex Developer Guide (`apexdev.txt`) by
`grep -n` line. Where the guide documents a field but ships no sample for it, the claim
carries an `UNVERIFIED (2026-09-05)` marker inline — not in a footnote.

**Negative result worth writing down:** the retired per-interview ceiling of 2,000
executed Flow elements appears **nowhere** in `api_meta.txt`, `apexdev.txt`, or the
Salesforce App Limits Cheat Sheet. Neither does the error string `Number of iterations
exceeded`. `grep -n -i "2,\?000"` across all three returns no line that also contains
`element`, `interview`, or `iteration`, and the cheat sheet's only `flow` hits are the
word "workflow" in unrelated rows. The sibling `flow/flow-bulkification` reached the same
conclusion independently. Treat any 2,000-element claim in this domain as unsourced by
these guides.

Canonical shapes this file deliberately does not re-invent:

- `templates/flow/RecordTriggered_Skeleton.flow-meta.xml` — the `<start>` block shape.
- `templates/flow/FaultPath_Template.md` — what a `faultConnector` must land on. The
  `Log_Loop_Failure` element below is that shape filled in.
- `templates/flow/Subflow_Pattern.md` — the bulk-safe subflow input contract, for the
  subflow-in-loop refactor described in `references/gotchas.md` Gotcha 5.
- `flow/flow-bulkification` owns the *bulk* framing and a `Shipment__c` model;
  `flow/fault-handling` owns the fault-path interior on `Invoice`/`Payment`;
  `flow/subflows-and-reusability` owns the parent/child contract on `Case`;
  `flow/flow-collection-processing` owns collection-element selection generally. This
  file uses a grants model that none of them touch, and stays on the Loop node.

---

## Assumed org model

A grants office scores applications during intake and ranks them nightly. Nothing here is
record-triggered — the Loop problems in this file are the ones that survive after you have
already moved off in-loop DML, so the flows are `AutoLaunchedFlow` with a `Scheduled`
trigger.

| Component | Type | Used by |
|---|---|---|
| `Grant_Application__c` | Custom object; `Score__c` (Number), `Program_Code__c` (Text), `Review_Stage__c` (Picklist: `Intake`, `Scored`, `Ranked`, `Awarded`), `Rank__c` (Number), `Reviewed_On__c` (DateTime) | the iterated collection in every flow |
| `Program_Rule__c` | Custom object; `Program_Code__c` (Text), `Minimum_Score__c` (Number), `Is_Active__c` (Checkbox) | the *second* collection — the one the anti-pattern nests a Loop over |
| `Review_Assignment__c` | Custom object; `Application__c` (Lookup → `Grant_Application__c`), `Reviewer_Queue__c` (Text), `Priority__c` (Number) | the output collection the Map processor builds |
| `Application_Log__c` | Custom object; `Source__c`, `Severity__c`, `Message__c` | every `faultConnector` target |

The shape that makes this a *Loop* problem rather than a bulkification problem: 4,000
applications and 60 active program rules. Nesting one loop inside the other is 240,000
element executions, and no DML is involved at all — so none of the DML-in-loop advice
applies and the flow still dies.

---

## 1. The anti-pattern — `Grant_Rank_Nightly_ANTIPATTERN.flow-meta.xml`

**DO NOT DEPLOY THIS.** It deploys cleanly and passes a 5-record debug run. Keep it in a
fixture directory as the negative case for `scripts/check_flow_loop_element_patterns.py`.

Three defects, all Loop-specific:

1. `Match_Rules` is a second `<loops>` whose `collectionReference` is a collection of a
   *different* object reached once per outer iteration — O(n×m).
2. `Stamp_Application` assigns to `currentApp.Rank__c` and stops. Nothing is added to
   another collection, and no `recordUpdates` exists anywhere in the flow.
3. `Rank_Applications` has no `noMoreValuesConnector`, so when the collection is
   exhausted the interview has nowhere to go — including on the empty-collection path,
   which reaches `noMoreValuesConnector` on the *first* evaluation.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>66.0</apiVersion>
    <assignments>
        <name>Stamp_Application</name>
        <label>Stamp Application</label>
        <locationX>314</locationX>
        <locationY>458</locationY>
        <assignmentItems>
            <assignToReference>currentApp.Rank__c</assignToReference>
            <operator>Assign</operator>
            <value>
                <elementReference>currentRule.Minimum_Score__c</elementReference>
            </value>
        </assignmentItems>
        <connector>
            <targetReference>Match_Rules</targetReference>
        </connector>
    </assignments>
    <environments>Default</environments>
    <interviewLabel>Grant Rank ANTIPATTERN {!$Flow.CurrentDateTime}</interviewLabel>
    <label>Grant Rank Nightly ANTIPATTERN</label>
    <loops>
        <name>Rank_Applications</name>
        <label>Rank Applications</label>
        <locationX>182</locationX>
        <locationY>242</locationY>
        <assignNextValueToReference>currentApp</assignNextValueToReference>
        <collectionReference>Get_Applications.records</collectionReference>
        <iterationOrder>Asc</iterationOrder>
        <nextValueConnector>
            <targetReference>Match_Rules</targetReference>
        </nextValueConnector>
    </loops>
    <loops>
        <name>Match_Rules</name>
        <label>Match Rules</label>
        <locationX>314</locationX>
        <locationY>350</locationY>
        <assignNextValueToReference>currentRule</assignNextValueToReference>
        <collectionReference>Get_Rules.records</collectionReference>
        <iterationOrder>Asc</iterationOrder>
        <nextValueConnector>
            <targetReference>Stamp_Application</targetReference>
        </nextValueConnector>
        <noMoreValuesConnector>
            <targetReference>Rank_Applications</targetReference>
        </noMoreValuesConnector>
    </loops>
    <processType>AutoLaunchedFlow</processType>
    <recordLookups>
        <name>Get_Applications</name>
        <label>Get Applications</label>
        <locationX>182</locationX>
        <locationY>134</locationY>
        <filterLogic>and</filterLogic>
        <filters>
            <field>Review_Stage__c</field>
            <operator>EqualTo</operator>
            <value>
                <stringValue>Scored</stringValue>
            </value>
        </filters>
        <getFirstRecordOnly>false</getFirstRecordOnly>
        <object>Grant_Application__c</object>
        <storeOutputAutomatically>true</storeOutputAutomatically>
        <connector>
            <targetReference>Get_Rules</targetReference>
        </connector>
    </recordLookups>
    <recordLookups>
        <name>Get_Rules</name>
        <label>Get Rules</label>
        <locationX>182</locationX>
        <locationY>188</locationY>
        <getFirstRecordOnly>false</getFirstRecordOnly>
        <object>Program_Rule__c</object>
        <storeOutputAutomatically>true</storeOutputAutomatically>
        <connector>
            <targetReference>Rank_Applications</targetReference>
        </connector>
    </recordLookups>
    <runInMode>DefaultMode</runInMode>
    <start>
        <locationX>50</locationX>
        <locationY>50</locationY>
        <connector>
            <targetReference>Get_Applications</targetReference>
        </connector>
        <schedule>
            <frequency>Daily</frequency>
            <startDate>2026-09-06</startDate>
            <startTime>02:00:00.000Z</startTime>
        </schedule>
        <triggerType>Scheduled</triggerType>
    </start>
    <status>Draft</status>
</Flow>
```

### How to read it

- `<loops>` is the Flow field that holds Loop nodes — `loops` is `FlowLoop[]`
  (`api_meta.txt` L68186), and `FlowLoop` extends `FlowNode`, available in API 30.0 and
  later (`api_meta.txt` L70698–70699).
- `assignNextValueToReference` is "The variable that's assigned to the current value in
  the collection before navigating to the target of `nextValueConnector`"
  (`api_meta.txt` L70701–70702). It is still a documented field in the v62/Summer '26
  guide — the loop variable is **not** implicitly the element's own name at the metadata
  layer, even though Flow Builder now creates and names it for you.
- `collectionReference` is "The collection being looped through" (`api_meta.txt` L70704).
  `Get_Applications.records` is the auto-stored output of a `recordLookups` element whose
  `storeOutputAutomatically` is `true` (`api_meta.txt` L71229–71239).
- `iterationOrder` takes only `Asc` ("in the order the values are listed, first to last")
  or `Desc` ("in the reverse order the values are listed, last to first") — `api_meta.txt`
  L70706–70710. Both are defined relative to the *collection's* order, not to any field.
- `nextValueConnector` is "A reference to the next element in the collection";
  `noMoreValuesConnector` is "The element to navigate to when all entries in the collection
  have been iterated through" (`api_meta.txt` L70712–70716). The second one is what this
  flow is missing on its outer loop.
- Governor context: 100 synchronous SOQL queries, 150 DML statements, 10,000 ms
  synchronous CPU time (`apexdev.txt` L19544, L19554, L19579). This flow issues 2 SOQL and
  0 DML — it fails on CPU time alone, which is why "no DML in the loop" is not a
  sufficient review.

---

## 2. The corrected flow — `Grant_Rank_Nightly.flow-meta.xml`

Three changes, in order of leverage:

1. A `SortCollectionProcessor` with `limit` bounds the working set **before** the Loop
   exists — the cheapest fix is always fewer iterations.
2. `Stage_Ranked_Application` mutates the loop variable *and* adds it to
   `applicationsToStamp` in the same Assignment. The mutation alone persists nothing; the
   `Add` is what carries the modified record out of the loop.
3. One `recordUpdates` after the loop, with a `faultConnector`.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>66.0</apiVersion>
    <assignments>
        <name>Stage_Ranked_Application</name>
        <label>Stage Ranked Application</label>
        <locationX>182</locationX>
        <locationY>458</locationY>
        <assignmentItems>
            <assignToReference>rankCounter</assignToReference>
            <operator>Add</operator>
            <value>
                <numberValue>1.0</numberValue>
            </value>
        </assignmentItems>
        <assignmentItems>
            <assignToReference>currentApp.Rank__c</assignToReference>
            <operator>Assign</operator>
            <value>
                <elementReference>rankCounter</elementReference>
            </value>
        </assignmentItems>
        <assignmentItems>
            <assignToReference>currentApp.Review_Stage__c</assignToReference>
            <operator>Assign</operator>
            <value>
                <stringValue>Ranked</stringValue>
            </value>
        </assignmentItems>
        <assignmentItems>
            <assignToReference>currentApp.Reviewed_On__c</assignToReference>
            <operator>Assign</operator>
            <value>
                <elementReference>$Flow.CurrentDateTime</elementReference>
            </value>
        </assignmentItems>
        <assignmentItems>
            <assignToReference>applicationsToStamp</assignToReference>
            <operator>Add</operator>
            <value>
                <elementReference>currentApp</elementReference>
            </value>
        </assignmentItems>
        <connector>
            <targetReference>Rank_Applications</targetReference>
        </connector>
    </assignments>
    <assignments>
        <name>Count_Staged</name>
        <label>Count Staged</label>
        <locationX>182</locationX>
        <locationY>566</locationY>
        <assignmentItems>
            <assignToReference>stagedCount</assignToReference>
            <operator>AssignCount</operator>
            <value>
                <elementReference>applicationsToStamp</elementReference>
            </value>
        </assignmentItems>
        <connector>
            <targetReference>Stamp_Applications</targetReference>
        </connector>
    </assignments>
    <collectionProcessors>
        <name>Top_Applications</name>
        <elementSubtype>SortCollectionProcessor</elementSubtype>
        <label>Top Applications</label>
        <locationX>182</locationX>
        <locationY>242</locationY>
        <collectionProcessorType>SortCollectionProcessor</collectionProcessorType>
        <collectionReference>Get_Applications.records</collectionReference>
        <limit>500</limit>
        <sortOptions>
            <doesPutEmptyStringAndNullFirst>false</doesPutEmptyStringAndNullFirst>
            <sortField>Score__c</sortField>
            <sortOrder>Desc</sortOrder>
        </sortOptions>
        <connector>
            <targetReference>Rank_Applications</targetReference>
        </connector>
    </collectionProcessors>
    <environments>Default</environments>
    <interviewLabel>Grant Rank Nightly {!$Flow.CurrentDateTime}</interviewLabel>
    <label>Grant Rank Nightly</label>
    <loops>
        <name>Rank_Applications</name>
        <label>Rank Applications</label>
        <locationX>182</locationX>
        <locationY>350</locationY>
        <assignNextValueToReference>currentApp</assignNextValueToReference>
        <collectionReference>Top_Applications</collectionReference>
        <iterationOrder>Asc</iterationOrder>
        <nextValueConnector>
            <targetReference>Stage_Ranked_Application</targetReference>
        </nextValueConnector>
        <noMoreValuesConnector>
            <targetReference>Count_Staged</targetReference>
        </noMoreValuesConnector>
    </loops>
    <processType>AutoLaunchedFlow</processType>
    <recordCreates>
        <name>Log_Loop_Failure</name>
        <label>Log Loop Failure</label>
        <locationX>380</locationX>
        <locationY>674</locationY>
        <inputAssignments>
            <field>Source__c</field>
            <value>
                <stringValue>Grant_Rank_Nightly.Stamp_Applications</stringValue>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Severity__c</field>
            <value>
                <stringValue>Error</stringValue>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Message__c</field>
            <value>
                <elementReference>$Flow.FaultMessage</elementReference>
            </value>
        </inputAssignments>
        <object>Application_Log__c</object>
        <storeOutputAutomatically>true</storeOutputAutomatically>
    </recordCreates>
    <recordLookups>
        <name>Get_Applications</name>
        <label>Get Applications</label>
        <locationX>182</locationX>
        <locationY>134</locationY>
        <faultConnector>
            <targetReference>Log_Loop_Failure</targetReference>
        </faultConnector>
        <filterLogic>and</filterLogic>
        <filters>
            <field>Review_Stage__c</field>
            <operator>EqualTo</operator>
            <value>
                <stringValue>Scored</stringValue>
            </value>
        </filters>
        <getFirstRecordOnly>false</getFirstRecordOnly>
        <limit>
            <numberValue>2000.0</numberValue>
        </limit>
        <object>Grant_Application__c</object>
        <sortField>Score__c</sortField>
        <sortOrder>Desc</sortOrder>
        <storeOutputAutomatically>true</storeOutputAutomatically>
        <connector>
            <targetReference>Top_Applications</targetReference>
        </connector>
    </recordLookups>
    <recordUpdates>
        <name>Stamp_Applications</name>
        <label>Stamp Applications</label>
        <locationX>182</locationX>
        <locationY>674</locationY>
        <faultConnector>
            <targetReference>Log_Loop_Failure</targetReference>
        </faultConnector>
        <inputReference>applicationsToStamp</inputReference>
    </recordUpdates>
    <runInMode>DefaultMode</runInMode>
    <start>
        <locationX>50</locationX>
        <locationY>50</locationY>
        <connector>
            <targetReference>Get_Applications</targetReference>
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
        <name>applicationsToStamp</name>
        <dataType>SObject</dataType>
        <isCollection>true</isCollection>
        <isInput>false</isInput>
        <isOutput>true</isOutput>
        <objectType>Grant_Application__c</objectType>
    </variables>
    <variables>
        <name>rankCounter</name>
        <dataType>Number</dataType>
        <isCollection>false</isCollection>
        <isInput>false</isInput>
        <isOutput>false</isOutput>
        <scale>0</scale>
        <value>
            <numberValue>0.0</numberValue>
        </value>
    </variables>
    <variables>
        <name>stagedCount</name>
        <dataType>Number</dataType>
        <isCollection>false</isCollection>
        <isInput>false</isInput>
        <isOutput>true</isOutput>
        <scale>0</scale>
    </variables>
</Flow>
```

### How to read it

- **The Assignment does two jobs and both are required.** `currentApp.Rank__c` etc. write
  into the variable named by `assignNextValueToReference`; the last `assignmentItems`
  entry uses `Add` on `applicationsToStamp`, which for a collection variable "appends the
  value to the end of the collection" (`api_meta.txt` L69800–69804). The guide describes
  `assignNextValueToReference` as the variable *assigned to* the current value; it
  documents no write-back path from that variable into `collectionReference`. Stage the
  record or lose the edit. **UNVERIFIED (2026-09-05):** whether an in-loop write to the
  loop variable additionally mutates the item still held in the source collection is not
  stated in `api_meta.txt` or `apexdev.txt`. The staged-collection construction above is
  correct either way, which is why it is the one to build.
- **`Add` on a Number is arithmetic, on a collection it is append.** The same
  `FlowAssignmentOperator` value means "adds the value to the variable" for number and
  currency, "appends the value to the end of the string" for string, and "appends the
  value to the end of the collection" for a collection variable (`api_meta.txt`
  L69787–69806). `rankCounter` and `applicationsToStamp` in the same Assignment both use
  `Add` and do different things. `Add` is explicitly **not supported** when the target is
  `boolean`, `dateTime`, or `sObject` (`api_meta.txt` L69805–69806).
- **`AssignCount` is how you count a collection without a loop.** "Supported only when the
  value is a collection variable or the `$Flow.ActiveStages` global variable. Counts the
  number of stages or items in the collection… Corresponds to *equals count* in the user
  interface. This operator is available in API version 43.0 and later" (`api_meta.txt`
  L69826–69830). A Loop that exists only to increment a counter is a Loop that should be
  one Assignment.
- **Sort before the Loop, and cap it.** `collectionProcessorType` is one of
  `SortCollectionProcessor` (API 50.0+), `RecommendationMapCollectionProcessor` (API 53.0+)
  or `FilterCollectionProcessor` (API 53.0+) — `api_meta.txt` L69934–69941. `limit` is
  "The maximum number of records to include in the generated collection. There's no
  default value. All items of the collection are kept if it's greater than the size of the
  collection. If `sortField` and `sortOrder` are also specified, the records are sorted
  before the limit takes effect… available in API version 51.0 and later" (`api_meta.txt`
  L69961–69967). Sort-then-limit is the documented order, so `limit` really is *top N*,
  not *first N encountered*.
- **`sortOptions` carries the sort, not the processor.** `FlowCollectionSortOption` holds
  `sortField`, `sortOrder` (`Asc`/`Desc`) and `doesPutEmptyStringAndNullFirst` (default
  `false`); `sortField` "Required for record collections and collections of Apex-defined
  variables" and "If the collection is a primitive data type, such as a list of string or
  integer values, `sortField` isn't supported" (`api_meta.txt` L69982–69996). Available in
  API 51.0 and later.
- **The Get Records also sorts and caps.** `recordLookups` has its own `sortField` /
  `sortOrder` (API 25.0+, `api_meta.txt` L71209–71226) and its own `limit`, whose "Valid
  values are between 2 and 20,000. Supported only when `getFirstRecordOnly` is `false`…
  available in API version 63.0 and later" (`api_meta.txt` L71180–71187). Note the shape
  difference: the `recordLookups` `limit` is a `FlowElementReferenceOrValue` (an element,
  hence `<numberValue>`), while the `collectionProcessors` `limit` is a bare `int`.
  Pushing the cut to the database is strictly cheaper than pushing it to a processor,
  which is strictly cheaper than pushing it to a Loop.
- **`elementSubtype` is echoed, not authored.** `FlowNode.elementSubtype` is documented as
  "Reserved for internal use" (`api_meta.txt` L70745). Retrieved collection processors
  carry it and it round-trips, so it is reproduced here; do not invent values for it, and
  do not treat its absence as a defect. `collectionProcessorType` is the load-bearing
  field.
- **Fault paths.** `recordLookups` and `recordUpdates` both define `faultConnector`
  ("Specifies which node to execute if the attempt … results in an error" —
  `api_meta.txt` L71114–71117, L71277–71279). `FlowLoop` has **no** `faultConnector` field
  at all — a Loop cannot fault, so the fault path belongs on the elements around it. Full
  treatment is `flow/fault-handling`.

---

## 3. Nested loop replaced by a Filter processor — `Grant_Assign_Reviewers.flow-meta.xml`

The anti-pattern in §1 nests a loop over `Program_Rule__c` inside a loop over
`Grant_Application__c` purely to find the rules that apply to the current application. A
`FilterCollectionProcessor` does that in one element per outer iteration instead of *m*.
The outer loop's variable is a flow-scoped resource, so the filter's `formula` can
reference it — that is what makes the substitution legal.

The same flow then uses a Map processor to build a `Review_Assignment__c` collection from
the applications, and creates it with a single `recordCreates`.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>66.0</apiVersion>
    <assignments>
        <name>Stage_Eligible</name>
        <label>Stage Eligible</label>
        <locationX>182</locationX>
        <locationY>566</locationY>
        <assignmentItems>
            <assignToReference>eligibleApplications</assignToReference>
            <operator>Add</operator>
            <value>
                <elementReference>currentApp</elementReference>
            </value>
        </assignmentItems>
        <connector>
            <targetReference>Assign_Eligible_Applications</targetReference>
        </connector>
    </assignments>
    <collectionProcessors>
        <name>Rules_For_This_Application</name>
        <elementSubtype>FilterCollectionProcessor</elementSubtype>
        <label>Rules For This Application</label>
        <locationX>182</locationX>
        <locationY>350</locationY>
        <assignNextValueToReference>currentRule</assignNextValueToReference>
        <collectionProcessorType>FilterCollectionProcessor</collectionProcessorType>
        <collectionReference>Get_Rules.records</collectionReference>
        <conditionLogic>Formula</conditionLogic>
        <formula>AND({!currentRule.Is_Active__c}, {!currentRule.Program_Code__c} = {!currentApp.Program_Code__c}, {!currentApp.Score__c} &gt;= {!currentRule.Minimum_Score__c})</formula>
        <connector>
            <targetReference>Any_Rule_Matched</targetReference>
        </connector>
    </collectionProcessors>
    <collectionProcessors>
        <name>Map_Review_Assignments</name>
        <elementSubtype>RecommendationMapCollectionProcessor</elementSubtype>
        <label>Map Review Assignments</label>
        <locationX>182</locationX>
        <locationY>782</locationY>
        <assignNextValueToReference>mapSourceApp</assignNextValueToReference>
        <collectionProcessorType>RecommendationMapCollectionProcessor</collectionProcessorType>
        <collectionReference>eligibleApplications</collectionReference>
        <mapItems>
            <assignToFieldReference>Map_Review_Assignments.Application__c</assignToFieldReference>
            <operator>Assign</operator>
            <value>
                <elementReference>mapSourceApp.Id</elementReference>
            </value>
        </mapItems>
        <mapItems>
            <assignToFieldReference>Map_Review_Assignments.Reviewer_Queue__c</assignToFieldReference>
            <operator>Assign</operator>
            <value>
                <elementReference>mapSourceApp.Program_Code__c</elementReference>
            </value>
        </mapItems>
        <mapItems>
            <assignToFieldReference>Map_Review_Assignments.Priority__c</assignToFieldReference>
            <operator>Assign</operator>
            <value>
                <elementReference>mapSourceApp.Score__c</elementReference>
            </value>
        </mapItems>
        <outputSObjectType>Review_Assignment__c</outputSObjectType>
        <connector>
            <targetReference>Create_Review_Assignments</targetReference>
        </connector>
    </collectionProcessors>
    <decisions>
        <name>Any_Rule_Matched</name>
        <label>Any Rule Matched?</label>
        <locationX>182</locationX>
        <locationY>458</locationY>
        <defaultConnector>
            <targetReference>Assign_Eligible_Applications</targetReference>
        </defaultConnector>
        <defaultConnectorLabel>No Matching Rule</defaultConnectorLabel>
        <rules>
            <name>Rule_Matched</name>
            <conditionLogic>and</conditionLogic>
            <conditions>
                <leftValueReference>Rules_For_This_Application</leftValueReference>
                <operator>IsEmpty</operator>
                <rightValue>
                    <booleanValue>false</booleanValue>
                </rightValue>
            </conditions>
            <connector>
                <targetReference>Stage_Eligible</targetReference>
            </connector>
            <label>Rule Matched</label>
        </rules>
    </decisions>
    <environments>Default</environments>
    <interviewLabel>Grant Assign Reviewers {!$Flow.CurrentDateTime}</interviewLabel>
    <label>Grant Assign Reviewers</label>
    <loops>
        <name>Assign_Eligible_Applications</name>
        <label>Assign Eligible Applications</label>
        <locationX>182</locationX>
        <locationY>242</locationY>
        <assignNextValueToReference>currentApp</assignNextValueToReference>
        <collectionReference>Get_Applications.records</collectionReference>
        <iterationOrder>Asc</iterationOrder>
        <nextValueConnector>
            <targetReference>Rules_For_This_Application</targetReference>
        </nextValueConnector>
        <noMoreValuesConnector>
            <targetReference>Map_Review_Assignments</targetReference>
        </noMoreValuesConnector>
    </loops>
    <processType>AutoLaunchedFlow</processType>
    <recordCreates>
        <name>Create_Review_Assignments</name>
        <label>Create Review Assignments</label>
        <locationX>182</locationX>
        <locationY>890</locationY>
        <faultConnector>
            <targetReference>Log_Map_Failure</targetReference>
        </faultConnector>
        <inputReference>Map_Review_Assignments</inputReference>
    </recordCreates>
    <recordCreates>
        <name>Log_Map_Failure</name>
        <label>Log Map Failure</label>
        <locationX>380</locationX>
        <locationY>890</locationY>
        <inputAssignments>
            <field>Source__c</field>
            <value>
                <stringValue>Grant_Assign_Reviewers.Create_Review_Assignments</stringValue>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Severity__c</field>
            <value>
                <stringValue>Error</stringValue>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Message__c</field>
            <value>
                <elementReference>$Flow.FaultMessage</elementReference>
            </value>
        </inputAssignments>
        <object>Application_Log__c</object>
        <storeOutputAutomatically>true</storeOutputAutomatically>
    </recordCreates>
    <recordLookups>
        <name>Get_Applications</name>
        <label>Get Applications</label>
        <locationX>182</locationX>
        <locationY>134</locationY>
        <filterLogic>and</filterLogic>
        <filters>
            <field>Review_Stage__c</field>
            <operator>EqualTo</operator>
            <value>
                <stringValue>Ranked</stringValue>
            </value>
        </filters>
        <getFirstRecordOnly>false</getFirstRecordOnly>
        <object>Grant_Application__c</object>
        <sortField>Rank__c</sortField>
        <sortOrder>Asc</sortOrder>
        <storeOutputAutomatically>true</storeOutputAutomatically>
        <connector>
            <targetReference>Get_Rules</targetReference>
        </connector>
    </recordLookups>
    <recordLookups>
        <name>Get_Rules</name>
        <label>Get Rules</label>
        <locationX>182</locationX>
        <locationY>188</locationY>
        <filterLogic>and</filterLogic>
        <filters>
            <field>Is_Active__c</field>
            <operator>EqualTo</operator>
            <value>
                <booleanValue>true</booleanValue>
            </value>
        </filters>
        <getFirstRecordOnly>false</getFirstRecordOnly>
        <object>Program_Rule__c</object>
        <storeOutputAutomatically>true</storeOutputAutomatically>
        <connector>
            <targetReference>Assign_Eligible_Applications</targetReference>
        </connector>
    </recordLookups>
    <runInMode>DefaultMode</runInMode>
    <start>
        <locationX>50</locationX>
        <locationY>50</locationY>
        <connector>
            <targetReference>Get_Applications</targetReference>
        </connector>
        <schedule>
            <frequency>Daily</frequency>
            <startDate>2026-09-06</startDate>
            <startTime>03:00:00.000Z</startTime>
        </schedule>
        <triggerType>Scheduled</triggerType>
    </start>
    <status>Draft</status>
    <variables>
        <name>eligibleApplications</name>
        <dataType>SObject</dataType>
        <isCollection>true</isCollection>
        <isInput>false</isInput>
        <isOutput>true</isOutput>
        <objectType>Grant_Application__c</objectType>
    </variables>
</Flow>
```

### How to read it

- **`conditionLogic` decides which of `formula` / `conditions` is live.**
  `FlowCollectionProcessor.conditionLogic` accepts `And`, `Or`, custom logic such as
  `(1 AND (2 OR 3))`, or `Formula` (`api_meta.txt` L69946–69953). `formula` is "The formula
  expression that filters the input collection. If the formula evaluates to true, the
  record is added to the output collection" (`api_meta.txt` L69957–69960); `conditions` is
  "An array of conditions for the input collection" (`api_meta.txt` L69954). They are two
  routes to the same output. Populating both leaves the element's intent ambiguous —
  `scripts/check_flow_loop_element_patterns.py` flags it, and Gotcha 11 explains why the
  `conditions` route silently wins nothing when `conditionLogic` says `Formula`.
- **A filter with a formula needs `assignNextValueToReference`.** The formula has to name
  the item under test; `assignNextValueToReference` is "The name of the variable that's
  assigned to the next value of the collection" (`api_meta.txt` L69931–69933). Here that
  is `currentRule`. `currentApp` — the *outer loop's* variable — is also legal inside the
  formula because Flow resources are flow-scoped, not block-scoped. That scoping is the
  same property that makes Gotcha 2 a hazard downstream, used deliberately here.
- **The Map processor's enum name is a trap.** The Flow Builder element is called Map; the
  metadata enum is `RecommendationMapCollectionProcessor`, available in API 53.0 and later
  (`api_meta.txt` L69937–69939). There is no `MapCollectionProcessor` value. Hand-authored
  XML that guesses the obvious name does not deploy.
- **Map output is a new collection of a new type.** `outputSObjectType` is "The sObject
  type of the output collection" and `mapItems` is `FlowCollectionMapItem[]`, "The rules to
  map each field of the collection variable" (`api_meta.txt` L69977–69980).
  `FlowCollectionMapItem` requires all three of `assignToFieldReference`, `operator` (a
  `FlowAssignmentOperator`) and `value` (`api_meta.txt` L70161–70172, API 51.0 and later).
  The processor's own name is then usable as the resulting collection —
  `Create_Review_Assignments` takes `inputReference` = `Map_Review_Assignments`.
  **UNVERIFIED (2026-09-05):** `api_meta.txt` documents every field of
  `FlowCollectionProcessor` and `FlowCollectionMapItem` but ships **no** sample XML for
  either, so the exact `assignToFieldReference` reference syntax
  (`<processorName>.<Field__c>`) and the use of the processor name as a downstream
  collection reference are reproduced from the shape Flow Builder emits, not from the
  guide. Retrieve one Builder-authored Map element into your project before trusting the
  literal strings.
- **The Decision reads the processor's output, not a loop.** `IsEmpty` is a valid
  `FlowComparisonOperator` from API 61.0 and later (`api_meta.txt` L74210). That is what
  replaces the inner loop's "did anything match?" bookkeeping.
- **`&gt;` is the escaped `>` in the formula.** XML content must escape `<` and `&`; `>` is
  escaped here for symmetry with what the platform emits. A raw `>` also parses.

---

## 4. `FlowTest` — `Grant_Rank_Nightly_StagesAndCommits.flowtest-meta.xml`

`FlowTest` components have the suffix `.flowtest`, live in the `flowtests` folder, and are
available in API version 55.0 and later (`api_meta.txt` L73961–73975). They cover
record-triggered, autolaunched, and Data Cloud-triggered flows — screen flows are not
testable this way.

`testPoints.elementApiName` accepts only `Start` and `Finish` (`api_meta.txt`
L74146–74152), so a flow test cannot assert *inside* a loop. What it can do — and what
this one does — is assert on the **flow-scoped variables the loop left behind**, which is
exactly the loop-variable scoping that Gotcha 2 warns about, used as a test surface.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<FlowTest xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Scheduled rank pass. Asserts the loop staged records into applicationsToStamp, that AssignCount saw them, and that the single post-loop Update did not fault.</description>
    <flowApiName>Grant_Rank_Nightly</flowApiName>
    <label>Nightly rank staged and committed once</label>
    <testPoints>
        <elementApiName>Start</elementApiName>
        <parameters>
            <leftValueReference>$Record</leftValueReference>
            <type>InputTriggeringRecordInitial</type>
            <value>
                <sobjectValue>{&quot;Name&quot;:&quot;GA-4471&quot;,&quot;Score__c&quot;:88,&quot;Program_Code__c&quot;:&quot;STEM-A&quot;,&quot;Review_Stage__c&quot;:&quot;Scored&quot;}</sobjectValue>
            </value>
        </parameters>
    </testPoints>
    <testPoints>
        <assertions>
            <conditions>
                <leftValueReference>applicationsToStamp</leftValueReference>
                <operator>IsEmpty</operator>
                <rightValue>
                    <booleanValue>false</booleanValue>
                </rightValue>
            </conditions>
            <errorMessage>The loop staged nothing. Editing currentApp inside the loop does not persist; the Add into applicationsToStamp is what carries the edit out.</errorMessage>
        </assertions>
        <assertions>
            <conditions>
                <leftValueReference>stagedCount</leftValueReference>
                <operator>GreaterThan</operator>
                <rightValue>
                    <numberValue>0.0</numberValue>
                </rightValue>
            </conditions>
            <errorMessage>AssignCount returned zero, so the loop ran zero iterations: the collection reached noMoreValuesConnector on its first evaluation.</errorMessage>
        </assertions>
        <assertions>
            <conditions>
                <leftValueReference>Stamp_Applications</leftValueReference>
                <operator>HasError</operator>
                <rightValue>
                    <booleanValue>false</booleanValue>
                </rightValue>
            </conditions>
            <errorMessage>The post-loop Update Records faulted. One bad row fails the whole staged collection; check Application_Log__c.</errorMessage>
        </assertions>
        <elementApiName>Finish</elementApiName>
    </testPoints>
    <testType>WithAssertion</testType>
</FlowTest>
```

### How to read it

- `flowApiName` (required) and `label` (required) name the flow under test; `testPoints`
  is `FlowTestPoint[]`, "Salesforce evaluates each test point in the order that it's
  listed" (`api_meta.txt` L74137–74145).
- `testType` has one possible value, `WithAssertion` — "The automated comparison of the
  actual flow outcome with the user-defined expected outcome that assertions define" —
  available in API version 66.0 and later (`api_meta.txt` L74060–74066).
- `HasError` as a `FlowComparisonOperator` is available in API version 64.0 and later, and
  `IsEmpty` in 61.0 and later (`api_meta.txt` L74196, L74210). `HasError` against an
  element name is how you assert a fault path did *not* fire.
- The `Start` test point's `sobjectValue` is a JSON string, so its quotes are
  XML-escaped as `&quot;` — the guide's own sample does the same (`api_meta.txt`
  L74327–74334).

---

## package.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Grant_Application__c</members>
        <members>Program_Rule__c</members>
        <members>Review_Assignment__c</members>
        <members>Application_Log__c</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>Grant_Rank_Nightly</members>
        <members>Grant_Assign_Reviewers</members>
        <name>Flow</name>
    </types>
    <types>
        <members>Grant_Rank_Nightly_StagesAndCommits</members>
        <name>FlowTest</name>
    </types>
    <version>66.0</version>
</Package>
```

`Grant_Rank_Nightly_ANTIPATTERN` is deliberately absent. It is a checker fixture, not a
deployable.

## Deploy order

```bash
# 0. Lint the loops before anything reaches an org.
python3 skills/flow/flow-loop-element-patterns/scripts/check_flow_loop_element_patterns.py \
  --manifest-dir force-app/main/default

# 1. Objects and fields first — a flow referencing a missing field fails validation,
#    and the failure names the flow, not the field.
sf project deploy start --source-dir force-app/main/default/objects --target-org myorg

# 2. Flows next, still Draft. Deploying Draft lets you debug before anything is scheduled.
sf project deploy start --source-dir force-app/main/default/flows --target-org myorg

# 3. FlowTests last — they reference the flow by flowApiName and fail to deploy without it.
sf project deploy start --source-dir force-app/main/default/flowtests --target-org myorg

# Round-trip an existing loop-bearing flow to compare against what Builder emits:
sf project retrieve start --metadata Flow:Grant_Rank_Nightly --target-org myorg
```

Activation is a separate, deliberate step: `<status>` accepts `Active`, `Draft` (shown as
Inactive in the UI), `Obsolete`, or `InvalidDraft` (`api_meta.txt` L68417–68421). Ship
`Draft`, debug, then activate.

## Verification

**1. The loop actually staged, and the DML actually ran once.** After a scheduled run,
count what the flow claims to have written:

```soql
SELECT COUNT(Id), Review_Stage__c
FROM Grant_Application__c
WHERE Reviewed_On__c = TODAY
GROUP BY Review_Stage__c
```

If `Ranked` is 0 while the applications still sit at `Scored`, the loop iterated and the
edits were dropped — the `Add` into the staged collection is missing, or the post-loop
`recordUpdates` is pointed at the wrong variable. That is the signature failure of this
skill and it produces no error anywhere.

**2. Confirm the iteration count and the transaction cost from the debug log.** Set the
**Workflow** category to `FINER` or above (Setup → Debug Logs) and run the flow, then grep
the log:

```bash
grep -E "FLOW_LOOP_DETAIL|FLOW_BULK_ELEMENT_DETAIL|FLOW_INTERVIEW_FINISHED_LIMIT_USAGE" \
  apex-debug.log
```

- `FLOW_LOOP_DETAIL` logs "Interview ID, index, and value. The index is the position in
  the collection variable for the item that the loop is operating on" at Workflow `FINER`
  and above (`apexdev.txt` L38843–38845). Counting these lines gives the real iteration
  count — the number your `body_elements × iterations` estimate was guessing at.
- `FLOW_BULK_ELEMENT_DETAIL` logs "Interview ID, element type, element name, number of
  records" at `FINER` and above, and `FLOW_BULK_ELEMENT_END` adds execution time
  (`apexdev.txt` L38724–38729). One `recordUpdates` line with a record count equal to the
  loop's iteration count is proof the collect-then-DML shape held.
- `FLOW_INTERVIEW_FINISHED_LIMIT_USAGE` reports usage toward SOQL queries, SOQL query rows,
  DML statements, DML rows, CPU time in ms, and heap at interview finish (`apexdev.txt`
  L38812–38830). CPU time is the number that matters for a loop-heavy flow — against the
  10,000 ms synchronous / 60,000 ms asynchronous ceiling (`apexdev.txt` L19579).

There is no debug-log event, and no limit row, for "executed elements". That absence is
the point of the negative result at the top of this file.
