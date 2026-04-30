# Well-Architected Notes — FLS in Async Contexts

## Relevant Pillars

- **Security** — The entire skill exists in this pillar. The core risk is silent FLS bypass when the user identity an async job *runs as* differs from the user whose intent the job was meant to honor. Bypass shows up as restricted fields appearing in exports, callout payloads, log messages, and persisted records. Without explicit handling, the bypass is invisible during code review and during testing — `Test.startTest` typically runs the async work as the test user, so cross-user drift never manifests.
- **Reliability** — A job that occasionally writes data the running user shouldn't have access to is unreliable in the security-correctness sense. Worse, the failure mode is silent: the job appears to succeed and downstream systems accept the data. The originating-user assertion (Pattern 1) converts silent drift into a loud, observable failure that can be caught by on-call and tested deterministically.

## Architectural Tradeoffs

- **Originating-user capture vs. system-mode declaration:** Capturing and asserting the originating user's identity preserves user intent across async hops, but it also means the job fails (correctly) if the entry point is later refactored to a system-context source like Platform Events. The alternative — declaring the job runs in system mode and documenting that contract — is simpler but pushes responsibility upstream: callers must filter data themselves before enqueueing.
- **Pre-filter at publish vs. per-record FLS in subscriber:** Pattern 3 (filter at publish) is operationally simpler and more performant — no FLS evaluation in the subscriber's hot path. The tradeoff is rigidity: every consumer of the event sees the same filtered view. If two subscribers need different field projections, the publisher must publish two events (or stream the unfiltered records via a different channel and filter in each subscriber, which moves back toward per-record FLS).
- **Cross-user FLS helper vs. Apex permission delegation:** Pattern 2 (cross-user FLS helper) reads `FieldPermissions` directly, which is portable but fragile against future FLS-related platform features (Permission Set Group muting nuance, Restriction Rules, etc.). The alternative is to enqueue the Queueable in a transaction that's *already* running as the target user — e.g., have the integration user log in via OAuth and execute the job through the API. That's more infrastructure but uses the platform's built-in FLS evaluation correctly.

## Anti-Patterns

1. **"Queueable runs as the enqueuing user, so I'm safe"** — True today, false after the next refactor. Any change to the entry point (PE handler, scheduled wrapper, retry-from-system-job) silently switches the running user. Always assert.
2. **Using `WITH USER_MODE` in Scheduled or PE-triggered Apex** — Compiles, runs without error, evaluates against the wrong identity. Practitioners assume `WITH USER_MODE` is "respect FLS" universally. It is not — it's "respect FLS for `UserInfo.getUserId()`."
3. **Trusting `Test.startTest`/`Test.stopTest` to verify FLS** — Tests run async work synchronously under the test's `runAs` user. Cross-user drift does not manifest in tests. Either test the entry-point chain end-to-end (PE publish → subscriber assertion) or accept that the test catches the synchronous case only.

## Official Sources Used

- Apex Developer Guide — Asynchronous Apex — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_async.htm
- Apex Developer Guide — Enforcing Object and Field Permissions — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_perms_enforcing.htm
- Apex Reference Guide — Security.stripInaccessible — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_Security.htm
- SOQL `WITH USER_MODE` — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_with_usermode.htm
- Platform Events Developer Guide — Subscribe with Apex Triggers — https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_subscribe_apex.htm
- Salesforce Well-Architected — Trusted — https://architect.salesforce.com/well-architected/trusted/secure
