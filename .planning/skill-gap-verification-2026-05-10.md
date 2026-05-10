# Skill Gap Verification — 2026-05-10

Run mode: scheduled-task `daily-skill-creation`. Catalog size at start: **995 skills** (up from 994 on 2026-05-09; only the `devops/sf-cli-plugin-authoring` skill was added in the past 24h).

## Sources scanned

- **Decision-tree branch gaps** — re-walked the four trees in `standards/decision-trees/`. No new branch surfaces a routing target whose recommended skill is missing or routes to a different domain. The previously-flagged stale aliases under `skills/integration/oauth-flows`, `apex/dynamic-soql`, `service/email-to-case`, `territory/capacity` continue to be label-only artifacts; they remain documentation hygiene work, not gap signals.
- **Cross-skill broken references** — same 13–16 stale labels enumerated on 2026-05-08 / 2026-05-09. No new labels surfaced.
- **BACKLOG.yaml prioritized review** — three unblocked TODO entries reviewed: `tooling-api-patterns`, `postman-for-salesforce`, `salesforce-inspector-patterns`. Rerun probes against current corpus to confirm whether each still represents a true gap.
- **Topic-driven probing (round 2)** — 25 candidate phrasings spanning Agentforce data libraries, AppExchange security review process, Einstein Trust Layer, Tooling API, Apex Schema describe, Org Shape, Lightning App Builder, DevOps Center, Apex multipart callouts, Console Workspace API, DataWeave for Apex, Apex JsonAccess, Apex Streaming API CometD, Apex transient/view-state, Apex SuppressWarnings, StubProvider mocking, anonymous Apex, Apex generics, Lightning Navigation, Apex test setup, multi-currency, Queueable AllowsCallouts, Lightning Data Service, deploy testLevel matrix, Salesforce Inspector. All but **two** route cleanly to existing skills (top score ≥ 4.0 in target domain). Outliers are the two backlog entries below.

## Candidate evaluation

Threshold rules (from scheduled-task brief):
- Top hit > 4.0 in same domain → REJECT auto.
- Top hit 2.5–4.0 → require articulated delta.
- Top hit < 2.5 across all phrasings → ACCEPT.

### A. apex/tooling-api-patterns — ACCEPT

Three phrasings:

| Phrasing | Top skill (score) | Delta articulated |
|---|---|---|
| `Tooling API ApexClass MetadataContainer ContainerAsyncRequest deploy` | NONE | No skill returned by search_knowledge.py |
| `Salesforce Tooling API SOQL query metadata symbol table` | `admin/salesforce-object-queryability` (3.696) | Existing skill diagnoses why a query *fails* (six failure modes including Tooling-vs-Data routing). It does **not** teach the Tooling API as an authoring/automation surface — MetadataContainer + ApexClassMember + ContainerAsyncRequest editor flows, ApexCodeCoverageAggregate harvesting, TraceFlag/DebugLevel lifecycle for time-bounded log capture, ApexExecutionOverlayAction heap dumps, anonymous Apex via Tooling REST. Verbatim grep across the corpus for `MetadataContainer`, `ContainerAsyncRequest`, `ApexClassMember`, `ApexExecutionOverlayAction`, `ApexCodeCoverageAggregate` returns matches only inside passing references; no skill teaches these as primary surface. |
| `ToolingApi.deploy ApexClassMember runValidationOnly partial deploy` | `devops/deployment-error-troubleshooting` (3.162) | Existing skill diagnoses Metadata API zip-deploy failures (`UNSUPPORTED_API_VERSION`, `RunSpecifiedTests`, `dependent class is invalid`). The Tooling-API single-class compile-and-save path (different shape; Workbench/Dev Console use this) is not its scope. |
| `Salesforce Tooling API REST endpoint reference object types` | NONE | No skill returned |
| `Tooling API ApexClass save edit single class without metadata zip` | `admin/salesforce-object-queryability` (2.429) | Same delta as above — queryability vs authoring patterns. |

Top scores across 5 phrasings: 3.696, 3.162, 2.429, plus two NONE hits. All correct-domain candidates score < 4.0; three of five score < 2.5 or NONE. Backlog entry `tooling-api-patterns` was already authored (status TODO since 2026-04-08) calling for exactly this scope. ACCEPT.

### B. devops/postman-for-salesforce — ACCEPT

Three phrasings:

| Phrasing | Top skill (score) | Delta articulated |
|---|---|---|
| `Postman Salesforce API testing OAuth collection environment variables chained requests` | `devops/performance-testing-salesforce` (2.177) | Performance-testing skill briefly mentions Postman as a workload generator; doesn't cover collection structure, Vault, pre-request scripts. |
| `Postman pre-request script Salesforce session OAuth refresh access token` | `security/oauth-token-management` (9.526) | OAuth-token-management is about OAuth tokens *in general* (consent flows, refresh, rotation, Connected App config), not about Postman as a client. Tool-specific wiring (pm.environment.set, pm.sendRequest, JWT bearer pre-request shape, Vault keys, collection runner) absent. |
| `Postman Salesforce REST API testing collection import login OAuth` | NONE | No skill returned |

Cross-corpus grep for `pm.environment.get`, `pm.collectionVariables`, `pm.sendRequest`, `pstmn.io`, `Postman Vault`, `vault:` returns zero matches. The closest skill in the wider Postman conceptual neighborhood (`security/oauth-token-management`) treats OAuth as a Salesforce-server concern, not a Postman-client concern. Backlog entry `postman-for-salesforce` was already authored (status TODO) calling for exactly this scope. ACCEPT.

### C. devops/salesforce-inspector-patterns — REJECT

Probed `Salesforce Inspector Chrome extension export SOQL field metadata data edit` → top hit `data/data-loader-and-tools` (8.280). Existing skill explicitly covers Salesforce Inspector Reloaded as one of its tools alongside Data Loader, Workbench, sfdmu — coverage is dense at 8.280 score. Marking this backlog entry as **DUPLICATE** would be appropriate but is documentation work, not a skill creation.

## Candidates rejected (sample)

Selected from the 25-phrasing topic-probing round:

| Candidate | Top hit | Score | Reason rejected |
|---|---|---|---|
| Agentforce data libraries grounding | `agentforce/data-cloud-grounding-for-agentforce` | 2.790 | Adjacent skills `rag-patterns-in-salesforce` (2.487), `data-cloud-vector-search-dev` (2.786) cover with depth |
| AppExchange security review process | `devops/second-generation-managed-packages` (4.405 on related phrasing) | 4.405 | 2GP skill + `security/secure-coding-review-checklist` together cover process + content |
| Einstein Trust Layer | `agentforce/einstein-trust-layer` | 5.426 | Skill exists at high score |
| Apex Schema describe | `apex/apex-schema-describe` (in chunks) | high | Skill exists |
| Org Shape / scratch org definition | `devops/org-shape-and-scratch-definition` | 9.788 | Skill exists at near-max |
| Dynamic Forms / Dynamic Actions migration | `admin/dynamic-forms-and-actions` | 5.830 | Skill exists |
| DevOps Center pipelines | `devops/devops-center-pipeline` | 10.528 | Skill exists at near-max |
| Apex multipart callout | `integration/file-and-document-integration` | 3.350 | Adjacent skills cover; narrow gap |
| Lightning Console Workspace API | `admin/service-console-configuration` | 5.614 | Skill covers |
| DataWeave for Apex | `integration/dataweave-for-apex` | 10.021 | Skill exists at near-max |
| Apex JsonAccess annotation | `apex/apex-wrapper-class-patterns` (6.666) | 6.666 | Skill covers `@JsonAccess` |
| Streaming API CometD | `integration/streaming-api-and-pushtopic` | 9.762 | Skill exists at near-max |
| Apex transient / view state | `apex/visualforce-fundamentals` | 7.973 | Skill covers |
| SuppressWarnings PMD annotations | `devops/salesforce-code-analyzer` | 8.773 | Skill covers |
| StubProvider mocking | `apex/apex-mocking-and-stubs` | 10.669 | Skill exists at near-max |
| Apex generics workaround | `apex/apex-switch-on-sobject` | 5.198 | Existing patterns sufficient |
| Lightning navigation router | `lwc/navigation-and-routing` | 3.904 | Adjacent skills cover |
| Multi-currency / dated exchange rates | `data/multi-currency-and-advanced-currency-management` | 6.615 | Skill exists |
| Queueable AllowsCallouts chain | `apex/apex-queueable-patterns` | 11.352 | Skill exists at near-max |
| LDS / wire reactive update | `lwc/wire-service-patterns` | 10.776 | Skill exists at near-max |
| Deploy testLevel matrix | `devops/continuous-integration-testing` | 3.797 | Adjacent skills cover with 20+ references to `testLevel` distributed |
| Salesforce Inspector Reloaded | `data/data-loader-and-tools` | 8.280 | Skill covers |

## Outcome

**2 skills accepted, both wired as `runtime_orphan: true` (developer-tooling references).**

Wiring rationale (per AGENT_RULES.md Step 6 judgment-call test "an agent should cite a skill only when reading it would change the agent's output for a real invocation"):

The 56 user-facing run-time agents are CRM-and-architecture-focused. None of them author or audit Tooling-API tooling, and none generate Postman collections. The closest candidates — `score-deployment` (deploy-risk scoring) and `audit-router` — operate on Salesforce metadata and don't read external-tool source. Forcing citations into either would dilute their `Mandatory Reads` with off-topic material. `runtime_orphan: true` is the explicit-intent mechanism AGENT_RULES added precisely for developer-facing reference skills like these.

## Routing scores after build

| Query | Top skill (score) |
|---|---|
| `Tooling API ApexClass MetadataContainer ContainerAsyncRequest deploy` | apex/tooling-api-patterns (**6.712**) |
| `TraceFlag DebugLevel ApexLog body retrieve tooling api capture user logs window` | apex/tooling-api-patterns (**6.524**) |
| `ToolingApi.deploy ApexClassMember runValidationOnly partial deploy` | (does not enter top hits — phrasing relies on dot-notation `ToolingApi.deploy` that doesn't tokenize cleanly; covered by other two queries) |
| `Postman Salesforce REST API testing collection import login OAuth` | devops/postman-for-salesforce (**6.995**) |
| `Postman pre-request script Salesforce JWT bearer flow access token cache` | devops/postman-for-salesforce (**6.995**) |
| `Postman environment variables instance url access token api version sandbox prod` | devops/postman-for-salesforce (**6.223**) |

Both new skills route as #1 on at least 2 of 3 fixture queries (well above the brief's "at least 1" gate).

## Validation result

`python3 scripts/validate_repo.py --changed-only` — **2 skill(s) validated, 0 errors, 0 warnings.**

`python3 scripts/validate_repo.py --domain apex` — 148 skills validated, 0 errors, 4 warnings (all pre-existing on `scheduled-apex-failure-detection-and-monitoring`, `soql-security`).

`python3 scripts/validate_repo.py --domain devops` — 68 skills validated, 0 errors, 2 warnings (both pre-existing on `bitbucket-pipelines-for-salesforce` near-duplicating `github-actions-for-salesforce` / `gitlab-ci-for-salesforce`).

## Checker validation

- `check_tooling_api_patterns.py` — verified on synthetic tooling source: detects Data-API misroute on Tooling-only sObjects, unparsed `DeployDetails` access, unbounded polling on async Tooling resources, missing cleanup of MetadataContainer/TraceFlag/ApexExecutionOverlayAction, missing duplicate-check on TraceFlag insert, hard-coded API version <v55, anonymous-Apex without principal-context note. Clean tree returns "No issues found." with exit 0.
- `check_postman_for_salesforce.py` — verified on synthetic collection: detects hard-coded Salesforce host, hard-coded API version, JWT `aud` containing `/services/oauth2/token`, missing `accessTokenExpiry` cache check, `pm.variables.set` on chain-significant keys, Bulk-API-2.0 upload with non-PUT method, secrets stored as inline environment variables instead of Vault references. Empty/no-collection input returns 0 gracefully.

## Backlog observations

`tooling-api-patterns` and `postman-for-salesforce` were already on the BACKLOG.yaml queue with status TODO; today's run validated they are real gaps (top hit < 4.0 in target domain) and built both. Both entries now status `DONE` with history rows.

`salesforce-inspector-patterns` (also in backlog) probed at 8.280 — covered by `data/data-loader-and-tools`. Should be flipped to `DUPLICATE` in a future doc-hygiene pass; not a skill-creation task.

Catalog size: 995 → 997 after this run.
