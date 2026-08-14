# Well-Architected Notes — Salesforce Functions Replacement

## Relevant Pillars

- **Scalability** — Functions' defining property was that it ran *outside* the
  Apex transaction. Every replacement decision is really a decision about where
  the new boundary sits. A synchronous callout pulls the work back inside the
  transaction, where it competes for the 100-callout limit and the 120-second
  cumulative callout budget; an event-driven handoff keeps it outside. Choose the
  boundary first; the runtime (Heroku, container, Apex, Agentforce Action) is the
  second decision and the cheaper one to change.

- **Reliability** — Functions failed as a single unit. A distributed replacement
  fails partially: the callout succeeded but the callback never arrived, the
  worker crashed mid-job, the dyno restarted during a deploy. That is not a
  regression to be engineered away, it is the cost of the boundary — so the
  replacement needs an explicit job state (`queued` / `running` / `failed`), an
  idempotent retry, and a way to answer "did this record get processed?" without
  reading logs.

- **Security** — Functions ran with an org-scoped identity that came with the
  platform. External compute does not. Every replacement introduces an
  authentication surface that has to be designed: Named Credentials for the
  outbound leg, a scoped integration user with a minimum permission set for the
  inbound leg, and no long-lived secrets in dyno config vars that outlive the
  people who set them.

## Architectural Tradeoffs

**Synchronous callout vs asynchronous handoff.** Synchronous is simpler to reason
about, gives the caller a result inline, and caps the workload at roughly 20–30
seconds in practice — Heroku's router terminates at 30 s and Apex's whole
transaction has 120 s of callout budget to spend. Asynchronous costs you a job
table, a callback path, and a "what if the callback never comes" story, and it is
the only option above that ceiling. The wrong choice is picking synchronous
because the Function's signature was synchronous.

**Heroku vs bring-your-own container.** Heroku is the lower-friction path:
Salesforce-owned, Postgres and Redis add-ons a command away, no cluster to run.
A container platform you already operate is cheaper if you already operate it —
and strictly more work if this migration is the reason you would start. The
deciding question is not which platform is better but which on-call rota already
exists.

**Rewriting in Apex vs keeping the language.** Apex removes an entire platform
from the estate — no dynos, no deploy pipeline, no separate observability. It
costs you the library ecosystem and hands you the governor limits, and the
synchronous ones (10,000 ms CPU, 6 MB heap) are much tighter than the
asynchronous ones (60,000 ms, 12 MB). Rewrite when the Function used only
standard-library work and finished in a couple of seconds; do not rewrite to
avoid managing a service you will end up needing anyway.

**Agentforce Action vs external service, for AI-shaped work.** An Action inherits
the Einstein Trust Layer, org context, and the Agentforce lifecycle. It is the
right home for prompt-shaped logic and the wrong home for deterministic compute
that merely happened to call a model API.

## Anti-Patterns

1. **Lift-and-shift onto a synchronous web endpoint.** The workloads that
   justified Functions are the ones that exceed Heroku's non-configurable
   30-second router timeout. The dyno keeps working on the request after the
   client is gone, degrading every request routed to it afterwards.
2. **One callout per record.** Functions did not consume the caller's budget; a
   callout does. This passes every single-record test and fails on the first bulk
   operation.
3. **Big-bang cutover.** Functions had no partial-failure story, so teams migrate
   as if the replacement has none either. Move one workload, measure it against
   the Function's observed latency and cost, then move the next.
4. **Declaring the migration done from the repo.** The inventory lives at the
   invocation sites in the org, not in the Functions project directory.

## Official Sources Used

- Salesforce Functions Release Notes — https://developer.salesforce.com/docs/platform/functions/guide/release-notes-intro.html — confirms the retirement notice verbatim: "Salesforce Functions is retiring on January 31, 2025. To keep the functionality of the functions deployed to your org, migrate them to a different product before the end-of-life date." (verified 2026-08-14)
- Apex Developer Guide — Execution Governors and Limits — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm — confirms 10,000 ms synchronous / 60,000 ms asynchronous maximum CPU time, 6 MB / 12 MB heap, 100 callouts per transaction, and 120 seconds maximum cumulative callout timeout (verified 2026-08-14)
- Apex Developer Guide — Callout Timeouts — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callouts_timeouts.htm — confirms "The default timeout is 10 seconds... the minimum is 1 millisecond and the maximum is 120,000 milliseconds" and that the 120-second cumulative limit "is additive across all callouts invoked by the Apex transaction" (verified 2026-08-14)
- Object Reference — FunctionInvocationRequest — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_functioninvocationrequest.htm — confirms the object exists from API 51.0 and records Function invocation information, which is what makes it usable as a discovery signal (verified 2026-08-14)
- Heroku Dev Center — Request Timeout — https://devcenter.heroku.com/articles/request-timeout — confirms the 30-second router timeout, the `H12` error code, that "The timeout value is not configurable", that "your application will not know that the request it is processing has reached a time-out, and your application will continue to work on the request", and — in the separate "Timeout behavior" section — that "Subsequent requests may then be routed to the same process which will be unable to respond (depending on the concurrency behavior of the application's language/framework) causing further degradation" (verified 2026-08-14)

**Not verified, deliberately omitted:** the specific Heroku plan / Private Space
requirements for PCI, HIPAA or equivalent regulated workloads. Those live behind
`help.salesforce.com` and contractual documentation that could not be read
directly, and they change by plan and region — confirm them with Salesforce
before moving regulated data, rather than taking a number from a skill file.
