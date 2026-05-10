# Gotchas — Tooling API Patterns

Non-obvious Salesforce platform behaviors that cause real production problems when building Tooling-API tooling.

## Gotcha 1: `ApexClass.Body` is silently empty when queried from the Data API

**What happens:** A query like `SELECT Id, Name, Body FROM ApexClass` against the Data endpoint (`/services/data/vXX.0/query/`) returns rows successfully, but the `Body` field is null or absent. There is no error — the query silently strips the source code.

**When it occurs:** Any time a tool intended to read Apex source uses the Data endpoint instead of the Tooling endpoint. Easy mistake when an existing data-layer client is reused for metadata queries.

**How to avoid:** Always hit `/services/data/vXX.0/tooling/query/...` for metadata sObjects (`ApexClass`, `ApexTrigger`, `ApexPage`, `ApexComponent`, `FlowDefinition`, `Flow`, `ValidationRule`, `EntityDefinition`, `FieldDefinition`). Maintain a lookup table in the client of which sObjects route to which endpoint, and assert at runtime that metadata-class fetches use the Tooling endpoint.

---

## Gotcha 2: A user can have only one active `TraceFlag` per `LogType` simultaneously

**What happens:** Inserting a second `TraceFlag` with the same `TracedEntityId` and `LogType` while the first is still active returns `DUPLICATE_VALUE: duplicate value found: <unknown> duplicates value on record with id: <existing trace flag>`. The second insert fails entirely.

**When it occurs:** Any tool that "always sets up a TraceFlag on this action" without first checking. Common in incident-capture scripts run multiple times, or in IDE save-with-logging features.

**How to avoid:** Before inserting, query existing TraceFlags: `SELECT Id, ExpirationDate FROM TraceFlag WHERE TracedEntityId = :userId AND LogType = 'USER_DEBUG' AND ExpirationDate > <now>`. Either reuse the existing flag (update its `ExpirationDate`) or delete it before inserting the new one. The same constraint applies to `LogType` values `DEVELOPER_LOG`, `CLASS_TRACING`, `USER_DEBUG`, etc. — each is independently single-active.

---

## Gotcha 3: `MetadataContainer` becomes sealed once a `ContainerAsyncRequest` is submitted

**What happens:** After inserting a `ContainerAsyncRequest` for a container, any further attempts to add `ApexClassMember` or `ApexTriggerMember` records to that container fail with `FIELD_INTEGRITY_EXCEPTION` or `MetadataContainerInvalidStateException`. The container is one-shot.

**When it occurs:** Editor flows that batch saves and then realize "one more class needs to go in this batch." Or test harnesses that submit a container, then on retry try to amend it instead of creating a fresh one.

**How to avoid:** Treat each `MetadataContainer` as immutable post-submission. If more components need to be added after submission, create a new `MetadataContainer`. Always delete completed containers (success or failure) — they don't auto-clean and accumulate.

---

## Gotcha 4: `ContainerAsyncRequest.DeployDetails` is a JSON-encoded string, not a structured field

**What happens:** On `State = Failed`, the `DeployDetails` field appears in the row as a single string. Treating it as a structured object yields nothing.

**When it occurs:** Every time a Tooling-API consumer first encounters a compile failure. The mistake is to access `row.DeployDetails.componentFailures` directly.

**How to avoid:** `JSON.parse(row.DeployDetails)` produces an object with `componentFailures: [...]` (and `componentSuccesses` and `runTestResult` if tests ran). Each failure has `lineNumber`, `columnNumber`, `problem`, `problemType`, `fileName`. The shape mirrors Metadata API deploy results, so existing deploy-result parsers can be reused after the JSON.parse step.

---

## Gotcha 5: `ApexCodeCoverageAggregate` rows reflect only the most recent test run

**What happens:** A coverage dashboard that queries `ApexCodeCoverageAggregate` once per day and writes "today's coverage" sees that yesterday's coverage row has been overwritten by today's. The skill assumes the row is historical; it is not.

**When it occurs:** Designing trending dashboards on top of `ApexCodeCoverageAggregate` directly. Also bites teams that re-run tests for one class — that row is overwritten with coverage from just that test run, dropping all other test attribution.

**How to avoid:** Snapshot externally with a timestamp every time a test run completes. The dashboard reads from the snapshot store, not directly from `ApexCodeCoverageAggregate`. For per-test attribution that's robust to single-class re-runs, query `ApexCodeCoverage` joined to `ApexTestQueueItem` immediately after each `runTestsAsynchronous` completes; persist before the next test run starts.

---

## Gotcha 6: `TraceFlag.ExpirationDate` cannot be more than ~24 hours in the future

**What happens:** Inserting a `TraceFlag` with `ExpirationDate` set 48 hours ahead returns `INVALID_FIELD_FOR_INSERT_UPDATE: ExpirationDate cannot be more than 24 hours in the future`. The platform-imposed cap surprises tools that want long-running capture.

**When it occurs:** "Production capture for the next week" use cases. Also bites support tools that copy an `ExpirationDate` from a related ticket where the ticket SLA is multi-day.

**How to avoid:** Cap `ExpirationDate` at `now + 24h` (or a safer 23h to allow clock skew). For longer-running capture, implement a refresh job that updates the `ExpirationDate` (or deletes and re-inserts) every 12 hours. Document the refresh dependency in the tool's runbook — if the refresh job dies, capture stops silently.

---

## Gotcha 7: Tooling API counts toward the same 24h API limit as the Data API

**What happens:** A coverage harvester polling every 5 minutes plus a log archiver fetching ApexLog bodies plus regular API integration traffic all share the org's daily limit. When the limit is hit, every API call (Tooling or Data) returns `REQUEST_LIMIT_EXCEEDED` until the rolling 24h window advances.

**When it occurs:** Multi-tool environments where Tooling-API tooling was added without budget planning, or when ApexLog body fetches (large payloads, expensive cost) were assumed to be "free" because the row query was small.

**How to avoid:** Read the `Sforce-Limit-Info` response header (`api-usage=12345/100000`) and instrument tooling with a budget. Cache aggressively (`EntityDefinition`, `FieldDefinition`, `ApexCodeCoverageAggregate` change rarely; use `LastModifiedDate` filters). Stagger non-time-critical tools to run during low-API-usage windows. For high-volume log capture, archive bodies to external storage and let the body-fetch budget cap how far the archiver falls behind.

---

## Gotcha 8: `ApexExecutionOverlayAction` has a per-user cap (~25 active)

**What happens:** Inserting a 26th active overlay for the same user returns a limit error. The cap is per-user, so debugging multiple sessions for the same dev exhausts it quickly.

**When it occurs:** Long debugging sessions where prior overlays weren't cleaned up. Also when shared service-account users run heap-dump tooling — every captured overlay counts.

**How to avoid:** Before inserting, query and clean up the user's existing overlays: `SELECT Id FROM ApexExecutionOverlayAction WHERE ScopeId = :userId AND ExpirationDate < :now`. After consuming `ApexExecutionOverlayResult`, delete the parent `ApexExecutionOverlayAction`. For shared service accounts, scope overlays by a synthetic key (e.g., a custom `Description` field convention) so concurrent debug sessions don't trample each other.

---

## Gotcha 9: Tooling SOQL relationship traversal is more restrictive than Data SOQL

**What happens:** A query like `SELECT Id, ApexClass.Name FROM ApexCodeCoverage` may fail with `MALFORMED_QUERY: Relationship 'ApexClass' is not supported` even though the Tooling endpoint exposes both objects.

**When it occurs:** Reusing a relationship-rich Data SOQL pattern against Tooling sObjects without testing. Also when traversing through polymorphic Tooling relationships (`ApexClassOrTrigger`).

**How to avoid:** Test each relationship traversal in Workbench's Tooling-mode Query before embedding. Where traversal is unsupported, query the parent Id and join client-side. The polymorphic `ApexClassOrTrigger` relationship is exposed via `ApexClassOrTrigger.Name` (works), `ApexClassOrTrigger.Type` (works) — the underlying `ApexClass` vs `ApexTrigger` distinction is in the `Type` field.

---

## Gotcha 10: Anonymous Apex via Tooling REST runs in the principal's user context

**What happens:** Anonymous Apex executed through `executeAnonymous` runs **as the calling user**, with that user's profile, permission sets, sharing, and FLS. Code that worked in Dev Console because the dev was a sysadmin fails when invoked from an integration user with restricted permissions.

**When it occurs:** Operational tools that run anonymous Apex from a service account. The script "works on my machine" (sysadmin in Dev Console) but fails in production (integration user without Modify All Data).

**How to avoid:** Run the integration user's profile/permset through the script's required permission check before deploying the tool. For tools that genuinely need elevated context, use a System Mode helper class (compiled, not anonymous) annotated `without sharing` and invoked from the anonymous body. Document the required permission set in the tool's setup runbook.
