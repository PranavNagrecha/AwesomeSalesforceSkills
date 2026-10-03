# Metadata Examples: Agent Action Unit Tests

The complete, deployable version of the `CloseCaseAction` used in `references/examples.md`: the action, the validation rule its `VALIDATION_BLOCKED` branch depends on, the test class, and the manifest. Apex rules come from the Apex Developer Guide (InvocableMethod and InvocableVariable annotations, Testing Apex, Using the runAs Method, Execution Governors and Limits).

## 1. Validation rule the test relies on

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/objects/Case/validationRules/Closed_Case_Requires_Description.validationRule-meta.xml -->
<ValidationRule xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Closed_Case_Requires_Description</fullName>
    <active>true</active>
    <description>A case cannot be closed without a resolution description.</description>
    <errorConditionFormula>AND(ISPICKVAL(Status, &quot;Closed&quot;), ISBLANK(Description))</errorConditionFormula>
    <errorDisplayField>Description</errorDisplayField>
    <errorMessage>Add a resolution description before closing the case.</errorMessage>
</ValidationRule>
```

## 2. The action

```apex
// force-app/main/default/classes/CloseCaseAction.cls
public with sharing class CloseCaseAction {

    public class Request {
        @InvocableVariable(required=true label='Case Id' description='Record ID of the case to close.')
        public String caseId;
        @InvocableVariable(label='Resolution Note' description='One or two sentences describing how the issue was resolved.')
        public String resolutionNote;
    }

    public class Response {
        @InvocableVariable(label='Case Id' description='Echo of the requested case ID, so results line up with requests.')
        public String caseId;
        @InvocableVariable(label='Reason Code' description='CLOSED, VALIDATION_BLOCKED, or UNKNOWN.')
        public String reasonCode;
        @InvocableVariable(label='User Message' description='Short text the agent can say to the customer.')
        public String userMessage;
    }

    @InvocableMethod(
        label='Close Case'
        description='Use when the customer confirms their issue is resolved and asks to close the case. Requires a resolution note.'
    )
    public static List<Response> run(List<Request> requests) {
        // Pre-size the response list so every input gets exactly one output in the same position.
        List<Response> responses = new List<Response>();
        List<Case> toUpdate = new List<Case>();
        List<Integer> positions = new List<Integer>();

        for (Integer i = 0; i < requests.size(); i++) {
            Request req = requests[i];
            Response res = new Response();
            res.caseId = req == null ? null : req.caseId;
            res.reasonCode = 'UNKNOWN';
            res.userMessage = 'I could not close that case. A service rep will follow up.';
            responses.add(res);

            Id caseRecordId = toIdOrNull(req == null ? null : req.caseId);
            if (caseRecordId != null) {
                toUpdate.add(new Case(Id = caseRecordId, Status = 'Closed', Description = req.resolutionNote));
                positions.add(i);
            }
        }

        if (!toUpdate.isEmpty()) {
            List<Database.SaveResult> results = Database.update(toUpdate, false, AccessLevel.USER_MODE);
            for (Integer j = 0; j < results.size(); j++) {
                Response res = responses[positions[j]];
                if (results[j].isSuccess()) {
                    res.reasonCode = 'CLOSED';
                    res.userMessage = 'Your case is closed.';
                } else if (isValidationFailure(results[j])) {
                    res.reasonCode = 'VALIDATION_BLOCKED';
                    res.userMessage = 'I need a short description of how the issue was resolved before I can close the case.';
                }
            }
        }
        return responses;
    }

    private static Id toIdOrNull(String value) {
        if (String.isBlank(value)) {
            return null;
        }
        try {
            return Id.valueOf(value);
        } catch (StringException e) {
            return null;
        }
    }

    private static Boolean isValidationFailure(Database.SaveResult result) {
        for (Database.Error err : result.getErrors()) {
            if (err.getStatusCode() == StatusCode.FIELD_CUSTOM_VALIDATION_EXCEPTION) {
                return true;
            }
        }
        return false;
    }
}
```

## 3. The test class

```apex
// force-app/main/default/classes/CloseCaseActionTest.cls
@IsTest
private class CloseCaseActionTest {

    @TestSetup
    static void makeData() {
        List<Case> cases = new List<Case>();
        for (Integer i = 0; i < 200; i++) {
            cases.add(new Case(Subject = 'bulk-' + i, Status = 'New', Origin = 'Web'));
        }
        insert cases;
    }

    private static CloseCaseAction.Request reqFor(Id caseId, String note) {
        CloseCaseAction.Request r = new CloseCaseAction.Request();
        r.caseId = caseId;           // set every @InvocableVariable explicitly
        r.resolutionNote = note;
        return r;
    }

    @IsTest
    static void closedOnHappyPath() {
        Case c = [SELECT Id FROM Case LIMIT 1];
        Test.startTest();
        List<CloseCaseAction.Response> out =
            CloseCaseAction.run(new List<CloseCaseAction.Request>{ reqFor(c.Id, 'Replaced the router.') });
        Test.stopTest();
        Assert.areEqual('CLOSED', out[0].reasonCode);
        Assert.areEqual('Closed', [SELECT Status FROM Case WHERE Id = :c.Id].Status);
    }

    @IsTest
    static void validationBlockedKeepsItsOwnCode() {
        Case c = [SELECT Id FROM Case LIMIT 1];
        Test.startTest();
        List<CloseCaseAction.Response> out =
            CloseCaseAction.run(new List<CloseCaseAction.Request>{ reqFor(c.Id, null) });
        Test.stopTest();
        Assert.areEqual('VALIDATION_BLOCKED', out[0].reasonCode,
            'a validation failure must not collapse into UNKNOWN');
    }

    @IsTest
    static void unknownForMissingOrMalformedId() {
        Test.startTest();
        CloseCaseAction.Request bad = new CloseCaseAction.Request();
        bad.caseId = 'not-an-id';
        List<CloseCaseAction.Response> out = CloseCaseAction.run(
            new List<CloseCaseAction.Request>{ reqFor(null, 'x'), bad });
        Test.stopTest();
        Assert.areEqual('UNKNOWN', out[0].reasonCode);
        Assert.areEqual('UNKNOWN', out[1].reasonCode);
    }

    @IsTest
    static void twoHundredRequestsKeepSizeOrderAndFlatLimits() {
        List<CloseCaseAction.Request> reqs = new List<CloseCaseAction.Request>();
        for (Case c : [SELECT Id FROM Case ORDER BY Subject]) {
            reqs.add(reqFor(c.Id, 'bulk resolution'));
        }
        Test.startTest();
        List<CloseCaseAction.Response> out = CloseCaseAction.run(reqs);
        Integer dmlUsed = Limits.getDmlStatements();
        Integer queriesUsed = Limits.getQueries();
        Test.stopTest();
        Assert.areEqual(reqs.size(), out.size(), 'one Response per Request');
        for (Integer i = 0; i < reqs.size(); i++) {
            Assert.areEqual(reqs[i].caseId, out[i].caseId, 'Response ' + i + ' must match Request ' + i);
        }
        Assert.isTrue(dmlUsed <= 1, 'DML must not scale with request count; saw ' + dmlUsed);
        Assert.isTrue(queriesUsed <= 1, 'queries must not scale with request count; saw ' + queriesUsed);
    }

    @IsTest
    static void respectsTheRunningUsersAccess() {
        Profile p = [SELECT Id FROM Profile WHERE Name = 'Standard User' LIMIT 1];
        User agentLike = new User(
            Alias = 'agtusr', Email = 'agent.like@example.com', EmailEncodingKey = 'UTF-8',
            LastName = 'AgentLike', LanguageLocaleKey = 'en_US', LocaleSidKey = 'en_US',
            ProfileId = p.Id, TimeZoneSidKey = 'America/Los_Angeles',
            Username = 'agent.like.' + System.currentTimeMillis() + '@example.com'
        );
        insert agentLike;
        Case c = [SELECT Id FROM Case LIMIT 1];
        List<CloseCaseAction.Response> out;
        System.runAs(agentLike) {
            Test.startTest();
            out = CloseCaseAction.run(new List<CloseCaseAction.Request>{ reqFor(c.Id, 'Fixed.') });
            Test.stopTest();
        }
        // A user who cannot see or edit the case must get a non-CLOSED code, never an exception.
        Assert.areEqual(1, out.size());
        Assert.isNotNull(out[0].reasonCode);
    }
}
```

UNVERIFIED (2026-10-03): the last test assumes a Standard User profile exists and that the org's sharing model decides whether that user can close the case; the assertion therefore checks only that the action answers without throwing. Replace the profile with a permission set copy of the real agent user for a sharper assertion.

## 4. Meta files and manifest

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/classes/CloseCaseAction.cls-meta.xml (CloseCaseActionTest.cls-meta.xml is identical) -->
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- manifest/package.xml -->
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>CloseCaseAction</members>
        <members>CloseCaseActionTest</members>
        <name>ApexClass</name>
    </types>
    <types>
        <members>Case.Closed_Case_Requires_Description</members>
        <name>ValidationRule</name>
    </types>
    <version>67.0</version>
</Package>
```

Run: `sf project deploy start --manifest manifest/package.xml --test-level RunSpecifiedTests --tests CloseCaseActionTest`, then `sf apex run test --class-names CloseCaseActionTest --code-coverage`.
