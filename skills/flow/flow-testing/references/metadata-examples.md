# Metadata Examples — Flow Testing

Deployable artifacts for the test surface this skill owns: a record-triggered flow, the
two `FlowTest` components that prove its branches, an autolaunched flow, and the Apex
test class that drives that autolaunched flow through `Flow.Interview`.

Object model is `Warranty_Claim__c` (custom) plus the repo-canonical `Application_Log__c`
fault sink. Deliberately different from the models the sibling skills use, so the four
flow packages can be read side by side without collision:
`flow/record-triggered-flow-patterns` (Opportunity), `flow/flow-loop-element-patterns`
(`Grant_Application__c`), `flow/fault-handling` (`Payment__c`).

**What FlowTest can and cannot reach.** "Before you activate a record-triggered,
autolaunched, or Data Cloud-triggered flow, you can test it to verify its expected results
and identify flow run-time failures" (`api_meta.txt` L73961–73962). Screen flows,
scheduled-only flows and platform-event-triggered flows are **not** in that list — the
Apex path in §5 is the only automated coverage they get.

---

## 1. `Warranty_Claim_AfterSave_TierApproval.flow-meta.xml`

The flow under test. Two branches, one shared Update, one fault route — the smallest shape
that needs more than one `FlowTest` to be honestly covered.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>66.0</apiVersion>
    <description>Stamps Approval_Tier__c when a submitted warranty claim changes amount. Covered by Warranty_Claim_Tier_Escalates_Above_10k and Warranty_Claim_Tier_Holds_At_Threshold.</description>
    <assignments>
        <name>Assign_Escalated_Tier</name>
        <label>Assign Escalated Tier</label>
        <locationX>50</locationX>
        <locationY>350</locationY>
        <assignmentItems>
            <assignToReference>assignedTier</assignToReference>
            <operator>Assign</operator>
            <value>
                <stringValue>Escalated</stringValue>
            </value>
        </assignmentItems>
        <connector>
            <targetReference>Set_Claim_Tier</targetReference>
        </connector>
    </assignments>
    <assignments>
        <name>Assign_Standard_Tier</name>
        <label>Assign Standard Tier</label>
        <locationX>310</locationX>
        <locationY>350</locationY>
        <assignmentItems>
            <assignToReference>assignedTier</assignToReference>
            <operator>Assign</operator>
            <value>
                <stringValue>Standard</stringValue>
            </value>
        </assignmentItems>
        <connector>
            <targetReference>Set_Claim_Tier</targetReference>
        </connector>
    </assignments>
    <decisions>
        <name>Check_Claim_Amount</name>
        <label>Check Claim Amount</label>
        <locationX>176</locationX>
        <locationY>230</locationY>
        <defaultConnector>
            <targetReference>Assign_Standard_Tier</targetReference>
        </defaultConnector>
        <defaultConnectorLabel>At or below threshold</defaultConnectorLabel>
        <rules>
            <name>Above_Escalation_Threshold</name>
            <conditionLogic>and</conditionLogic>
            <conditions>
                <leftValueReference>$Record.Claim_Amount__c</leftValueReference>
                <operator>GreaterThan</operator>
                <rightValue>
                    <numberValue>10000.0</numberValue>
                </rightValue>
            </conditions>
            <connector>
                <targetReference>Assign_Escalated_Tier</targetReference>
            </connector>
            <label>Above escalation threshold</label>
        </rules>
    </decisions>
    <environments>Default</environments>
    <interviewLabel>Warranty Claim Tier Approval {!$Flow.CurrentDateTime}</interviewLabel>
    <label>Warranty Claim AfterSave Tier Approval</label>
    <processType>AutoLaunchedFlow</processType>
    <recordCreates>
        <name>Log_Tier_Failure</name>
        <label>Log Tier Failure</label>
        <locationX>440</locationX>
        <locationY>470</locationY>
        <inputAssignments>
            <field>Flow_API_Name__c</field>
            <value>
                <stringValue>Warranty_Claim_AfterSave_TierApproval</stringValue>
            </value>
        </inputAssignments>
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
        <object>Application_Log__c</object>
        <storeOutputAutomatically>true</storeOutputAutomatically>
    </recordCreates>
    <recordUpdates>
        <name>Set_Claim_Tier</name>
        <label>Set Claim Tier</label>
        <locationX>176</locationX>
        <locationY>470</locationY>
        <faultConnector>
            <targetReference>Log_Tier_Failure</targetReference>
        </faultConnector>
        <inputAssignments>
            <field>Approval_Tier__c</field>
            <value>
                <elementReference>assignedTier</elementReference>
            </value>
        </inputAssignments>
        <inputReference>$Record</inputReference>
    </recordUpdates>
    <runInMode>DefaultMode</runInMode>
    <start>
        <locationX>176</locationX>
        <locationY>50</locationY>
        <connector>
            <targetReference>Check_Claim_Amount</targetReference>
        </connector>
        <doesRequireRecordChangedToMeetCriteria>true</doesRequireRecordChangedToMeetCriteria>
        <filterLogic>and</filterLogic>
        <filters>
            <field>Status__c</field>
            <operator>EqualTo</operator>
            <value>
                <stringValue>Submitted</stringValue>
            </value>
        </filters>
        <object>Warranty_Claim__c</object>
        <recordTriggerType>Update</recordTriggerType>
        <triggerType>RecordAfterSave</triggerType>
    </start>
    <status>Draft</status>
    <variables>
        <name>assignedTier</name>
        <dataType>String</dataType>
        <isCollection>false</isCollection>
        <isInput>false</isInput>
        <isOutput>false</isOutput>
    </variables>
</Flow>
```

### How to read it

- **`<status>Draft</status>` is the point of the exercise.** `FlowVersionStatus` accepts
  `Active`, `Draft` (shown as Inactive in the UI), `Obsolete`, `InvalidDraft`, and
  `UnderReview` (`api_meta.txt` L68416–68425). FlowTest exists to be run *before* you
  flip that value — "before you activate a record-triggered, autolaunched, or Data
  Cloud-triggered flow, you can test it" (`api_meta.txt` L73961–73962).
- **`assignedTier` is a flow-scoped variable that exists only so the test has a surface.**
  `testPoints.elementApiName` accepts only `Start` and `Finish` (`api_meta.txt`
  L74133–74142), so a `FlowTest` cannot assert mid-flow. A named variable that each branch
  writes is how you tell which branch ran from the `Finish` point.
- **`<faultConnector>` on `Set_Claim_Tier` is what makes the `HasError` assertion in §2
  meaningful.** `faultConnector` "specifies which node to execute if the attempt to
  create a record results in an error" (`api_meta.txt` L70965–70967, and the parallel
  entry for update at L71120). Without it the interview dies and there is nothing to
  assert against.
- **`<recordTriggerType>Update</recordTriggerType>` with `RecordAfterSave` is what makes
  the paired `InputTriggeringRecordInitial` / `InputTriggeringRecordUpdated` test
  parameters legal.** The guide's own `recordTriggerType` entry narrows availability to
  `RecordBeforeSave` or `DataCloudDataChange` (`api_meta.txt` L72458–72461);
  `flow/record-triggered-flow-patterns` documents that discrepancy — this skill does not
  restate it.
- **Element and variable API names are the test's public contract.** Renaming
  `assignedTier` or `Set_Claim_Tier` silently breaks every `leftValueReference` in §2 and
  §3, because those are strings, not references the deployer resolves.

---

## 2. `Warranty_Claim_Tier_Escalates_Above_10k.flowtest-meta.xml`

Happy path. Two test points, assertions on **both** `Start` and `Finish`.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<FlowTest xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>A submitted claim whose amount rises from 4,000 to 25,000 must land in the Escalated tier without taking the fault route.</description>
    <flowApiName>Warranty_Claim_AfterSave_TierApproval</flowApiName>
    <label>Tier escalates above 10k</label>
    <testPoints>
        <assertions>
            <conditions>
                <leftValueReference>$Record.Status__c</leftValueReference>
                <operator>EqualTo</operator>
                <rightValue>
                    <stringValue>Submitted</stringValue>
                </rightValue>
            </conditions>
            <errorMessage>The updated record does not satisfy the Start entry filter Status__c = Submitted, so this test proves nothing about the branch below it.</errorMessage>
        </assertions>
        <elementApiName>Start</elementApiName>
        <parameters>
            <leftValueReference>$Record</leftValueReference>
            <type>InputTriggeringRecordInitial</type>
            <value>
                <sobjectValue>{&quot;Name&quot;:&quot;WC-10041&quot;,&quot;Status__c&quot;:&quot;Submitted&quot;,&quot;Claim_Amount__c&quot;:4000,&quot;Approval_Tier__c&quot;:&quot;Standard&quot;}</sobjectValue>
            </value>
        </parameters>
        <parameters>
            <leftValueReference>$Record</leftValueReference>
            <type>InputTriggeringRecordUpdated</type>
            <value>
                <sobjectValue>{&quot;Name&quot;:&quot;WC-10041&quot;,&quot;Status__c&quot;:&quot;Submitted&quot;,&quot;Claim_Amount__c&quot;:25000,&quot;Approval_Tier__c&quot;:&quot;Standard&quot;}</sobjectValue>
            </value>
        </parameters>
    </testPoints>
    <testPoints>
        <assertions>
            <conditions>
                <leftValueReference>assignedTier</leftValueReference>
                <operator>EqualTo</operator>
                <rightValue>
                    <stringValue>Escalated</stringValue>
                </rightValue>
            </conditions>
            <errorMessage>Check_Claim_Amount routed to the default outcome. Claim_Amount__c 25000 must satisfy GreaterThan 10000.</errorMessage>
        </assertions>
        <assertions>
            <conditions>
                <leftValueReference>$Record.Approval_Tier__c</leftValueReference>
                <operator>EqualTo</operator>
                <rightValue>
                    <stringValue>Escalated</stringValue>
                </rightValue>
            </conditions>
            <errorMessage>The variable was set but Set_Claim_Tier did not write it to the record. Check inputReference and inputAssignments.</errorMessage>
        </assertions>
        <assertions>
            <conditions>
                <leftValueReference>Set_Claim_Tier</leftValueReference>
                <operator>HasError</operator>
                <rightValue>
                    <booleanValue>false</booleanValue>
                </rightValue>
            </conditions>
            <errorMessage>Set_Claim_Tier faulted and the interview took the Log_Tier_Failure route. Read the Application_Log__c row before reading this assertion.</errorMessage>
        </assertions>
        <elementApiName>Finish</elementApiName>
    </testPoints>
    <testType>WithAssertion</testType>
</FlowTest>
```

### How to read it

- **Two `testPoints`, evaluated in order.** "Salesforce evaluates each test point in the
  order that it's listed" (`api_meta.txt` L74130–74132). `elementApiName` is required and
  accepts only `Start` and `Finish` (L74143–74150).
- **`FlowTestPoint` carries both `assertions` and `parameters`** (`api_meta.txt`
  L74133–74156), which is why the `Start` point above asserts as well as feeds. Asserting
  the entry-criteria precondition at `Start` is what stops a green test that never entered
  the flow from reading as coverage.
- **The `Start` point takes the before *and* after image.** `FlowTestParameter.type` is
  required; `InputTriggeringRecordInitial` and `InputTriggeringRecordUpdated` both demand
  `leftValueReference` = `$Record` (`api_meta.txt` L74296–74320). Supplying only the
  initial image tests a create, not an update.
- **`sobjectValue` is a JSON *string*, so its quotes are XML-escaped as `&quot;`** — the
  guide's own sample does exactly this (`api_meta.txt` L74349–74360).
- **`HasError` against an element API name is available from API version 64.0**
  (`api_meta.txt` L74196). Asserting it is `false` is how you prove the happy path stayed
  happy rather than quietly logging and finishing.
- **One failed assertion fails the run.** "If one assertion evaluates to false, the test
  run fails" (`api_meta.txt` L74157–74159), and "if one condition evaluates to false, the
  assertion fails" (L74181–74183). `errorMessage` is the only diagnostic Flow Builder
  shows, so write it as the next reader's first clue, not as a restatement of the
  condition.

---

## 3. `Warranty_Claim_Tier_Holds_At_Threshold.flowtest-meta.xml`

The negative path — the branch that must **not** fire. Boundary value 10,000 exactly,
because `GreaterThan` excludes it.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<FlowTest xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Negative path. A claim rising to exactly the 10,000 threshold must stay Standard, must not reach the escalation assignment, and must not enter the fault route.</description>
    <flowApiName>Warranty_Claim_AfterSave_TierApproval</flowApiName>
    <label>Tier holds at threshold</label>
    <testPoints>
        <elementApiName>Start</elementApiName>
        <parameters>
            <leftValueReference>$Record</leftValueReference>
            <type>InputTriggeringRecordInitial</type>
            <value>
                <sobjectValue>{&quot;Name&quot;:&quot;WC-10042&quot;,&quot;Status__c&quot;:&quot;Submitted&quot;,&quot;Claim_Amount__c&quot;:9000,&quot;Approval_Tier__c&quot;:&quot;Standard&quot;}</sobjectValue>
            </value>
        </parameters>
        <parameters>
            <leftValueReference>$Record</leftValueReference>
            <type>InputTriggeringRecordUpdated</type>
            <value>
                <sobjectValue>{&quot;Name&quot;:&quot;WC-10042&quot;,&quot;Status__c&quot;:&quot;Submitted&quot;,&quot;Claim_Amount__c&quot;:10000,&quot;Approval_Tier__c&quot;:&quot;Standard&quot;}</sobjectValue>
            </value>
        </parameters>
    </testPoints>
    <testPoints>
        <assertions>
            <conditions>
                <leftValueReference>assignedTier</leftValueReference>
                <operator>NotEqualTo</operator>
                <rightValue>
                    <stringValue>Escalated</stringValue>
                </rightValue>
            </conditions>
            <errorMessage>10000 is not GreaterThan 10000. If this fails, the Decision rule was widened to GreaterThanOrEqualTo and every claim at the threshold now escalates.</errorMessage>
        </assertions>
        <assertions>
            <conditions>
                <leftValueReference>$Record.Approval_Tier__c</leftValueReference>
                <operator>EqualTo</operator>
                <rightValue>
                    <stringValue>Standard</stringValue>
                </rightValue>
            </conditions>
            <errorMessage>The default outcome ran but Set_Claim_Tier wrote something other than Standard. assignedTier was probably left null by an unconnected default branch.</errorMessage>
        </assertions>
        <assertions>
            <conditions>
                <leftValueReference>Log_Tier_Failure</leftValueReference>
                <operator>WasVisited</operator>
                <rightValue>
                    <booleanValue>false</booleanValue>
                </rightValue>
            </conditions>
            <errorMessage>The fault route ran on a path that cannot legitimately fail. An Application_Log__c row exists for a clean save.</errorMessage>
        </assertions>
        <elementApiName>Finish</elementApiName>
    </testPoints>
    <testType>WithAssertion</testType>
</FlowTest>
```

### How to read it

- **Boundary, not midpoint.** `GreaterThan` and `GreaterThanOrEqualTo` are separate
  `FlowComparisonOperator` values (`api_meta.txt` L74190–74195). A test at 5,000 passes
  under either one and so proves nothing about which was configured; a test at exactly
  10,000 fails the moment someone widens the rule.
- **`NotEqualTo` is the assertion that catches a silently-widened branch.** Asserting
  `EqualTo Standard` alone would also pass if `assignedTier` were left null by a broken
  default connector, which is why both assertions are present.
- `WasVisited` is a documented `FlowComparisonOperator` (`api_meta.txt` L74208).
  **UNVERIFIED (2026-09-05):** the guide lists `WasVisited` among the operators a
  `FlowTestCondition` may use but ships no sample applying it to a flow *element* API
  name, and does not state whether `leftValueReference` in a `FlowTestCondition` may
  name an element rather than a resource. The `HasError` usage in §2 follows the same
  shape and is equally unsampled. Run both tests once in Flow Builder before treating
  either assertion as load-bearing; if `WasVisited` is rejected, drop this assertion and
  assert on an `Application_Log__c` count in the SOQL verification below instead.

---

## 4. `Warranty_Claim_Assign_Adjuster.flow-meta.xml`

The autolaunched flow that §5's Apex test drives. It has **no** `triggerType`, which is
the whole reason `Flow.Interview` can start it: "if you exclude this field, the flow has
no trigger and starts only when a user or app launches the flow" (`api_meta.txt`
L72496–72499), and `start()` "can be used only with flows that have one of these types:
Autolaunched Flow, User Provisioning Flow" (`apexrefguide.txt` L158164–158177).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>66.0</apiVersion>
    <description>Autolaunched. Stamps an adjuster onto a warranty claim and returns the outcome through output variables so an Apex caller can assert on it.</description>
    <assignments>
        <name>Record_Assignment_Outcome</name>
        <label>Record Assignment Outcome</label>
        <locationX>176</locationX>
        <locationY>350</locationY>
        <assignmentItems>
            <assignToReference>assignedAdjusterId</assignToReference>
            <operator>Assign</operator>
            <value>
                <elementReference>adjusterId</elementReference>
            </value>
        </assignmentItems>
        <assignmentItems>
            <assignToReference>adjusterAssigned</assignToReference>
            <operator>Assign</operator>
            <value>
                <booleanValue>true</booleanValue>
            </value>
        </assignmentItems>
        <connector>
            <targetReference>Stamp_Adjuster</targetReference>
        </connector>
    </assignments>
    <decisions>
        <name>Claim_Found</name>
        <label>Claim Found</label>
        <locationX>176</locationX>
        <locationY>230</locationY>
        <defaultConnectorLabel>Not found</defaultConnectorLabel>
        <rules>
            <name>Found</name>
            <conditionLogic>and</conditionLogic>
            <conditions>
                <leftValueReference>Get_Claim.Id</leftValueReference>
                <operator>IsNull</operator>
                <rightValue>
                    <booleanValue>false</booleanValue>
                </rightValue>
            </conditions>
            <connector>
                <targetReference>Record_Assignment_Outcome</targetReference>
            </connector>
            <label>Found</label>
        </rules>
    </decisions>
    <environments>Default</environments>
    <interviewLabel>Assign Warranty Adjuster {!$Flow.CurrentDateTime}</interviewLabel>
    <label>Warranty Claim Assign Adjuster</label>
    <processType>AutoLaunchedFlow</processType>
    <recordCreates>
        <name>Log_Assign_Failure</name>
        <label>Log Assign Failure</label>
        <locationX>440</locationX>
        <locationY>470</locationY>
        <inputAssignments>
            <field>Flow_API_Name__c</field>
            <value>
                <stringValue>Warranty_Claim_Assign_Adjuster</stringValue>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Message__c</field>
            <value>
                <elementReference>$Flow.FaultMessage</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Related_Record_Id__c</field>
            <value>
                <elementReference>claimId</elementReference>
            </value>
        </inputAssignments>
        <object>Application_Log__c</object>
        <storeOutputAutomatically>true</storeOutputAutomatically>
    </recordCreates>
    <recordLookups>
        <name>Get_Claim</name>
        <label>Get Claim</label>
        <locationX>176</locationX>
        <locationY>110</locationY>
        <connector>
            <targetReference>Claim_Found</targetReference>
        </connector>
        <faultConnector>
            <targetReference>Log_Assign_Failure</targetReference>
        </faultConnector>
        <filterLogic>and</filterLogic>
        <filters>
            <field>Id</field>
            <operator>EqualTo</operator>
            <value>
                <elementReference>claimId</elementReference>
            </value>
        </filters>
        <getFirstRecordOnly>true</getFirstRecordOnly>
        <object>Warranty_Claim__c</object>
        <storeOutputAutomatically>true</storeOutputAutomatically>
    </recordLookups>
    <recordUpdates>
        <name>Stamp_Adjuster</name>
        <label>Stamp Adjuster</label>
        <locationX>176</locationX>
        <locationY>470</locationY>
        <faultConnector>
            <targetReference>Log_Assign_Failure</targetReference>
        </faultConnector>
        <inputAssignments>
            <field>Adjuster__c</field>
            <value>
                <elementReference>assignedAdjusterId</elementReference>
            </value>
        </inputAssignments>
        <inputReference>Get_Claim</inputReference>
    </recordUpdates>
    <runInMode>DefaultMode</runInMode>
    <start>
        <locationX>50</locationX>
        <locationY>50</locationY>
        <connector>
            <targetReference>Get_Claim</targetReference>
        </connector>
    </start>
    <status>Draft</status>
    <variables>
        <name>adjusterAssigned</name>
        <dataType>Boolean</dataType>
        <isCollection>false</isCollection>
        <isInput>false</isInput>
        <isOutput>true</isOutput>
    </variables>
    <variables>
        <name>adjusterId</name>
        <dataType>String</dataType>
        <isCollection>false</isCollection>
        <isInput>true</isInput>
        <isOutput>false</isOutput>
    </variables>
    <variables>
        <name>assignedAdjusterId</name>
        <dataType>String</dataType>
        <isCollection>false</isCollection>
        <isInput>false</isInput>
        <isOutput>true</isOutput>
    </variables>
    <variables>
        <name>claimId</name>
        <dataType>String</dataType>
        <isCollection>false</isCollection>
        <isInput>true</isInput>
        <isOutput>false</isOutput>
    </variables>
</Flow>
```

`isInput` "indicates whether the variable can be set at" interview start (`api_meta.txt`
L72886); only `isInput` variables can appear as keys in the Apex `inputVariables` map.

---

## 5. `WarrantyClaimAdjusterFlowTest.cls` — driving a flow from Apex

Test data comes from `templates/apex/tests/TestDataFactory.cls` (relative to repo root)
for the standard objects, extended locally for `Warranty_Claim__c`. Do not fork that file
— call it. See `apex/test-data-factory-patterns` for the extension pattern.

```apex
@IsTest
private class WarrantyClaimAdjusterFlowTest {

    // TestDataFactory owns the standard-object graph; only the custom object is local.
    // templates/apex/tests/TestDataFactory.cls
    private static Warranty_Claim__c newClaim(Decimal amount) {
        return new Warranty_Claim__c(
            Name = 'WC-' + String.valueOf(Crypto.getRandomInteger()).right(6),
            Status__c = 'Submitted',
            Claim_Amount__c = amount
        );
    }

    @TestSetup
    static void seed() {
        Account acct = TestDataFactory.createAccounts(1, new Map<String, Object>())[0];
        Warranty_Claim__c claim = newClaim(25000);
        claim.Account__c = acct.Id;
        insert claim;
    }

    @IsTest
    static void assignsAdjusterAndReturnsOutputVariables() {
        Warranty_Claim__c claim = [SELECT Id FROM Warranty_Claim__c LIMIT 1];
        Id adjuster = UserInfo.getUserId();

        Map<String, Object> inputs = new Map<String, Object>{
            'claimId'   => String.valueOf(claim.Id),
            'adjusterId'=> String.valueOf(adjuster)
        };

        // Static construction. The flow must exist at compile time, so a rename or a
        // delete breaks the build instead of failing at run time -- unlike
        // Flow.Interview.createInterview(), where "if you delete a flow, Salesforce
        // doesn't check if it's referenced" (apexrefguide.txt L157941-157945).
        Flow.Interview.Warranty_Claim_Assign_Adjuster run =
            new Flow.Interview.Warranty_Claim_Assign_Adjuster(inputs);

        Test.startTest();
        run.start();
        Test.stopTest();

        // getVariableValue returns Object and resolves at run time only, "not at compile
        // time" (apexrefguide.txt L158150-158153). A typo'd name returns null, not an
        // error -- so assert the value, never just that the call did not throw.
        Object assignedFlag = run.getVariableValue('adjusterAssigned');
        Assert.isNotNull(assignedFlag, 'adjusterAssigned came back null: the output variable is misspelled or is not marked isOutput.');
        Assert.areEqual(true, (Boolean) assignedFlag, 'Claim_Found routed to the default outcome; Get_Claim returned no record.');
        Assert.areEqual(
            String.valueOf(adjuster),
            (String) run.getVariableValue('assignedAdjusterId'),
            'The flow echoed back a different adjuster than the one passed in.'
        );

        // Output variables prove the interview's state. Only a query proves the DML.
        Warranty_Claim__c after = [SELECT Adjuster__c FROM Warranty_Claim__c WHERE Id = :claim.Id];
        Assert.areEqual(adjuster, after.Adjuster__c, 'Stamp_Adjuster did not commit; the interview may have taken the fault route to Log_Assign_Failure.');
        Assert.areEqual(0, [SELECT COUNT() FROM Application_Log__c], 'The fault route ran on the happy path.');
    }

    @IsTest
    static void unknownClaimIdLeavesTheRecordUntouched() {
        Warranty_Claim__c claim = [SELECT Id, Adjuster__c FROM Warranty_Claim__c LIMIT 1];

        Map<String, Object> inputs = new Map<String, Object>{
            'claimId'   => '',
            'adjusterId'=> String.valueOf(UserInfo.getUserId())
        };
        Flow.Interview.Warranty_Claim_Assign_Adjuster run =
            new Flow.Interview.Warranty_Claim_Assign_Adjuster(inputs);

        Test.startTest();
        run.start();
        Test.stopTest();

        Object assignedFlag = run.getVariableValue('adjusterAssigned');
        Assert.areNotEqual(true, assignedFlag, 'The flow reported an assignment for a claim id that matches nothing.');
        Warranty_Claim__c after = [SELECT Adjuster__c FROM Warranty_Claim__c WHERE Id = :claim.Id];
        Assert.isNull(after.Adjuster__c, 'The not-found branch still wrote to the record.');
    }
}
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>66.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

### How to read it

- **`Flow.Interview.<FlowApiName>` is the static form; `createInterview()` is the dynamic
  one.** The guide recommends the static form: `createInterview` requires adding the flow
  manually when the class is packaged, and deleting the flow is not checked against
  references (`apexrefguide.txt` L157938–157950). Static construction also gives you
  `run.myVar` directly, where the uncast `Flow.Interview` type forces
  `getVariableValue()` (L158080–158086).
- **`start()` is restricted to Autolaunched Flow and User Provisioning Flow**
  (`apexrefguide.txt` L158164–158177). This is why §1's record-triggered flow gets a
  `FlowTest` and not an Apex driver: there is no `start()` path to it. An Apex test
  exercises a record-triggered flow only indirectly, by doing the DML that triggers it.
- **Version selection differs by caller.** "When a flow user invokes an autolaunched flow,
  the active flow version runs. If there's no active version, the latest version runs.
  When a flow admin invokes a flow, the latest version always runs"
  (`apexrefguide.txt` L158178–158181). A test run by an admin and the same test run by an
  integration user can execute different flow versions.
- **Sharing is a deliberate declaration.** "To enforce sharing rules, run the flow or Apex
  on API version 62.0 or later. The Apex class must be declared using the `with sharing`
  keyword… Data access is restricted to the sharing rules of the user that executed the
  Apex class" (`apexrefguide.txt` L157958–157963). The test class above is left without a
  sharing declaration on purpose — add `with sharing` and wrap the interview in
  `System.runAs(standardUser)` when the flow's record access is the thing under test.
- **`Test.startTest()` / `Test.stopTest()` bracket the interview, not the setup.** The
  seed DML happens in `@TestSetup`, so the interview gets the fresh governor allowance;
  `FLOW_INTERVIEW_FINISHED_LIMIT_USAGE` in the debug log then reports the interview's own
  consumption of SOQL queries, DML statements, CPU time and heap
  (`apexdev.txt` L38821–38838).

---

## package.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Warranty_Claim__c</members>
        <members>Application_Log__c</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>Warranty_Claim_AfterSave_TierApproval</members>
        <members>Warranty_Claim_Assign_Adjuster</members>
        <name>Flow</name>
    </types>
    <types>
        <members>Warranty_Claim_Tier_Escalates_Above_10k</members>
        <members>Warranty_Claim_Tier_Holds_At_Threshold</members>
        <name>FlowTest</name>
    </types>
    <types>
        <members>WarrantyClaimAdjusterFlowTest</members>
        <name>ApexClass</name>
    </types>
    <version>66.0</version>
</Package>
```

`FlowTest` is a first-class manifest type — the guide's own sample manifest names it
directly and it "supports the wildcard character `*`" (`api_meta.txt` L74451–74466).
`FlowTest` members are the component full names, which are **not** the labels: the
`<label>` above is `Tier escalates above 10k`, the member and file name are
`Warranty_Claim_Tier_Escalates_Above_10k`.

## Deploy order

```bash
# 0. Lint before anything reaches an org. Exits 1 if --manifest-dir does not exist.
python3 skills/flow/flow-testing/scripts/check_flow_testing.py \
  --manifest-dir force-app/main/default

# 1. Objects and fields. A FlowTest whose sobjectValue names a field that does not exist
#    deploys clean and fails at run time, so the object has to be real first.
sf project deploy start --source-dir force-app/main/default/objects --target-org myorg

# 2. Flows, still Draft. FlowTest exists to run before activation, so do not ship Active.
sf project deploy start --source-dir force-app/main/default/flows --target-org myorg

# 3. FlowTests. flowApiName is a required reference to a flow that must already exist.
#    Components carry the .flowtest suffix and live in the flowtests folder
#    (api_meta.txt L73976-73978).
sf project deploy start --source-dir force-app/main/default/flowtests --target-org myorg

# 4. Apex last -- Flow.Interview.<FlowApiName> will not compile before step 2 lands.
sf project deploy start --source-dir force-app/main/default/classes --target-org myorg
```

## Verification

**1. Run the flow tests.** The `flowtesting` namespace "provides dynamically generated
Apex classes for flow tests that are created in Flow Builder… You can run flow tests with
the Salesforce CLI command `sf flow run test`" (`apexrefguide.txt` L158183–158187).

```bash
sf flow run test --target-org myorg
sf apex run test --class-names WarrantyClaimAdjusterFlowTest --result-format human --target-org myorg
```

**UNVERIFIED (2026-09-05):** the corpus names `sf flow run test` but documents none of its
flags — the guide's own instruction is "for more details about the command, use the
Salesforce CLI `--help` flag" (`apexrefguide.txt` L158186–158187). Whether it accepts a
`--flow-name`-style filter, and what its exit code is on assertion failure, is not stated
anywhere in these guides. Run `sf flow run test --help` before wiring it into CI and gate
on the observed exit code.

**2. Confirm both branches actually wrote.** After a manual smoke pass in the sandbox:

```soql
SELECT Approval_Tier__c, COUNT(Id)
FROM Warranty_Claim__c
WHERE Status__c = 'Submitted' AND LastModifiedDate = TODAY
GROUP BY Approval_Tier__c
```

Two rows — `Escalated` and `Standard` — means both Decision outcomes ran at least once.
One row means half the flow has never executed in this org, whatever the tests report.

**3. Confirm the fault route stayed quiet.**

```soql
SELECT Flow_API_Name__c, Message__c, CreatedDate
FROM Application_Log__c
WHERE Flow_API_Name__c IN ('Warranty_Claim_AfterSave_TierApproval', 'Warranty_Claim_Assign_Adjuster')
  AND CreatedDate = TODAY
ORDER BY CreatedDate DESC
```

Any row here is a fault the tests' `HasError` assertions were supposed to catch. If rows
exist and every test is green, the assertions are pointed at the wrong element name —
`leftValueReference` is a string and a typo asserts against nothing.

**4. Check flow coverage from the deploy result, not from a percentage.** A `DeployResult`
carries `flowCoverage` (`FlowCoverageResult[]`) and `flowCoverageWarnings`
(`FlowCoverageWarning[]`), both from API version 44.0 (`api_meta.txt` L7600–7606).
`FlowCoverageResult` reports `numElements`, `numElementsNotCovered` and
`elementsNotCovered` — the *names of the elements no test reached*
(`api_meta.txt` L7714–7736). That list, not a ratio, is the review artifact: read
`elementsNotCovered` and decide per element whether it needs a test.

The corpus states a 75% coverage requirement **for Apex only** — "unit tests must cover at
least 75% of your Apex code" (`apexdev.txt` L728, L773, L35283). **No required flow-test
coverage percentage for activating or deploying an active flow appears anywhere in
`api_meta.txt` or `apexdev.txt`.** `FlowCoverageWarning` exists and its `flowName` "is
null" when "the warning applies to the overall test coverage of flows within your org"
(`api_meta.txt` L7750–7753), which implies an org-level threshold exists somewhere — but
these guides never quantify it. Treat any specific percentage you see quoted as
unsourced until you find it in a Salesforce doc yourself.
