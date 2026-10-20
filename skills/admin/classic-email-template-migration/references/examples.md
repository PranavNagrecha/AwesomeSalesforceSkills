# Examples — Classic Email Template Migration

UNVERIFIED (2026-10-20): the Lightning merge syntax in Examples 2-3 (`{{Recipient.X}}`, `{{Sender.X}}`, `{{Related.X}}`, and the NOT-supported rows) has no corpus line; pkg2_dev 264 L8196-8197 names only a Recipients prefix. Sandbox-test every translation.

## Example 1: Inventory Query

```sql
-- Classic templates by type
SELECT TemplateType, COUNT(Id) cnt
FROM EmailTemplate
WHERE UiType = 'Aloha'
GROUP BY TemplateType

-- Per-template Email Alert count: alerts name the template in <template>
-- (a named reference, api_meta 264 L143888), so count from retrieved metadata:
-- grep -rho '<template>[^<]*</template>' force-app/main/default/workflows | sort | uniq -c

-- Find Apex code referencing Classic template IDs (run via Tooling API or grep on retrieved metadata)
-- grep -rn 'setTemplateId' src/classes
```

---

## Example 2: Lightning Email Template Builder Source HTML (Custom HTML Migration)

**Original Classic Custom HTML body:**

```html
<html>
<body style="font-family:Arial,sans-serif">
    <h2>Welcome, {!Contact.FirstName}!</h2>
    <p>Your order #{!Order.OrderNumber} on {!Order.EffectiveDate} has been received.</p>
    <p>Account contact: {!Account.Owner.FirstName} {!Account.Owner.LastName}</p>
    <p>Reach us at {!System.URLENCODE($Setup.SupportSettings__c.SupportURL__c)}</p>
</body>
</html>
```

**Migrated Lightning Email Template body (paste into source view):**

```html
<html>
<body style="font-family:Arial,sans-serif">
    <h2>Welcome, {{Recipient.FirstName}}!</h2>
    <p>Your order #{{Related.OrderNumber}} on {{Related.EffectiveDate}} has been received.</p>
    <p>Account contact: {{Recipient.Account.Owner.FirstName}} {{Recipient.Account.Owner.LastName}}</p>
    <p>Reach us at {{Recipient.Account.Support_URL__c}}</p>
</body>
</html>
```

**What changed:**

- `{!Contact.FirstName}` → `{{Recipient.FirstName}}` (recipient is the Contact)
- `{!Order.OrderNumber}` → `{{Related.OrderNumber}}` (Order is the related-object merge context)
- `{!System.URLENCODE($Setup.SupportSettings__c.SupportURL__c)}` → not supported. Pre-computed onto Account as `Support_URL__c` (formula field) and merged from there.

---

## Example 3: Merge Field Translation Map

| Use case | Classic | Lightning |
|---|---|---|
| Recipient first name (Contact recipient) | `{!Contact.FirstName}` | `{{Recipient.FirstName}}` |
| Recipient first name (User recipient) | `{!User.FirstName}` | `{{Recipient.FirstName}}` |
| Recipient's account name | `{!Account.Name}` | `{{Recipient.Account.Name}}` |
| Recipient's account owner email | `{!Account.Owner.Email}` | `{{Recipient.Account.Owner.Email}}` |
| Sending user's name | `{!User.FirstName}` (when User = sender) | `{{Sender.FirstName}}` |
| Sending user's signature | `{!User.Signature}` | `{{Sender.Signature}}` |
| Related object (e.g., Case being responded to) | `{!Case.Subject}` | `{{Related.Subject}}` |
| Related object's lookup | `{!Case.Account.Name}` | `{{Related.Account.Name}}` |
| Today's date | `{!TODAY()}` | NOT supported — pre-compute on a record formula |
| Conditional fallback | `{!IF(Email != null, Email, 'noreply@x')}` | NOT supported — pre-compute on a record formula |

---

## Example 4: Email Alert Update via Metadata API

**Retrieved Workflow file, one `WorkflowAlert` (before):**

```xml
<!-- excerpt of Account.workflow-meta.xml: alerts are <alerts> children of <Workflow> (api_meta 264 L143765, sample L144411-144413) -->
<Workflow xmlns="http://soap.sforce.com/2006/04/metadata">
<alerts>
    <fullName>Welcome_New_Account</fullName>
    <description>Welcome email for new Accounts</description>
    <protected>false</protected>
    <recipients>
        <recipient>AccountOwner</recipient>
        <type>accountOwner</type>
    </recipients>
    <senderType>CurrentUser</senderType>
    <template>unfiled$public/Welcome_New_Account_Classic</template>
</alerts>
</Workflow>
```

**Updated XML (after):**

```xml
<!-- excerpt of Account.workflow-meta.xml: alerts are <alerts> children of <Workflow> (api_meta 264 L143765, sample L144411-144413) -->
<Workflow xmlns="http://soap.sforce.com/2006/04/metadata">
<alerts>
    <fullName>Welcome_New_Account</fullName>
    <description>Welcome email for new Accounts</description>
    <protected>false</protected>
    <recipients>
        <recipient>AccountOwner</recipient>
        <type>accountOwner</type>
    </recipients>
    <senderType>CurrentUser</senderType>
    <template>Customer_Communications/Welcome_New_Account_Lightning</template>
</alerts>
</Workflow>
```

**Verification after deploy:** re-retrieve the Workflow files and search each `<template>` for the old names — expect zero hits.

```bash
grep -rn 'Welcome_New_Account_Classic' force-app/main/default/workflows   # expect no output
```

---

## Example 5: Apex setTemplateId Update

**Before:**

```apex
Messaging.SingleEmailMessage msg = new Messaging.SingleEmailMessage();
msg.setTemplateId('00X8E000001ABC1');  // Classic template
msg.setTargetObjectId(contactId);
msg.setSaveAsActivity(true);
Messaging.sendEmail(new Messaging.Email[] { msg });
```

**After (using mapping table):**

```apex
// Resolve via mapping table or by name
EmailTemplate lightning = [SELECT Id FROM EmailTemplate
                           WHERE DeveloperName = 'Welcome_New_Account_Lightning'
                           AND UiType = 'SFX' LIMIT 1];

Messaging.SingleEmailMessage msg = new Messaging.SingleEmailMessage();
msg.setTemplateId(lightning.Id);
msg.setTargetObjectId(contactId);
msg.setOrgWideEmailAddressId(System.Label.NoReply_OWA_Id);  // explicit sender
msg.setSaveAsActivity(true);
Messaging.sendEmail(new Messaging.Email[] { msg });
```

**About the OWA line:** no email template stores a sender (object_reference 264 L106331-106749); the Apex caller sets it with `setOrgWideEmailAddressId` (apexdev 264 L27130-27133). Add it only when the From should be the OWA — the template swap itself does not change who sends.

---

## Example 6: Build the Migration Map Object

```apex
// Custom object: Email_Template_Migration_Map__c
// Fields: Old_Template_Id__c (Text 18 Unique), New_Template_Id__c (Text 18),
//         Old_Template_Name__c, New_Template_Name__c,
//         Migration_Date__c (Date), Migrated_By__c (User Lookup),
//         Status__c (Picklist: Pending, Migrated, Retained_VF, Failed)

List<Email_Template_Migration_Map__c> rows = new List<Email_Template_Migration_Map__c>();
for (EmailTemplate classicT : [SELECT Id, Name, DeveloperName FROM EmailTemplate WHERE UiType = 'Aloha']) {
    rows.add(new Email_Template_Migration_Map__c(
        Old_Template_Id__c = classicT.Id,
        Old_Template_Name__c = classicT.DeveloperName,
        Status__c = 'Pending'
    ));
}
insert rows;
// Update Status__c + New_Template_Id__c as each migration completes
```

---

## Example 7: Visualforce Template Retention with Apex Bridge

**Scenario:** A Classic Visualforce template renders an itemized invoice from a complex object hierarchy. Migration decision: keep VF template; modernize the *triggering surface* to a Lightning Email Composer button.

**Retained VF template (`InvoiceEmailTemplate`):** stays as-is.

**New Lightning bridge — Apex method invoked from a Lightning Quick Action:**

```apex
public with sharing class SendInvoiceEmail {
    @AuraEnabled
    public static String sendInvoice(Id invoiceId, Id contactId) {
        Messaging.SingleEmailMessage msg = new Messaging.SingleEmailMessage();
        msg.setTemplateId([SELECT Id FROM EmailTemplate
                           WHERE DeveloperName = 'InvoiceEmailTemplate' LIMIT 1].Id);
        msg.setWhatId(invoiceId);
        msg.setTargetObjectId(contactId);
        msg.setOrgWideEmailAddressId(System.Label.Billing_OWA_Id);
        msg.setSaveAsActivity(true);
        Messaging.SendEmailResult[] results = Messaging.sendEmail(new Messaging.Email[] { msg });
        return results[0].isSuccess() ? 'Sent' : results[0].getErrors()[0].getMessage();
    }
}
```

**Outcome:** The user-facing surface is a modern Lightning Quick Action. The rendering engine remains Classic VF because the document layout requires Apex-driven iteration. Best of both — admins still maintain the template; users get a Lightning UX.
