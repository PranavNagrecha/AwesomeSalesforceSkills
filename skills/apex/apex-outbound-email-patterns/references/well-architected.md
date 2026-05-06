# Well-Architected Notes — Apex Outbound Email Patterns

## Relevant Pillars

- **Operational Excellence** — Outbound email is one of the most
  common production problems on Salesforce: replies go to the wrong
  inbox, sandbox sends customer email, daily limits trip silently
  during a campaign, and the From address doesn't match SPF/DMARC
  for the company domain. Centralizing the build of every
  `Messaging.SingleEmailMessage` through a single helper
  (`OutboundEmail.build(...)`) — that always reads OWE/ReplyTo from
  Custom Metadata, always sets `saveAsActivity`, and always returns
  a parseable result — makes audits and rollouts predictable.
- **Reliability** — `Messaging.sendEmail` is non-transactional.
  Architecting around that requires queuing the send post-commit
  (Queueable, Platform Event-driven), capping the daily-limit
  exposure with monitoring, and explicit retry logic for
  `SINGLE_EMAIL_LIMIT_EXCEEDED`. Treating email as fire-and-forget
  produces silent customer-facing outages.

## Architectural Tradeoffs

The main tradeoff is **declarative agility vs programmatic control**.
Email Alerts triggered from Flow are admin-editable end-to-end —
the template, the recipient set, the from-address — and respect
OWE/Reply-To. Apex `Messaging.SingleEmailMessage` gives full
programmatic control (conditional content, runtime attachments,
custom merge against custom objects, error handling) but every
change is a deployment.

Specifically:

- **Status-change notifications, simple alerts**: Email Alert from
  Flow.
- **Confirmation emails with PDFs generated at runtime**: Apex
  SingleEmailMessage.
- **Bulk personalized sends > 100 recipients**: Apex with chunking.
- **Marketing campaigns**: Marketing Cloud, not Apex.

## Anti-Patterns

1. **Sending inside a trigger without async.** Email is not
   transactional; rollbacks don't unsend. Buffer to a Queueable.
2. **Hard-coding addresses.** Sandbox refreshes will email
   customers. Read addresses from Custom Metadata.
3. **Ignoring SendEmailResult.** With `allOrNone=false`, per-
   recipient failures appear only in the result list. Discarding
   the return value means bounces and opt-outs are invisible.

## Official Sources Used

- Messaging.SingleEmailMessage Class — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_Messaging_SingleEmailMessage.htm
- Messaging.sendEmail() — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_methods_system_messaging.htm
- OrgWideEmailAddress (Object Reference) — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_orgwideemailaddress.htm
- Email Limits in Salesforce — https://help.salesforce.com/s/articleView?id=sf.limits_email.htm
- Email Deliverability Settings — https://help.salesforce.com/s/articleView?id=sf.emailadmin_setup_deliverability.htm
- Salesforce Well-Architected: Resilient — https://architect.salesforce.com/well-architected/resilient/observable
