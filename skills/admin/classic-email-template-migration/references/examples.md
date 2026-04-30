# Examples — Classic Email Template Migration

## Example 1: Inventory Query

```sql
-- Classic templates by type
SELECT TemplateType, COUNT(Id) cnt
FROM EmailTemplate
WHERE UiType = 'Aloha'
GROUP BY TemplateType

-- Per-template downstream consumer count (Email Alerts)
SELECT t.Id, t.Name, t.TemplateType,
    (SELECT COUNT() FROM WorkflowAlerts WHERE TemplateId = t.Id) AlertCount
FROM EmailTemplate t
WHERE UiType = 'Aloha'
ORDER BY AlertCount DESC

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

**Retrieved `WorkflowAlert` XML (before):**

```xml
<workflowAlert>
    <fullName>Account.Welcome_New_Account</fullName>
    <description>Welcome email for new Accounts</description>
    <protected>false</protected>
    <recipients>
        <recipient>AccountOwner</recipient>
        <type>accountOwner</type>
    </recipients>
    <senderType>CurrentUser</senderType>
    <template>unfiled$public/Welcome_New_Account_Classic</template>
</workflowAlert>
```

**Updated XML (after):**

```xml
<workflowAlert>
    <fullName>Account.Welcome_New_Account</fullName>
    <description>Welcome email for new Accounts</description>
    <protected>false</protected>
    <recipients>
        <recipient>AccountOwner</recipient>
        <type>accountOwner</type>
    </recipients>
    <senderType>CurrentUser</senderType>
    <template>Customer_Communications/Welcome_New_Account_Lightning</template>
</workflowAlert>
```

**Verification SOQL after deploy:**

```sql
SELECT Id, FullName, TemplateId
FROM WorkflowAlert
WHERE TemplateId IN (
    SELECT Old_Template_Id__c FROM Email_Template_Migration_Map__c
)
-- Expect: zero rows
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

**Why the OWA reset:** Lightning templates don't store sender. If the Classic template was paired with a no-reply OWA, the Apex caller must restate it.

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
