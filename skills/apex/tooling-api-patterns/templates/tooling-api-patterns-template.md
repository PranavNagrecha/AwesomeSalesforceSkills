# Tooling API Patterns — Work Template

Use this template when building or auditing external tooling that talks to the Salesforce Tooling API.

## Scope

**Skill:** `tooling-api-patterns`

**Request summary:** (one line — what tool is being built/audited and why)

## Tool Category

Pick one (drives the rest of this template):

- [ ] IDE-style single-class compile-and-save (MetadataContainer flow)
- [ ] Code-coverage harvester (ApexCodeCoverageAggregate / ApexCodeCoverage)
- [ ] Time-bounded debug-log capture (TraceFlag + DebugLevel + ApexLog)
- [ ] Heap-dump / SOQL-overlay capture (ApexExecutionOverlayAction)
- [ ] Schema crawler (EntityDefinition / FieldDefinition)
- [ ] Anonymous-Apex runner (executeAnonymous)
- [ ] Other (describe): _________________

## Context Gathered

- **Auth model**: OAuth user / JWT bearer service account / sf CLI session reuse → ____
- **Principal permissions verified**: Modify Metadata? Author Apex? View All Data? → ____
- **API version pinned**: v____ (must be ≥ v55)
- **REST or SOAP**: ____ (REST default unless legacy WSDL constraint)
- **Daily API budget posture**: how does this tool's expected QPS compare to org's 24h limit? → ____
- **Cleanup strategy**: where do scratch sObjects (MetadataContainer / TraceFlag / Overlay) get deleted? → ____

## Endpoint Routing

For each sObject this tool queries, confirm Tooling vs Data:

| sObject | Endpoint chosen | Correct? |
|---|---|---|
| (e.g. ApexClass) | tooling | yes — metadata sObject |
|   |   |   |

(Refer to *Core Concepts → Tooling-only sObjects* table in SKILL.md when in doubt.)

## Async Polling Plan

For any async ticket (ContainerAsyncRequest, AsyncApexJob, ApexExecutionOverlayAction):

- Initial backoff: ____ ms
- Max backoff: ____ ms
- Hard timeout: ____ s
- Terminal states checked: Completed / Failed / Invalidated / Aborted
- Failure path: how is `DeployDetails` (or equivalent) parsed and surfaced?

## Cleanup Plan

- [ ] MetadataContainer deleted in `finally` block
- [ ] TraceFlag deleted (or expires within 24h cap) and orphan check runs at startup
- [ ] ApexExecutionOverlayAction deleted after result consumption
- [ ] Cleanup also runs on uncaught crash (supervisor / signal handler)

## Anti-Patterns Self-Check

Run through references/llm-anti-patterns.md and confirm none apply:

- [ ] Tooling-only sObjects always go through `/tooling/query/...`
- [ ] `DeployDetails` is parsed via `JSON.parse` / `json.loads` before structured access
- [ ] Polling has a deadline; no `while True:` without timeout
- [ ] TraceFlag insert is preceded by a duplicate query
- [ ] Scratch sObjects have explicit cleanup paths
- [ ] Anonymous Apex caller's permissions are documented in setup

## Validation

- [ ] `python3 scripts/check_tooling_api_patterns.py --source-root <tool-dir>` returns 0
- [ ] Manual end-to-end run in a sandbox with realistic auth principal
- [ ] API limit headers (`Sforce-Limit-Info`) instrumented and observed during a representative run
- [ ] README documents the required principal permissions

## Notes

(Record any deviations from the standard patterns and why.)
