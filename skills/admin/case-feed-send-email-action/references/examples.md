# Examples — Case Feed Send Email Action

All code and metadata below is illustrative scaffolding authored from the official Salesforce
Help, Apex Reference, and Metadata API guides. Replace object/field API names, template
developer names, and mailboxes with your own. Prerequisite for every example: **Email-to-Case
must be enabled** before the Send Email quick action can be used on Case.

## Example 1: Declarative reply composer

**Context:** a support team replies to customers from Case Feed with a branded template.
Recipients come from the case contact. Nothing varies by case attribute.

**Problem:** agents open a blank composer, paste a signature by hand, and occasionally
overwrite the subject line — which breaks the visual thread for the customer.

**Solution:**

Create the action in Setup: **Object Manager → Case → Buttons, Links, and Actions → New
Action**, then choose **Send Email** in the **Action Type** picklist. The retrieved metadata
looks like this:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- quickActions/Case.Reply_To_Customer.quickAction-meta.xml -->
<QuickAction xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Reply to Customer</label>
    <optionsCreateFeedItem>true</optionsCreateFeedItem>
    <type>SendEmail</type>
    <quickActionLayout>
        <layoutSectionStyle>OneColumn</layoutSectionStyle>
        <quickActionLayoutColumns>
            <quickActionLayoutItems>
                <field>ValidatedFromAddress</field>
                <uiBehavior>Edit</uiBehavior>
            </quickActionLayoutItems>
            <quickActionLayoutItems>
                <field>ToAddress</field>
                <uiBehavior>Edit</uiBehavior>
            </quickActionLayoutItems>
            <quickActionLayoutItems>
                <field>Subject</field>
                <uiBehavior>Edit</uiBehavior>
            </quickActionLayoutItems>
            <quickActionLayoutItems>
                <field>HTMLBody</field>
                <uiBehavior>Edit</uiBehavior>
            </quickActionLayoutItems>
        </quickActionLayoutColumns>
    </quickActionLayout>
</QuickAction>
```

Then, on the action's Setup detail page:

- **Default Email Template** → pick a template whose type is **Custom**. Salesforce Help:
  *"create an email template of the type Custom. Only Custom type templates are supported."*
- **Don't Apply Template Subject** → select it, so a reply keeps the subject already in play.
- **Predefined Field Values** → add entries for To / CC / BCC using an ID field such as
  `Contact.Id`, or a string field such as a custom email field on Contact. Contact, lead, and
  person-account IDs are supported.

Finally, add the action to the Case page layout. This step is not optional and is not automatic —
Salesforce Help documents it as its own procedure, *"Add Quick Actions to the Case Page Layout for
Lightning Experience."*

If the action agents can't find is the **standard** Email action rather than this custom one, the
layout is the wrong place to look. The Salesforce Knowledge article *"Email Quick Action Not
Available on Case Feed"* resolves that symptom at the org level: set the email deliverability access
level to **All email**, enable Email-to-Case, and select **Enable Case Feed Actions and Feed Items**
in Support Settings.

**Why it works:** `<type>SendEmail</type>` is the documented `QuickActionType` value for this
composer (available in API version 31.0 and later). The template and predefined values are
applied when the composer opens, so the agent starts from a correct draft rather than a blank
one. Field names in the layout use the casing the LWC guide documents for the email composer's
fields — `ValidatedFromAddress`, `ToAddress`, `CcAddress`, `BccAddress`, `Subject`, `HTMLBody`,
`RelatedToId`.

---

## Example 2: Context-dependent defaults with `QuickActionDefaultsHandler`

**Context:** the template must differ between a first touch and a reply, and every outbound
case email must BCC a compliance mailbox chosen by `Case.Reason`.

**Problem:** predefined field values are static. A formula on the action cannot see whether the
agent clicked Reply on an existing feed item, nor which case is in context.

**Solution:** implement `QuickAction.QuickActionDefaultsHandler`. The interface requires
*"an empty parameterless constructor"* and works in both Salesforce Classic and Lightning
Experience.

```apex
/**
 * Sets context-dependent defaults for the standard case-feed Email action.
 */
global class CaseEmailDefaults implements QuickAction.QuickActionDefaultsHandler {

    // Required by the interface: empty, parameterless.
    global CaseEmailDefaults() {}

    global void onInitDefaults(QuickAction.QuickActionDefaults[] defaults) {
        QuickAction.SendEmailQuickActionDefaults emailDefaults = findEmailDefaults(defaults);
        if (emailDefaults == null) {
            return;
        }

        // One bounded query per init — getContextId() is the Case Id.
        Case ctx = [
            SELECT Id, Reason
            FROM Case
            WHERE Id = :emailDefaults.getContextId()
            WITH USER_MODE
            LIMIT 1
        ];

        EmailMessage draft = (EmailMessage) emailDefaults.getTargetSObject();
        draft.BccAddress = auditMailboxFor(ctx.Reason);

        if (emailDefaults.getInReplyToId() == null) {
            // First outbound touch on this case: lead with the acknowledgement template.
            emailDefaults.setTemplateId(templateId('Case_First_Touch'));
            emailDefaults.setInsertTemplateBody(false);    // replace existing body content
            emailDefaults.setIgnoreTemplateSubject(false); // template supplies the subject
        } else {
            // Reply to an existing email: keep the customer's subject so the thread holds.
            emailDefaults.setTemplateId(templateId('Case_Reply'));
            emailDefaults.setInsertTemplateBody(false);
            emailDefaults.setIgnoreTemplateSubject(true);  // use the original subject
        }
    }

    private QuickAction.SendEmailQuickActionDefaults findEmailDefaults(
        QuickAction.QuickActionDefaults[] defaults
    ) {
        for (QuickAction.QuickActionDefaults qad : defaults) {
            if (qad instanceof QuickAction.SendEmailQuickActionDefaults
                && qad.getTargetSObject().getSObjectType() == EmailMessage.sObjectType
                && qad.getActionName().equals('Case.Email')
                && qad.getActionType().equals('Email')) {
                return (QuickAction.SendEmailQuickActionDefaults) qad;
            }
        }
        return null;
    }

    private Id templateId(String developerName) {
        List<EmailTemplate> found = [
            SELECT Id FROM EmailTemplate
            WHERE DeveloperName = :developerName
            WITH USER_MODE
            LIMIT 1
        ];
        // A missing template must not block the composer — return null and log upstream.
        return found.isEmpty() ? null : found[0].Id;
    }

    private String auditMailboxFor(String caseReason) {
        if (caseReason == 'Billing')   { return 'billing-audit@example.com'; }
        if (caseReason == 'Technical') { return 'tech-audit@example.com'; }
        return 'support-audit@example.com';
    }
}
```

**Why it works:** `getActionName()` returns `Case.Email` and `getActionType()` returns `Email`
for the standard case-feed Email action, so the `instanceof` + name + type filter is what keeps
the handler from mutating an unrelated action's payload. `getTargetSObject()` hands back the
`EmailMessage` being drafted, so writing `BccAddress` on it defaults the field.
`getInReplyToId()` is non-null only when reply/reply-all was invoked on an email message feed
item — the cleanest available signal for first-touch vs. reply.

`setInsertTemplateBody(false)` replaces the existing body content; `true` inserts the template
body above it. `setIgnoreTemplateSubject(true)` keeps the original subject rather than the
template's — the same decision the **Don't Apply Template Subject** checkbox makes
declaratively.

Enforce CRUD/FLS on anything the handler reads or writes beyond the draft (see
`templates/apex/SecurityUtils.cls`) and route the missing-template case through
`templates/apex/ApplicationLogger.cls` rather than swallowing it silently.

---

## Example 3: Prepopulating the composer from an LWC quick action

**Context:** the agent must answer a short prompt (which order is this about?) before the
composer opens, and the answer determines the recipient and subject.

**Problem:** neither predefined field values nor the Apex handler can collect input from the
agent first — both resolve before the composer renders, with no user interaction.

**Solution:** an LWC quick action that navigates to the standard email composer with encoded
default field values.

```javascript
// caseEmailLauncher.js
import { LightningElement, api } from 'lwc';
import { NavigationMixin } from 'lightning/navigation';
import { encodeDefaultFieldValues } from 'lightning/pageReferenceUtils';

export default class CaseEmailLauncher extends NavigationMixin(LightningElement) {
    @api recordId;

    launchComposer(toAddress, subject) {
        const defaults = encodeDefaultFieldValues({
            ToAddress: toAddress,
            Subject: subject,
            RelatedToId: this.recordId
        });

        this[NavigationMixin.Navigate]({
            type: 'standard__quickAction',
            attributes: { apiName: 'Case.Email' },
            state: { recordId: this.recordId, defaultFieldValues: defaults }
        });
    }
}
```

**Why it works:** `encodeDefaultFieldValues` from `lightning/pageReferenceUtils` prepopulates
the supported email fields — `ValidatedFromAddress`, `ToAddress`, `CcAddress`, `BccAddress`,
`Subject`, `HTMLBody`, and `RelatedToId`.

Two documented constraints bound this pattern: the fields you pass **must not be Read-Only on
the action's layout** (if `HTMLBody` and `Subject` are read-only, the draft opens without the
prepopulated text), and *"The LWC quick email action isn't supported in Experience Builder
sites."*

---

## Anti-Pattern: sending case email with `Messaging.SingleEmailMessage`

**What practitioners do:** an agent asks for a one-click "email the customer" button, and the
build produces an Apex `@AuraEnabled` method that constructs a `Messaging.SingleEmailMessage`
and calls `Messaging.sendEmail`.

**What goes wrong:** the agent never sees a draft, cannot edit the body, cannot attach a file,
and cannot use quick text. The composer's template, predefined-value, and layout configuration
is bypassed entirely, and the message is sent the instant the button is clicked.

**Correct approach:** configure the Send Email quick action so the composer opens with the
right draft, and let the agent review before sending. If the draft needs case-dependent
content, use `QuickAction.QuickActionDefaultsHandler` (Example 2) — it defaults the
`EmailMessage` the composer is about to render rather than replacing the composer.

---

## Anti-Pattern: reparenting a misfiled email with a data fix

**What practitioners do:** an email threads onto the wrong case, so someone updates
`EmailMessage.ParentId` through Data Loader or anonymous Apex.

**What goes wrong:** the correction happens outside the agent-facing path Salesforce ships for
it, so it is invisible to the people who need to know, and it does not scale past the one
record someone happened to notice.

**Correct approach:** enable the move-email capability for agents (*"Let Agents Move Emails to
a Different Case"*) and let them move the email from inside Case Feed. The Winter '25 release note
scopes the capability to emails created by Email-to-Case in orgs using Lightning threading, so
confirm both before relying on it. Then treat a rising volume of moves as a signal to fix
Email-to-Case matching upstream, which is where the actual defect lives
(`admin/email-to-case-configuration`).
