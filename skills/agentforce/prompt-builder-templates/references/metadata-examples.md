# Metadata Examples: Field Generation Template Grounded by Apex

A complete, deployable set: an Apex grounding class with its test class, a Field Generation prompt template that uses it, and the manifest. The Apex contract (one `@InvocableMethod`, `List<Request>` with a `RelatedEntity` of the template's object, `List<Response>` with a String `Prompt`, and the Field Generation `CapabilityType`) follows the Generative AI guide's "Add Apex Merge Fields to a Field Generation Prompt Template" example. GenAiPromptTemplate element names follow the Metadata API Developer Guide, Version 67.0.

## File: `force-app/main/default/classes/OpenCasesPrompt.cls`

```apex
public with sharing class OpenCasesPrompt {
    @InvocableMethod(label='Open Cases'
        description='Find open Cases for an Account'
        CapabilityType='PromptTemplateType://einstein_gpt__fieldCompletion')
    public static List<Response> getCasesPrompt(List<Request> requests) {
        if (requests.size() != 1) {
            throw new ListException('The requests list must contain one entry only');
        }
        Id accountId = requests[0].RelatedEntity.Id;
        List<Case> cases = [
            SELECT Subject, Description
            FROM Case
            WHERE AccountId = :accountId AND IsClosed = false
            WITH USER_MODE
            ORDER BY CreatedDate DESC
            LIMIT 20
        ];
        List<String> lines = new List<String>();
        for (Case c : cases) {
            lines.add(String.format('Case details: {0}, {1}.', new List<Object>{ c.Subject, c.Description }));
        }
        Response res = new Response();
        res.Prompt = lines.isEmpty() ? 'There are no open cases.' : String.join(lines, '\n');
        return new List<Response>{ res };
    }

    public class Request {
        @InvocableVariable(required=true)
        public Account RelatedEntity;
    }

    public class Response {
        @InvocableVariable
        public String Prompt;
    }
}
```

## File: `force-app/main/default/classes/OpenCasesPrompt_Test.cls`

```apex
@IsTest
private class OpenCasesPrompt_Test {
    @IsTest
    static void returnsOpenCasesOnly() {
        Account a = new Account(Name = 'Test Account');
        insert a;
        insert new List<Case>{
            new Case(Subject = 'Open one', Description = 'Needs work', Status = 'New', AccountId = a.Id),
            new Case(Subject = 'Done', Description = 'Closed', Status = 'Closed', AccountId = a.Id)
        };
        OpenCasesPrompt.Request req = new OpenCasesPrompt.Request();
        req.RelatedEntity = a;

        Test.startTest();
        List<OpenCasesPrompt.Response> out = OpenCasesPrompt.getCasesPrompt(new List<OpenCasesPrompt.Request>{ req });
        Test.stopTest();

        Assert.areEqual(1, out.size());
        Assert.areEqual('Case details: Open one, Needs work.', out[0].Prompt);
    }

    @IsTest
    static void saysWhenNothingIsOpen() {
        Account a = new Account(Name = 'Quiet Account');
        insert a;
        OpenCasesPrompt.Request req = new OpenCasesPrompt.Request();
        req.RelatedEntity = a;
        List<OpenCasesPrompt.Response> out = OpenCasesPrompt.getCasesPrompt(new List<OpenCasesPrompt.Request>{ req });
        Assert.areEqual('There are no open cases.', out[0].Prompt);
    }
}
```

## File: `force-app/main/default/genAiPromptTemplates/Summarize_Open_Cases.genAiPromptTemplate-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<GenAiPromptTemplate xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Fills Account.Open_Case_Summary__c with a summary of open cases.</description>
    <masterLabel>Summarize Open Cases</masterLabel>
    <relatedEntity>Account</relatedEntity>
    <relatedField>Account.Open_Case_Summary__c</relatedField>
    <templateVersions>
        <content>You are a support representative preparing an account manager for a customer call.
Account: {!$Input:Account.Name}
Open cases:
{!$Apex:OpenCasesPrompt.Prompt}

Instructions:
"""
Summarize the open cases in three sentences or fewer. Mention the oldest unresolved issue first.
Generate only the summary text.
"""</content>
        <inputs>
            <apiName>Account</apiName>
            <definition>SOBJECT://Account</definition>
            <referenceName>Input:Account</referenceName>
            <required>true</required>
        </inputs>
        <status>Draft</status>
        <templateDataProviders>
            <definition>apex://OpenCasesPrompt</definition>
            <label>Open Cases</label>
            <parameters>
                <definition>SOBJECT://Account</definition>
                <isRequired>true</isRequired>
                <parameterName>RelatedEntity</parameterName>
                <valueExpression>{!$Input:Account}</valueExpression>
            </parameters>
            <referenceName>Apex:OpenCasesPrompt</referenceName>
        </templateDataProviders>
    </templateVersions>
    <type>einstein_gpt__fieldCompletion</type>
    <visibility>Global</visibility>
</GenAiPromptTemplate>
```

UNVERIFIED (2026-10-03): the Metadata API sample shows only a flow data provider (`flow://Fetch_Products`, reference `Flow:Fetch_Products`, merge field `{!$Flow:Fetch_Products.Prompt}`). The Apex equivalents above (`apex://OpenCasesPrompt`, `Apex:OpenCasesPrompt`, `{!$Apex:OpenCasesPrompt.Prompt}`) and the `relatedField` value format are inferred from that sample and from the guide's statement that the class "is inserted into the prompt template as Apex:ContactEventsPrompt." Build the template once in Prompt Builder, retrieve it, and keep the retrieved shape. The version is deployed as Draft with no `versionIdentifier` ("If a unique value is not specified then it will be generated for you"); activate it in Prompt Builder after preview. If the target org has Deploy Active Prompt Template Versions Only turned on, a template with no active version fails to deploy.

Create `Account.Open_Case_Summary__c` (Long Text Area) before deploying, then log out and back in so Prompt Builder can see it.

## Manifest: `manifest/package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>OpenCasesPrompt</members>
        <members>OpenCasesPrompt_Test</members>
        <name>ApexClass</name>
    </types>
    <types>
        <members>Summarize_Open_Cases</members>
        <name>GenAiPromptTemplate</name>
    </types>
    <version>67.0</version>
</Package>
```

## Deploy order and verification

1. Deploy `Account.Open_Case_Summary__c` and the two Apex classes; run `OpenCasesPrompt_Test`.
2. Run `python3 skills/agentforce/prompt-builder-templates/scripts/check_prompt_builder_templates.py --manifest-dir force-app/main/default`.
3. Deploy the template with a user who has Prompt Template Manager.
4. In Prompt Builder, preview with an account that has open cases, check the resolution, then activate.
5. Add the template to the Open Case Summary field on the Account Lightning record page, and assign Prompt Template User to the account team.
