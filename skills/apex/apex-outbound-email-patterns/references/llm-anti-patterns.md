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

**Detection hint.** Any `Messaging.sendEmail(..., false)` call whose
return value is discarded. Note the converse trap: wrapping that same
`allOrNone=false` call in a `try/catch` is equally wrong, because it
does not throw — see Anti-Pattern 7.

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
development. Use SingleEmailMessage in a chunked loop (≤150
recipients per message, counting `toAddresses` + `ccAddresses` +
`bccAddresses` together). The mass form lacks attachment, OWE, and
allOrNone control.

**Detection hint.** Any `Messaging.MassEmailMessage` reference in
a file that does not have a comment justifying legacy maintenance.

---

## Anti-Pattern 7: Catching `System.HandledException` for `SINGLE_EMAIL_LIMIT_EXCEEDED`

**What the LLM generates.**

```apex
try {
    Messaging.sendEmail(msgs, false);
} catch (System.HandledException e) {                       // wrong type…
    if (e.getMessage().contains('SINGLE_EMAIL_LIMIT_EXCEEDED')) {
        EmailRetryQueue.enqueue(msgs);                      // …never runs
    }
}
```

**Why it happens.** Two independent errors reinforce each other. The exception type is wrong because `HandledException` sounds like the generic base for "errors you are expected to handle" — a reasonable reading of the name. It is actually the Visualforce/Aura surface exception, described in the reference as merely "A generic handled exception", and it is never raised by `Messaging.sendEmail`. The email exception is `EmailException` ("Any problem with email, such as failure to deliver"). Separately, `allOrNone = false` means the call **does not throw at all** — failures come back inside `Messaging.SendEmailResult` — so even the correct `catch (EmailException e)` would be dead code in this snippet. Both errors are invisible: the class compiles, deploys, and passes every test that does not actually exhaust the org's daily email allocation. The retry queue looks implemented and is not, and the failure surfaces as customers silently not receiving mail.

**Correct pattern.** Match the error-delivery mechanism to the `allOrNone` argument.

```apex
// allOrNone = true (the default): it throws.
try {
    Messaging.sendEmail(msgs);
} catch (System.EmailException e) {
    if (e.getMessage().contains('SINGLE_EMAIL_LIMIT_EXCEEDED')) { /* retry */ }
    else { throw e; }
}

// allOrNone = false: it does NOT throw — read the results.
Messaging.SendEmailResult[] rs = Messaging.sendEmail(msgs, false);
for (Integer i = 0; i < rs.size(); i++) {
    if (rs[i].isSuccess()) { continue; }
    for (Messaging.SendEmailError err : rs[i].getErrors()) {
        if (err.getStatusCode() == StatusCode.SINGLE_EMAIL_LIMIT_EXCEEDED) { /* retry */ }
    }
}
```

**Detection hint.** grep for `catch\s*\(\s*(System\.)?HandledException` in any `.cls` — in email code it is always wrong, and outside Visualforce/Aura controllers it is nearly always wrong. Stronger and fully mechanical: flag any `Messaging.sendEmail\([^)]*,\s*false\s*\)` that is lexically inside a `try` block, and any `Messaging.sendEmail` with a second argument of `false` whose return value is not assigned. Conversely flag `Messaging.sendEmail\(\s*\w+\s*\)` (single-argument, therefore throwing) that is *not* inside a `try`. Cross-check any exception class named in email guidance against the built-in exception list; `EmailException` is the only email-specific member.
