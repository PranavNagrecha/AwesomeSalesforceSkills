# Gotchas — Apex Outbound Email Patterns

Non-obvious Salesforce platform behaviors that cause real production problems with outbound email.

---

## Gotcha 1: Email is not transactional — rollback does not unsend

`Messaging.sendEmail` queues the send to the platform's mail
infrastructure as a side effect. If the transaction rolls back
afterwards (DML failure, uncaught exception), the email *still
goes out*. Practical implication: send email **after** all DML
that must succeed, not before. Or use a Queueable that runs
post-commit so the email send is gated on the data being
persisted.

---

## Gotcha 2: Daily limit counts recipients, not calls

The 5,000-email/day cap is total external recipients. One call
with 100 To-addresses burns 100 from the bucket; two calls with 50
each burn the same 100. CC and BCC also count. Resetting happens
on a rolling 24h window, not at midnight.

---

## Gotcha 3: `setTemplateId` + `setTargetObjectId` requires Contact / Lead / User

```apex
msg.setTemplateId(tplId);
msg.setTargetObjectId(account.Id);  // RUNTIME ERROR
```

`targetObjectId` must be a Contact, Lead, or User Id. To merge
against any other object, use `Messaging.renderStoredEmailTemplate(
templateId, targetObjectId /* may be null */, whatId)` and pass the
record Id as `whatId`.

---

## Gotcha 4: `setHtmlBody` literal string is not merged

`setHtmlBody('Hello {!Contact.FirstName}')` sends the literal
braces. Merge happens only when the template path
(`setTemplateId` + `renderStoredEmailTemplate`) is used, or when
you build the merged string yourself before calling `setHtmlBody`.

---

## Gotcha 5: OrgWideEmailAddress must be verified and accessible

Just having a row in `OrgWideEmailAddress` is not enough — the
address must be verified (admin clicks the verification link sent
during setup) and the running user's profile must be in the
allowed-profiles list for that OWE. Otherwise sends silently fall
back to the running user as From.

---

## Gotcha 6: `setReplyTo` and OrgWideEmailAddress are independent

Setting both is the common case (From = `orders@acme.com`, Reply-To
= `support@acme.com`). Setting neither makes the running user both.
Setting only OWE sends From = OWE and replies also go to the OWE.
Recipients sometimes filter / route on Reply-To rather than From,
so the distinction matters.

---

## Gotcha 7: `setSaveAsActivity(true)` requires `setWhatId` or `setTargetObjectId`

Without one of those, the activity record cannot be related to
anything and the save silently no-ops.

---

## Gotcha 8: Tests do not actually send mail

In `@isTest`, `Messaging.sendEmail` short-circuits — no real send,
but the call still consumes governor counters and returns a
`SendEmailResult`. To assert behavior, query
`Limits.getEmailInvocations()` or check the message contents on the
fake queue. Do not rely on inspecting an Inbox in CI.

---

## Gotcha 9: `EmailFileAttachment` size is bounded

The total size of a SingleEmailMessage including all attachments is
~25MB; individual attachments are bounded by the API limit (~10MB
for inline encoded). Build the message and check
`getBodyAsBlob().size()` before sending; oversize attaches return
`STORAGE_LIMIT_EXCEEDED` not a clean error.
