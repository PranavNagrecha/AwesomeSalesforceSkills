# Examples — Apex Custom Permissions Check

## Example 1: Gating a service entry point, with both-sides test coverage

**Context:** Only Deal Desk staff may approve an Opportunity above a discount threshold. The approval action is exposed to an LWC through an `@AuraEnabled` method.

**Problem:** Profile-based gating means a new user population needs a cloned profile. Hiding the LWC button gates nothing — the `@AuraEnabled` method is callable directly. And a test that only proves the happy path leaves the deny branch uncovered, so a later refactor can delete the check without failing a build.

**Solution:**

`force-app/main/default/customPermissions/Approve_Big_Deals.customPermission-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomPermission xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Approve Big Deals</label>
    <description>Allows approval of Opportunities discounted beyond the standard band.</description>
    <isLicensed>false</isLicensed>
</CustomPermission>
```

The service:

```apex
public with sharing class ApprovalService {

    @TestVisible
    private static final String PERM_APPROVE = 'Approve_Big_Deals';

    @AuraEnabled
    public static void approve(Id opportunityId) {
        if (!FeatureManagement.checkPermission(PERM_APPROVE)) {
            throw new AuraHandledException('You are not authorized to approve this record.');
        }
        Opportunity opp = new Opportunity(Id = opportunityId, StageName = 'Closed Won');
        update as user opp;
    }
}
```

The test, exercising both branches:

```apex
@IsTest
private class ApprovalServiceTest {

    private static User buildUser(List<String> permSetNames) {
        // templates/apex/tests/TestUserFactory.cls
        return TestUserFactory.createUser('Standard User', permSetNames);
    }

    @IsTest
    static void approvesWhenPermissionGranted() {
        User dealDesk = buildUser(new List<String>{ 'Big_Deal_Approvers' });
        Opportunity opp = new Opportunity(
            Name = 'Bulk', StageName = 'Prospecting', CloseDate = Date.today().addDays(30));
        insert opp;

        System.runAs(dealDesk) {
            Test.startTest();
            ApprovalService.approve(opp.Id);
            Test.stopTest();
        }

        Assert.areEqual('Closed Won',
            [SELECT StageName FROM Opportunity WHERE Id = :opp.Id].StageName);
    }

    @IsTest
    static void rejectsWhenPermissionMissing() {
        User plain = buildUser(new List<String>());
        Opportunity opp = new Opportunity(
            Name = 'Bulk', StageName = 'Prospecting', CloseDate = Date.today().addDays(30));
        insert opp;

        System.runAs(plain) {
            try {
                ApprovalService.approve(opp.Id);
                Assert.fail('Expected AuraHandledException for unpermissioned user');
            } catch (AuraHandledException e) {
                // expected
            }
        }
        Assert.areEqual('Prospecting',
            [SELECT StageName FROM Opportunity WHERE Id = :opp.Id].StageName);
    }
}
```

**Why it works:** `FeatureManagement.checkPermission(String apiName)` "Checks whether a custom permission is enabled" for the running user and returns a Boolean showing "whether the permission is enabled (true) or disabled (false)" — so the same call serves both branches, and `System.runAs` is what makes the deny branch reachable in a test. `update as user` is separate and complementary: it enforces the running user's object and field permissions, which the custom-permission check knows nothing about.

Note that `TestUserFactory` in `templates/apex/tests/` assigns permission sets as part of user creation; if you assign a `PermissionSetAssignment` yourself, insert it **outside** the `System.runAs` block, because setup-object DML mixed with the record DML in one transaction throws `System.DmlException: MIXED_DML_OPERATION`.

---

## Example 2: One permission, three surfaces

**Context:** The same `Approve_Big_Deals` gate must apply in Apex, in the LWC that renders the button, and in a validation rule that blocks the stage change from any other entry point (Data Loader, Flow, API).

**Problem:** Teams gate one surface and assume the others follow. The validation rule is the one that actually closes the API hole; the LWC is the one that stops users seeing a button that will fail.

**Solution:**

LWC:

```js
import { LightningElement, api } from 'lwc';
import hasApproveBigDeals from '@salesforce/customPermission/Approve_Big_Deals';
import approve from '@salesforce/apex/ApprovalService.approve';

export default class ApproveButton extends LightningElement {
    @api recordId;

    get canApprove() {
        return hasApproveBigDeals === true;
    }

    async handleClick() {
        await approve({ opportunityId: this.recordId });
    }
}
```

```html
<template>
    <lightning-button
        if:true={canApprove}
        label="Approve"
        onclick={handleClick}>
    </lightning-button>
</template>
```

Validation rule, `objects/Opportunity/validationRules/Big_Deal_Approval_Gate.validationRule-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ValidationRule xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Big_Deal_Approval_Gate</fullName>
    <active>true</active>
    <errorConditionFormula>AND(
  ISCHANGED(StageName),
  ISPICKVAL(StageName, &quot;Closed Won&quot;),
  Discount__c &gt; 0.30,
  NOT($Permission.Approve_Big_Deals)
)</errorConditionFormula>
    <errorDisplayField>StageName</errorDisplayField>
    <errorMessage>Deals discounted over 30% must be approved by Deal Desk.</errorMessage>
</ValidationRule>
```

**Why it works:** Three surfaces, one API name. The LWC import gives the render hint (normalised through `canApprove` so `undefined` never leaks into a strict comparison), Apex enforces on the callable entry point, and `$Permission.Approve_Big_Deals` in the validation rule catches every path that never touches your code — imports, Flows, and integration users.

---

## Anti-Pattern: Permission checks against a hard-coded Profile name or user Id

**What practitioners do:** `if (UserInfo.getProfileId() == '00e5g000001abcXAAQ')` or `if (UserInfo.getName() == 'Deal Desk Bot')`.

**What goes wrong:** Profile Ids are org-specific and break on every sandbox refresh and package install — the same class of defect as a hard-coded record-type Id. Profile *names* are renameable and translatable. Either check has to be edited whenever a new team needs the feature, which means a code deploy for what should be an admin assignment.

**Correct approach:** One custom permission, granted through a Permission Set. Adding a team becomes a Permission Set assignment; the code never changes. If the feature also needs a kill switch that an admin can flip org-wide, pair the custom permission with a hierarchy Custom Setting or Custom Metadata flag — the permission answers "may this user", the setting answers "is this feature on".
