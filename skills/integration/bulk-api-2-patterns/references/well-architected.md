# Well-Architected Notes — Bulk API 2.0 Patterns (Integration)

## Relevant Pillars

- **Reliability** — Bulk pipelines must encode explicit state transitions, durable checkpoints, and partial-failure recovery because job success is not equivalent to row success.
- **Scalability** — Daily and per-request limits mean integrations should stream uploads, backoff polling, and shard work across multiple sequenced jobs when volumes approach caps.
- **Operational Excellence** — Emit structured logs with Salesforce job IDs, states, durations, and record counters; retain result CSV artifacts for audits and replay analysis.
- **Security** — Store OAuth tokens and refresh flows outside CSV files; use least-privilege integration users; avoid embedding secrets in job JSON or multipart boundaries logged by proxies.

## Architectural Tradeoffs

- **Multipart vs staged uploads** — Multipart reduces round trips for small payloads but is less flexible for generated streams that exceed multipart size guidance; staged uploads add client complexity yet fit large files.
- **Aggressive parallelism vs sequencing** — Parallel jobs maximize throughput but break foreign-key dependencies; sequencing trades throughput for determinism—encode dependencies explicitly in middleware.
- **Immediate retry vs quarantine** — Rapid retries on `Failed` jobs can amplify lock contention; sometimes pausing and splitting objects produces higher eventual throughput.

## Anti-Patterns

1. **Single boolean “sync success” per job** — Loses critical nuance when `JobComplete` coexists with failed rows; replace with structured status plus file references.
2. **Polling without exponential backoff** — Can hammer REST limits and shared infrastructure; combine `InProgress` polling with sane sleep jitter.
3. **Skipping parent reconciliation** — Launching child jobs when parent jobs still have unresolved `failedResults` guarantees intermittent production failures.

## Official Sources Used

- [Bulk API 2.0 Developer Guide](https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/asynch_api_intro.htm) — ingest/query resources, job states, upload completion requirement, locator pagination
- [REST API Developer Guide](https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_what_is_rest_api.htm) — OAuth, HTTP verbs, and REST conventions used by Bulk 2.0 endpoints
- [Integration Patterns and Best Practices](https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html) — batch vs synchronous tradeoffs for large data exchange
- [Salesforce Well-Architected Overview](https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html) — trusted, easy, adaptable quality model for integration solutions

## Related Skills (cross-reference)

- `data/bulk-api-patterns` — Complements this skill with call-level Bulk API 2.0 mechanics, CSV format tables, and Bulk API v1 comparisons; use it when the task is primarily “how do I format this REST request?”
- `integration/real-time-vs-batch-integration` — Use when the open question is whether Bulk API 2.0 is the right mechanism versus Platform Events, CDC, or synchronous callouts.
- `data/bulk-api-and-large-data-loads` — Use for LDV-oriented sizing, monitoring bulk throughput, and strategic guidance when volumes approach org-wide limits.
- `integration/rest-api-patterns` — Use alongside this skill for shared OAuth session handling, Named Credential patterns, and general REST error taxonomy that bulk jobs inherit.
- `integration/error-handling-in-integrations` — Use when mapping Salesforce job and row errors into middleware retry policies and dead-letter queues.
- `integration/composite-api-patterns` — Use when comparing smaller transactional REST bundles versus true bulk jobs for sub-2k record updates.
