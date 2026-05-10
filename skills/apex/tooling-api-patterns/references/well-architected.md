# Well-Architected Notes — Tooling API Patterns

## Relevant Pillars

- **Operational Excellence** — Tooling that talks to the Tooling API is part of the org's operational fabric: editor save flows, coverage dashboards, log capture, schema crawlers. Each tool's reliability, observability, and cleanup posture directly affect engineering velocity. A tool that leaves orphan TraceFlags or MetadataContainers degrades the org for everyone using it.
- **Reliability** — Async workflows (`ContainerAsyncRequest`, `runTestsAsynchronous`, `ApexExecutionOverlayAction`) need bounded polling, retry budgets, and explicit failure paths. Tools that poll forever, or that swallow `Failed`/`Aborted` states, cause silent corruption (a developer thinks their save succeeded; the org has the old code).
- **Security** — Tooling API access requires elevated permissions (Modify Metadata, Author Apex, View All Data for cross-user log reads). The principal's identity matters: anonymous Apex via Tooling runs in the caller's context, not as a system superuser. Mis-scoped service accounts are a real privilege-escalation surface.

## Architectural Tradeoffs

**Tooling API vs Metadata API for code edits.** Tooling API's `MetadataContainer` workflow is dramatically faster for single-component edits (sub-second versus 4–8 seconds for an equivalent zip deploy) but has no batch-zip primitive. The crossover point is roughly *3 components*: below that, Tooling wins on latency; above that, Metadata API wins on simplicity (one zip, one deploy, one result).

**Tooling REST vs SOAP.** REST is simpler, more idiomatic for modern tooling, and supports JSON. SOAP is required only for the few legacy WSDL-only operations and for shops that already standardized on SOAP for Salesforce integration. Mixing both in one tool multiplies the auth-and-error-handling surface; pick one.

**Polling cadence vs. API-limit budget.** Tight polling (every 250 ms) gives sub-second feedback for editor saves; loose polling (every 5 s) preserves API budget for batch tools. The right cadence depends on whether the tool is foreground-interactive or background-scheduled.

**Cache freshness vs. correctness for schema crawlers.** Schema sObjects (`EntityDefinition`, `FieldDefinition`) change rarely. Caching for hours saves substantial API calls, at the cost of stale views immediately after a metadata deploy. Cache invalidation should hook into the deploy event (post-deploy hook or webhook), not run on a fixed TTL.

**Per-user TraceFlag uniqueness vs. concurrent capture.** Only one active TraceFlag per (user, LogType) means concurrent debug sessions for the same user step on each other. The architectural fix is per-tool log routing (each tool captures different `LogType`s) or an external coordinator that owns the TraceFlag for a user.

## Anti-Patterns

1. **Treating Tooling API as a Data API replacement.** Some teams discover Tooling can query `User`, `Profile`, `PermissionSet` and route *all* queries through the Tooling endpoint "for consistency." This burns API budget on extra metadata fields the tool doesn't need and routes business-data queries through a slower endpoint. Use Tooling for metadata sObjects only.
2. **Polling without a max-wait ceiling.** `ContainerAsyncRequest` and `runTestsAsynchronous` are usually fast, but failure modes exist where a job hangs in `Queued` indefinitely. Tools that poll forever are silent reliability hazards. Always cap (e.g., 60 seconds for compile, 60 minutes for full-suite tests) and surface the timeout as an explicit failure to the caller.
3. **Skipping cleanup of scratch sObjects.** Orphan MetadataContainers, TraceFlags, and ApexExecutionOverlayActions accumulate in active orgs. A coverage harvester running nightly for a year leaves 365 dead containers; a debug-on-save IDE leaves thousands of stale TraceFlags. Cleanup must run on success, on caught failure, *and* on uncaught crash (use a finalizer or supervisor pattern).
4. **Using anonymous Apex as a privilege-escalation hack.** "It runs anonymously, so it has full access" is wrong — anonymous Apex via Tooling REST runs in the caller's context. Tools that depend on elevated access should use a compiled `without sharing` helper class invoked from anonymous Apex, with explicit permission-set requirements documented for the calling principal.
5. **Hard-coding API version.** A tool authored against `v50.0` continues to work as new releases ship, but loses access to new sObjects, fields, and behavior. Pin the version explicitly *and* maintain a per-release upgrade ritual; never let "default API version" implicitly drift.

## Official Sources Used

- Tooling API Developer Guide (overview, sObject reference) — https://developer.salesforce.com/docs/atlas.en-us.api_tooling.meta/api_tooling/intro_api_tooling.htm
- Tooling API — Compile Apex code (`MetadataContainer` flow) — https://developer.salesforce.com/docs/atlas.en-us.api_tooling.meta/api_tooling/sforce_api_objects_metadatacontainer.htm
- Tooling API — `ContainerAsyncRequest` reference — https://developer.salesforce.com/docs/atlas.en-us.api_tooling.meta/api_tooling/sforce_api_objects_containerasyncrequest.htm
- Tooling API — `ApexClassMember` reference — https://developer.salesforce.com/docs/atlas.en-us.api_tooling.meta/api_tooling/sforce_api_objects_apexclassmember.htm
- Tooling API — `TraceFlag` and `DebugLevel` references — https://developer.salesforce.com/docs/atlas.en-us.api_tooling.meta/api_tooling/sforce_api_objects_traceflag.htm
- Tooling API — `ApexLog` reference — https://developer.salesforce.com/docs/atlas.en-us.api_tooling.meta/api_tooling/sforce_api_objects_apexlog.htm
- Tooling API — `ApexExecutionOverlayAction` and `ApexExecutionOverlayResult` references — https://developer.salesforce.com/docs/atlas.en-us.api_tooling.meta/api_tooling/sforce_api_objects_apexexecutionoverlayaction.htm
- Tooling API — `ApexCodeCoverageAggregate` reference — https://developer.salesforce.com/docs/atlas.en-us.api_tooling.meta/api_tooling/sforce_api_objects_apexcodecoverageaggregate.htm
- Tooling API — `EntityDefinition` and `FieldDefinition` references — https://developer.salesforce.com/docs/atlas.en-us.api_tooling.meta/api_tooling/sforce_api_objects_entitydefinition.htm
- Apex Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm
- Salesforce Well-Architected — Operational Excellence — https://architect.salesforce.com/well-architected/adaptable/resilient
