# LLM Anti-Patterns — Case Feed Send Email Action

Common mistakes AI coding assistants make when generating or advising on the Case Feed Send
Email action. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Answering the outbound question with Email-to-Case setup

**What the LLM generates:** asked "how do agents email the customer from a case," it produces
routing addresses, verification emails, thread-ID settings, and `Case.SuppliedEmail` — the
inbound channel.

**Why it happens:** "Salesforce" + "case" + "email" is overwhelmingly Email-to-Case in training
data. The outbound composer is a much smaller corpus.

**Correct pattern:**

```text
Setup → Object Manager → Case → Buttons, Links, and Actions → New Action
  Action Type = Send Email
Then: Default Email Template (Custom type) → add the action to the Case page layout.
(Email-to-Case must already be enabled — it is a prerequisite, not the answer.)
```

**Detection hint:** output that mentions routing addresses, `EmailServicesAddress`, or
thread-ID matching in response to a question about *sending*.

---

## Anti-Pattern 2: Replacing the composer with `Messaging.SingleEmailMessage`

**What the LLM generates:** an `@AuraEnabled` Apex method that builds a
`Messaging.SingleEmailMessage`, sets `setWhatId`/`setTargetObjectId`, and calls
`Messaging.sendEmail` — wired to a button labelled "Email Customer."

**Why it happens:** `Messaging.sendEmail` is the single most-represented "send email in
Salesforce" snippet in training data, and it superficially satisfies the request.

**Correct pattern:** configure the Send Email quick action so a *draft* opens. If the draft
needs case-dependent content, default it:

```apex
global class CaseEmailDefaults implements QuickAction.QuickActionDefaultsHandler {
    global CaseEmailDefaults() {}
    global void onInitDefaults(QuickAction.QuickActionDefaults[] defaults) { /* ... */ }
}
```

**Detection hint:** `Messaging.sendEmail` or `SingleEmailMessage` anywhere in a response about
the Case Feed email composer.

---

## Anti-Pattern 3: Casting `QuickActionDefaults` without the name/type filter

**What the LLM generates:**

```apex
// WRONG — mutates whatever happens to be at index 0
QuickAction.SendEmailQuickActionDefaults d =
    (QuickAction.SendEmailQuickActionDefaults) defaults[0];
```

…and often omits the required empty constructor entirely.

**Why it happens:** the model compresses the documented loop into "grab the first element," and
constructors that do nothing look like dead code worth deleting.

**Correct pattern:**

```apex
global CaseEmailDefaults() {}   // required: empty, parameterless

for (QuickAction.QuickActionDefaults qad : defaults) {
    if (qad instanceof QuickAction.SendEmailQuickActionDefaults
        && qad.getTargetSObject().getSObjectType() == EmailMessage.sObjectType
        && qad.getActionName().equals('Case.Email')
        && qad.getActionType().equals('Email')) {
        // safe to cast
    }
}
```

**Detection hint:** `defaults[0]`, `defaults.get(0)`, a cast with no `instanceof` guard, or a
handler class with no zero-argument constructor.

---

## Anti-Pattern 4: Inventing a template field on the `QuickAction` metadata

**What the LLM generates:** a `quickAction-meta.xml` containing a fabricated element such as
`<defaultEmailTemplate>` or `<emailTemplateName>`, presented as the way to attach the default
template in source control.

**Why it happens:** the model assumes anything configurable in Setup has a symmetric Metadata
API element, and confabulates a plausible tag name.

**Correct pattern:** the Metadata API `QuickAction` documentation lists `label`, `type`,
`targetObject`, `quickActionLayout`, `fieldOverrides`, and `optionsCreateFeedItem` — it does not
document a template field. Treat **Default Email Template** as a Setup-surface setting and
verify it after every org migration.

**Detection hint:** any `<...Template...>` element inside a `<QuickAction>` block. Also flag a
`<type>` value other than `SendEmail` for this action (`SendEmail` is available in API version
31.0 and later).

---

## Anti-Pattern 5: Recommending a Lightning or HTML template as the action default

**What the LLM generates:** "point the action's Default Email Template at your Lightning email
template" — sometimes with confident instructions for building one first.

**Why it happens:** Lightning email templates are the modern, most-discussed template type, so
the model reaches for them by default.

**Correct pattern:**

```text
Default Email Template must be a template of type Custom.
"Only Custom type templates are supported."
```

**Detection hint:** the words "Lightning email template" or "HTML template" adjacent to
"Default Email Template" on the Send Email action.

---

## Anti-Pattern 6: Prepopulating fields the action can't take

**What the LLM generates:** predefined field values (or an `encodeDefaultFieldValues` call) for
`AttachmentId` or `ContentDocumentIds`, or a prepopulated `Subject` on an action whose layout
marks Subject read-only.

**Why it happens:** the model reasons from the `EmailMessage` object's full field list rather
than from the quick action's layout, and treats "field exists on the sObject" as "field is
settable here."

**Correct pattern:**

```text
Supported prepopulation targets: ValidatedFromAddress, ToAddress, CcAddress,
BccAddress, Subject, HTMLBody, RelatedToId — and none of them may be Read-Only on
the action layout, or the value is silently dropped.
AttachmentId / ContentDocumentIds are not supported.
```

**Detection hint:** `AttachmentId` or `ContentDocumentIds` in a predefined-values or
`encodeDefaultFieldValues` block; any prepopulation advice that never mentions the layout's
read-only setting.

---

## Anti-Pattern 7: Offering `apex:emailPublisher` as the Lightning answer

**What the LLM generates:** a Visualforce page using `apex:emailPublisher` with
`toVisibility="readOnly"` and `emailBodyFormat="HTML"`, presented as how to customize the
Lightning Case Feed composer.

**Why it happens:** the component's documentation is rich and explicitly about "customizing the
Email action," so it retrieves strongly — without the model registering that it belongs to the
Visualforce-era Case Feed.

**Correct pattern:** in Lightning Experience, field visibility and editability come from the
**action's layout**, not from VF attributes. Reach for `apex:emailPublisher` (which requires an
`entityId`, API 25.0+) only when maintaining an existing Visualforce Case Feed surface. If you do
touch it, the visibility enums differ: `toVisibility` / `ccVisibility` / `bccVisibility` accept
`editable`, `editableWithLookup`, `readOnly`, or `hidden`, while `subjectVisibility` accepts only
`editable`, `readOnly`, or `hidden`.

**Detection hint:** `apex:emailPublisher`, `ccVisibility`, `subjectVisibility`, or `entityId` in
a response about Lightning Case Feed; `subjectVisibility="editableWithLookup"`, which is not a
documented value.

---

## Anti-Pattern 8: Stamping a maturity level, or widening a scoped limit

**What the LLM generates:** "the Send Email quick action became GA in Spring '21," or "Move
Emails to a Different Case is currently in Beta," or "each attachment can be up to 10 MB," or
"Salesforce caps every outbound email at 25 MB."

**Why it happens:** models pattern-fill release-status labels, round numeric limits from adjacent
features, and promote a UI-scoped limit into a platform-wide one because the qualifier is the
easiest clause to drop.

**Correct pattern:**

```text
No GA / Beta / Pilot label exists for the Send Email quick action or for
Move Emails to a Different Case. Both are documented as standard features.

Attachment limits are documented per UI:
  Lightning Experience — up to 10 files, total file size <= 25 MB
  Salesforce Classic   — more than 10 files, total file size <= 18 MB
Both are attachment totals. No per-attachment size cap is documented.
```

**Detection hint:** any "GA," "Beta," "Pilot," or "generally available since" claim about these
features; a per-attachment size limit; a "25 MB" claim with no Lightning Experience qualifier, or
one that folds the body, headers, inline images, and signature into the same total.
