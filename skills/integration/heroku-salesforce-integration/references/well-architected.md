# Well-Architected Notes — Heroku ↔ Salesforce Integration

## Relevant Pillars

- **Reliability** — Heroku Connect is the only path with managed
  bidirectional sync, trigger-log replay, and retry. Plan-tier choice
  drives the recovery window: 7-day trigger log on demo, 31-day on
  Enterprise / Shield. AppLink, Platform Events, and Apex callouts each
  require their own retry / idempotency story; don't assume "Heroku
  has Connect" means everything is durable.
- **Security** — Two security touchpoints. (1) Integration user
  hygiene: dedicated per add-on, scoped permissions (`API Enabled` +
  `View All` + `Modify All` only on synced objects), documented
  rotation. (2) Canvas auth choice: Signed Request for embedded-only
  apps avoids a consent screen but requires the Heroku app to verify
  the signature before trusting the payload — failure to verify is the
  classic confused-deputy bug.
- **Operational Excellence** — Region co-location is the highest-yield
  operational lever. The next is the integration user provisioning
  checklist — most production-incident postmortems for Heroku Connect
  trace back to a missing `View All` or a shared user.

## Architectural Tradeoffs

- **Heroku Connect vs Pub/Sub API subscriber.** Connect mirrors data
  with eventual consistency; Pub/Sub is event-driven with at-least-once.
  Pick Connect when the Heroku side queries the data structurally
  (joins, aggregates); pick Pub/Sub when the Heroku side reacts to
  events without needing the full record state.
- **Heroku AppLink vs Apex `@InvocableMethod` callout class.** AppLink
  surfaces a Heroku API directly inside Flow / Agentforce; the Apex
  wrapper does the same thing with code. AppLink wins on
  maintenance-by-admins (new params don't need a code deploy); Apex
  wrapper wins when you need pre/post processing inside the org.
- **External Objects vs Connect mirror.** External Objects keep data in
  Postgres (no Salesforce data-storage cost) but every query is a round
  trip. Connect copies into Salesforce (storage cost, index cost) but
  queries hit local Salesforce indexes. Read-heavy with low latency →
  Connect. Read-occasional with low storage budget → External Objects.
- **Demo plan vs Enterprise.** Demo's 10K-row cap and 10-minute polling
  are POC-only. Enterprise's per-contract row count and configurable
  polling are the production tier. Skipping the upgrade is the most
  common cause of "Heroku Connect went silent" tickets.

## Anti-Patterns

1. **Demo plan in production.** 10K-row cap, 10-minute polling. Always
   plan to upgrade before launch.
2. **Shared integration user across multiple Heroku Connect add-ons.**
   Per-user concurrent-query and OAuth-token caps cause silent
   throttling. One integration user per add-on.
3. **Missing `View All` on the integration user.** Manifests as
   `OPERATION_TOO_LARGE` errors on large pulls; the error doesn't name
   the cause.
4. **Mixing Canvas Signed Request and OAuth Web Server Flow.** Pick
   one. Mixing produces confused-deputy auth.
5. **Region mismatch between Heroku Postgres, Connect add-on, and
   Salesforce instance.** Multiplies sync lag. Co-locate.

## Official Sources Used

- Heroku Connect — https://devcenter.heroku.com/articles/heroku-connect
- Integrating Heroku and Salesforce (overview of paths) — https://devcenter.heroku.com/articles/integrating-heroku-and-salesforce
- Salesforce Canvas Developer Guide — Canvas App Authentication — https://developer.salesforce.com/docs/atlas.en-us.platform_connect.meta/platform_connect/canvas_app_authentication.htm
- Salesforce Pub/Sub API Overview — https://developer.salesforce.com/docs/platform/pub-sub-api/overview
- Sibling skill (AWS path) — `skills/integration/aws-salesforce-patterns/SKILL.md`
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
