---
name: tooling-api-patterns
description: "Use when building external tooling, IDE-style automation, or scripts that talk to the Salesforce **Tooling API** — single-class compile-and-deploy via `MetadataContainer`/`ApexClassMember`/`ContainerAsyncRequest`, querying Tooling-only sObjects (`ApexClass`, `ApexCodeCoverage`, `FlowDefinition`, `EntityDefinition`/`FieldDefinition`), debug-log retrieval (`ApexLog`, `TraceFlag`, `DebugLevel`), heap-dump overlays (`ApexExecutionOverlayAction`, `ApexExecutionOverlayResult`), and anonymous Apex execution. Triggers: 'tooling api compile single apex class', 'MetadataContainer ContainerAsyncRequest', 'ApexCodeCoverageAggregate query', 'ApexLog retrieve via tooling api', 'TraceFlag debug level setup', 'EntityDefinition FieldDefinition queryable', 'tooling api vs metadata api', 'tooling api vs data api'. NOT for runtime Apex metadata operations (use `apex/apex-metadata-api` for the `Metadata.Operations` namespace), Metadata API zip-based deploys (use `devops/metadata-api-retrieve-deploy`), Data API SOQL fundamentals (use `apex/soql-fundamentals`), or general deployment-error diagnosis (use `devops/deployment-error-troubleshooting`)."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
  - Security
triggers:
  - "I want to compile and save a single Apex class via the Tooling API like Dev Console does"
  - "how do I query ApexCodeCoverage or ApexCodeCoverageAggregate from a script"
  - "what is the MetadataContainer ContainerAsyncRequest workflow"
  - "I need to retrieve ApexLog bodies after running anonymous Apex from a tool"
  - "how do I set a TraceFlag programmatically with the right DebugLevel"
  - "is FlowDefinition queryable from the Data API or only the Tooling API"
  - "EntityDefinition FieldDefinition tooling api custom field metadata"
  - "I want to capture a heap dump on a specific line via tooling api"
tags:
  - tooling-api
  - apex
  - apex-class-compile
  - code-coverage
  - debug-logs
  - heap-dump
  - schema-introspection
  - dev-tooling
  - metadata-container
inputs:
  - "tool category — IDE/editor save, code-coverage harvester, debug-log fetcher, schema crawler, heap-dump capture, or anonymous-Apex runner"
  - "auth mechanism — OAuth user token, JWT bearer flow service account, or session reuse from sf CLI"
  - "API version (the Tooling API endpoint is `/services/data/vXX.0/tooling/`); Tooling API tracks Salesforce releases"
  - "REST vs SOAP preference (REST is default; SOAP only for legacy clients)"
  - "rate-limit posture — Tooling API counts against the org's 24h API limit"
outputs:
  - "REST or SOAP request shape for the chosen workflow (compile, query, log retrieval, overlay)"
  - "polling pattern for async ContainerAsyncRequest state transitions"
  - "SOQL queries hitting Tooling-only sObjects with the correct endpoint"
  - "TraceFlag/DebugLevel lifecycle for time-bounded log capture"
  - "ApexExecutionOverlayAction setup + ApexExecutionOverlayResult retrieval"
  - "list of which sObjects are Tooling-only vs Data-API-only vs both"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-10
runtime_orphan: true
---

# Tooling API Patterns

Activate when a developer or platform team is **building external tooling against the Salesforce Tooling API** — an editor save flow, a code-coverage harvester for a coverage dashboard, a debug-log fetcher for an incident-response script, a schema-introspection crawler for a metadata diff tool, or a heap-dump capture utility. The skill produces concrete request shapes, async-polling patterns, and the routing rules between Tooling API, Data API, and Metadata API for the most common workflows.

This skill is not for runtime Apex code that creates metadata via the `Metadata.Operations` namespace (use `apex/apex-metadata-api`), zip-based deployments (`devops/metadata-api-retrieve-deploy`), or business SOQL against `Account`/`Contact` (`apex/soql-fundamentals`). It is also not for diagnosing why a deployment failed (`devops/deployment-error-troubleshooting`) — that skill covers the deploy outcome; this one covers the API surface a tool uses to *trigger* compiles, fetch coverage, or read logs.

---

## Before Starting

Gather this context before any code is written:

- **Why Tooling API and not Metadata API?** Metadata API is built around zip-based retrieve/deploy of large component sets. Tooling API exposes individual components as queryable/insertable sObjects, optimized for *one-class-at-a-time* edits, queries against Tooling-only sObjects, and developer tooling. If the task is "deploy 200 components from source control," that's Metadata API. If the task is "save and compile this single class like the Dev Console does," that's Tooling API.
- **Why Tooling API and not Data API?** Some objects (`ApexClass` body, `ApexTrigger`, `FlowDefinition`, `ValidationRule`, `EntityDefinition`, `FieldDefinition`, `ApexLog`, `ApexCodeCoverage`) are exposed *only* in Tooling. Hitting `/services/data/vXX.0/query/?q=SELECT+Id+FROM+ApexClass` against the Data API returns `INVALID_TYPE`; the same query against `/services/data/vXX.0/tooling/query/?q=...` works.
- **REST or SOAP?** Tooling API ships both. REST is the default for new tooling — JSON, simpler auth, no WSDL ceremony. SOAP is appropriate only when reusing legacy WSDL-based clients or when consuming the few SOAP-only methods (`runTests`, `executeAnonymous` is in both).
- **Auth model.** OAuth user-context tokens work for IDE-like tooling. Service-account JWT bearer flow is the right choice for unattended automation (CI scrapers, coverage harvesters, log archivers). The token's identity must have *Modify Metadata* + *Author Apex* (or specific equivalents) for compile workflows; *View All Data* is required to read other users' `ApexLog` bodies.
- **API limit posture.** Tooling API calls count against the org's 24h API limit. A coverage scraper that polls every 5 minutes will burn limits fast; design with caching, conditional polling, and `If-Modified-Since`/`LastModifiedDate` filters from day one.

---

## Core Concepts

### Tooling-only sObjects (and the routing question)

The most common gotcha in Tooling API work is sending a query to the wrong endpoint. The list below covers the sObjects that practitioners reach for most often.

| sObject | Endpoint | Purpose |
|---|---|---|
| `ApexClass` | Tooling | The class body, `Body`, `Status`, `IsValid`, `SymbolTable`. Data API exposes only an Id-stub view that lacks `Body`. |
| `ApexClassMember` | Tooling | The "in-progress edit" of an `ApexClass` inside a `MetadataContainer`. Used by editor save flows. |
| `ApexTrigger` / `ApexTriggerMember` | Tooling | Same pattern as `ApexClass`/`ApexClassMember`. |
| `ApexCodeCoverage` | Tooling | Per-test, per-class coverage rows captured after a test run. |
| `ApexCodeCoverageAggregate` | Tooling | Per-class coverage aggregated across all tests. The "75% coverage" gate reads this. |
| `ApexLog` | Tooling | Debug log header. Body is fetched via `GET /services/data/vXX.0/tooling/sobjects/ApexLog/<id>/Body`. |
| `TraceFlag` | Tooling | "Capture logs for this user/class for this window." |
| `DebugLevel` | Tooling | Reusable log-level config referenced by a `TraceFlag`. |
| `ApexExecutionOverlayAction` | Tooling | Set a heap dump or SOQL inspector on a specific line. |
| `ApexExecutionOverlayResult` | Tooling | The captured heap state after the overlay fires. |
| `EntityDefinition` | Tooling | Schema row per sObject (standard + custom). Data API equivalent is partial. |
| `FieldDefinition` | Tooling | Schema row per field. Includes `IsCalculated`, `IsHighScaleNumber`, `IsCompound`, etc. |
| `FlowDefinition` | Tooling | The flow definition (one per developer name); `Flow` (versions) is also Tooling. |
| `ValidationRule` | Tooling | Per-object validation rule rows. |
| `MetadataContainer` | Tooling | Wrapper sObject for save-as-a-batch workflows. |
| `ContainerAsyncRequest` | Tooling | Async compile-and-deploy ticket for a `MetadataContainer`. |
| `User`, `Profile`, `PermissionSet` | Both | These are queryable on Data and Tooling; Tooling adds metadata-shape fields. |

Rule of thumb: any object that represents *org configuration metadata* lives in Tooling; objects that represent *org data* live in Data; a few cross-cutting (User, Profile) live in both. If a query fails with `INVALID_TYPE` on the Data API, retry against Tooling before assuming the object doesn't exist.

### The MetadataContainer / ApexClassMember / ContainerAsyncRequest workflow

The single most important Tooling API workflow is the one editors use to save individual Apex classes. The sequence:

1. **Create a `MetadataContainer`** — a session-scoped scratch space.
   `POST /services/data/v59.0/tooling/sobjects/MetadataContainer/` body `{"Name": "ide-save-<timestamp>"}`. Response is the container Id.
2. **Add an `ApexClassMember` for each class being edited** — references the existing class Id and carries the new body.
   `POST /services/data/v59.0/tooling/sobjects/ApexClassMember/` body `{"MetadataContainerId": "...", "ContentEntityId": "<existing ApexClass Id>", "Body": "public class Foo { ... }"}`.
3. **Submit the container by inserting a `ContainerAsyncRequest`** — this triggers compile-and-save server-side.
   `POST /services/data/v59.0/tooling/sobjects/ContainerAsyncRequest/` body `{"MetadataContainerId": "...", "IsCheckOnly": false}`.
4. **Poll the `ContainerAsyncRequest` Id until `State` ∈ {`Completed`, `Failed`, `Invalidated`, `Aborted`}**.
   `GET /services/data/v59.0/tooling/sobjects/ContainerAsyncRequest/<id>` — typical state transitions: `Queued` → `InProgress` → `Completed`. Poll every 1s for the first 5s, then back off.
5. **On `Failed`, the `DeployDetails` field contains the per-component error JSON**. Surface line/column to the user so the editor can highlight.
6. **Delete the `MetadataContainer`** when done. Containers persist for ~24h but eat metadata space; clean up after success or hard failure.

`IsCheckOnly: true` performs a validation-only compile — used by lint-on-save tooling.

### TraceFlag / DebugLevel lifecycle

`ApexLog` records are produced only when an active `TraceFlag` matches the executing context (a user, an Apex class, an Apex trigger, etc.). Setting up time-bounded log capture from a script:

1. Look up an existing `DebugLevel` or insert a new one with the categories you want (`ApexCode=DEBUG`, `Db=INFO`, `Workflow=INFO`, etc.).
2. Insert a `TraceFlag`: `{"TracedEntityId": "<UserId>", "DebugLevelId": "<DebugLevelId>", "StartDate": "<now>", "ExpirationDate": "<now+30m>", "LogType": "USER_DEBUG"}`. The user-debug `LogType` captures both UI and API activity.
3. Trigger the workload (anonymous Apex, REST callout from the tool, or wait for the user to act).
4. Query `ApexLog` filtered by `LogUserId`, `StartTime > :traceStart`, ordered by `StartTime DESC LIMIT 50`.
5. For each `ApexLog` row, fetch the body: `GET /services/data/vXX.0/tooling/sobjects/ApexLog/<id>/Body` — returns plaintext, **not JSON**.
6. Delete the `TraceFlag` when done (or let it expire). Stale active TraceFlags accumulate quickly and slow down the org's logging pipeline.

Two important constraints:

- A user can have only one active `TraceFlag` of each `LogType` at a time. Inserting a second returns `DUPLICATE_VALUE`.
- `TraceFlag.ExpirationDate` is capped to ~24h in the future; longer windows are rejected.

### ApexExecutionOverlayAction (heap dumps)

A heap dump captures the value of every variable in scope at a specific line. Used by Apex Replay Debugger and by ad-hoc "what was the value of `acc` on line 42?" investigations.

1. Insert an `ApexExecutionOverlayAction`: `{"ScopeId": "<UserId>", "ExecutableEntityId": "<ApexClass Id>", "Line": 42, "Iteration": 1, "IsDumpingHeap": true, "ExpirationDate": "<now+24h>"}`.
2. Trigger the line (run a test, hit a UI flow). Each *iteration* the line executes records one heap snapshot up to the iteration count specified.
3. Query `ApexExecutionOverlayResult WHERE ApexExecutionOverlayActionId = :id ORDER BY ExpirationDate DESC LIMIT 5`.
4. The `HeapDumpJson` field contains the serialized heap (variables, values, types). Parse, render, or attach to the bug report.
5. Delete the overlay action — orphaned actions count against the per-user limit of 25.

`IsDumpingHeap: false` captures only the SOQL plan / governor counters at that line, much smaller payload, useful for hot-path performance work.

### Anonymous Apex via Tooling API

`GET /services/data/vXX.0/tooling/executeAnonymous/?anonymousBody=<URL-encoded Apex>` is the REST equivalent of Dev Console's *Execute Anonymous*. The response is JSON: `compiled`, `success`, `compileProblem`, `exceptionStackTrace`, `line`, `column`. To capture the executed code's debug log, set up a `TraceFlag` first; the response itself contains only the success/error envelope, not the log body.

For multi-line scripts (>2k chars), `POST` to the same endpoint with the body in the request body. URL-encoding constraints (`+`, `%2B`, etc.) make `GET` impractical for anything beyond one-liners.

### Code coverage harvesting

`ApexCodeCoverageAggregate` rows are populated only after a full test run; rows reflect the *most recent* aggregate per class, not historical. Pattern for a coverage dashboard:

1. Trigger `runTests` (Tooling SOAP) or `POST /services/data/vXX.0/tooling/runTestsAsynchronous/` with the class Ids and `coverage: true`.
2. Poll the `AsyncApexJob` row for completion.
3. Query `ApexCodeCoverageAggregate`: `SELECT ApexClassOrTrigger.Name, NumLinesCovered, NumLinesUncovered, Coverage FROM ApexCodeCoverageAggregate`.
4. For per-test detail (which test covered which lines), query `ApexCodeCoverage` joined to `ApexTestQueueItem` via `ApexTestRunResultId`.

Coverage is **not** persisted across deploys to non-production orgs the same way it is to production; in scratch/sandbox orgs, every deploy of a class invalidates its coverage rows.

### Flow tests in CI (Tooling API 65.0+, CLI)

Flow tests moved from Flow Builder-only to CLI- and Tooling-API-addressable in Winter '26. Use them when a CI gate must cover autolaunched flow logic, not only Apex.

- **CLI:** `sf flow run test --target-org ALIAS --code-coverage --tests FlowTesting.MyFlowTest` (requires **View All Data**). Discover tests with the Tooling **Retrieve Unit Tests** resource (`/tooling/runTestsAsynchronous/` family) — available in Tooling API **65.0+**; the `category=flow` filter arrives in **66.0+**. Flow tests live in the **`FlowTesting`** namespace (`FlowTesting.<FlowTestName>` or `FlowTesting.<Namespace>.<FlowTestName>` for packaged tests).
- **Unified runner (Beta):** `sf logic run test --test-category Flow` runs Apex and Flow tests in one invocation — see `devops/github-actions-for-salesforce` for CI wiring.

Do not assume Flow coverage appears in Apex-only harvesters — query Flow test results separately or use `--code-coverage` on the flow/ logic test commands.

## Common Patterns

### Pattern 1 — IDE-style "save single class" flow

**When to use:** Building an editor extension or web IDE that needs to save and compile one Apex class without a metadata zip.

**How it works:** `MetadataContainer` → `ApexClassMember` → `ContainerAsyncRequest` polled to terminal state, then `MetadataContainer` deleted. On `Failed`, surface `DeployDetails` JSON to the user with line/column highlighting.

**Why not the alternative:** A full `sf project deploy start` for one class incurs zip packaging, source-tracking comparison, and a heavyweight deploy job; the Tooling-API path is sub-second for most classes.

### Pattern 2 — Code-coverage harvester for a dashboard

**When to use:** A nightly job that captures coverage from CI sandboxes and posts to an internal dashboard.

**How it works:** `runTestsAsynchronous` → poll `AsyncApexJob` → query `ApexCodeCoverageAggregate`. For per-test attribution, additionally query `ApexCodeCoverage`. Cache results by `LastModifiedDate` to avoid re-querying static rows.

**Why not the alternative:** `sf apex test run --code-coverage` works for one-shot use but doesn't give you the individual rows for trending; the underlying data the CLI prints is exactly what `ApexCodeCoverageAggregate` exposes.

### Pattern 3 — Time-bounded debug log capture for an incident

**When to use:** A diagnostic tool that says "capture the next 30 minutes of logs for user X, then archive."

**How it works:** Insert `DebugLevel` (or look up an existing one) → insert `TraceFlag` with `ExpirationDate = now + 30m` and `LogType = 'USER_DEBUG'` → wait for the window → query `ApexLog WHERE LogUserId = :u AND StartTime > :start` → for each row, fetch `/sobjects/ApexLog/<id>/Body` → archive → delete the `TraceFlag`.

**Why not the alternative:** Keeping a `TraceFlag` open indefinitely floods the log pipeline and risks hitting the org's 250 MB rolling log buffer; logs older than the buffer are silently dropped.

### Pattern 4 — Schema crawler over EntityDefinition / FieldDefinition

**When to use:** A metadata-diff tool that needs the field shape of every queryable sObject.

**How it works:** Query `EntityDefinition WHERE IsQueryable = true LIMIT 2000`. For each, query `FieldDefinition WHERE EntityDefinitionId = :id`. The `FieldDefinition` rows expose `DataType`, `IsCompound`, `IsCalculated`, `IsHighScaleNumber`, `ReferenceTo`, etc. — fields the Data API's describe response also exposes but in a more flexible queryable form.

**Why not the alternative:** `Schema.getGlobalDescribe()` from Apex is callable only from inside the org; for an external tool, the Tooling API queries are equivalent and cacheable.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Compile-and-save a single Apex class from a tool | Tooling REST: MetadataContainer + ApexClassMember + ContainerAsyncRequest | Single-class path is sub-second; full Metadata API zip-deploy is overkill |
| Deploy 50+ components from source control | Metadata API zip deploy via `sf project deploy start` | Tooling API has no batch zip primitive; per-component overhead dominates |
| Validate-only compile (lint-on-save) | Same Tooling API path with `IsCheckOnly: true` on the `ContainerAsyncRequest` | Saves the post-compile metadata-write step |
| Capture coverage for a dashboard | `runTestsAsynchronous` → `ApexCodeCoverageAggregate` query | The CLI's `--code-coverage` is reading these same rows; query directly for trending |
| Time-bounded debug log capture | `TraceFlag` + `DebugLevel` with bounded `ExpirationDate` | Prevents indefinite log flooding |
| Capture a heap dump for replay debugging | `ApexExecutionOverlayAction` + poll `ApexExecutionOverlayResult` | Same primitive Apex Replay Debugger uses |
| Run anonymous Apex from a tool | `executeAnonymous` REST endpoint, with `TraceFlag` if log capture needed | Direct equivalent of Dev Console behavior |
| Query metadata-shape sObjects (`ApexClass.Body`, `FlowDefinition`, `ValidationRule`) | Tooling endpoint, not Data | Data API returns `INVALID_TYPE` |
| Query business data (`Account`, `Contact`, custom records) | Data endpoint | Tooling does not expose data sObjects |
| Reading `ApexLog` body | `GET .../sobjects/ApexLog/<id>/Body` (returns plaintext) | The rest of the row comes from a normal SOQL query |
| Bulk schema crawl | `EntityDefinition` + `FieldDefinition` SOQL with caching by LastModifiedDate | More queryable than per-sObject describe REST calls |

---

## Recommended Workflow

Step-by-step for an agent or practitioner building Tooling-API tooling:

1. **Confirm the workflow truly needs Tooling API** (not Metadata API or Data API). Use the Decision Guidance table above.
2. **Choose the transport and pin the version.**
   - REST (default) or SOAP (legacy clients only). All examples in this skill assume REST.
   - Tooling API tracks Salesforce releases — for production tools, pin to a specific version (e.g., `v59.0`) and bump deliberately, not implicitly.
3. **Establish auth:** OAuth user token for IDE-like tools; JWT bearer service account for unattended automation. Verify the principal has the permissions required for the chosen workflow (Modify Metadata + Author Apex for compiles, View All Data for reading other users' logs).
4. **Implement the request shape per the chosen pattern** (single-class save, coverage harvest, log capture, schema crawl, heap dump, anonymous Apex). Code against the smallest necessary primitive — don't over-orchestrate.
   - For async workflows (`ContainerAsyncRequest`, `runTestsAsynchronous`, `ApexExecutionOverlayAction` capture), implement polling with bounded retries and exponential backoff. Always have a max-wait ceiling and a clear failure path.
5. **Clean up and cache.**
   - Always clean up scratch sObjects: delete `MetadataContainer`s, expire/delete `TraceFlag`s, delete `ApexExecutionOverlayAction`s when the capture is consumed. Orphan accumulation degrades org performance.
   - Cache aggressively. `EntityDefinition` and `FieldDefinition` rows change rarely; `ApexCodeCoverageAggregate` only changes after test runs. Use `LastModifiedDate` in the WHERE clause to fetch only deltas.
6. **Instrument for limits.**
   - Treat Tooling API limits the same as Data API limits — counts against the org's 24h API limit. Instrument your tool with limit telemetry from the response headers (`Sforce-Limit-Info`).
   - Handle rate-limit responses (`REQUEST_LIMIT_EXCEEDED`) with backoff plus user-facing messaging — Tooling API does not have its own retry-after header.

---

## Review Checklist

Run through these before merging Tooling-API tooling changes:

- [ ] The endpoint is `/services/data/vXX.0/tooling/...`, not `/services/data/vXX.0/...`
- [ ] API version is pinned, not implicit (no relying on the org's default)
- [ ] Async workflows have bounded polling with exponential backoff and a max-wait ceiling
- [ ] All scratch sObjects (`MetadataContainer`, `TraceFlag`, `ApexExecutionOverlayAction`) are cleaned up on success and on failure
- [ ] `ApexLog` body is fetched via `/sobjects/ApexLog/<id>/Body` (plaintext), not parsed as JSON
- [ ] Code-coverage queries use `ApexCodeCoverageAggregate` for per-class totals; `ApexCodeCoverage` for per-test attribution
- [ ] Auth principal has the minimum permissions required (Modify Metadata + Author Apex for compile workflows; View All Data for cross-user log reads)
- [ ] Rate-limit handling — `REQUEST_LIMIT_EXCEEDED` triggers backoff, not infinite retry
- [ ] Cache keys include `LastModifiedDate` to avoid redundant queries against schema sObjects
- [ ] No use of the Data API endpoint for Tooling-only sObjects (`ApexClass`, `FlowDefinition`, `ValidationRule`, etc.)

---

## Salesforce-Specific Gotchas

Non-obvious behaviors that bite real Tooling-API consumers:

1. **`ApexClass` queried from the Data API returns rows but **not** `Body`.** Older code "works" against the Data API because the Id is returned; the silent-truncation of `Body` is the bug. Always use the Tooling endpoint for `ApexClass`/`ApexTrigger` queries that need the source.
2. **A user can have only one active `TraceFlag` per `LogType` at a time.** Inserting a second returns `DUPLICATE_VALUE`. Tools that "set up logging on every save" must first query and delete (or update) the existing TraceFlag for that user/LogType.
3. **`TraceFlag.ExpirationDate` is capped to ~24h in the future.** Longer windows are rejected. Long-running log capture must re-insert the flag periodically.
4. **`MetadataContainer` rejects further `ApexClassMember` inserts after a `ContainerAsyncRequest` is submitted.** The container is sealed once submitted. To make additional edits, create a new container.
5. **`ContainerAsyncRequest.State = Failed` returns errors in `DeployDetails` as a JSON string, not as a structured field.** Parsing requires `JSON.parse(deployDetails)` and walking the resulting `componentFailures` array; the structure mirrors Metadata API deploy results.
6. **`ApexCodeCoverageAggregate` rows persist only the *latest* aggregate per class.** There is no historical row. Trending dashboards must snapshot the rows externally — querying the future doesn't get you the past.
7. **`ApexLog` body retrieval is rate-limited separately from the row query.** The `GET /sobjects/ApexLog/<id>/Body` call uses the same 24h API budget but returns large payloads (up to 20 MB per log); a script that fetches 10k log bodies will burn limits faster than the equivalent count of regular SOQL calls suggests.
8. **`EntityDefinition.IsQueryable = true` is not the same as "you can query this object."** Some `EntityDefinition` rows are queryable in name only — the underlying object requires permission set assignment, edition feature gates, or a license. Crawlers must handle `INSUFFICIENT_ACCESS_OR_READONLY` gracefully on the per-object query.
9. **Tooling SOQL has stricter relationship-traversal limits than Data SOQL.** Some parent-child traversals that work in Data SOQL fail in Tooling with `MALFORMED_QUERY`. Test relationship-heavy queries early.
10. **The Tooling API does not implement `composite` request batching the same way the Data API does.** Bulk-insert-25 works, but full composite-graph patterns from `integration/composite-api-patterns` may not apply uniformly. Validate the specific composite pattern against the Tooling endpoint before assuming parity.
11. **`ApexExecutionOverlayAction` has a per-user cap (~25 active).** Orphan overlays from old debugging sessions count against this limit; tools that set up overlays should always delete prior orphans by `ScopeId`.
12. **Anonymous Apex executed via Tooling REST runs in the principal's user context, not as a system-level operation.** Sharing rules and FLS apply. Code that worked in Dev Console because the dev was a sysadmin may fail when invoked as an integration user with restricted access.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Single-class save module | Function/class wrapping the MetadataContainer → ApexClassMember → ContainerAsyncRequest flow with bounded polling |
| Coverage harvester | Job invoking `runTestsAsynchronous` and querying `ApexCodeCoverageAggregate` and `ApexCodeCoverage`, with snapshot persistence |
| Log capture module | TraceFlag + DebugLevel lifecycle wrapper, with `ApexLog` body retrieval and cleanup |
| Heap-dump capture | `ApexExecutionOverlayAction` insert + `ApexExecutionOverlayResult` polling, with overlay cleanup |
| Schema crawler | `EntityDefinition` + `FieldDefinition` query loop with `LastModifiedDate` caching |
| Endpoint-routing reference | Per-sObject table of which endpoint (Tooling, Data, both) to use, customized to the codebase's needs |

---

## Related Skills

- apex/apex-metadata-api — for runtime-Apex metadata operations using the `Metadata.Operations` namespace (a different surface for a different scenario)
- devops/metadata-api-retrieve-deploy — for zip-based bulk deploys
- devops/deployment-error-troubleshooting — for diagnosing why a Metadata API deploy failed (after the deploy)
- apex/sf-cli-and-sfdx-essentials — many `sf` CLI commands wrap Tooling API calls; reading their `--json` output mirrors what tooling against Tooling API receives
- devops/salesforce-cli-automation — for consuming `sf` (which itself uses Tooling API) from CI scripts
- apex/apex-test-coverage — for the `@isTest` design side; this skill covers harvesting the resulting coverage rows
- admin/salesforce-object-queryability — for the broader "this query failed, why?" diagnostic flow that includes Tooling vs Data routing
