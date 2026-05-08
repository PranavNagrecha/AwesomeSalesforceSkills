# Skill Gap Verification — 2026-05-08

Run mode: scheduled-task `daily-skill-creation`. Catalog size at start: **981 skills** (up from 950 on 2026-05-05; ~31 skills shipped in the four days since the last verification run).

## Sources scanned

- **Decision-tree branch gaps** — every skill cited under `standards/decision-trees/*.md` resolves to an existing skill. The single broken label (`skills/integration/oauth-flows`) is a stale cross-reference for the existing `skills/integration/oauth-flows-and-connected-apps` and is the same doc-fix item flagged on 2026-05-05. Not a real gap.
- **Cross-skill broken references** — grepped `skills/**/SKILL.md` and `skills/**/references/*.md` for `skills/<domain>/<slug>` paths and tested existence. 13 broken paths surfaced; **all 13** were stale label references for existing skills under different names:
  - `skills/admin/order-of-execution` → exists as `apex/order-of-execution-deep-dive`
  - `skills/admin/approval-process-design` → covered by `admin/approval-processes` + `admin/approval-process-apex-patterns`
  - `skills/apex/apex-security-crud-fls` → covered by `apex/apex-security-patterns` + `apex/apex-stripinaccessible-and-fls-enforcement`
  - `skills/apex/apex-testing-patterns` → covered by `apex/apex-test-setup-patterns` + `apex/test-class-standards` + `apex/test-data-factory-patterns`
  - `skills/apex/apex-with-user-mode-soql` → covered by `apex/apex-dynamic-soql-binding-safety` + `apex/soql-security`
  - `skills/devops/sandbox-strategy-designer` → it's an agent, not a skill
  - `skills/devops/sfdx-cicd-pipeline` → covered by `devops/bitbucket-pipelines-for-salesforce` / `devops/gitlab-ci-for-salesforce` / `devops/devops-center-pipeline`
  - `skills/flow/flow-best-practices` / `skills/flow/flow-screen-flows` → exist as `flow/screen-flows`, `flow/flow-screen-input-validation-patterns`
  - `skills/flow/flow-screen-flow-accessibility` → exists as `flow/screen-flow-accessibility`
  - `skills/lwc/lwc-component-skeleton` → covered by `lwc/lwc-base-component-recipes` and `lwc/lifecycle-hooks`
  - `skills/lwc/lwc-flow-properties` → covered by `flow/flow-screen-lwc-components` (4.515 score) + `lwc/lwc-in-flow-screens`
  - `skills/security/oauth-flows-and-connected-apps` → exists at `integration/oauth-flows-and-connected-apps`
  
  No real gap surfaced. The 13 stale labels remain a doc-cleanup item, not skill gaps.
- **Topic-driven probing** — ran `search_knowledge.py` against ~80 candidate phrasings spanning admin, apex, lwc, flow, devops, security, integration, agentforce, omnistudio, and architect domains. Most landed on existing skills with score ≥ 4.0. Three candidate phrasings produced NONE coverage in same-domain depth:
  - **AsyncOperationEvent / async job failure platform-event** — closest `architect/org-limits-monitoring` (3.114) plus `apex/error-handling-framework` Example 3 already covers BatchApexErrorEvent + AsyncApexJob query mechanics. Delta too thin; rejected.
  - **OAuth device authorization grant** — `integration/oauth-flows-and-connected-apps` (3.617) names device flow explicitly in description and routes to it; sub-flow-specific depth not warranted as a standalone skill. Rejected.
  - **ISV License Management App (LMA) + Trialforce + Feature Parameters + AppExchange Checkout** — repeated NONE coverage across four phrasings (lead phrasing `ISV License Management App LMA license enforcement subscriber org feature parameter` returned only `knowledge/imports/pkg1-dev.md` chunks at 1.0/0.5/0.333/0.25, no skill chunks scored). Closest existing skills: `devops/managed-package-development` (covers package mechanics and PostInstall but **does not cover** LMA, license records, Trialforce templates/TSO/TMO, or Feature Parameters as cross-org configuration channels) and `devops/second-generation-managed-packages` (mentions the Subscriber Support Console in passing only). The two passing references in `architect/experience-cloud-licensing-model` and `devops/second-generation-managed-packages/references/gotchas.md` are one-line mentions, not coverage. **Verified gap.**

## Candidate evaluation

Threshold rules (from scheduled-task brief):
- Top hit > 4.0 in same domain → REJECT auto.
- Top hit 2.5–4.0 → require articulated delta.
- Top hit < 2.5 across both phrasings → ACCEPT.

### A. devops/isv-license-management-and-trialforce — ACCEPT

| Phrasing | Top skill (score) | Top chunks |
|---|---|---|
| `ISV License Management App LMA license enforcement subscriber org feature parameter` | NONE — no skill above threshold | only `knowledge/imports/pkg1-dev.md` chunks |
| `AppExchange listing trialforce template trialforce source organization signup request` | NONE — no skill above threshold | only `knowledge/imports/salesforce-packaging-guide.md` chunks |
| `feature parameter LMA-to-subscriber subscriber-to-LMO checkbox boolean managed package configuration` | NONE — no skill above threshold | only `knowledge/imports/pkg1-dev.md` chunks |
| `ISV partner business org partner program AppExchange checkout licensing model` | NONE — no skill above threshold | only `knowledge/imports/salesforce-packaging-guide.md` chunks |
| `managed package licensing trialforce template provisioning user subscription` | NONE — no skill above threshold | only `knowledge/imports/salesforce-packaging-guide.md` + `pkg1-dev.md` chunks |

NONE coverage on every phrasing. The two related skills (`devops/managed-package-development`, `devops/second-generation-managed-packages`) both focus on the *package itself* — version creation, dependencies, ancestor pinning, install URLs, PostInstall handlers. Neither covers the *license + provisioning surface*: License Management App (LMA) install, License object lifecycle, sfLma usage, Trialforce TSO (Trialforce Source Org) vs TMO (Trialforce Management Org) split, Trialforce Templates, SignupRequest API, AppExchange Checkout integration, Feature Parameters as the LMO ↔ subscriber configuration channel (`LmoToSubscriber`, `SubscriberToLmo` directions), or the License-aware feature gating pattern in subscriber Apex.

ACCEPT — verified gap with rich official-source backing in `knowledge/imports/pkg1-dev.md` (ISVforce Guide) and `knowledge/imports/salesforce-packaging-guide.md`.

## Candidates rejected

| Candidate | Top hit | Score | Reason rejected |
|---|---|---|---|
| AsyncOperationEvent / async job failure monitoring | `architect/org-limits-monitoring` + `apex/error-handling-framework` | 3.114 + Example 3 in error-handling-framework | BatchApexErrorEvent + AsyncApexJob coverage already exists; AsyncOperationEvent narrowly applies to CRMA Data Manager and a handful of internal async ops. Delta too thin; defer until concrete demand. |
| OAuth Device Authorization grant | `integration/oauth-flows-and-connected-apps` | 3.617 | Device flow is named in the existing skill's description and routed to in body. Sub-flow-specific deep-dive doesn't justify a separate skill. |
| LWC media-stream / getUserMedia recording | `architect/ai-ready-data-architecture` | 0.6 (chunk) | Niche browser-API surface; no signal that practitioners hit this. Defer until concrete demand. |
| screen flow display image / dynamic file upload | `flow/screen-flow-accessibility` + `flow/screen-flows` | various | The image-display + file-upload sub-questions are absorbed by the existing screen-flow accessibility and screen-flow base skills. Delta too thin. |
| salesforce-backup-and-restore (configure-mechanics) | `data/salesforce-backup-and-restore` | 4.163 | Skill already exists at high score (added since 2026-05-05). Not a gap. |
| AppExchange Security Review (standalone) | `devops/second-generation-managed-packages` template | 1.79 | The Security Review checklist is already represented in the 2GP template's AppExchange section; isolating it as a separate skill would fragment package-prep guidance. |
| Decision-tree label-mismatch repairs (13 stale paths) | various | n/a | All 13 are stale references to existing skills under different names — doc-fix items, not skill gaps. |

## Outcome

**1 skill accepted.** Building it as a high-quality, deeply-grounded reference rather than chasing the per-run cap of 3.

## Routing scores after build

| Skill | Query | Top skill (score) |
|---|---|---|
| devops/isv-license-management-and-trialforce | `ISV License Management App LMA register managed package subscriber org enforce expiration` | devops/isv-license-management-and-trialforce (**6.511**) |
| devops/isv-license-management-and-trialforce | `Trialforce Management Org TMO Trialforce Source Org TSO template signup AppExchange trial` | devops/isv-license-management-and-trialforce (**3.436**) |
| devops/isv-license-management-and-trialforce | `FeatureParameterBoolean LmoToSubscriber SubscriberToLmo managed package feature flag without release` | devops/isv-license-management-and-trialforce (**5.747**) |

The new skill ranks #1 on all three target queries, two with score ≥ 5 (well above the >2.5 fixture-required ranking).

## Agent wiring

2 agent-skill citations added across 2 agents (developer + strategic tier):

| Agent | Section | Skill | Why this agent benefits |
|---|---|---|---|
| `deployment-risk-scorer` | Mandatory Reads | devops/isv-license-management-and-trialforce | Flags risk on managed-package deployments that change LMA wiring, alter Feature Parameter direction, or attempt FP propagation testing on beta versions (which silently fails the LMA channel) |
| `release-train-planner` | Mandatory Reads | devops/isv-license-management-and-trialforce | ISV release-cycle items are distinct from in-org releases: LMA registration, Trialforce template re-snapshot/re-approval, and Feature Parameter rollout become first-class release-train deliverables for any cycle that ships a managed package |

`agents/_shared/SKILL_MAP.md` updated for `release-train-planner` (Wave-tracked agent). `deployment-risk-scorer` is developer-tier and tracked only in its own AGENT.md per AGENT_RULES Step 6.

## Validation result

`python3 scripts/validate_repo.py --changed-only` — **4 skills validated, 0 errors, 0 warnings.** Full-domain run (`--domain devops`) — **66 skills validated, 0 errors, 2 warnings** (both pre-existing, on `bitbucket-pipelines-for-salesforce` near-duplicating `github-actions-for-salesforce` and `gitlab-ci-for-salesforce`; not related to the new skill).

Checker script verified on synthetic metadata: detects suspicious license object names, missing FP `dataflowDirection` / `defaultValue`, one-arg `FeatureManagement.checkPackage*Value` calls, and synchronous-FP set/check pairs in the same class.

## Backlog observations

The catalog continues to saturate; quality bar is high enough that "0–1 skills shipped per run" is now the steady-state outcome on a 2-day cadence. The cross-skill broken-reference list (13 stale label paths) is a doc-cleanup wave that should be tackled separately from this gap-analysis loop — relabeling existing skills doesn't add knowledge, only tidies cross-references.
