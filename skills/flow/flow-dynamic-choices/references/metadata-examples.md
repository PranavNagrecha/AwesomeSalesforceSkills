# Metadata Examples — Flow Dynamic Choices

A complete, parseable **two-screen screen flow** that uses all four choice sources in one interview:
a **picklist choice set**, **static `FlowChoice` resources** (one with a `userInput`), a **record
choice set** dependent on the first screen's selection with `filters` / `sortField` / `limit` /
`outputAssignments`, a **collection choice set** fed by a Get Records, and a
**MultiSelectCheckboxes** field whose semicolon-delimited output is decomposed with a formula and an
Assignment. Then the `package.xml`, the deploy order, and the debug-run verification checklist —
**not** a `FlowTest`, because screen flows are out of `FlowTest`'s documented scope (§6).

Every element name, enum value and version floor below is cited to the Metadata API Developer Guide
text (`api_meta.txt`, Summer '26 / v62 extract of
<https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf>). Where the guide
documents a field but never states the behaviour, the claim carries an explicit
`UNVERIFIED (2026-09-05)` marker beside it rather than in a footnote.

The screen-flow skeleton conventions (`<start>`, connector shape, fault routing) come from
`templates/flow/RecordTriggered_Skeleton.flow-meta.xml` and `templates/flow/FaultPath_Template.md` —
read those rather than re-deriving them here.

---

## 0. The schema this flow assumes

Training enrolment: a learner picks a track, the platform offers the course offerings open on that
track, and the request is filed against a cohort. This object set is used by no other `flow/` skill
in this repo, so the XML below deploys into a scratch org alongside theirs without a name collision.

| Object | Fields used here |
|---|---|
| `Course_Offering__c` | `Name`, `Training_Track__c` (picklist), `Start_On__c` (Date), `Seats_Remaining__c` (Number, 0 dp), `Is_Open__c` (Checkbox), `Location_Name__c` (Text 80) |
| `Training_Cohort__c` | `Name`, `Cohort_Label__c` (Text 80), `Training_Track__c` (picklist), `Is_Accepting__c` (Checkbox) |
| `Enrollment_Request__c` | `Training_Track__c` (picklist — **the picklist choice set reads this field's metadata**), `Course_Offering__c` (Lookup), `Cohort__c` (Lookup), `Delivery_Mode__c` (Text 40), `Accommodations__c` (Long Text) |
| `Application_Log__c` | `Message__c` (Long Text), `Related_Record_Id__c` (Text 18), `Severity__c` (picklist), `Source__c` (Text) |

`Enrollment_Request__c.Training_Track__c` and `Course_Offering__c.Training_Track__c` must share a
value set, because screen 1 stores the picklist choice's **API value** and screen 2 filters
`Course_Offering__c` on it. `picklistField` / `picklistObject` name the field whose *metadata* is
read, not a record (`api_meta.txt` L70341–L70360) — so the field can live on the object the flow
writes to even though no record exists yet.

`Application_Log__c` is the shared fault-log object the other `flow/` skills also write to; keep one
definition per org.

---

## 1. `Enrollment_Request_Intake.flow-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>63.0</apiVersion>
    <assignments>
        <name>Add_Interpreter_To_List</name>
        <label>Add Interpreter To List</label>
        <locationX>50</locationX>
        <locationY>674</locationY>
        <assignmentItems>
            <assignToReference>varAccommodationList</assignToReference>
            <operator>Add</operator>
            <value>
                <stringValue>Interpreter</stringValue>
            </value>
        </assignmentItems>
        <connector>
            <targetReference>Route_On_Choices</targetReference>
        </connector>
    </assignments>
    <choices>
        <name>Choice_Instructor_Led</name>
        <choiceText>Instructor-Led (classroom or virtual)</choiceText>
        <dataType>String</dataType>
        <value>
            <stringValue>Instructor_Led</stringValue>
        </value>
    </choices>
    <choices>
        <name>Choice_Large_Print</name>
        <choiceText>Large-print materials</choiceText>
        <dataType>String</dataType>
        <value>
            <stringValue>Large Print</stringValue>
        </value>
    </choices>
    <choices>
        <name>Choice_Other_Mode</name>
        <choiceText>Something else - tell us</choiceText>
        <dataType>String</dataType>
        <userInput>
            <isRequired>true</isRequired>
            <promptText>Describe the delivery mode you need</promptText>
            <validationRule>
                <errorMessage>Give the training team at least 10 characters to act on.</errorMessage>
                <formulaExpression>LEN({!Select_Mode}) &gt;= 10</formulaExpression>
            </validationRule>
        </userInput>
        <value>
            <stringValue>Other</stringValue>
        </value>
    </choices>
    <choices>
        <name>Choice_Self_Paced</name>
        <choiceText>Self-Paced (on demand)</choiceText>
        <dataType>String</dataType>
        <value>
            <stringValue>Self_Paced</stringValue>
        </value>
    </choices>
    <choices>
        <name>Choice_Step_Free</name>
        <choiceText>Step-free access</choiceText>
        <dataType>String</dataType>
        <value>
            <stringValue>Step Free</stringValue>
        </value>
    </choices>
    <choices>
        <name>Choice_Interpreter</name>
        <choiceText>Sign-language interpreter</choiceText>
        <dataType>String</dataType>
        <value>
            <stringValue>Interpreter</stringValue>
        </value>
    </choices>
    <decisions>
        <name>Route_On_Choices</name>
        <label>Seats Left On This Offering?</label>
        <locationX>176</locationX>
        <locationY>782</locationY>
        <defaultConnector>
            <targetReference>Create_Enrollment</targetReference>
        </defaultConnector>
        <defaultConnectorLabel>Enroll</defaultConnectorLabel>
        <rules>
            <name>Waitlist_Instructor_Led</name>
            <conditionLogic>and</conditionLogic>
            <conditions>
                <leftValueReference>varSeatsRemaining</leftValueReference>
                <operator>LessThanOrEqualTo</operator>
                <rightValue>
                    <numberValue>0.0</numberValue>
                </rightValue>
            </conditions>
            <conditions>
                <leftValueReference>Choice_Instructor_Led</leftValueReference>
                <operator>WasSelected</operator>
                <rightValue>
                    <booleanValue>true</booleanValue>
                </rightValue>
            </conditions>
            <connector>
                <targetReference>Waitlist_Notice</targetReference>
            </connector>
            <label>Waitlist</label>
        </rules>
    </decisions>
    <decisions>
        <name>Split_Accommodations</name>
        <label>Interpreter Requested?</label>
        <locationX>176</locationX>
        <locationY>566</locationY>
        <defaultConnector>
            <targetReference>Route_On_Choices</targetReference>
        </defaultConnector>
        <defaultConnectorLabel>No</defaultConnectorLabel>
        <rules>
            <name>Interpreter_Requested</name>
            <conditionLogic>and</conditionLogic>
            <conditions>
                <leftValueReference>fxNeedsInterpreter</leftValueReference>
                <operator>EqualTo</operator>
                <rightValue>
                    <booleanValue>true</booleanValue>
                </rightValue>
            </conditions>
            <connector>
                <targetReference>Add_Interpreter_To_List</targetReference>
            </connector>
            <label>Yes</label>
        </rules>
    </decisions>
    <dynamicChoiceSets>
        <name>Cohort_Choices</name>
        <collectionReference>varOpenCohorts</collectionReference>
        <dataType>String</dataType>
        <displayField>Cohort_Label__c</displayField>
        <valueField>Id</valueField>
    </dynamicChoiceSets>
    <dynamicChoiceSets>
        <name>Offering_Choices</name>
        <dataType>String</dataType>
        <displayField>Name</displayField>
        <filters>
            <field>Training_Track__c</field>
            <operator>EqualTo</operator>
            <value>
                <elementReference>Select_Track</elementReference>
            </value>
        </filters>
        <filters>
            <field>Is_Open__c</field>
            <operator>EqualTo</operator>
            <value>
                <booleanValue>true</booleanValue>
            </value>
        </filters>
        <limit>25</limit>
        <object>Course_Offering__c</object>
        <outputAssignments>
            <assignToReference>varOfferingId</assignToReference>
            <field>Id</field>
        </outputAssignments>
        <outputAssignments>
            <assignToReference>varSeatsRemaining</assignToReference>
            <field>Seats_Remaining__c</field>
        </outputAssignments>
        <outputAssignments>
            <assignToReference>varOfferingLocation</assignToReference>
            <field>Location_Name__c</field>
        </outputAssignments>
        <sortField>Start_On__c</sortField>
        <sortOrder>Asc</sortOrder>
        <valueField>Id</valueField>
    </dynamicChoiceSets>
    <dynamicChoiceSets>
        <name>Track_Choices</name>
        <dataType>Picklist</dataType>
        <picklistField>Training_Track__c</picklistField>
        <picklistObject>Enrollment_Request__c</picklistObject>
    </dynamicChoiceSets>
    <environments>Default</environments>
    <formulas>
        <name>fxAccommodationText</name>
        <dataType>String</dataType>
        <expression>SUBSTITUTE({!Select_Accommodations}, &quot;;&quot;, &quot;, &quot;)</expression>
    </formulas>
    <formulas>
        <name>fxNeedsInterpreter</name>
        <dataType>Boolean</dataType>
        <expression>CONTAINS({!Select_Accommodations}, &quot;Interpreter&quot;)</expression>
    </formulas>
    <interviewLabel>Enrollment Request Intake {!$Flow.CurrentDateTime}</interviewLabel>
    <label>Enrollment Request Intake</label>
    <processType>Flow</processType>
    <recordCreates>
        <name>Create_Enrollment</name>
        <label>Create Enrollment Request</label>
        <locationX>314</locationX>
        <locationY>890</locationY>
        <assignRecordIdToReference>varEnrollmentId</assignRecordIdToReference>
        <connector>
            <targetReference>Confirmation</targetReference>
        </connector>
        <faultConnector>
            <targetReference>Log_Choice_Fault</targetReference>
        </faultConnector>
        <inputAssignments>
            <field>Accommodations__c</field>
            <value>
                <elementReference>fxAccommodationText</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Cohort__c</field>
            <value>
                <elementReference>Select_Cohort</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Course_Offering__c</field>
            <value>
                <elementReference>varOfferingId</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Delivery_Mode__c</field>
            <value>
                <elementReference>Select_Mode</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Training_Track__c</field>
            <value>
                <elementReference>Select_Track</elementReference>
            </value>
        </inputAssignments>
        <object>Enrollment_Request__c</object>
        <storeOutputAutomatically>false</storeOutputAutomatically>
    </recordCreates>
    <recordCreates>
        <name>Log_Choice_Fault</name>
        <label>Log Choice Fault</label>
        <locationX>500</locationX>
        <locationY>890</locationY>
        <connector>
            <targetReference>Fault_Notice</targetReference>
        </connector>
        <inputAssignments>
            <field>Message__c</field>
            <value>
                <elementReference>$Flow.FaultMessage</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Related_Record_Id__c</field>
            <value>
                <elementReference>varOfferingId</elementReference>
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
                <stringValue>Enrollment_Request_Intake</stringValue>
            </value>
        </inputAssignments>
        <object>Application_Log__c</object>
        <storeOutputAutomatically>false</storeOutputAutomatically>
    </recordCreates>
    <recordLookups>
        <name>Get_Open_Cohorts</name>
        <label>Get Open Cohorts</label>
        <locationX>176</locationX>
        <locationY>350</locationY>
        <assignNullValuesIfNoRecordsFound>false</assignNullValuesIfNoRecordsFound>
        <connector>
            <targetReference>Offering_And_Details</targetReference>
        </connector>
        <faultConnector>
            <targetReference>Log_Choice_Fault</targetReference>
        </faultConnector>
        <filterLogic>and</filterLogic>
        <filters>
            <field>Training_Track__c</field>
            <operator>EqualTo</operator>
            <value>
                <elementReference>Select_Track</elementReference>
            </value>
        </filters>
        <filters>
            <field>Is_Accepting__c</field>
            <operator>EqualTo</operator>
            <value>
                <booleanValue>true</booleanValue>
            </value>
        </filters>
        <object>Training_Cohort__c</object>
        <outputReference>varOpenCohorts</outputReference>
        <queriedFields>Id</queriedFields>
        <queriedFields>Cohort_Label__c</queriedFields>
        <sortField>Cohort_Label__c</sortField>
        <sortOrder>Asc</sortOrder>
        <storeOutputAutomatically>false</storeOutputAutomatically>
    </recordLookups>
    <screens>
        <name>Confirmation</name>
        <label>Request Filed</label>
        <locationX>314</locationX>
        <locationY>998</locationY>
        <allowBack>false</allowBack>
        <allowFinish>true</allowFinish>
        <allowPause>false</allowPause>
        <fields>
            <name>Confirmation_Text</name>
            <fieldText>Filed for {!Select_Track} at {!varOfferingLocation}. Accommodations: {!fxAccommodationText}</fieldText>
            <fieldType>DisplayText</fieldType>
        </fields>
        <showFooter>true</showFooter>
        <showHeader>true</showHeader>
    </screens>
    <screens>
        <name>Fault_Notice</name>
        <label>Something Went Wrong</label>
        <locationX>500</locationX>
        <locationY>998</locationY>
        <allowBack>false</allowBack>
        <allowFinish>true</allowFinish>
        <allowPause>false</allowPause>
        <fields>
            <name>Fault_Text</name>
            <fieldText>We could not load the choices for this track. The training team has been notified.</fieldText>
            <fieldType>DisplayText</fieldType>
        </fields>
        <showFooter>true</showFooter>
        <showHeader>true</showHeader>
    </screens>
    <screens>
        <name>Offering_And_Details</name>
        <label>Pick an Offering</label>
        <locationX>176</locationX>
        <locationY>458</locationY>
        <allowBack>true</allowBack>
        <allowFinish>false</allowFinish>
        <allowPause>false</allowPause>
        <connector>
            <targetReference>Split_Accommodations</targetReference>
        </connector>
        <fields>
            <name>Select_Offering</name>
            <choiceReferences>Offering_Choices</choiceReferences>
            <dataType>String</dataType>
            <fieldText>Course offering</fieldText>
            <fieldType>DropdownBox</fieldType>
            <isRequired>true</isRequired>
        </fields>
        <fields>
            <name>Select_Cohort</name>
            <choiceReferences>Cohort_Choices</choiceReferences>
            <dataType>String</dataType>
            <fieldText>Cohort</fieldText>
            <fieldType>RadioButtons</fieldType>
            <isRequired>false</isRequired>
        </fields>
        <fields>
            <name>Select_Accommodations</name>
            <choiceReferences>Choice_Interpreter</choiceReferences>
            <choiceReferences>Choice_Step_Free</choiceReferences>
            <choiceReferences>Choice_Large_Print</choiceReferences>
            <dataType>String</dataType>
            <fieldText>Accommodations needed</fieldText>
            <fieldType>MultiSelectCheckboxes</fieldType>
            <isRequired>false</isRequired>
        </fields>
        <showFooter>true</showFooter>
        <showHeader>true</showHeader>
    </screens>
    <screens>
        <name>Track_And_Mode</name>
        <label>Choose Your Track</label>
        <locationX>176</locationX>
        <locationY>242</locationY>
        <allowBack>true</allowBack>
        <allowFinish>false</allowFinish>
        <allowPause>false</allowPause>
        <connector>
            <targetReference>Get_Open_Cohorts</targetReference>
        </connector>
        <fields>
            <name>Select_Track</name>
            <choiceReferences>Track_Choices</choiceReferences>
            <dataType>String</dataType>
            <fieldText>Training track</fieldText>
            <fieldType>DropdownBox</fieldType>
            <isRequired>true</isRequired>
        </fields>
        <fields>
            <name>Select_Mode</name>
            <choiceReferences>Choice_Instructor_Led</choiceReferences>
            <choiceReferences>Choice_Self_Paced</choiceReferences>
            <choiceReferences>Choice_Other_Mode</choiceReferences>
            <dataType>String</dataType>
            <defaultSelectedChoiceReference>Choice_Instructor_Led</defaultSelectedChoiceReference>
            <fieldText>Delivery mode</fieldText>
            <fieldType>RadioButtons</fieldType>
            <isRequired>true</isRequired>
        </fields>
        <showFooter>true</showFooter>
        <showHeader>true</showHeader>
    </screens>
    <screens>
        <name>Waitlist_Notice</name>
        <label>Added to the Waitlist</label>
        <locationX>50</locationX>
        <locationY>890</locationY>
        <allowBack>false</allowBack>
        <allowFinish>true</allowFinish>
        <allowPause>false</allowPause>
        <fields>
            <name>Waitlist_Text</name>
            <fieldText>That offering is full. Go back and pick another date, or ask for the self-paced track.</fieldText>
            <fieldType>DisplayText</fieldType>
        </fields>
        <showFooter>true</showFooter>
        <showHeader>true</showHeader>
    </screens>
    <start>
        <locationX>50</locationX>
        <locationY>0</locationY>
        <connector>
            <targetReference>Track_And_Mode</targetReference>
        </connector>
    </start>
    <status>Draft</status>
    <variables>
        <name>varAccommodationList</name>
        <dataType>String</dataType>
        <isCollection>true</isCollection>
        <isInput>false</isInput>
        <isOutput>false</isOutput>
    </variables>
    <variables>
        <name>varEnrollmentId</name>
        <dataType>String</dataType>
        <isCollection>false</isCollection>
        <isInput>false</isInput>
        <isOutput>true</isOutput>
    </variables>
    <variables>
        <name>varOfferingId</name>
        <dataType>String</dataType>
        <isCollection>false</isCollection>
        <isInput>false</isInput>
        <isOutput>false</isOutput>
    </variables>
    <variables>
        <name>varOfferingLocation</name>
        <dataType>String</dataType>
        <isCollection>false</isCollection>
        <isInput>false</isInput>
        <isOutput>false</isOutput>
    </variables>
    <variables>
        <name>varOpenCohorts</name>
        <dataType>SObject</dataType>
        <isCollection>true</isCollection>
        <isInput>false</isInput>
        <isOutput>false</isOutput>
        <objectType>Training_Cohort__c</objectType>
    </variables>
    <variables>
        <name>varSeatsRemaining</name>
        <dataType>Number</dataType>
        <isCollection>false</isCollection>
        <isInput>false</isInput>
        <isOutput>false</isOutput>
        <scale>0</scale>
    </variables>
</Flow>
```

### How to read it

- **`Track_Choices` is a picklist choice set** because it sets `picklistField` **and**
  `picklistObject`, and for exactly that reason it carries `dataType` `Picklist`: "If a dynamic
  choice has the `picklistField` and `picklistObject` parameters set, it's a picklist choice and it
  **must** have a data type of `Picklist` or `Multipicklist`" (`api_meta.txt` L70273–L70276).
  `filters`, `limit`, `object`, `outputAssignments`, `sortField`, `sortOrder`, `displayField` and
  `valueField` are all "Not supported for picklist choices" — a picklist choice set has no query to
  shape (L70303–L70386). `picklistField` / `picklistObject` are API 35.0 and later (L70349,
  L70360).
- **`Offering_Choices` is a record choice set** because it sets `object` and no `picklistField`, and
  for exactly that reason it *cannot* carry `dataType` `Picklist` or `Multipicklist` (L70269–L70272).
  `displayField` is what the user reads, `valueField` is what the flow stores — "the `displayField`
  could be the account 'Name' while the `valueField` is the account 'Id'" (L70383–L70386).
- **The dependency is one `filters` entry.** `FlowRecordFilter.value` is a
  `FlowElementReferenceOrValue` (L71069–L71090), so `<elementReference>Select_Track</elementReference>`
  points the second screen's query at the first screen's stored choice value. No reactive component,
  no subflow, no Apex — the choice set re-queries when its screen renders.
- **`limit` 25 is deliberate.** `limit` is an `int` whose "Maximum **and default**: 200"
  (L70319–L70321) — omitting it does not mean "all rows", it means 200 rows fetched per render. It
  has been available since API 25.0 and nillable since API 45.0 (L70323–L70325).
- **`sortField` + `sortOrder` run before `limit`:** "If `sortField` and `sortOrder` are also
  specified, the records are sorted before the limit takes effect" (L70321–L70322). Without them
  "the returned records aren't sorted" (L70367–L70379), so a `limit` alone gives an arbitrary N, not
  a top N. `sortField` only accepts fields carrying the Sort API field property (L70370–L70372).
- **`outputAssignments` fire on selection, not on render.** Each entry needs `assignToReference` and
  `field`, both required (L70813–L70823); the guide's example is assigning "the ID and AnnualRevenue
  from the user-selected account to variables" (L70333–L70340). That is how `varSeatsRemaining`
  reaches the `Route_On_Choices` decision without a second Get Records.
- **`Cohort_Choices` is a collection choice set** — `collectionReference` names the record collection
  that Get Records filled, and is available in API version 54.0 and later (L70278–L70280).
  `UNVERIFIED (2026-09-05)`: the guide documents `collectionReference` and the `Record` `dataType`
  (API 54.0+, L70298–L70301) but never states which of `dataType` / `displayField` / `valueField` a
  *collection* choice set requires — the field table qualifies them only as "Required for record
  choices" / "Not supported for picklist choices". The `String` + `displayField` + `valueField`
  combination above is the shape Flow Builder round-trips; retrieve after the first save and diff.
- **`Select_Track` declares `dataType` `String`, not `Picklist`.** `FlowScreenField.dataType` has a
  different, shorter enum than `FlowDynamicChoiceSet.dataType`: Boolean, Currency, Date, DateTime,
  Number, String, Time (L71611–L71621). There is no `Picklist` value. Copying the choice set's
  `Picklist` onto the field is the single most common deploy failure in this area — see
  `references/gotchas.md` Gotcha 8.
- **`Select_Accommodations` stores one semicolon-joined string.** "At runtime, each multi-select
  field stores its field value as a concatenation of the user-selected choice values, separated by
  semicolons. Any semicolons in the selected choice values are removed when added to the multi-select
  field value" (L71714–L71720), and "only the string data type is supported for multi-select
  checkboxes and multi-select picklist fields" (L71625–L71628). `fxNeedsInterpreter` tests it with
  `CONTAINS`, `fxAccommodationText` makes it readable with `SUBSTITUTE`, and the Assignment's `Add`
  operator appends one literal to `varAccommodationList` — see §3 for why that is the only route to a
  real collection.
- **`Select_Mode` names one default.** `defaultSelectedChoiceReference` is supported on
  RadioButtons, DropdownBox, MultiSelectCheckboxes and MultiSelectPicklist, and it must name a
  `FlowChoice` — "you can specify only **one** FlowChoice element as the default value for
  multi-select checkboxes and multi-select picklist fields" (L71634–L71659). `Select_Offering`
  deliberately omits it: "For DropdownBox field types only, if `defaultSelectedChoiceReference` is
  empty or null, the reference at index 0 of `choiceReferences` is used as the default value"
  (L71642–L71646) — a record choice set's first sorted row becomes the default whether you meant it
  to or not.
- **`Choice_Other_Mode` carries a `userInput`.** `FlowChoiceUserInput` adds `isRequired`,
  `promptText` and a `validationRule`, and "user input isn't supported for choices in multi-select
  fields" (L69902–L69920) — which is why it hangs off a RadioButtons choice and not one of the three
  accommodation choices. `UNVERIFIED (2026-09-05)`: the guide states `formulaExpression` is "a
  formula that's used to validate the user input" (L70686–L70694) but never prints what the formula
  references for a *choice* user input; `{!Select_Mode}` is the screen-field reference and should be
  confirmed in a debug run before you rely on the message firing.
- **Both screens set `allowFinish` false and `allowBack` true; the terminal screens invert it.** "You
  can set either `allowBack` or `allowFinish` to false, but not both" (L71434–L71464). `allowPause`
  is false throughout because a paused interview resumes with re-rendered choice sets — see Gotcha 4.
- **`Log_Choice_Fault` is reachable from both the Get Records and the Create.** `FlowRecordLookup`
  and `FlowRecordCreate` both declare `faultConnector` (L71120, L70965); `FlowDynamicChoiceSet`
  extends `FlowElement`, not `FlowNode`, so **it has no `faultConnector` of its own** — a choice
  set's query failure surfaces on the screen that renders it, not on a fault path you can route.

---

## 2. Variant — a picklist choice set on a `Multipicklist` field

The only shape change when the source field is a multi-select picklist:

```xml
<dynamicChoiceSets>
    <name>Skill_Tag_Choices</name>
    <dataType>Multipicklist</dataType>
    <picklistField>Skill_Tags__c</picklistField>
    <picklistObject>Enrollment_Request__c</picklistObject>
</dynamicChoiceSets>
```

`Multipicklist` is a `FlowDynamicChoiceSet.dataType` value for picklist choices only, available in
API 35.0 and later (L70290–L70301). The screen field consuming it is still
`<dataType>String</dataType>` with `fieldType` `MultiSelectPicklist`, and the flow **variable** that
holds it may be `dataType` `Multipicklist` (a `FlowVariable` value since API 34.0, L72862–L72884) —
which is the only variable type the `AddItem` assignment operator accepts, since `AddItem` "adds the
value to the picklist, **including the semicolon** that's required to mark a value as a separate
item" (L69798–L69802).

`UNVERIFIED (2026-09-05)`: nothing in the Metadata API guide states whether a picklist choice set is
scoped to the running user's **record type** or returns the field's full value set. The
`picklistField` / `picklistObject` descriptions name a field and an object and no record type
(L70341–L70360), and `FlowDynamicChoiceSet` has no record-type field. Record-type-scoped picklist
values are documented on help.salesforce.com, which cannot be fetched here — treat the choice set as
full-value-set until a debug run under a restricted record type proves otherwise, and see
`admin/picklist-and-value-sets` for the value-set design.

---

## 3. Turning the semicolon string into a real collection

The Metadata API guide enumerates **no** split. `FlowAssignmentOperator` has fifteen values —
`Add`, `AddAtStart`, `AddItem`, `Assign`, `AssignCount`, `RemoveAfterFirst`, `RemoveAll`,
`RemoveBeforeFirst`, `RemoveFirst`, `RemovePosition`, `RemoveUncommon`, `Subtract` and the
collection variants (L69767–L69865) — and none of them decomposes a delimited string.
`FlowFormula.dataType` is Boolean, Currency, Date, DateTime, Number, String or Time (L70596–L70612):
a formula returns one scalar, never a collection.

So the semicolon string is decomposed **one membership test at a time**, which is exactly what the
flow above does:

```xml
<formulas>
    <name>fxNeedsStepFree</name>
    <dataType>Boolean</dataType>
    <expression>CONTAINS({!Select_Accommodations}, &quot;Step Free&quot;)</expression>
</formulas>
```

…then a Decision on `fxNeedsStepFree` routing to an Assignment with `Add` and a `<stringValue>`
literal. `Add` "appends the value to the end of the collection" when `assignToReference` is a
collection variable (L69783–L69790). Three accommodations means three Decision/Assignment pairs.

Two consequences worth designing around:

1. **Do not pass a collection variable as the `value` of an `Add`.** Support for that exists "in API
   version 43.0 and later, **but only via Metadata API**. From Flow Builder, you can't save an
   Assignment element that contains a collection variable in the Value column for the `Add`
   operator" (L69786–L69790). Hand-written XML that does it deploys and then makes the flow
   un-editable in Builder.
2. **If the downstream consumer accepts a delimited string, skip the decomposition entirely.** A
   Decision using the `Contains` comparison operator (`FlowComparisonOperator`, L70066–L70110) reads
   the semicolon string directly, and `AddItem` on a `Multipicklist` variable rebuilds one.

---

## 4. `package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Course_Offering__c</members>
        <members>Training_Cohort__c</members>
        <members>Enrollment_Request__c</members>
        <members>Application_Log__c</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>Enrollment_Request_Intake</members>
        <name>Flow</name>
    </types>
    <version>63.0</version>
</Package>
```

The `Flow` member carries **no version number**: from API 44.0 "the field no longer includes the
version number", the `flowDefinitions` directory must be empty, and the file must be
`Enrollment_Request_Intake.flow-meta.xml` rather than `…-1.flow-meta.xml` (`api_meta.txt`
L73175–L73198). A flow deployed with no `<status>` value lands as `Draft` (L73187–L73188).

---

## 5. Deploy order

Choice sets resolve object and field names at **deploy** time, so nothing about them is
order-tolerant.

| # | What | Why it must come first |
|---|---|---|
| 1 | `Course_Offering__c`, `Training_Cohort__c`, `Enrollment_Request__c`, `Application_Log__c` and every field named in §0 | `object`, `picklistObject`, `displayField`, `valueField`, `sortField`, `filters/field` and `outputAssignments/field` are all name references validated at deploy |
| 2 | The `Training_Track__c` value set on **both** `Enrollment_Request__c` and `Course_Offering__c` | Screen 1 stores the API value; screen 2's `filters` compares against it. A mismatch deploys clean and returns zero choices |
| 3 | FLS on `Seats_Remaining__c` and `Location_Name__c` for the running user's permission set | `outputAssignments` reads fields the user may not have; the flow's `runInMode` decides whether that is enforced |
| 4 | `Enrollment_Request_Intake.flow-meta.xml` with `<status>Draft</status>` | Deploy inactive, debug-run it (§6), then activate |

```bash
# Retrieve the flow after the first save in Flow Builder and diff against this file
sf project retrieve start --metadata Flow:Enrollment_Request_Intake

# Validate without committing
sf project deploy start --manifest manifest/package.xml --dry-run

# Deploy
sf project deploy start --manifest manifest/package.xml
```

Before either deploy, run the package checker over the source tree:

```bash
python3 skills/flow/flow-dynamic-choices/scripts/check_flow_dynamic_choices.py \
    --manifest-dir force-app --strict
```

---

## 6. Verifying it worked — a debug-run checklist, not a `FlowTest`

**`FlowTest` does not cover screen flows.** The guide's own scope sentence: "Before you activate a
**record-triggered, autolaunched, or Data Cloud-triggered** flow, you can test it to verify its
expected results and identify flow run-time failures" (`api_meta.txt` L73960–L73962). `processType`
here is `Flow` — "a flow that requires user interaction because it contains one or more screens or
local actions, choices, or dynamic choices. In the UI and Salesforce Help, it's a screen flow"
(L68270–L68274). So there is no `.flowtest-meta.xml` in this package, and any generated one that
names this flow is dead metadata. See `flow/flow-testing` for what `FlowTest` *does* cover.

What replaces it, in order:

1. **Debug the flow in Flow Builder as the least-privileged persona**, not as the admin who built
   it. Record for each screen: how many choices rendered, and whether the label came from
   `displayField` while the stored value came from `valueField`.
2. **Turn on a Workflow debug log at FINER or finer and read `FLOW_ELEMENT_LIMIT_USAGE`.** That
   event reports "incremented usage toward a limit for this element" across SOQL queries, SOQL query
   rows, DML statements, CPU time and heap (`apexdev.txt` L38795–L38805). It is how you find out
   what one screen render of two choice sets actually costs.
   `UNVERIFIED (2026-09-05)`: neither the Metadata API guide nor the Apex Developer Guide states
   that each record choice set issues one SOQL query per screen render. `FLOW_ELEMENT_LIMIT_USAGE`
   is the instrument that settles it for your org — read the delta across a screen with one choice
   set and the same screen with two.
3. **Go back and forward across screen 2.** `allowBack` is true, so the choice sets re-render. Check
   whether the previous selection survived: `inputsOnNextNavToAssocScrn` defaults to
   `UseStoredValues` and the alternative is `ResetValues` (L71733–L71745).
   `UNVERIFIED (2026-09-05)`: the guide states this property "applies to screen components in API
   version 51.0 and later and to record fields on flow screens in API version 57.0 and later"
   without saying whether a plain `DropdownBox` counts as a "screen component" for this purpose. The
   guide's own sample only sets it on `ComponentInstance` fields (L73505, L73545). Confirm in the
   debug run rather than assuming.
4. **Change a `Course_Offering__c` record to `Is_Open__c = false` mid-interview**, then navigate back
   and forward. A record choice set re-queries; a stale stored value that no longer appears in the
   set is the failure mode Gotcha 3 describes.
5. **Select every accommodation, then read the created record:**

   ```sql
   SELECT Id, Training_Track__c, Course_Offering__r.Name, Cohort__r.Cohort_Label__c,
          Delivery_Mode__c, Accommodations__c
   FROM Enrollment_Request__c
   WHERE CreatedDate = TODAY
   ORDER BY CreatedDate DESC
   LIMIT 5
   ```

   `Accommodations__c` should read `Interpreter, Step Free, Large Print` — the `SUBSTITUTE` output.
   If it reads `Interpreter;Step Free;Large Print`, the formula was bypassed and the raw multi-select
   value was written.
6. **Confirm the empty-set path.** Pick a track with no open offering. The second screen must render
   *something* — `Select_Offering` is `isRequired` `true` over an empty choice set, which is a screen
   the user cannot leave. Route around it with a Decision on the Get Records result before the
   screen, not with a message on it.
7. **Confirm the fault path.** Deny the running user read on `Training_Cohort__c` and re-run; the Get
   Records `faultConnector` should land on `Fault_Notice` and write one `Application_Log__c` row.
