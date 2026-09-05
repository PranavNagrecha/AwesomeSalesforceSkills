# Well-Architected Notes — Inbound Email Service

## Relevant Pillars

- **Reliability** — Inbound mail has no retry the sender controls. The
  three fields that decide whether a message survives an outage are
  `functionInactiveAction`, `overLimitAction` and the pair
  `isErrorRoutingEnabled` / `errorRoutingAddress`. `Requeue` holds a
  message for 24 hours; `Discard` loses it with no notification to anyone.
  Choosing these is a resilience decision, not a Setup formality.
- **Security** — `InboundEmailResult.message` is mailed back to the
  original sender, who may be anonymous. It is an egress channel, so it
  gets the same treatment as any other: no exception detail, no record
  Ids, no internal hostnames. The complementary control is inbound:
  `authorizedSenders` plus `isAuthenticationRequired`
  (SPF / SenderId / DomainKeys) so unverified senders never reach Apex.
- **Operational Excellence** — The routing address is generated per org and
  cannot be promoted from sandbox, so "which address is live in which org"
  is operational state that must live in Custom Metadata and be re-read
  after every refresh, not in a wiki page.
- **Performance / Scalability** — The daily processing limit is org-wide
  (user licences x 1,000, capped at 1,000,000) and is shared with On-Demand
  Email-to-Case. Adding an email service spends a budget another feature is
  already drawing on.

## Architectural Tradeoffs

- **Email-to-Case vs custom service.** E2C wins for case creation: it
  brings threading, auto-response and routing that would otherwise be
  hand-built. Custom wins for every other record type, and for intake that
  is not a support conversation at all.
- **One service, many addresses vs many services.** One service is simpler
  and keeps a single `apexClass`, but `authorizationFailureAction`,
  `overLimitAction` and `functionInactiveAction` are service-level. Two
  address populations that need different rejection behaviour need two
  services, even when they share the handler.
- **Platform-level attachment filtering vs Apex-level.** `attachmentOption`
  rejects before Apex runs — cheaper, and the bytes never reach the heap —
  but it is coarse and invisible to the handler. Apex filtering is
  auditable and configurable per policy, but only after the platform has
  already delivered the payload. Production designs use both.
- **Header threading vs subject-token threading.** `messageId` /
  `inReplyTo` / `references` are standards-compliant and free; subject
  tokens survive clients that recompose instead of replying. Neither alone
  is sufficient for a public inbox.
- **Synchronous DML in the handler vs async via Platform Event.**
  Synchronous is simpler and keeps the 50 MB email-service heap. Async is
  required once callouts enter the picture, but the Blob must not travel
  with it.
- **Allow-list in Custom Metadata vs hardcoded.** Custom Metadata is
  admin-editable without a deploy and is also where the per-org routing
  address belongs; hardcoding is simpler until the first sandbox refresh.

## Anti-Patterns

1. **Declaring the handler `global` reflexively.** `public with sharing`
   matches the guide's own samples; `global` is a packaging decision.
2. **Stack trace in the `message` field.** Information disclosure to a
   potentially anonymous sender.
3. **Synchronous callout in the handler.** Latency times volume backs up
   inbound processing.
4. **Iterating `headers` for `In-Reply-To`.** The platform already parsed
   it onto `email.inReplyTo`.
5. **Threading on `inReplyTo` alone,** with no `references` check and no
   subject-token fallback.
6. **No attachment size / count / MIME-type policy,** and no
   `attachmentOption` set deliberately.
7. **`overLimitAction` or `functionInactiveAction` left at
   `UseSystemDefault`** on a business-critical intake — the failure mode is
   then whatever the org default happens to be.
8. **Hardcoding the generated routing address** in Apex, tests or runbooks.
9. **Error notifications going to the sender** because
   `isErrorRoutingEnabled` was never turned on — nobody internal learns
   that intake is broken.

## Official Sources Used

- Metadata API Developer Guide v62, `EmailServicesFunction` section — field
  table, required flags, `EmailServicesAttOptions` and
  `EmailServicesErrorAction` enum values, the nested `EmailServicesAddress`
  table (`runAsUser`, `localPart`, `developerName`), and the no-wildcard
  note (grounds `references/metadata-examples.md` and gotchas 6, 8, 13, 15,
  16) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Apex Developer Guide v62, "Email Services" and "Using the InboundEmail
  Object" — the `CreateTaskEmailExample` / `unsubscribe` samples declared
  `public with sharing`, the ~25 MB combined-size rejection, and "email
  service addresses that you create in your sandbox can't be copied to your
  production org" (grounds gotchas 1, 4, 12) —
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- Apex Developer Guide v62, "Email Limits / Inbound Email Limits" and the
  Apex governor-limit table footnote 4 — daily processing limit of user
  licences x 1,000 capped at 1,000,000 shared with On-Demand Email-to-Case,
  and the 50 MB email-services heap (grounds gotchas 10 and 11) — same PDF
  as above.
- Apex Reference Guide v62, `InboundEmail`, `InboundEmail.Header`,
  `InboundEmail.BinaryAttachment`, `InboundEmail.TextAttachment`,
  `InboundEmail.AuthenticationResult`, `InboundEmailResult` and
  `InboundEnvelope` classes — property signatures for `messageId`,
  `inReplyTo`, `references`, the `*IsTruncated` flags, `charset`, and the
  documented behaviour that a `false` `success` sends the `message` back to
  the sender (grounds gotchas 2, 3, 7, 14 and the handler in
  `metadata-examples.md`) —
  https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_Messaging_InboundEmail.htm
- Object Reference for the Salesforce Platform v62, `EmailServicesAddress`
  and `EmailServicesFunction` standard objects — the read-only
  `EmailDomainName` domain part, `RunAsUserId`, `FunctionId`, and the
  `AddressInactiveAction` picklist that has no Metadata API counterpart
  (grounds gotchas 5, 16 and the verification SOQL) —
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- Object Reference for the Salesforce Platform v62, `EmailMessage` standard
  object — `MessageIdentifier` (idLookup), `ThreadIdentifier` and
  `ClientThreadIdentifier`, which is what makes the header-based case
  lookup in `references/examples.md` § 2 possible — same PDF as above.
- Salesforce Developer Limits and Allocations Quick Reference — Apex
  Governor Limits table, footnote 4 "Email services heap size is 50 MB"
  (corroborates gotcha 11).
- Salesforce Well-Architected — Reliable / Secure —
  https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Sibling skill `skills/admin/email-to-case-configuration/SKILL.md` — the
  built-in alternative this skill routes away from for case creation.
- Sibling skill `skills/apex/apex-email-services/SKILL.md` — the Apex-side
  handler treatment; this skill owns the configuration side.
