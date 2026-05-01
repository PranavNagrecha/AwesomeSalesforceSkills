# Well-Architected Notes — AWS Salesforce Integration Patterns

## Relevant Pillars

- **Security** — Auth model selection drives the security envelope.
  Authorization-Code OAuth (AppFlow default) keeps the access token in
  the AWS-managed connected app and never on the integration code path.
  JWT Bearer for server-to-server eliminates interactive consent but
  requires the right Refresh-Token Policy ("Valid until revoked"). Apex
  → Lambda callouts must use Named Credentials, never hard-coded secrets.
  Event Relay uses an IAM trust relationship with an external-id —
  treat the external-id rotation cadence the same as any third-party
  IAM credential.
- **Reliability** — Event Relay is the only path with built-in
  at-least-once delivery and a 72-hour replay window. AppFlow has run
  retry but no replay. Apex callouts have neither — the calling
  transaction must implement its own retry and idempotency. The
  recommendation in this skill leans on Event Relay for any flow where
  losing an event has business impact.
- **Operational Excellence** — Managed paths (AppFlow, Event Relay,
  Service Cloud Voice + Connect, Data Cloud S3 connector) reduce
  operational debt to "watch the dashboard". Custom Apex callout +
  Lambda equals "watch four places: Salesforce debug logs, Apex
  exception emails, CloudWatch Logs, Lambda error metrics". Pick managed
  unless a constraint forces you off it.

## Architectural Tradeoffs

- **AppFlow vs Event Relay (Salesforce → AWS).** AppFlow is the right
  choice when the contract is record-level snapshot-or-upsert at a
  scheduled cadence; Event Relay is right when the contract is
  event-level "react to this thing happening". The split is *what
  consumes the data downstream* — a warehouse wants AppFlow, a Lambda
  wants Event Relay.
- **AppFlow vs Apex callout (synchronous).** AppFlow cannot run inside
  a Salesforce transaction. If the design needs the integration's
  result before commit, Apex callout is the only path. The cost is
  governor budget and operational debt.
- **Data Cloud S3 connector vs AppFlow source-from-S3.** Both ingest
  S3 files; Data Cloud writes to DMOs (correct shape for analytics /
  identity-resolution at scale), AppFlow writes to Salesforce custom
  objects (correct shape only for transactional CRM data, capped at
  15 GB / run). For data-lake-to-CRM bridging, the destination shape
  decides.
- **High-Volume Platform Events vs standard PE for Event Relay.**
  Event Relay requires a high-volume Platform Event channel for
  durability; standard PE doesn't survive subscriber slowness. Cost
  trade-off but it's not optional.

## Anti-Patterns

1. **Apex callout when Event Relay would have worked** — reinventing
   at-least-once delivery, retry, replay, and back-pressure inside a
   custom subscriber. If the answer doesn't need to come back inside
   the transaction, this is the wrong shape. Use Event Relay.
2. **AppFlow with Bulk API + compound fields** — silent data loss.
   The flow reports success; the destination has no `BillingAddress`
   column. Force `Standard` API preference or remove compound fields
   from scope.
3. **Bring-your-own connected app with the default Refresh Token
   Policy** — flow works for one access-token lifetime then dies. Set
   policy to "Valid until revoked" before the connection authorizes.
4. **AppFlow upserting to the Salesforce Id field** — silent insert
   failures. Use an explicit external-id field.
5. **Configuring Event Relay and assuming bidirectional event flow** —
   it's one-way. The reverse direction needs EventBridge API
   Destinations and a Salesforce REST endpoint, configured separately.

## Official Sources Used

- Amazon AppFlow Salesforce connector — https://docs.aws.amazon.com/appflow/latest/userguide/salesforce.html
- Salesforce Event Relay — https://help.salesforce.com/s/articleView?id=sf.event_relay.htm
- Salesforce Pub/Sub API — https://developer.salesforce.com/docs/platform/pub-sub-api/overview
- AWS EventBridge — https://docs.aws.amazon.com/eventbridge/
- Salesforce Integration Patterns — https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- integration-pattern-selection — `standards/decision-trees/integration-pattern-selection.md`
- Sibling skill (Event Relay setup recipe) — `skills/integration/event-relay-configuration/SKILL.md`
