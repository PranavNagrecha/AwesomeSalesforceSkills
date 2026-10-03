# Metadata Examples: Custom Agent Actions Apex

A complete, deployable read-only agent action: the Apex class, its test, the `GenAiFunction` that exposes it to agents, and the manifest. Apex rules come from the Apex Developer Guide (InvocableMethod and InvocableVariable annotations); the action metadata comes from the Metadata API Developer Guide (GenAiFunction, API 60.0+, available only when Agents is enabled).

## 1. Apex class

```apex
// force-app/main/default/classes/GetCaseStatusAction.cls
public with sharing class GetCaseStatusAction {

    public class Request {
        @InvocableVariable(
            required=true
            label='Case Number'
            description='The customer-facing case number, for example 00001042. Ask the customer for it if it is not known.'
        )
        public String caseNumber;
    }

    public class Response {
        @InvocableVariable(label='Success' description='True when a case with this number was found and is visible to the agent user.')
        public Boolean success;
        @InvocableVariable(label='Status' description='Current status of the case, for example New, Working, or Closed. Blank when success is false.')
        public String status;
        @InvocableVariable(label='Subject' description='Subject line of the case. Blank when success is false.')
        public String subject;
        @InvocableVariable(label='Error Message' description='Plain-language reason the lookup failed. Blank when success is true.')
        public String errorMessage;
    }

    @InvocableMethod(
        label='Get Case Status'
        description='Use when a customer asks about the status of an existing support case and gives a case number. Returns the status and subject. Does not change the case.'
        category='Service'
    )
    public static List<Response> getStatus(List<Request> requests) {
        Set<String> numbers = new Set<String>();
        for (Request req : requests) {
            if (req != null && String.isNotBlank(req.caseNumber)) {
                numbers.add(req.caseNumber.trim());
            }
        }

        Map<String, Case> byNumber = new Map<String, Case>();
        if (!numbers.isEmpty()) {
            for (Case c : [
                SELECT CaseNumber, Status, Subject
                FROM Case
                WHERE CaseNumber IN :numbers
                WITH USER_MODE
            ]) {
                byNumber.put(c.CaseNumber, c);
            }
        }

        // One Response per Request, in the same order (Apex Developer Guide, Inputs and Outputs).
        List<Response> responses = new List<Response>();
        for (Request req : requests) {
            Response res = new Response();
            String key = (req == null || req.caseNumber == null) ? null : req.caseNumber.trim();
            Case found = key == null ? null : byNumber.get(key);
            if (found == null) {
                res.success = false;
                res.status = '';
                res.subject = '';
                res.errorMessage = 'No case with that number is visible to me. Please check the number.';
            } else {
                res.success = true;
                res.status = found.Status;
                res.subject = found.Subject;
                res.errorMessage = '';
            }
            responses.add(res);
        }
        return responses;
    }
}
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/classes/GetCaseStatusAction.cls-meta.xml -->
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

Choices tied to the gotchas: primitive fields only; one query outside the loop; failures returned as data, not thrown; `WITH USER_MODE` so the agent user's sharing and FLS apply; no callout, so no `callout` modifier.

## 2. Test class

```apex
// force-app/main/default/classes/GetCaseStatusActionTest.cls
@IsTest
private class GetCaseStatusActionTest {

    @TestSetup
    static void makeData() {
        insert new Case(Subject = 'Router will not power on', Status = 'New', Origin = 'Web');
    }

    private static GetCaseStatusAction.Request req(String caseNumber) {
        GetCaseStatusAction.Request r = new GetCaseStatusAction.Request();
        r.caseNumber = caseNumber;
        return r;
    }

    @IsTest
    static void returnsStatusForKnownCase() {
        String num = [SELECT CaseNumber FROM Case LIMIT 1].CaseNumber;
        Test.startTest();
        List<GetCaseStatusAction.Response> out =
            GetCaseStatusAction.getStatus(new List<GetCaseStatusAction.Request>{ req(num) });
        Test.stopTest();
        Assert.isTrue(out[0].success);
        Assert.areEqual('New', out[0].status);
        Assert.areEqual('Router will not power on', out[0].subject);
    }

    @IsTest
    static void unknownCaseIsReportedNotThrown() {
        Test.startTest();
        List<GetCaseStatusAction.Response> out =
            GetCaseStatusAction.getStatus(new List<GetCaseStatusAction.Request>{ req('99999999') });
        Test.stopTest();
        Assert.isFalse(out[0].success);
        Assert.isTrue(String.isNotBlank(out[0].errorMessage));
    }

    @IsTest
    static void outputsMatchInputsBySizeAndOrder() {
        String num = [SELECT CaseNumber FROM Case LIMIT 1].CaseNumber;
        List<GetCaseStatusAction.Request> reqs = new List<GetCaseStatusAction.Request>{
            req('99999999'), req(num), req(null)
        };
        Test.startTest();
        List<GetCaseStatusAction.Response> out = GetCaseStatusAction.getStatus(reqs);
        Test.stopTest();
        Assert.areEqual(3, out.size());
        Assert.isFalse(out[0].success);
        Assert.isTrue(out[1].success);
        Assert.isFalse(out[2].success);
    }
}
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/classes/GetCaseStatusActionTest.cls-meta.xml -->
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

## 3. GenAiFunction (asset-library action)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/genAiFunctions/Get_Case_Status/Get_Case_Status.genAiFunction-meta.xml -->
<GenAiFunction xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Use when a customer asks about the status of an existing support case and gives a case number. Returns the status and subject. Does not change the case.</description>
    <invocationTarget>GetCaseStatusAction</invocationTarget>
    <invocationTargetType>apex</invocationTargetType>
    <isConfirmationRequired>false</isConfirmationRequired>
    <masterLabel>Get Case Status</masterLabel>
</GenAiFunction>
```

`force-app/main/default/genAiFunctions/Get_Case_Status/input/schema.json`:

```json
{
  "required": ["caseNumber"],
  "properties": {
    "caseNumber": {
      "title": "Case Number",
      "description": "The customer-facing case number, for example 00001042. Ask the customer for it if it is not known.",
      "lightning:type": "lightning__textType",
      "lightning:isPII": false,
      "copilotAction:isUserInput": true
    }
  },
  "lightning:type": "lightning__objectType"
}
```

`force-app/main/default/genAiFunctions/Get_Case_Status/output/schema.json`:

```json
{
  "properties": {
    "success": {
      "title": "Success",
      "description": "True when a case with this number was found and is visible to the agent user.",
      "lightning:type": "lightning__booleanType",
      "lightning:isPII": false,
      "copilotAction:isDisplayable": false,
      "copilotAction:isUsedByPlanner": true
    },
    "status": {
      "title": "Status",
      "description": "Current status of the case.",
      "lightning:type": "lightning__textType",
      "lightning:isPII": false,
      "copilotAction:isDisplayable": true,
      "copilotAction:isUsedByPlanner": true
    },
    "subject": {
      "title": "Subject",
      "description": "Subject line of the case.",
      "lightning:type": "lightning__textType",
      "lightning:isPII": false,
      "copilotAction:isDisplayable": true,
      "copilotAction:isUsedByPlanner": true
    },
    "errorMessage": {
      "title": "Error Message",
      "description": "Plain-language reason the lookup failed.",
      "lightning:type": "lightning__textType",
      "lightning:isPII": false,
      "copilotAction:isDisplayable": false,
      "copilotAction:isUsedByPlanner": true
    }
  },
  "lightning:type": "lightning__objectType"
}
```

The property names match the Apex `@InvocableVariable` field names, and each schema's top-level `lightning:type` is `lightning__objectType`, as the guide requires. Remove the `//` header line from each JSON file; it only records the path.

UNVERIFIED (2026-10-03): the guide describes `input` and `output` folders containing `schema.json` inside a GenAiFunction component and shows the layout as an image; the folder-per-function source layout above follows that description. Generate one action in Agentforce Builder and retrieve it to confirm the exact layout in your org before hand-writing more.

## 4. package.xml member form

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- manifest/package.xml -->
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>GetCaseStatusAction</members>
        <members>GetCaseStatusActionTest</members>
        <name>ApexClass</name>
    </types>
    <types>
        <members>Get_Case_Status</members>
        <name>GenAiFunction</name>
    </types>
    <version>65.0</version>
</Package>
```

Deploy order: the Apex class first (the `invocationTarget` must exist), then the `GenAiFunction`, then add the action to a topic. In Winter '26 and later, an action created inside one agent is retrieved through that agent's `GenAiPlannerBundle` instead.
