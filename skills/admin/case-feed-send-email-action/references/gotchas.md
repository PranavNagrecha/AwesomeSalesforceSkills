# Gotchas — Case Feed Send Email Action

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: The outbound composer requires the inbound feature

**What happens:** you go to add a Send Email quick action to Case and the configuration doesn't
hold, even though the team never intends to receive email into Salesforce.

**When it occurs:** Email-to-Case is off. Salesforce Help states the dependency directly:
*"Email-to-Case must be enabled to use the Send Email quick action on the Cases object."*

**How to avoid:** treat Email-to-Case enablement as a prerequisite of the outbound composer,
not as a separate initiative. Confirm it before scoping any Send Email work. Configuring the
inbound channel itself is `admin/email-to-case-configuration`.

---

## Gotcha 2: A missing Email action has two very different root causes

**What happens:** the action exists in Setup, the template is attached, and agents report they
still cannot email the customer from the case.

**When it occurs:** two independent surfaces hide the action, and practitioners reflexively blame
the first one.

1. **The layout.** A custom Send Email action is invisible until it is added to the Case page
   layout. Salesforce Help documents that placement as its own procedure — *"Add Quick Actions to
   the Case Page Layout for Lightning Experience."*
2. **Org-level settings.** For the *standard* Email action, the Salesforce Knowledge article
   *"Email Quick Action Not Available on Case Feed"* prescribes no layout change at all. Its
   documented resolution is to change the email deliverability access level from **System Email
   Only** to **All email**, enable Email-to-Case (which cannot be disabled afterwards), and, if the
   action is still unavailable, select **Enable Case Feed Actions and Feed Items** in Support
   Settings. The article also notes that agents sending through Office 365 or Gmail need the
   matching permission set assigned.

**How to avoid:** triage both. Enumerate every Case page layout assigned to a support persona (not
just the one you were looking at) and add the action to each; re-check after any record-type or
profile change that swaps layouts. If the *standard* Email action is the one missing, walk the
three org-level causes above before touching a layout.

---

## Gotcha 3: Only Custom-type templates can be the action's default

**What happens:** the **Default Email Template** lookup won't accept the polished Lightning
template marketing built, or the composer opens without the expected body.

**When it occurs:** the template's type is anything other than Custom. Salesforce Help:
*"create an email template of the type Custom. Only Custom type templates are supported."*

**How to avoid:** author (or re-author) the default as a **Custom**-type template. Related
skills: `admin/email-templates-and-alerts` for authoring, `admin/classic-email-template-migration`
for moving legacy templates into a supported type.

---

## Gotcha 4: The template's subject silently overwrites a reply's subject

**What happens:** an agent replies to a customer, the composer applies the default template,
and the subject line changes — so the customer's mail client breaks the message out of the
existing thread.

**When it occurs:** the action has a default template with a subject, and **Don't Apply Template
Subject** is cleared. The Apex equivalent is `setIgnoreTemplateSubject(false)`.

**How to avoid:** select **Don't Apply Template Subject** on reply-oriented actions (or call
`setIgnoreTemplateSubject(true)` in a `QuickActionDefaultsHandler`) so the subject already in
play survives. Clear it only for first-touch actions where the template is meant to name the
conversation.

---

## Gotcha 5: A read-only field on the action layout discards prepopulated values

**What happens:** predefined field values (or `encodeDefaultFieldValues`, or a value the Apex
handler wrote onto the draft `EmailMessage`) don't appear. There is no error — the composer
simply opens with the field blank.

**When it occurs:** the field is Read-Only on the Send Email action's layout. The LWC guide
warns explicitly that if `HTMLBody` and `Subject` are Read-Only, the draft doesn't include
pre-populated text for those fields.

**How to avoid:** make every field you intend to prepopulate editable on the action layout.
If a field must be locked, prepopulating it is not the right tool — lock the content in the
template instead.

---

## Gotcha 6: The attachment limits are per-UI, not platform-wide

**What happens:** an agent attaches a handful of screenshots and a log file, clicks Send, and
the email fails.

**When it occurs:** the send exceeds the limits Salesforce Knowledge documents for the UI the agent
is in. In **Lightning Experience**, up to 10 files can be attached and *"the total file size can't
exceed 25MB."* In **Salesforce Classic**, more than 10 files are allowed but *"the total file size
can't exceed 18 MB."* Both numbers are attachment-total limits, and the 25 MB figure is a Lightning
Experience limit — not a universal cap on outbound Salesforce email.

**How to avoid:** budget the attachment total against the limit for the UI the support team
actually uses, and don't quote 25 MB at a Classic org. Train agents to link to files in Salesforce
rather than attach them, and to send more than 10 files as a link rather than a second email. No
official source states a per-attachment size cap, so don't promise one.

---

## Gotcha 7: Unsupported fields in predefined field values

**What happens:** an attempt to default an attachment onto the action does nothing.

**When it occurs:** `AttachmentId` and `ContentDocumentIds` are used as predefined field values.
They aren't supported, because they aren't part of the email quick action layout. Only fields
available on the action are supported. For recipients, use ID fields (such as `Contact.Id`) or
string fields (such as a custom email field); Contact, lead, and person-account IDs are
supported.

**How to avoid:** restrict predefined values to fields that appear on the action layout. If a
standard attachment must accompany every email, embed it in the template rather than defaulting
the field.
