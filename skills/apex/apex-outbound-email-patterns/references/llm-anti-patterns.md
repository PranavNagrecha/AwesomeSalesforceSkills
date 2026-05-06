# LLM Anti-Patterns — Apex Outbound Email Patterns

Common mistakes AI coding assistants make when generating outbound email Apex.

---

## Anti-Pattern 1: Setting From by string instead of OrgWideEmailAddress

**What the LLM generates.**

```apex
msg.setSenderDisplayName('Acme Orders');
// (and no setOrgWideEmailAddressId)
```

**Correct pattern.**

```apex
msg.setOrgWideEmailAddressId(oweId);  // verified address row
```

`setSenderDisplayName` only changes the display name; the
underlying email address is still the running user. Recipients see
"Acme Orders <integration.user@acme.com.dev>", which fails DMARC
and undermines trust.

**Detection hint.** Any `setSenderDisplayName` without a matching
`setOrgWideEmailAddressId` in the same builder is incomplete.

---

## Anti-Pattern 2: `setHtmlBody` with template merge syntax

**What the LLM generates.**

```apex
msg.setHtmlBody('Hi {!Contact.FirstName}, your order {!Order__c.Name}...');
```

**Correct pattern.** Use `Messaging.renderStoredEmailTemplate(
templateId, targetObjectId, whatId)` to get a pre-merged
SingleEmailMessage, *or* render the merge in Apex with
`String.format(...)` against fields you queried explicitly.

**Detection hint.** Any `setHtmlBody` or `setPlainTextBody` whose
argument contains `{!` is a literal-merge string that will be sent
verbatim.

---

## Anti-Pattern 3: `setTargetObjectId(account.Id)` with a template

**What the LLM generates.**

```apex
msg.setTemplateId(tplId);
msg.setTargetObjectId(account.Id);
```

**Correct pattern.** Use `renderStoredEmailTemplate(tplId, null,
account.Id)`. `setTargetObjectId` requires a Contact, Lead, or User
— anything else fails at runtime with `INVALID_ID_FIELD`.

**Detection hint.** Any `setTargetObjectId` whose argument is
demonstrably an Account, Case, Opportunity, or custom object Id.

---

## Anti-Pattern 4: Sending from inside a trigger without async

**What the LLM generates.**

```apex
trigger OrderTrigger on Order__c (after update) {
    for (Order__c o : Trigger.new) {
        // ... build msg ...
        Messaging.sendEmail(new Messaging.SingleEmailMessage[]{ msg });
    }
}
```

**Correct pattern.** Buffer outbound mail to a Queueable that runs
post-commit. Mail sends are not transactional — if the trigger's
DML rolls back, the email already went. Worse, the unbulkified loop
exhausts `Limits.getEmailInvocations()` (10/transaction).

**Detection hint.** Any `Messaging.sendEmail` invocation inside a
`for (... : Trigger.new)` loop is unbulkified and violates the
post-commit principle.

---

## Anti-Pattern 5: Ignoring `Messaging.SendEmailResult`

**What the LLM generates.**

```apex
Messaging.sendEmail(new Messaging.SingleEmailMessage[]{ msg });
return true;
```

**Correct pattern.** Iterate `results`, check `isSuccess()`, log
`getErrors()`. With `allOrNone=false`, individual recipient
failures (bounces, opt-outs) appear here and nowhere else — the
call itself returns normally.

**Detection hint.** Any `Messaging.sendEmail` call whose return
value is discarded, with no surrounding `try/catch` for
`SINGLE_EMAIL_LIMIT_EXCEEDED`.

---

## Anti-Pattern 6: Hardcoded From address with no override path

**What the LLM generates.**

```apex
msg.setReplyTo(new String[]{ 'no-reply@acme.com' });
```

**Correct pattern.** Read From / Reply-To from Custom Metadata
(`EmailConfig__mdt`) keyed by integration. Hardcoded addresses
break sandbox refreshes (sandbox should not email customers) and
require deployments to change supplier-of-record.

**Detection hint.** Any literal `@` string in a `setReplyTo` /
`setBccAddresses` / `setCcAddresses` argument outside of test
classes.

---

## Anti-Pattern 7: Treating MassEmailMessage as a viable option

**What the LLM generates.**

```apex
Messaging.MassEmailMessage mass = new Messaging.MassEmailMessage();
mass.setTargetObjectIds(...);
Messaging.sendEmail(new Messaging.MassEmailMessage[]{ mass });
```

**Correct pattern.** `MassEmailMessage` is deprecated for new
development. Use SingleEmailMessage in a chunked loop (≤100
recipients per call). The mass form lacks attachment, OWE, and
allOrNone control.

**Detection hint.** Any `Messaging.MassEmailMessage` reference in
a file that does not have a comment justifying legacy maintenance.
