# Well-Architected Notes — Inbound Email Service

## Relevant Pillars

- **Reliability** — Subject-token threading is more robust than
  `In-Reply-To` parsing because the token is part of the visible
  subject; email clients can't strip it without the user
  noticing.
- **Security** — `success = false` messages reach the sender;
  generic friendly text is the right answer (never expose stack
  traces). Allow-list public-facing addresses to limit spam.
- **Operational Excellence** — Synchronous callouts from the
  handler block email processing under load; publish to a
  Platform Event for async fan-out so the handler returns
  quickly.

## Architectural Tradeoffs

- **Email-to-Case vs custom service.** E2C wins for case
  creation. Custom wins for everything else.
- **Inbound subject-token threading vs `In-Reply-To` parsing.**
  Subject token is robust; `In-Reply-To` is standards-compliant
  but client-mangled in practice.
- **Allow-list in Custom Metadata vs hardcoded.** Custom Metadata
  is admin-editable without redeploy; hardcoded is simpler but
  brittle.
- **Synchronous DML in handler vs async via Platform Event.**
  Sync is simpler for low-volume; async is required for
  high-volume.

## Anti-Patterns

1. **`public` instead of `global` for the handler.** Doesn't
   satisfy the interface contract.
2. **Stack trace in `success = false` message.** Information
   disclosure to potentially-anonymous senders.
3. **Synchronous callout in the handler.** Latency × volume
   blocks email processing.
4. **Treating `email.headers` as a Map.** It's a List; iterate.
5. **Threading purely on `In-Reply-To`.** Unreliable; subject
   token is more robust.
6. **No attachment-size / count / MIME-type policy.** File
   storage fills; org-wide effects.

## Official Sources Used

- Apex Reference: Messaging.InboundEmailHandler — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_interface_System_Messaging_InboundEmailHandler.htm
- Apex Reference: Messaging.InboundEmail — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_Messaging_InboundEmail.htm
- Email Services Setup — https://help.salesforce.com/s/articleView?id=sf.code_email_services.htm&type=5
- EmailServicesAddress Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_emailservicesaddress.htm
- Email-to-Case Considerations — https://help.salesforce.com/s/articleView?id=sf.customizesupport_email_overview.htm&type=5
- Sibling skill — `skills/service/email-to-case/SKILL.md` (when one exists)
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
