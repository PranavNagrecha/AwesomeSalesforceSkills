# Examples — Custom Button to Action Migration

## Example 1: Inventory Custom Buttons via the WebLink Object

```bash
sf data query --query \
  "SELECT Name, PageOrSobjectType, DisplayType, LinkType, OpenType, Url FROM WebLink ORDER BY PageOrSobjectType"
```

Group by:

- `DisplayType`: `link`, `button`, `massActionButton` (api_meta 264 L47857-47860)
- `LinkType`: `url`, `sControl`, `javascript`, `page` (api_meta 264 L47926-47932)

Read each `javascript` body (the `Url` column) to categorize per the SKILL.md Decision Guidance table.

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
        Opportunity opp = [SELECT Id, IsHotProspect__c FROM Opportunity WHERE Id = :oppId WITH USER_MODE LIMIT 1];
        opp.IsHotProspect__c = true;
        update opp;
    }
}
```

`WITH USER_MODE` is the read idiom; in API version 67.0 and later you can't use `WITH SECURITY_ENFORCED` in Apex SOQL and the guide says to use `WITH USER_MODE` instead (apexdev 264 L11926-11927). The gate is the `apiVersion` in the class's `.cls-meta.xml`, not the org's release. UNVERIFIED (2026-10-20): the 57.0 floor for `WITH USER_MODE` and the claim that a class pinned at 56.0 or lower cannot use it are Help release-note figures.

**Headless LWC (`markHotProspect.js`):**

```js
import { LightningElement, api } from 'lwc';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';
import { RefreshEvent } from 'lightning/refresh';
import markAsHotProspect from '@salesforce/apex/OpportunityActions.markAsHotProspect';

export default class MarkHotProspect extends LightningElement {
    @api recordId; // set by the platform after construction; not available in connectedCallback()

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

**Configure as Quick Action:** Setup → Object Manager → Case → Buttons, Links, and Actions → New Action. Action Type = "Flow" (`QuickActionType` Flow, which api_meta 264 L102962 labels Beta as of API 41.0); Flow = `Close_Case_With_Reason`.

---

## Example 4: List Button JS → Apex for a Selected-Records Action

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

**Migrated Apex (partial-success safe):**

```apex
public with sharing class AccountActions {
    @AuraEnabled
    public static Integer markAsKey(List<Id> ids) {
        List<Account> accounts = [SELECT Id, Is_Key_Account__c FROM Account WHERE Id IN :ids WITH USER_MODE];
        for (Account a : accounts) a.Is_Key_Account__c = true;
        Database.SaveResult[] results = Database.update(accounts, false, AccessLevel.USER_MODE);
        Integer ok = 0;
        for (Database.SaveResult sr : results) if (sr.isSuccess()) ok++;
        return ok;
    }
}
```

**Surface:** an LWC quick action cannot host this. LWC quick actions run on record pages only and cannot be global (LWC guide `use-config-for-quick-actions`), so the `lightning__RecordAction` target in Example 2 does not apply to a list view. A mass quick action is not it either: it adds an existing create or update action (api_meta 264 L47565-47572), not Apex. UNVERIFIED (2026-10-20): which list-view surface passes the selected IDs to this method (a Screen Flow calling an invocable wrapper, or a Visualforce page with a standard set controller) is Help-only; confirm it in a sandbox before committing to a pattern.

---

## Example 5: URL Button Translation

**Original Classic URL button (External CRM Lookup):**

```
https://external-crm.example.com/lookup?type=account&id={!Account.Id}&name={!URLENCODE(Account.Name)}
```

**Lightning equivalent — headless LWC Quick Action that navigates:**

```js
import { LightningElement, api, wire } from 'lwc';
import { NavigationMixin } from 'lightning/navigation';
import { getRecord } from 'lightning/uiRecordApi';
import NAME_FIELD from '@salesforce/schema/Account.Name';

export default class OpenCrmLookup extends NavigationMixin(LightningElement) {
    @api recordId;
    name;

    @wire(getRecord, { recordId: '$recordId', fields: [NAME_FIELD] })
    wiredAccount({ data }) { if (data) this.name = data.fields.Name.value; }

    @api invoke() {
        const url = `https://external-crm.example.com/lookup?type=account&id=${this.recordId}&name=${encodeURIComponent(this.name)}`;
        this[NavigationMixin.Navigate]({ type: 'standard__webPage', attributes: { url } });
    }
}
```

Use the Example 2 `js-meta.xml` (`lightning__RecordAction`, `actionType` `Action`). `QuickActionType` has no URL value (api_meta 264 L102947-102971), so the encoding is done in JavaScript rather than with `URLENCODE`. `standard__webPage` is the web-page `PageReference` type (LWC guide `reference-page-reference-type`).

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
        Opportunity opp = [SELECT Id, Last_Action_Source__c FROM Opportunity WHERE Id = :oppId WITH USER_MODE];
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
    - Display_Type__c (Picklist: link, button, massActionButton)
    - Link_Type__c (Picklist: url, sControl, javascript, page)
    - Lightning_Replacement_Type__c (Picklist: Quick Action, LWC Quick Action, Screen Flow, Headless Navigation Action, Retained Classic Only, Retired)
    - Lightning_Replacement_Name__c (Text)
    - Migration_Date__c (Date)
    - Status__c (Picklist: In Progress, Migrated, Tested, Active in Production, Classic Retired)
    - Notes__c (LongTextArea)
```

Reports run off this object: migration completeness per object, status breakdown, retired vs active.
