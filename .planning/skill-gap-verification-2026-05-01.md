# Skill Gap Verification — 2026-05-01

Run mode: scheduled-task `daily-skill-creation`. Catalog size at start: 925 skills.

## Sources scanned

- Decision-tree branches under `standards/decision-trees/*.md` — every referenced skill resolves to an existing `skills/<domain>/<slug>/SKILL.md`. No gap candidates from this source.
- Cross-skill broken references — grep across decision trees and SKILL.md/well-architected.md surfaced 7 dead paths (`apex/apex-security-crud-fls`, `apex/apex-testing-patterns`, `flow/flow-screen-flow-accessibility`, `flow/flow-screen-flows`, `integration/oauth-flows`, `lwc/lwc-component-skeleton`, `lwc/lwc-flow-properties`). For each I ran `search_knowledge.py` with the topic phrasing — every one resolves to a renamed skill that scores 4.0+ (e.g. `apex-stripinaccessible-and-fls-enforcement` for CRUD/FLS, `screen-flow-accessibility` for accessibility, `oauth-flows-and-connected-apps` for oauth, `lwc/aura-to-lwc-migration` + `lwc/message-channel-patterns` cluster). No genuine gaps; these are stale citation strings, out of scope for this run (would be a separate ref-fixup pass).
- Topic probes (10 queries against high-traffic Salesforce surfaces): `apex transaction finalizer queueable`, `salesforce hyperforce data residency`, `lwc light dom slots scoping`, `agentforce reasoning loop debugging`, `salesforce data cloud activation targets`, `scratch org snapshots branching`, `platform event high volume replay`, `salesforce shield event monitoring`, `lwc lightning record edit form layout`, `flow http callout action resilience`. All return existing skills with scores ≥2.5 except where noted below.
- Second-pass topic probes (10 more): `hyperforce data residency compliance EU`, `salesforce hyperforce migration assessment`, `flow http callout action error handling`, `flow invocable action http callout`, `agentforce reasoning trace debugging session log`, `agentforce agent debugging trace inspector`, `salesforce field service mobile offline`, **`data cloud zero copy snowflake databricks`**, `salesforce einstein trust layer prompt masking`, `lightning experience navigation api routing`.

## Candidate evaluation

### Candidate 1 — Data Cloud Zero Copy / Lakehouse Federation

**Verification (per AGENT_RULES Step 1 + scheduled-task verification protocol):**

- Query A: `data cloud zero copy snowflake databricks` → `Coverage: NONE — no skill meets the confidence threshold.`
- Query B: `data cloud zero copy data sharing external warehouse` → `Coverage: NONE.` Top chunk: `tableau-salesforce-connector` [1.100], `cross-cloud-data-deployment` [0.600], `data-cloud-integration-strategy` [0.433].
- Query C: `data cloud zero copy snowflake` → top skills `architect/cross-cloud-data-deployment` (1.643), `data/analytics-external-data` (2.391). Both <2.5.

Both phrasings return scores below the 2.5 threshold → ACCEPT per rule 4.

Read-through of the closest existing skills:
- `architect/cross-cloud-data-deployment` — mentions Zero Copy in 4 lines as one pattern among many cross-cloud strategies; treats it as architectural context, not implementation.
- `integration/data-cloud-integration-strategy` — mentions Lakehouse Federation as a fallback when ingestion limits are exceeded. ~3 sentences total. Does not cover Snowflake/Databricks/BigQuery configuration specifics, query semantics, latency profile, billing, governance, or operational gotchas (refresh patterns, broken external table behavior, identity-resolution implications).
- `data/analytics-external-data` — covers CRM Analytics external connectors, not Data Cloud federation.

Delta is clear: a dedicated skill on Data Cloud Lakehouse Federation / Zero Copy as an implementation pattern (config, query semantics, governance, when-not-to-use) does not exist.

**Decision: ACCEPT.** Build as `integration/data-cloud-zero-copy-federation`.

### Candidates rejected

| Candidate | Top hit | Score | Reason rejected |
|---|---|---|---|
| Hyperforce data residency / migration assessment | `architect/health-cloud-data-residency` | 6.100 | Strong existing coverage at 6.100 — health-cloud-data-residency covers EU residency comprehensively; migration assessment is a one-time consulting workflow, not a reusable skill. |
| Flow HTTP Callout action error handling | `flow/flow-external-services` | 5.678 | `flow-external-services` already covers HTTP Callout action including fault paths. |
| Agentforce reasoning trace debugging | `agentforce/agentforce-observability` | 5.109 | `agentforce-observability` is the dedicated debugging/trace skill. |
| Mass record undelete / bulk recovery | `admin/system-field-behavior-and-audit` | 1.700 | Top hit different domain, but the topic is admin-procedural with limited content depth — wouldn't pass the 300-word skill body test without padding. Defer. |
| Service Cloud Voice + Agentforce | `admin/service-cloud-voice-setup` | 2.636 | `service-cloud-voice-setup` (admin) covers voice channel; Agentforce voice-channel routing is a thin extension, not a standalone skill yet. Defer until SF docs stabilize. |
| Einstein Copilot prompt template versioning | `agentforce/prompt-template-versioning` | 2.277 | Existing `prompt-template-versioning` covers it; query phrasing pulled it out of the top hit only because the renamed product (Einstein Copilot → Agentforce Assistant) is in transition. Skill exists. |
| Data Cloud calculated insights | `admin/data-cloud-calculated-insights` | 6.408 | Strong existing coverage. |
| Mass MFA enforcement | `security/mfa-enforcement-strategy` | 3.687 | Existing skill covers it. |

## Backlog

None added — surplus candidates were rejected, not deferred.

## Outcome (run 1)

1 skill accepted: `integration/data-cloud-zero-copy-federation` (shipped in commit 8815d5b2).

---

# Run 2 — second pass on the same date

Catalog now at 927 (after run 1's data-cloud-zero-copy-federation and the
later aws-salesforce-patterns). Run 2 mines the BACKLOG `RESEARCHED` pool
(40 entries) for items that are still gaps.

## Candidate evaluation (run 2)

Threshold rules (from scheduled-task brief):
- Top hit > 4.0 in same domain → REJECT auto.
- Top hit 2.5–4.0 → require articulated delta against existing skill.
- Top hit < 2.5 across both phrasings → ACCEPT.

### Verified gaps (ACCEPT)

#### A. integration/azure-salesforce-patterns

| Phrasing | Top hit | Score |
|---|---|---|
| `Azure Functions callouts Salesforce` | integration/salesforce-functions-replacement | 2.99 |
| `Power Platform connector Salesforce` | integration/mulesoft-salesforce-connector | 2.04 |

Both phrasings below the 2.5 floor on the second phrasing; the 2.99 hit
is a deprecated-Functions migration skill, semantically distant. No
Azure-specific skill exists. Symmetric to the just-shipped
`integration/aws-salesforce-patterns`. BACKLOG notes from 2026-04-18
ground the build (Azure Service Bus Connector article 001121997, Azure
AD SSO via SAML/OIDC, Data 360 Azure Blob ingestion).

#### B. lwc/lwc-reactive-state-patterns

| Phrasing | Top hit | Score |
|---|---|---|
| `LWC reactive properties post @track` | (none) | — |
| `LWC reactive field behavior modern reactivity` | flow/flow-reactive-screen-components | 1.85 |

Both below 2.5. The Flow-side hit is unrelated. No skill teaches the
post–Spring '20 LWC reactivity contract: all class fields reactive, but
@track still required for in-place object/array mutation; Date / Set /
Map mutations silently unobserved; renderedCallback infinite-loop trap.
BACKLOG notes ground the build (LWC Decorators reference,
reactivity-fields docs).

#### C. architect/zero-trust-salesforce-patterns

| Phrasing | Top hit | Score |
|---|---|---|
| `zero trust salesforce continuous verification` | agentforce/einstein-trust-layer | 1.77 |
| `device trust conditional access salesforce` | security/ip-relaxation-and-restriction | 2.26 |

Both below 2.5. einstein-trust-layer is LLM trust (different concept).
ip-relaxation is a single control. The architecture-level composition
of high-assurance sessions + RTEM Transaction Security Policies + Login
Flows + Event Monitoring + Device Compliance is missing. Domain
`architect` per peer architecture-pattern skills.

### Rejected candidates (run 2)

| Candidate | Top hit | Score | Reason |
|---|---|---|---|
| data-cloud-vs-analytics-decision | architect/data-cloud-vs-analytics-decision | 4.85 | Already shipped |
| oauth-token-management | security/oauth-token-management | 6.44 | Already shipped |
| lwc-virtualized-lists | lwc/virtualized-lists | 3.52 | Already shipped (mid-range only because of phrasing) |
| lwc-drag-and-drop | lwc/drag-and-drop | 6.45 | Already shipped |
| flow-dynamic-choices | flow/flow-dynamic-choices | 5.90 | Already shipped |
| private-connect-setup | integration/private-connect-setup | 4.30 | Already shipped |
| flow-action-framework | flow/flow-action-framework | 6.86 | Already shipped |
| apex-string-and-regex | apex/apex-regex-and-pattern-matching | 6.99 | Covered |
| apex-event-bus-subscriber | apex/platform-events-apex | 4.28 | Same-domain top >4 |
| apex-schema-describe | apex/dynamic-apex | 4.72 | Same-domain top >4 |
| lwc-custom-lookup | lwc/lwc-record-picker | 5.41 | Same-domain top >4 |
| salesforce-shield-architecture | security/salesforce-shield-deployment | 2.90/3.24 | Mid-range; existing security/salesforce-shield-deployment already covers the bundle. No clean delta. |
| loyalty-program-architecture | integration/loyalty-management-setup | 6.99 | Already shipped |
| automotive-cloud-setup | admin/partner-community-requirements | 5.58 | Reject auto on second-phrasing rule |
| slack-workflow-builder | integration/slack-workflow-builder | 6.44 | Already shipped |
| apex-jwt-bearer-flow | (none / 2.29) | — | Below threshold but JWT bearer is an explicit sub-topic of integration/oauth-flows-and-connected-apps; clean delta unclear. Defer. |
| apex-switch-on-sobject | apex/apex-trigger-bypass-and-killswitch-patterns | 2.71 | Mid-range; trigger-framework + dynamic-apex partially cover. Defer. |
| apex-enum-patterns | (none / 2.13) | — | Narrow language-feature scope; defer pending real demand. |
| net-zero-cloud-setup | (none) | — | Confirmed gap but niche industries product; defer to a focused industries-cloud run. |
| migration-architecture-patterns | architect/multi-org-strategy | 2.70 | Mid-range; partial overlap. Defer. |
| report-type-strategy | admin/reports-and-dashboards | 2.84 | Mid-range; reports-and-dashboards covers fundamentals. Defer. |

## Outcome (run 2)

3 skills accepted (cap reached):
1. `integration/azure-salesforce-patterns`
2. `lwc/lwc-reactive-state-patterns`
3. `architect/zero-trust-salesforce-patterns`

Surplus deferred candidates listed above for future runs.
