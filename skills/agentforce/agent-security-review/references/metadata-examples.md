# Metadata Examples: Agent Security Review

A review is only repeatable if its findings are executable. This file gives three artefacts that live beside the agent metadata: a least-privilege permission set for the agent user, queries that prove effective access, and the planner-bundle elements a reviewer reads to confirm that sensitive subagents are gated.

## Example 1: A least-privilege data-access permission set for a service agent user

**Context.** A service agent closes cases and answers contact questions through two Apex classes from `references/examples.md`: `CloseCaseAction` and `ContactGroundingSelector`. The agent user already holds the standard permission set that carries the agent user license (the Generative AI guide names "Agentforce Service Agent User" as the example). This second permission set grants only the data the two actions need.

**File path:** `force-app/main/default/permissionsets/Agent_Service_Data_Access.permissionset-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <classAccesses>
        <apexClass>CloseCaseAction</apexClass>
        <enabled>true</enabled>
    </classAccesses>
    <classAccesses>
        <apexClass>ContactGroundingSelector</apexClass>
        <enabled>true</enabled>
    </classAccesses>
    <description>Data the service agent user needs for CloseCaseAction and ContactGroundingSelector. Nothing else. Reviewed 2026-10-03.</description>
    <fieldPermissions>
        <editable>true</editable>
        <field>Case.Resolution__c</field>
        <readable>true</readable>
    </fieldPermissions>
    <fieldPermissions>
        <editable>false</editable>
        <field>Contact.Preferred_Language__c</field>
        <readable>true</readable>
    </fieldPermissions>
    <hasActivationRequired>false</hasActivationRequired>
    <label>Agent Service Data Access</label>
    <objectPermissions>
        <allowCreate>false</allowCreate>
        <allowDelete>false</allowDelete>
        <allowEdit>true</allowEdit>
        <allowRead>true</allowRead>
        <modifyAllRecords>false</modifyAllRecords>
        <object>Case</object>
        <viewAllRecords>false</viewAllRecords>
    </objectPermissions>
    <objectPermissions>
        <allowCreate>false</allowCreate>
        <allowDelete>false</allowDelete>
        <allowEdit>false</allowEdit>
        <allowRead>true</allowRead>
        <modifyAllRecords>false</modifyAllRecords>
        <object>Contact</object>
        <viewAllRecords>false</viewAllRecords>
    </objectPermissions>
</PermissionSet>
```

What a reviewer checks in this file:

- `viewAllRecords` and `modifyAllRecords` are `false` on every object. Either one overrides sharing for that object.
- The field list equals the union of fields the actions read or write. `Social_Security_Number__c` is absent, so no grounding selector running as this user can read it.
- `classAccesses` names exactly the action and selector classes. When an agent action references Apex, access depends on that class.
- The custom fields `Case.Resolution__c` and `Contact.Preferred_Language__c` come from the examples in `references/examples.md`; substitute your own.

UNVERIFIED (2026-10-03): which object permissions the agent user license allows at all; the Generative AI guide says only that the agent user needs a permission set containing the Agent User license and enough access for its tasks. Deploy to a sandbox first and read any license errors.

## Example 2: Who may use an employee agent

Employee agents are reached by people, not by an agent user, so the review also covers who can open them. `PermissionSet.agentAccesses` (API 63.0 and later) lists the employee agents visible to the permission set's users.

**File path:** `force-app/main/default/permissionsets/Sales_Assistant_Users.permissionset-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <agentAccesses>
        <agentName>Sales_Assistant</agentName>
        <enabled>true</enabled>
    </agentAccesses>
    <description>Grants use of the Sales_Assistant employee agent. Assign through the sales permission set group only.</description>
    <hasActivationRequired>false</hasActivationRequired>
    <label>Sales Assistant Users</label>
</PermissionSet>
```

UNVERIFIED (2026-10-03): `agentName` is documented only as "the name of the employee agent"; the API name is assumed. Retrieve an existing permission set with agent access to confirm the format.

## package.xml member form

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Agent_Service_Data_Access</members>
        <members>Sales_Assistant_Users</members>
        <name>PermissionSet</name>
    </types>
    <version>66.0</version>
</Package>
```

Deploy the Apex classes and custom fields first; a permission set that names a missing class or field fails to deploy. Deploy the whole permission set each time: from API 40.0, a deployed permission set replaces its contents, so a partial file silently removes access.

## Example 3: Queries that prove effective access

Effective access is the union of the profile and every assigned permission set and group, so the review queries it instead of reading one file. Run these as an admin, replacing the username.

```sql
-- 1. Every permission set the agent user holds, including the one owned by its profile.
SELECT PermissionSet.Name, PermissionSet.IsOwnedByProfile, PermissionSetGroup.DeveloperName
FROM PermissionSetAssignment
WHERE Assignee.Username = 'service.agent@example.com'

-- 2. Object access granted through any of them; any ViewAll or ModifyAll row is a finding.
SELECT Parent.Name, SobjectType, PermissionsRead, PermissionsEdit, PermissionsDelete,
       PermissionsViewAllRecords, PermissionsModifyAllRecords
FROM ObjectPermissions
WHERE ParentId IN (SELECT PermissionSetId FROM PermissionSetAssignment
                   WHERE Assignee.Username = 'service.agent@example.com')

-- 3. Regulated fields readable by the agent user; the expected result is zero rows.
SELECT Parent.Name, Field, PermissionsRead
FROM FieldPermissions
WHERE Field IN ('Contact.Social_Security_Number__c')
  AND PermissionsRead = true
  AND ParentId IN (SELECT PermissionSetId FROM PermissionSetAssignment
                   WHERE Assignee.Username = 'service.agent@example.com')

-- 4. Permission sets that grant access to agents (SetupEntityType BotDefinition, API 64.0 and later).
SELECT Parent.Name, SetupEntityId
FROM SetupEntityAccess
WHERE SetupEntityType = 'BotDefinition'
```

`SetupEntityAccess` accepts `BotDefinition` as a setup entity type from API 64.0 (Object Reference). Store the query results with the review so the next review can diff them.

## Example 4: Planner-bundle elements a reviewer reads

Retrieve the agent's `GenAiPlannerBundle` and read two element types. Do not hand-edit retrieved agent metadata to fix findings; the Agentforce Developer Guide warns that uploading edited agent metadata can corrupt the org. Fix in Agentforce Builder or Agent Script and re-retrieve.

**File path (retrieved, read-only):** `force-app/main/default/genAiPlannerBundles/<AgentName>/<AgentName>.genAiPlannerBundle`

```xml
<!-- Excerpt of a retrieved GenAiPlannerBundle, trimmed to the two element types under review.
     Element names and values follow the Metadata API reference sample. -->
<GenAiPlannerBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <attributeMappings>
        <attributeName>SvcCopilotTmpl__ServiceCustomerVerification.SvcCopilotTmpl__VerifyCustomer.isVerified</attributeName>
        <attributeType>StandardPluginFunctionOutput</attributeType>
        <mappingTargetName>isVerified</mappingTargetName>
        <mappingType>Variable</mappingType>
    </attributeMappings>
    <ruleExpressionAssignments>
        <ruleExpressionName>Verified_User</ruleExpressionName>
        <targetName>SvcCopilotTmpl__CaseManagement</targetName>
        <targetType>Plugin</targetType>
    </ruleExpressionAssignments>
    <ruleExpressions>
        <conditions>
            <leftOperand>isVerified</leftOperand>
            <leftOperandType>Variable</leftOperandType>
            <operator>equal</operator>
            <rightOperandValue>true</rightOperandValue>
        </conditions>
        <expression>Verified_User</expression>
        <expressionLabel>Verified User</expressionLabel>
        <expressionName>Verified_User</expressionName>
        <expressionType>sel</expressionType>
    </ruleExpressions>
</GenAiPlannerBundle>
```

Review assertions:

1. Every subagent that reads or changes a customer's own records has a `ruleExpressionAssignments` entry tied to a verification variable. A rule expression "conditionally locks or unlocks topics and actions based on defined security criteria."
2. Verified identifiers reach actions through `attributeMappings` from a verification action's output, not from what the user typed. The Metadata API reference describes attribute mapping as a way "to propagate sensitive data safely without relying on untrusted user input."

## Verification

- Deploy the permission sets to a sandbox and assign them to the agent user. Query 2 shows no ViewAll or ModifyAll row; query 3 returns zero rows.
- As a low-privilege test user, ask the agent about a contact owned by someone else and confirm it cannot answer.
- Re-run the queries after each release and diff the results against the stored copy.
