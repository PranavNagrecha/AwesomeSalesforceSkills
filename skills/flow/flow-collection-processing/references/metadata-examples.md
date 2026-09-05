# Metadata Examples — Flow Collection Processing

A complete, parseable record-triggered flow that does all of its collection work with
**collection processors and a Transform — no Loop element at all** — plus the `FlowTest` that
asserts on the counts those processors produce, the `package.xml`, the deploy order, and the
verification step.

Every element name, enum value and version floor below is cited to the Metadata API Developer
Guide text (`api_meta.txt`, Summer '26 / v62 extract of
<https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf>). Where the guide
documents a field but ships no sample XML for it, the claim carries an explicit
`UNVERIFIED (2026-09-05)` marker beside it rather than in a footnote.

The record-triggered skeleton this adapts is `templates/flow/RecordTriggered_Skeleton.flow-meta.xml`;
the fault-route convention is `templates/flow/FaultPath_Template.md`. Read them rather than
re-deriving the `<start>` block.

---

## 0. The schema this flow assumes

Freight rating: a quote fans out into legs, each leg is priced, the cheapest few become
recommendations. This object set is not used by any sibling flow skill, so the XML below can be
deployed into a scratch org next to theirs without a name collision.

| Object | Fields used here |
|---|---|
| `Freight_Quote__c` | `Name`, `Status__c` (picklist: `Draft`, `Rating`, `Quoted`) |
| `Quote_Leg__c` | `Freight_Quote__c` (Master-Detail or Lookup), `Leg_Sequence__c` (Number), `Origin_Zone__c` (Text), `Destination_Zone__c` (Text), `Weight_Kg__c` (Number), `Quoted_Cost__c` (Currency), `Is_Serviceable__c` (Checkbox), `Carrier_Code__c` (Text), `Rate_Status__c` (picklist: `Unrated`, `Recommended`) |
| `Rate_Recommendation__c` | `Freight_Quote__c` (Lookup), `Quote_Leg__c` (Lookup), `Carrier_Code__c` (Text), `Recommended_Cost__c` (Currency), `Quote_Total_At_Rating__c` (Currency) |
| `Application_Log__c` | `Message__c` (Long Text), `Related_Record_Id__c` (Text 18), `Severity__c` (picklist), `Source__c` (Text) |

`Application_Log__c` is the shared fault-log object the other `flow/` skills also write to; keep
one definition per org.

---

## 1. `Freight_Quote_Rate_Legs.flow-meta.xml`

Six collection operations, zero loops: Filter (conditions) → Filter (formula) → Transform (Sum) →
Sort (with `limit`, i.e. top N) → Map (new type) → Map (same type, for a loop-free field stamp) →
Assignment set algebra → Assignment `AssignCount` → two collection DMLs.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>63.0</apiVersion>
    <assignments>
        <name>Stage_Collection_Sets</name>
        <label>Stage Collection Sets</label>
        <locationX>50</locationX>
        <locationY>950</locationY>
        <assignmentItems>
            <assignToReference>legsForReview</assignToReference>
            <operator>Add</operator>
            <value>
                <elementReference>allLegs</elementReference>
            </value>
        </assignmentItems>
        <assignmentItems>
            <assignToReference>legsForReview</assignToReference>
            <operator>RemoveAll</operator>
            <value>
                <elementReference>Filter_Serviceable_Legs</elementReference>
            </value>
        </assignmentItems>
        <assignmentItems>
            <assignToReference>legsCheapAndPriority</assignToReference>
            <operator>Add</operator>
            <value>
                <elementReference>Sort_Cheapest_Legs</elementReference>
            </value>
        </assignmentItems>
        <assignmentItems>
            <assignToReference>legsCheapAndPriority</assignToReference>
            <operator>RemoveUncommon</operator>
            <value>
                <elementReference>Filter_Priority_Legs</elementReference>
            </value>
        </assignmentItems>
        <connector>
            <targetReference>Count_Collections</targetReference>
        </connector>
    </assignments>
    <assignments>
        <name>Count_Collections</name>
        <label>Count Collections</label>
        <locationX>50</locationX>
        <locationY>1058</locationY>
        <assignmentItems>
            <assignToReference>serviceableLegCount</assignToReference>
            <operator>AssignCount</operator>
            <value>
                <elementReference>Filter_Serviceable_Legs</elementReference>
            </value>
        </assignmentItems>
        <assignmentItems>
            <assignToReference>reviewLegCount</assignToReference>
            <operator>AssignCount</operator>
            <value>
                <elementReference>legsForReview</elementReference>
            </value>
        </assignmentItems>
        <connector>
            <targetReference>Create_Recommendations</targetReference>
        </connector>
    </assignments>
    <collectionProcessors>
        <name>Filter_Serviceable_Legs</name>
        <label>Filter Serviceable Legs</label>
        <locationX>50</locationX>
        <locationY>266</locationY>
        <assignNextValueToReference>currentServiceableLeg</assignNextValueToReference>
        <collectionProcessorType>FilterCollectionProcessor</collectionProcessorType>
        <collectionReference>allLegs</collectionReference>
        <conditionLogic>And</conditionLogic>
        <conditions>
            <leftValueReference>currentServiceableLeg.Is_Serviceable__c</leftValueReference>
            <operator>EqualTo</operator>
            <rightValue>
                <booleanValue>true</booleanValue>
            </rightValue>
        </conditions>
        <conditions>
            <leftValueReference>currentServiceableLeg.Weight_Kg__c</leftValueReference>
            <operator>GreaterThan</operator>
            <rightValue>
                <numberValue>0.0</numberValue>
            </rightValue>
        </conditions>
        <connector>
            <targetReference>Filter_Priority_Legs</targetReference>
        </connector>
    </collectionProcessors>
    <collectionProcessors>
        <name>Filter_Priority_Legs</name>
        <label>Filter Priority Legs</label>
        <locationX>50</locationX>
        <locationY>374</locationY>
        <assignNextValueToReference>currentPriorityLeg</assignNextValueToReference>
        <collectionProcessorType>FilterCollectionProcessor</collectionProcessorType>
        <collectionReference>Filter_Serviceable_Legs</collectionReference>
        <conditionLogic>Formula</conditionLogic>
        <formula>OR({!currentPriorityLeg.Weight_Kg__c} &gt;= 500, {!currentPriorityLeg.Destination_Zone__c} = "INTL")</formula>
        <connector>
            <targetReference>Sum_Quoted_Cost</targetReference>
        </connector>
    </collectionProcessors>
    <collectionProcessors>
        <name>Sort_Cheapest_Legs</name>
        <label>Sort Cheapest Legs</label>
        <locationX>50</locationX>
        <locationY>590</locationY>
        <collectionProcessorType>SortCollectionProcessor</collectionProcessorType>
        <collectionReference>Filter_Serviceable_Legs</collectionReference>
        <limit>3</limit>
        <sortOptions>
            <doesPutEmptyStringAndNullFirst>false</doesPutEmptyStringAndNullFirst>
            <sortField>Quoted_Cost__c</sortField>
            <sortOrder>Asc</sortOrder>
        </sortOptions>
        <connector>
            <targetReference>Map_Rate_Recommendations</targetReference>
        </connector>
    </collectionProcessors>
    <collectionProcessors>
        <name>Map_Rate_Recommendations</name>
        <label>Map Rate Recommendations</label>
        <locationX>50</locationX>
        <locationY>698</locationY>
        <assignNextValueToReference>currentTopLeg</assignNextValueToReference>
        <collectionProcessorType>RecommendationMapCollectionProcessor</collectionProcessorType>
        <collectionReference>Sort_Cheapest_Legs</collectionReference>
        <outputSObjectType>Rate_Recommendation__c</outputSObjectType>
        <mapItems>
            <assignToFieldReference>Map_Rate_Recommendations.Freight_Quote__c</assignToFieldReference>
            <operator>Assign</operator>
            <value>
                <elementReference>$Record.Id</elementReference>
            </value>
        </mapItems>
        <mapItems>
            <assignToFieldReference>Map_Rate_Recommendations.Quote_Leg__c</assignToFieldReference>
            <operator>Assign</operator>
            <value>
                <elementReference>currentTopLeg.Id</elementReference>
            </value>
        </mapItems>
        <mapItems>
            <assignToFieldReference>Map_Rate_Recommendations.Carrier_Code__c</assignToFieldReference>
            <operator>Assign</operator>
            <value>
                <elementReference>currentTopLeg.Carrier_Code__c</elementReference>
            </value>
        </mapItems>
        <mapItems>
            <assignToFieldReference>Map_Rate_Recommendations.Recommended_Cost__c</assignToFieldReference>
            <operator>Assign</operator>
            <value>
                <elementReference>currentTopLeg.Quoted_Cost__c</elementReference>
            </value>
        </mapItems>
        <mapItems>
            <assignToFieldReference>Map_Rate_Recommendations.Quote_Total_At_Rating__c</assignToFieldReference>
            <operator>Assign</operator>
            <value>
                <elementReference>Sum_Quoted_Cost</elementReference>
            </value>
        </mapItems>
        <connector>
            <targetReference>Map_Leg_Stamps</targetReference>
        </connector>
    </collectionProcessors>
    <collectionProcessors>
        <name>Map_Leg_Stamps</name>
        <label>Map Leg Stamps</label>
        <locationX>50</locationX>
        <locationY>806</locationY>
        <assignNextValueToReference>currentStampLeg</assignNextValueToReference>
        <collectionProcessorType>RecommendationMapCollectionProcessor</collectionProcessorType>
        <collectionReference>Sort_Cheapest_Legs</collectionReference>
        <outputSObjectType>Quote_Leg__c</outputSObjectType>
        <mapItems>
            <assignToFieldReference>Map_Leg_Stamps.Id</assignToFieldReference>
            <operator>Assign</operator>
            <value>
                <elementReference>currentStampLeg.Id</elementReference>
            </value>
        </mapItems>
        <mapItems>
            <assignToFieldReference>Map_Leg_Stamps.Rate_Status__c</assignToFieldReference>
            <operator>Assign</operator>
            <value>
                <stringValue>Recommended</stringValue>
            </value>
        </mapItems>
        <connector>
            <targetReference>Stage_Collection_Sets</targetReference>
        </connector>
    </collectionProcessors>
    <description>Rates the legs of a freight quote with collection processors only: Filter (conditions), Filter (formula), Sum transform, Sort with limit, and two Map processors. No Loop element. Hand-authored against Metadata API Developer Guide v63.0.</description>
    <environments>Default</environments>
    <interviewLabel>Freight Quote Rate Legs {!$Flow.CurrentDateTime}</interviewLabel>
    <label>Freight Quote Rate Legs</label>
    <processType>AutoLaunchedFlow</processType>
    <recordCreates>
        <name>Create_Recommendations</name>
        <label>Create Recommendations</label>
        <locationX>50</locationX>
        <locationY>1166</locationY>
        <connector>
            <targetReference>Update_Leg_Stamps</targetReference>
        </connector>
        <faultConnector>
            <targetReference>Log_Rating_Fault</targetReference>
        </faultConnector>
        <inputReference>Map_Rate_Recommendations</inputReference>
    </recordCreates>
    <recordCreates>
        <name>Log_Rating_Fault</name>
        <label>Log Rating Fault</label>
        <locationX>314</locationX>
        <locationY>1166</locationY>
        <inputAssignments>
            <field>Message__c</field>
            <value>
                <elementReference>$Flow.FaultMessage</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Related_Record_Id__c</field>
            <value>
                <elementReference>$Record.Id</elementReference>
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
                <stringValue>Freight_Quote_Rate_Legs</stringValue>
            </value>
        </inputAssignments>
        <object>Application_Log__c</object>
        <storeOutputAutomatically>true</storeOutputAutomatically>
    </recordCreates>
    <recordLookups>
        <name>Get_Quote_Legs</name>
        <label>Get Quote Legs</label>
        <locationX>50</locationX>
        <locationY>158</locationY>
        <connector>
            <targetReference>Filter_Serviceable_Legs</targetReference>
        </connector>
        <faultConnector>
            <targetReference>Log_Rating_Fault</targetReference>
        </faultConnector>
        <filterLogic>and</filterLogic>
        <filters>
            <field>Freight_Quote__c</field>
            <operator>EqualTo</operator>
            <value>
                <elementReference>$Record.Id</elementReference>
            </value>
        </filters>
        <getFirstRecordOnly>false</getFirstRecordOnly>
        <limit>
            <numberValue>2000.0</numberValue>
        </limit>
        <object>Quote_Leg__c</object>
        <outputReference>allLegs</outputReference>
        <queriedFields>Id</queriedFields>
        <queriedFields>Carrier_Code__c</queriedFields>
        <queriedFields>Destination_Zone__c</queriedFields>
        <queriedFields>Is_Serviceable__c</queriedFields>
        <queriedFields>Leg_Sequence__c</queriedFields>
        <queriedFields>Quoted_Cost__c</queriedFields>
        <queriedFields>Rate_Status__c</queriedFields>
        <queriedFields>Weight_Kg__c</queriedFields>
        <sortField>Leg_Sequence__c</sortField>
        <sortOrder>Asc</sortOrder>
        <storeOutputAutomatically>false</storeOutputAutomatically>
    </recordLookups>
    <recordUpdates>
        <name>Update_Leg_Stamps</name>
        <label>Update Leg Stamps</label>
        <locationX>50</locationX>
        <locationY>1274</locationY>
        <faultConnector>
            <targetReference>Log_Rating_Fault</targetReference>
        </faultConnector>
        <inputReference>Map_Leg_Stamps</inputReference>
    </recordUpdates>
    <runInMode>DefaultMode</runInMode>
    <start>
        <locationX>50</locationX>
        <locationY>50</locationY>
        <connector>
            <targetReference>Get_Quote_Legs</targetReference>
        </connector>
        <doesRequireRecordChangedToMeetCriteria>true</doesRequireRecordChangedToMeetCriteria>
        <filterLogic>and</filterLogic>
        <filters>
            <field>Status__c</field>
            <operator>EqualTo</operator>
            <value>
                <stringValue>Rating</stringValue>
            </value>
        </filters>
        <object>Freight_Quote__c</object>
        <recordTriggerType>CreateAndUpdate</recordTriggerType>
        <triggerType>RecordAfterSave</triggerType>
    </start>
    <status>Draft</status>
    <transforms>
        <name>Sum_Quoted_Cost</name>
        <label>Sum Quoted Cost</label>
        <locationX>50</locationX>
        <locationY>482</locationY>
        <connector>
            <targetReference>Sort_Cheapest_Legs</targetReference>
        </connector>
        <dataType>Number</dataType>
        <isCollection>false</isCollection>
        <scale>2</scale>
        <transformValues>
            <transformValueActions>
                <inputParameters>
                    <name>aggregationValues</name>
                    <value>
                        <elementReference>Filter_Serviceable_Legs</elementReference>
                    </value>
                </inputParameters>
                <inputParameters>
                    <name>aggregationField</name>
                    <value>
                        <stringValue>Quoted_Cost__c</stringValue>
                    </value>
                </inputParameters>
                <transformType>Sum</transformType>
            </transformValueActions>
        </transformValues>
    </transforms>
    <variables>
        <name>allLegs</name>
        <dataType>SObject</dataType>
        <isCollection>true</isCollection>
        <isInput>false</isInput>
        <isOutput>false</isOutput>
        <objectType>Quote_Leg__c</objectType>
    </variables>
    <variables>
        <name>currentServiceableLeg</name>
        <dataType>SObject</dataType>
        <isCollection>false</isCollection>
        <isInput>false</isInput>
        <isOutput>false</isOutput>
        <objectType>Quote_Leg__c</objectType>
    </variables>
    <variables>
        <name>currentPriorityLeg</name>
        <dataType>SObject</dataType>
        <isCollection>false</isCollection>
        <isInput>false</isInput>
        <isOutput>false</isOutput>
        <objectType>Quote_Leg__c</objectType>
    </variables>
    <variables>
        <name>currentTopLeg</name>
        <dataType>SObject</dataType>
        <isCollection>false</isCollection>
        <isInput>false</isInput>
        <isOutput>false</isOutput>
        <objectType>Quote_Leg__c</objectType>
    </variables>
    <variables>
        <name>currentStampLeg</name>
        <dataType>SObject</dataType>
        <isCollection>false</isCollection>
        <isInput>false</isInput>
        <isOutput>false</isOutput>
        <objectType>Quote_Leg__c</objectType>
    </variables>
    <variables>
        <name>legsForReview</name>
        <dataType>SObject</dataType>
        <isCollection>true</isCollection>
        <isInput>false</isInput>
        <isOutput>false</isOutput>
        <objectType>Quote_Leg__c</objectType>
    </variables>
    <variables>
        <name>legsCheapAndPriority</name>
        <dataType>SObject</dataType>
        <isCollection>true</isCollection>
        <isInput>false</isInput>
        <isOutput>false</isOutput>
        <objectType>Quote_Leg__c</objectType>
    </variables>
    <variables>
        <name>serviceableLegCount</name>
        <dataType>Number</dataType>
        <isCollection>false</isCollection>
        <isInput>false</isInput>
        <isOutput>true</isOutput>
        <scale>0</scale>
    </variables>
    <variables>
        <name>reviewLegCount</name>
        <dataType>Number</dataType>
        <isCollection>false</isCollection>
        <isInput>false</isInput>
        <isOutput>true</isOutput>
        <scale>0</scale>
    </variables>
</Flow>
```

### How to read it

- **`<apiVersion>63.0</apiVersion>` is a floor, not a preference.** Three things in this flow have
  documented version gates and 63.0 is the highest of them: `FlowRecordLookup.limit` is "available
  in API version 63.0 and later" (`api_meta.txt` L71177–L71183), `FlowTransform`'s scalar
  `dataType` values (`Number`, `String`, `Boolean`, `Currency`, `Date`, `DateTime`) are "available
  in API version 62.0" (L72707–L72712), and `FlowTransform` itself is API 59.0 and later
  (L72685–L72687). Set the flow lower and the deploy fails on a field the schema of that version
  has never heard of. Setting it higher is fine.
- **`<collectionProcessors>` and `<transforms>` are different root arrays.** `collectionProcessors`
  is `FlowCollectionProcessor[]`, "an array of nodes that process collections… available in API
  version 50.0 and later" (`api_meta.txt` L68092–L68093). `transforms` is `FlowTransform[]`,
  "available in API version 59.0 and later" (L68435–L68436). A third root field,
  `collectionFilterCriteria`, is documented as **"Reserved for future use"** (L68090) — it is not
  the Collection Filter element and writing it does nothing.
- **The first Filter uses `conditions`; the second uses `formula`.** `conditionLogic` selects
  between them: valid values are `And`, `Or`, custom logic such as `(1 AND (2 OR 3))`, and
  `Formula` (`api_meta.txt` L69945–L69951). `formula` is "the formula expression that filters the
  input collection. If the formula evaluates to true, the record is added to the output collection"
  (L69957–L69959). The formula needs a name for the item under test, which is what
  `assignNextValueToReference` supplies — "the name of the variable that's assigned to the next
  value of the collection" (L69931–L69932). Formula *syntax* belongs to
  `flow/flow-formula-and-expression-patterns`; this file only shows where the string goes.
- **`Sum_Quoted_Cost` is a Transform, and its two input keys are named by the guide.**
  `FlowTransformValueActionInputParameter.name` is "a key that specifies the configuration of input
  parameters for this data transformation when `transformType` is set to `Sum` or `Count`. Valid
  values are: `aggregationField` — the field on each item in a source collection that's used to
  calculate the transformed value; `aggregationValues` — the source collection that's used to
  calculate the transformed value" (`api_meta.txt` L72808–L72814, available in API version 60.0 and
  later). `Sum` "adds the numeric values of a field on each item in a collection" and `Count`
  "calculates the number of items in a source collection" (L72776, L72787–L72788).
  **UNVERIFIED (2026-09-05):** the guide names the two keys but ships no sample, so passing the
  field API name as a `<stringValue>` inside `aggregationField` — rather than as an
  `<elementReference>` — is the shape Flow Builder emits, reproduced here, not a shape the guide
  states. Retrieve one Builder-authored Transform before trusting the literal.
- **The Transform's result is addressed by the element's own name.** `FlowTransformValueAction`
  documents `assignToReference` as **"Reserved for future use"** (`api_meta.txt` L72765), and
  `FlowTransform.storeOutputAutomatically` likewise as "Reserved for future use" (L72726) — so
  there is no field that names an output variable. **UNVERIFIED (2026-09-05):** referencing the
  transform by element name (`Sum_Quoted_Cost`, used here inside `Map_Rate_Recommendations`) is the
  only route left once those two fields are excluded, and it matches how a `storeOutputAutomatically`
  Get Records is referenced, but the guide never states it.
- **`Sort_Cheapest_Legs` is the top-N idiom, and `limit` alone is not.** `limit` is "the maximum
  number of records to include in the generated collection. There's no default value… If
  `sortField` and `sortOrder` are also specified, the records are sorted before the limit takes
  effect", API 51.0 and later (`api_meta.txt` L69961–L69967). Sort-then-limit is documented order,
  so `limit` + `sortOptions` is a genuine top N; `limit` with no `sortOptions` is an arbitrary N.
  `scripts/check_flow_collection_processing.py` rule **E2** is exactly that case.
  `flow/flow-loop-element-patterns` owns the near-miss between this `int` `limit` and the
  `FlowElementReferenceOrValue` `limit` on Get Records — read its Gotcha 13 rather than a second
  copy here.
- **`sortOptions` is where the sort lives.** `FlowCollectionSortOption` (API 51.0 and later) carries
  `sortField`, `sortOrder` (`Asc` / `Desc`) and `doesPutEmptyStringAndNullFirst`, whose default is
  `false` (`api_meta.txt` L69986–L70002). It is an array, so multi-key sorts are expressed as
  repeated `<sortOptions>` blocks. `sortField` is "required for record collections and collections
  of Apex-defined variables", and "if the collection is a primitive data type, such as a list of
  string or integer values, `sortField` isn't supported" (L69994–L69998) — a Text collection
  therefore goes through a Sort processor with `sortOptions` that omits `sortField`, not through no
  processor at all.
- **`Map_Rate_Recommendations` builds a *new* collection of a *new* type.** `outputSObjectType` is
  "the sObject type of the output collection" (`api_meta.txt` L69979) and `mapItems` is
  `FlowCollectionMapItem[]`, "the rules to map each field of the collection variable" (L69977).
  Every `FlowCollectionMapItem` requires all three of `assignToFieldReference`, `operator` (a
  `FlowAssignmentOperator`) and `value` (L70161–L70173, API 51.0 and later) — the guide marks all
  three **Required**, so a mapping that omits `operator` is not "defaulting to Assign", it is
  incomplete. **UNVERIFIED (2026-09-05):** the `<processorName>.<Field__c>` shape of
  `assignToFieldReference` is reproduced from what Flow Builder emits, not from the guide, which
  ships no sample for `FlowCollectionProcessor` or `FlowCollectionMapItem`.
  `flow/flow-loop-element-patterns` records the same caveat; it is repeated here because this file
  is deployable on its own.
- **`Map_Leg_Stamps` is the loop-free bulk field stamp.** Its `outputSObjectType` is the *same*
  type as its input, and its `mapItems` carry `Id` plus the one field being changed. The result is
  a `Quote_Leg__c` collection that `Update_Leg_Stamps` consumes through `inputReference` — "the
  record variable whose field values are used to update the record's fields"
  (`api_meta.txt` L71283–L71286). That is the answer to "set a field on every record in a
  collection" without a Loop + Assignment; a Map processor never edits its input in place, so this
  works only because the mapped `Id` tells the DML which rows to write.
- **`Stage_Collection_Sets` does set algebra in one element.** `RemoveAll` "removes all instances
  of the value from the variable… when the value is a collection variable, the operator removes all
  instances of each item" — set difference (`api_meta.txt` L69823–L69829). `RemoveUncommon` is
  "supported only when `assignToReference` and `value` are both collection variables. Keeps items
  that are in both collections and removes the rest" — intersection (L69847–L69851). Both are API
  43.0 and later. The two `Add` items that seed `legsForReview` and `legsCheapAndPriority` from
  another collection are the Metadata-API-only form of `Add` — see
  `flow/flow-bulkification`'s gotcha on that, and the `<description>` note this flow carries so the
  next admin does not open it in Builder and silently destroy them.
- **`Count_Collections` uses `AssignCount`, and the collection goes in `value`.** `AssignCount` is
  "supported only when the **value** is a collection variable or the `$Flow.ActiveStages` global
  variable. Counts the number of stages or items in the collection, and assigns that number to the
  variable in the `assignToReference` field" (`api_meta.txt` L69813–L69818, API 43.0 and later).
  Both targets here are declared `dataType` `Number` with `isCollection` `false`; checker rule
  **E5** fails the build when they are not.
- **`getFirstRecordOnly` and `outputReference` are a matched pair.** This Get Records sets
  `storeOutputAutomatically` to `false` and names `outputReference` — "supported only when
  `storeOutputAutomatically` is `false`" (`api_meta.txt` L71195–L71200). `getFirstRecordOnly` is
  "supported only when `storeOutputAutomatically` is `true`. When `storeOutputAutomatically` is
  `false`, what determines whether one or multiple records are stored is whether `outputReference`
  specifies a record variable or a record collection variable" (L71153–L71164). The collection
  shape is therefore decided by `allLegs` having `isCollection` `true`, not by the flag.
- **A collection processor cannot fault-route.** `FlowCollectionProcessor` extends `FlowNode`
  (`api_meta.txt` L69926–L69928) and neither type declares a `faultConnector`; the guide lists one
  on `FlowRecordCreate` (L70965), `FlowRecordUpdate` (L71283), `FlowRecordLookup` (L71120) and
  `FlowRecordDelete` (L71046). Every fault route in this flow therefore hangs off a DML or Get
  element, never off a Filter, Sort, Map or Transform.

---

## 2. Transform variants the flow above does not use

### `Map` on a Transform (not the Map processor)

Two different elements are called "Map". The processor
(`RecommendationMapCollectionProcessor`) produces an sObject collection through `mapItems`. A
`FlowTransform` whose `transformType` is `Map` "specifies a mapping between the datasets in
flows. In Flow Builder, it corresponds to the mapping between source data fields and target data
fields" (`api_meta.txt` L72784–L72786), names its target field through `outputFieldApiName`
(L72770–L72772), and — unlike the processor — can carry a **formula** in `value`:

```xml
<transforms>
    <name>Build_Carrier_Label</name>
    <label>Build Carrier Label</label>
    <locationX>314</locationX>
    <locationY>482</locationY>
    <dataType>sObject</dataType>
    <isCollection>true</isCollection>
    <objectType>Rate_Recommendation__c</objectType>
    <transformValues>
        <transformValueActions>
            <outputFieldApiName>Carrier_Code__c</outputFieldApiName>
            <transformType>Map</transformType>
            <value>
                <formulaDataType>String</formulaDataType>
                <formulaExpression>UPPER({!currentTopLeg.Carrier_Code__c}) &amp; "-" &amp; TEXT({!currentTopLeg.Leg_Sequence__c})</formulaExpression>
            </value>
        </transformValueActions>
    </transformValues>
</transforms>
```

`FlowElementReferenceOrValue.formulaExpression` is "the formula expression that transforms the data
in the flow. In Flow Builder, it corresponds to the target data field in the Transform element.
This field requires the `formulaDataType` field. This field is available in API version 59.0 and
later. **See FlowTransform**" (`api_meta.txt` L70479–L70482); `formulaDataType` carries the matching
"See FlowTransform" cross-reference (L70464–L70477). Both fields exist *because of* the Transform
element, which is why the widely-repeated claim that "Transform does not support formula
expressions" does not survive contact with the guide.

### `InnerJoin` — the only documented cross-collection join

```xml
<transforms>
    <name>Join_Legs_To_Rate_Card</name>
    <label>Join Legs To Rate Card</label>
    <locationX>314</locationX>
    <locationY>590</locationY>
    <dataType>sObject</dataType>
    <isCollection>true</isCollection>
    <objectType>Rate_Recommendation__c</objectType>
    <transformValues>
        <transformValueActions>
            <transformType>InnerJoin</transformType>
            <value>
                <complexValueType>JoinDefinition</complexValueType>
                <complexValue>REPLACE WITH THE JOIN DEFINITION RETRIEVED FROM YOUR ORG</complexValue>
            </value>
        </transformValueActions>
    </transformValues>
</transforms>
```

`InnerJoin` "joins selected data from two source collections that are stored in a target collection
in a flow. This value is available in API version 63.0 and later. See `complexValueType` on
`FlowElementReferenceOrValue`. `InnerJoin` isn't a valid value for `FlowInlineTransform`"
(`api_meta.txt` L72778–L72782). `complexValueType` `JoinDefinition` "indicates flow resources for
source and target collections, join keys, selected fields to join, and field mappings in a join
transformation", available API 63.0 and later, and `complexValue` is a `string` describing the
structure through `fieldReference`, `objectType`, `type` and `elementReference`
(`api_meta.txt` L70423–L70444).

**UNVERIFIED (2026-09-05):** `complexValue` is typed `string` and the guide names the four keys it
carries but gives no example of the serialised payload, so the placeholder above is deliberately
not filled in. Build one join in Flow Builder and retrieve it before hand-authoring a second. This
is the single documented way to join two collections declaratively — a nested Loop is the
alternative, and `flow/flow-loop-element-patterns` Anti-Pattern 3 owns why that is wrong.

---

## 3. `Rating_Counts_Serviceable_And_Review_Legs.flowtest-meta.xml`

The assertions target the *outputs of the collection processors* — the counts — not a staged loop
collection, because that is what this flow's correctness reduces to.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<FlowTest xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Four legs seeded by FreightQuoteRatingTestData: three serviceable, one zero-weight. Asserts the two counts the collection processors produce, and that the fault route did not run.</description>
    <flowApiName>Freight_Quote_Rate_Legs</flowApiName>
    <flowTestDataSources>
        <apexClass>FreightQuoteRatingTestData</apexClass>
        <dataSourceType>ApexClass</dataSourceType>
    </flowTestDataSources>
    <label>Rating counts serviceable and review legs</label>
    <testPoints>
        <assertions>
            <conditions>
                <leftValueReference>$Record.Status__c</leftValueReference>
                <operator>EqualTo</operator>
                <rightValue>
                    <stringValue>Rating</stringValue>
                </rightValue>
            </conditions>
            <errorMessage>The updated image does not satisfy the Start filter Status__c = Rating, so no element below this point ran and the Finish assertions prove nothing.</errorMessage>
        </assertions>
        <elementApiName>Start</elementApiName>
        <parameters>
            <leftValueReference>$Record</leftValueReference>
            <type>InputTriggeringRecordInitial</type>
            <value>
                <sobjectValue>{&quot;Name&quot;:&quot;FQ-3308&quot;,&quot;Status__c&quot;:&quot;Draft&quot;}</sobjectValue>
            </value>
        </parameters>
        <parameters>
            <leftValueReference>$Record</leftValueReference>
            <type>InputTriggeringRecordUpdated</type>
            <value>
                <sobjectValue>{&quot;Name&quot;:&quot;FQ-3308&quot;,&quot;Status__c&quot;:&quot;Rating&quot;}</sobjectValue>
            </value>
        </parameters>
    </testPoints>
    <testPoints>
        <assertions>
            <conditions>
                <leftValueReference>serviceableLegCount</leftValueReference>
                <operator>EqualTo</operator>
                <rightValue>
                    <numberValue>3.0</numberValue>
                </rightValue>
            </conditions>
            <errorMessage>Filter_Serviceable_Legs kept a number of legs other than 3. Either a condition was widened, or conditionLogic was switched to Formula and the conditions block is now dead XML.</errorMessage>
        </assertions>
        <assertions>
            <conditions>
                <leftValueReference>reviewLegCount</leftValueReference>
                <operator>EqualTo</operator>
                <rightValue>
                    <numberValue>1.0</numberValue>
                </rightValue>
            </conditions>
            <errorMessage>legsForReview is not the complement of the serviceable set. RemoveAll ran against the wrong collection, or the Add that seeded legsForReview from allLegs was dropped by a Flow Builder save.</errorMessage>
        </assertions>
        <assertions>
            <conditions>
                <leftValueReference>Log_Rating_Fault</leftValueReference>
                <operator>WasVisited</operator>
                <rightValue>
                    <booleanValue>false</booleanValue>
                </rightValue>
            </conditions>
            <errorMessage>A fault route ran on a path with no legitimate failure. An Application_Log__c row exists for a clean rating run.</errorMessage>
        </assertions>
        <elementApiName>Finish</elementApiName>
    </testPoints>
    <testType>WithAssertion</testType>
</FlowTest>
```

### How to read it

- **Two version numbers, two jobs.** The flow's own `<apiVersion>63.0</apiVersion>` is its runtime
  version. The `package.xml` `<version>` in §4 is 66.0 because this test uses two API-66.0 fields:
  `flowTestDataSources` (`api_meta.txt` L74000–L74004) and `testType` (L74041–L74049). Deploy the
  same flow under a 63.0 manifest and the `FlowTest` is rejected while the flow itself succeeds.
- **`testType` has exactly one documented value.** `WithAssertion` — "the automated comparison of
  the actual flow outcome with the user-defined expected outcome that assertions define"
  (`api_meta.txt` L74048–L74049). It is `Required` from API 66.0.
- **Assertions can only sit at `Start` and `Finish`.** `FlowTestPoint.elementApiName` is Required
  and its "possible values are: `Start`, `Finish`" (`api_meta.txt` L74139–L74146). There is no test
  point *between* the Filter and the Sort, which is precisely why this test asserts on the counts —
  they are the only evidence of the intermediate collections that survives to `Finish`. Give every
  processor chain a terminal `AssignCount` if you want it testable at all.
- **`flowTestDataSources` is the answer to "how do I seed the child records?", and it is Apex.**
  `FlowTestDataSource` requires `apexClass` and `dataSourceType`, whose "possible value is
  `ApexClass`" (`api_meta.txt` L74070–L74087, API 66.0 and later). The declarative `parameters`
  block only carries the *triggering* record (`InputTriggeringRecordInitial`,
  `InputTriggeringRecordUpdated`, `InputVariable`, `ScheduledPath` —
  `api_meta.txt` L74321–L74329). A flow whose collections come from a Get Records against related
  data therefore has nothing to assert on below API 66.0 unless the org already holds the rows.
  `flow/flow-testing` owns the wider FlowTest strategy; this bullet is here only because it decides
  whether a collection-processing flow is testable.
- **`WasVisited` on the fault element.** `WasVisited` "requires a node on the left side" and is a
  valid `FlowComparisonOperator` for test conditions (`api_meta.txt` L74226). Asserting it
  `false` is what turns "the counts happen to be right" into "the counts are right *and* nothing
  faulted on the way".

---

## 4. Deploying it

`manifest/package.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Freight_Quote__c</members>
        <members>Quote_Leg__c</members>
        <members>Rate_Recommendation__c</members>
        <members>Application_Log__c</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>FreightQuoteRatingTestData</members>
        <name>ApexClass</name>
    </types>
    <types>
        <members>Freight_Quote_Rate_Legs</members>
        <name>Flow</name>
    </types>
    <types>
        <members>Rating_Counts_Serviceable_And_Review_Legs</members>
        <name>FlowTest</name>
    </types>
    <version>66.0</version>
</Package>
```

**Deploy order matters here in a way it does not for a loop-only flow.** A collection processor
names its output type in `outputSObjectType` and its map targets in `assignToFieldReference`, so
every one of those fields must already exist or the Flow deploy fails with an unresolved-field
error rather than a helpful one:

1. `CustomObject` — all four objects and every field named in `queriedFields`, `mapItems`,
   `conditions` and `inputAssignments`.
2. `ApexClass` — `FreightQuoteRatingTestData`, before the `FlowTest` that names it.
3. `Flow` — `Freight_Quote_Rate_Legs`, as `Draft`.
4. `FlowTest` — it names `flowApiName`, so the flow must exist first.
5. Only then activate.

```bash
# Validate without committing anything
sf project deploy start --manifest manifest/package.xml --dry-run --target-org rating-sandbox

# Deploy
sf project deploy start --manifest manifest/package.xml --target-org rating-sandbox

# Run just this flow's tests
sf flow run test --flow-api-name Freight_Quote_Rate_Legs --target-org rating-sandbox

# Round-trip check: retrieve what the org actually stored and diff it against what you wrote.
# For collection processors this is not optional — the guide ships no sample XML for them, so the
# org is the only authority on the shapes marked UNVERIFIED above.
sf project retrieve start --metadata Flow:Freight_Quote_Rate_Legs --target-org rating-sandbox
```

---

## 5. Verifying it worked

**Static, before deploy:**

```bash
python3 skills/flow/flow-collection-processing/scripts/check_flow_collection_processing.py \
  --manifest-dir force-app --strict
```

**In the org, after one quote moves to `Rating`** — the recommendation count must equal the
`limit` on `Sort_Cheapest_Legs` (3), or the serviceable-leg count if that is smaller, and every
recommended leg must carry the stamp `Map_Leg_Stamps` wrote:

```soql
SELECT Freight_Quote__c,
       COUNT(Id) recommendationCount,
       SUM(Recommended_Cost__c) recommendedTotal,
       MAX(Quote_Total_At_Rating__c) transformSum
FROM Rate_Recommendation__c
WHERE Freight_Quote__r.Status__c = 'Rating'
GROUP BY Freight_Quote__c
```

```soql
SELECT Id, Rate_Status__c, Quoted_Cost__c
FROM Quote_Leg__c
WHERE Freight_Quote__c = :quoteId AND Rate_Status__c = 'Recommended'
ORDER BY Quoted_Cost__c ASC
```

Three checks read off those two queries:

| Check | Passing shape | What a failure means |
|---|---|---|
| `recommendationCount` | `MIN(3, serviceable legs)` | `limit` is missing or `sortOptions` was dropped, so `Sort_Cheapest_Legs` passed the whole collection through |
| `transformSum` vs `recommendedTotal` | `transformSum` ≥ `recommendedTotal` | `Sum_Quoted_Cost` aggregated the wrong collection — it must read `Filter_Serviceable_Legs` (all serviceable legs), not the top-3 output |
| `Rate_Status__c` rows | exactly the rows the second query returns, ordered cheapest-first | `Map_Leg_Stamps` dropped the `Id` mapItem, so `Update_Leg_Stamps` had nothing to key on and wrote nothing |

**In the debug log**, with the `Workflow` category at `FINER` or above, the collection sizes are
directly observable: `FLOW_BULK_ELEMENT_DETAIL` logs "Interview ID, element type, element name,
number of records" and `FLOW_BULK_ELEMENT_END` adds execution time
(`apexdev.txt` L38724–L38729). `FLOW_INTERVIEW_FINISHED_LIMIT_USAGE` reports usage against SOQL
queries, SOQL query rows, DML statements, DML rows, CPU time and heap size (`apexdev.txt` L38821–L38834) — and
notably **not** against any element count, which is the empirical form of the negative recorded in
`references/gotchas.md`.
