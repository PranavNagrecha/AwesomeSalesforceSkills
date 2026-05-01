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

## Outcome

1 skill accepted: `integration/data-cloud-zero-copy-federation`.
