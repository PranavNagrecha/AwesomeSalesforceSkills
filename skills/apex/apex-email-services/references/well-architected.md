# Well-Architected Notes — Apex Email Services

## Relevant Pillars

- **Security** — Email Services run in system context with no sharing enforcement. Every handler is a potential privilege escalation vector if sender identity is not validated and `Accept Email From` is not restricted. Audit logging of inbound mail activity is a production requirement, not an optional enhancement.
- **Reliability** — The handler's `success` return value and the Email Service Error Action together determine whether failed messages are retried, bounced, or silently lost. Getting this configuration wrong results in data loss or flooding sender inboxes with bounces. Null-guard patterns for body fields and attachment lists are reliability patterns, not defensive style.
- **Performance** — Synchronous handler execution runs inside a single Apex transaction's governor limits. Large attachment processing belongs in a `Queueable` to isolate heap and CPU consumption from the acceptance transaction. Handlers that do too much in-line degrade reliability and hit limits under load.
- **Scalability** — The default limit of 1,000 emails processed per day per Email Service address (varies by org edition) is a hard ceiling. High-volume inbound scenarios must be architected with this in mind: consider batching strategies, middleware pre-filtering, or alternative integration channels (REST API push) before committing to Email Services for large-scale automation.
- **Operational Excellence** — Email Service addresses must be explicitly activated and their configuration is environment-specific (sandbox vs production have separate addresses). Deployment runbooks must include post-deployment activation steps. Monitoring for silent discard behavior requires either an audit log record written by the handler or an alert on the daily limit metric.

## Architectural Tradeoffs

**Sync processing vs. Queueable delegation:** Processing everything in `handleInboundEmail` is simpler and results are visible immediately, but it couples reliability to governor limits. Delegating to a `Queueable` decouples acceptance from processing — the email is accepted immediately, work happens asynchronously — at the cost of eventual consistency (the record does not exist until the Queueable runs) and harder debugging.

**Single handler vs. routing by address:** Using one Apex class for multiple Email Service addresses (differentiated by `envelope.toAddress`) consolidates code but makes the handler harder to test in isolation and increases the blast radius of a bug. Separate handler classes per logical routing path are easier to test, deploy, and decommission individually.

**Restrictive vs. open sender filtering:** Setting `Accept Email From` to a specific domain reduces spoofing risk dramatically but requires coordination with senders and makes the integration brittle to sender domain changes. Open acceptance (blank field) simplifies onboarding but requires the handler itself to validate sender identity programmatically.

## Anti-Patterns

1. **Performing all attachment processing synchronously** — Processing large binary attachments inline inside `handleInboundEmail` is the most common production failure mode. Attachment Blobs up to 25 MB are passed directly to the handler; in-line decoding or parsing exhausts heap and causes `LimitException`, which fails the email acceptance and triggers the Error Action (often a bounce storm). Correct approach: persist the Blob to ContentVersion immediately, enqueue a Queueable for all subsequent processing.

2. **Assuming sender identity from `fromAddress` without validation** — `fromAddress` on `InboundEmail` reflects the email header `From:`, which is trivially spoofable. Handlers that grant elevated DML access or expose sensitive query results based solely on `fromAddress` are vulnerable to spoofed inbound email. Correct approach: validate `fromAddress` against a known allowlist stored in Custom Metadata or a Custom Setting, and configure `Accept Email From` in the Email Service to add a transport-level filter.

3. **Leaving the Email Service address inactive after deployment** — Deploying a handler without activating the Email Service address is a silent failure. All inbound mail is discarded. Because there is no error surface, debugging typically takes 30–60 minutes of investigation. Correct approach: include `EmailServicesFunction` metadata with `isActive: true` in every deployment package, and add an activation verification step to the post-deployment runbook.

## Official Sources Used

- Apex Developer Guide: Email Service — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_email_inbound_overview.htm
- Apex Developer Guide: InboundEmail Class — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_email_inbound_inbemail.htm
- Apex Developer Guide: InboundEmailHandler Interface — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_email_inbound_handler.htm
- Apex Reference Guide — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_ref_guide.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
