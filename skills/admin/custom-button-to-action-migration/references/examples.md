# Examples — Custom Button to Action Migration

## Example 1: Inventory Custom Buttons via Tooling API

```bash
sf data query --use-tooling-api --query \
  "SELECT Name, EntityDefinition.QualifiedApiName, BehaviorType, ContentSource, Url FROM WebLink ORDER BY EntityDefinition.QualifiedApiName"
```

Group by:

- `BehaviorType`: `Detail` (page button), `List`, `Mass`
- `ContentSource`: `URL`, `OnClickJavaScript`, `VisualforcePage`, `S Control`

Read each `OnClickJavaScript` body to categorize per the SKILL.md Decision Guidance table.

---

## Example 2: Headless LWC Quick Action Replacing JS Button (Apex Call + Toast)

**Original Classic JavaScript button:**

```javascript
{!REQUIRESCRIPT("/soap/ajax/58.0/connection.js")}
{!REQUIRESCRIPT("/soap/ajax/58.0/apex.js")}
var result = sforce.apex.execute("OpportunityActions","markAsHotProspect", {oppId: "{!Opportunity.Id}"});
if (result == "OK") {
    alert("Marked as hot prospect");
    location.reload();
} else {
    alert("Failed: " + result);
}
```

**Migrated Apex (no controller change needed beyond `@AuraEnabled`):**

```apex
public with sharing class OpportunityActions {
    @AuraEnabled
    public static void markAsHotProspect(Id oppId) {
        Opportunity opp = [SELECT Id, IsHotProspect__c FROM Opportunity WHERE Id = :oppId WITH SECURITY_ENFORCED LIMIT 1];
        opp.IsHotProspect__c = true;
        update opp;
    }
}
```

**Headless LWC (`markHotProspect.js`):**

```js
import { LightningElement, api } from 'lwc';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';
import { RefreshEvent } from 'lightning/refresh';
import markAsHotProspect from '@salesforce/apex/OpportunityActions.markAsHotProspect';

export default class MarkHotProspect extends LightningElement {
    @api recordId;

    @api async invoke() {
        try {
            await markAsHotProspect({ oppId: this.recordId });
            this.dispatchEvent(new ShowToastEvent({
                title: 'Marked as hot prospect',
                variant: 'success'
            }));
            this.dispatchEvent(new RefreshEvent());
        } catch (error) {
            this.dispatchEvent(new ShowToastEvent({
                title: 'Action failed',
                message: error.body?.message || error.message,
                variant: 'error'
            }));
        }
    }
}
```

**`markHotProspect.html`:** empty (no UI).

**`markHotProspect.js-meta.xml`:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>62.0</apiVersion>
    <isExposed>true</isExposed>
    <targets>
        <target>lightning__RecordAction</target>
    </targets>
    <targetConfigs>
        <targetConfig targets="lightning__RecordAction">
            <actionType>Action</actionType>
            <objects>
                <object>Opportunity</object>
            </objects>
        </targetConfig>
    </targetConfigs>
</LightningComponentBundle>
```

**Configure as Quick Action:** Setup → Object Manager → Opportunity → Buttons, Links, and Actions → New Action. Action Type = "Lightning Web Component"; LWC = `c:markHotProspect`.

**Add to layout:** Page Layout → Salesforce Mobile and Lightning Experience Actions → drag the new Quick Action into the action bar.

---

## Example 3: Screen Flow Replacing JS Button with User Input

**Original Classic JS button:**

```javascript
var reason = prompt("Reason for closing this Case:");
if (reason && reason.length > 0) {
    var result = sforce.apex.execute("CaseActions","closeWithReason", {
        caseId: "{!Case.Id}", reason: reason
    });
    alert(result);
    location.reload();
}
```

**Migrated Screen Flow (`Close_Case_With_Reason`):**

```text
Start: Variable inputs
    - recordId (Text, Available for input, Available for output, Default: passed by Quick Action)

Screen 1: Collect Reason
    - Long Text Area "Reason" (Required)

Action: Update Records
    - Object: Case
    - Filter: Id = recordId
    - Set Status = "Closed"
    - Set Close_Reason__c = {!Reason}

Screen 2 (optional): Confirmation message
    - Display Text: "Case closed with reason: {!Reason}"
```

**Configure as Quick Action:** Setup → Object Manager → Case → Buttons, Links, and Actions → New Action. Action Type = "Flow"; Flow = `Close_Case_With_Reason`.

---

## Example 4: List Button JS → Mass Quick Action with LWC

**Original Classic JS list button:**

```javascript
{!REQUIRESCRIPT("/soap/ajax/58.0/connection.js")}
var records = {!GETRECORDIDS($ObjectType.Account)};
if (records.length === 0) {
    alert("Select at least one Account");
} else {
    var result = sforce.apex.execute("AccountActions","markAsKey", {ids: records});
    alert("Marked " + result + " accounts as key");
    location.reload();
}
```

**Migrated Apex:**

```apex
public with sharing class AccountActions {
    @AuraEnabled
    public static Integer markAsKey(List<Id> ids) {
        List<Account> accounts = [SELECT Id, Is_Key_Account__c FROM Account WHERE Id IN :ids WITH SECURITY_ENFORCED];
        for (Account a : accounts) a.Is_Key_Account__c = true;
        update accounts;
        return accounts.size();
    }
}
```

**Mass Quick Action LWC (`markAccountsAsKey.js`):**

```js
import { LightningElement, api } from 'lwc';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';
import markAsKey from '@salesforce/apex/AccountActions.markAsKey';

export default class MarkAccountsAsKey extends LightningElement {
    @api selectedIds;  // populated by Mass Quick Action framework

    @api async invoke() {
        if (!this.selectedIds || this.selectedIds.length === 0) {
            this.dispatchEvent(new ShowToastEvent({
                title: 'No records selected',
                variant: 'warning'
            }));
            return;
        }
        try {
            const count = await markAsKey({ ids: this.selectedIds });
            this.dispatchEvent(new ShowToastEvent({
                title: `Marked ${count} accounts as key`,
                variant: 'success'
            }));
        } catch (error) {
            this.dispatchEvent(new ShowToastEvent({
                title: 'Action failed',
                message: error.body?.message || error.message,
                variant: 'error'
            }));
        }
    }
}
```

**`markAccountsAsKey.js-meta.xml`:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>62.0</apiVersion>
    <isExposed>true</isExposed>
    <targets>
        <target>lightning__RecordAction</target>
    </targets>
    <targetConfigs>
        <targetConfig targets="lightning__RecordAction">
            <actionType>Action</actionType>
            <objects>
                <object>Account</object>
            </objects>
        </targetConfig>
    </targetConfigs>
</LightningComponentBundle>
```

**Note:** As of Spring '25 the Mass Action surface for LWC is invoked via Setup → Object Manager → Account → Search Layouts → List View → add the action. Configuration UI varies; consult release notes for the exact path on your org.

---

## Example 5: URL Button Translation

**Original Classic URL button (External CRM Lookup):**

```
https://external-crm.example.com/lookup?type=account&id={!Account.Id}&name={!URLENCODE(Account.Name)}
```

**Lightning equivalent — URL Quick Action:**

In Setup → Object Manager → Account → Buttons, Links, and Actions → New Action:

- Action Type: URL
- URL: `https://external-crm.example.com/lookup?type=account&id={!Account.Id}&name={!Account.Name}`
- Behavior: Display in new window

**Add to page layout** (Mobile and Lightning Actions section).

**Note:** `URLENCODE` may not be available as a merge function in Quick Action URLs depending on the org's release; if needed, encode at the destination side or build via LWC URL action.

---

## Example 6: Coexistence Period — Tracking Lightning Adoption

**Custom field on Opportunity (or any object) to track which UI invoked the action:**

```text
Field: Last_Action_Source__c (Picklist: Classic Button, Lightning Action, Both)
```

```apex
public with sharing class OpportunityActions {
    @AuraEnabled
    public static void markAsHotProspect(Id oppId) {
        Opportunity opp = [SELECT Id, Last_Action_Source__c FROM Opportunity WHERE Id = :oppId WITH SECURITY_ENFORCED];
        opp.IsHotProspect__c = true;
        opp.Last_Action_Source__c = 'Lightning Action';
        update opp;
    }
}
```

(Update the Classic button JS to set `Last_Action_Source__c = 'Classic Button'` similarly.)

**Audit query:**

```sql
SELECT Last_Action_Source__c, COUNT(Id)
FROM Opportunity
WHERE LastModifiedDate = LAST_N_DAYS:30
GROUP BY Last_Action_Source__c
```

When 95%+ of invocations come from "Lightning Action", retire the Classic button.

---

## Example 7: Migration Audit Log

```text
Custom Object: Custom_Button_Migration_Log__c
Fields:
    - Classic_Button_Name__c (Text)
    - Object__c (Text)
    - Behavior_Type__c (Picklist: Detail, List, Mass)
    - Content_Source__c (Picklist: URL, OnClickJavaScript, VisualforcePage, S_Control)
    - Lightning_Replacement_Type__c (Picklist: Quick Action, LWC Quick Action, Screen Flow, URL Action, Retained Classic Only, Retired)
    - Lightning_Replacement_Name__c (Text)
    - Migration_Date__c (Date)
    - Status__c (Picklist: In Progress, Migrated, Tested, Active in Production, Classic Retired)
    - Notes__c (LongTextArea)
```

Reports run off this object: migration completeness per object, status breakdown, retired vs active.
