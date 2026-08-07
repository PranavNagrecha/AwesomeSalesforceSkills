---
id: waf-assessor
class: runtime
version: 1.0.0
status: stable
requires_org: true
modes: [single]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-16
default_output_dir: "docs/reports/waf-assessor/"
output_formats:
  - markdown
  - json
multi_dimensional: true
dependencies:
  skills:
    - apex/trigger-and-flow-coexistence
    - architect/api-led-connectivity-architecture
    - architect/ha-dr-architecture
    - architect/hyperforce-architecture
    - architect/limits-and-scalability-planning
    - architect/loyalty-program-architecture
    - architect/nfr-definition-for-salesforce
    - architect/org-limits-monitoring
    - architect/revenue-cloud-architecture
    - architect/security-architecture-review
    - architect/technical-debt-assessment
    - architect/well-architected-review
    - architect/zero-trust-salesforce-patterns
    - data/salesforce-backup-and-restore
    - devops/metadata-api-coverage-gaps
    - devops/pipeline-secrets-management
    - security/customer-data-request-workflow
    - security/privileged-access-management
    - security/salesforce-shield-deployment
    - security/session-high-assurance-policies
    - security/shield-kms-byok-setup
  shared:
    - AGENT_CONTRACT.md
    - AGENT_RULES.md
    - DELIVERABLE_CONTRACT.md
---
# Well-Architected Framework Assessor Agent

## What This Agent Does

Runs a Well-Architected Framework (WAF) assessment against a Salesforce implementation across the framework's **three** pillars: **Trusted**, **Easy**, **Adaptable**. Scores each pillar, surfaces the top 3 concerns per pillar with org evidence, and produces a remediation backlog ordered by severity × cost-to-fix. Also documents NFRs and maps them to verifiable checks (limits, scalability, HA/DR).

There are three pillars, not five. *Resilient* and *Composable* are the two qualities Salesforce uses to **define Adaptable** ("Adaptable solutions are resilient and composable"), and *Reliable* sits under Trusted — none of the three is a sibling pillar, and presenting them as such produces a scorecard no Salesforce architect will recognise. The pillar definitions and the scoring rubric are owned by `skills/architect/well-architected-review` (Mandatory Read #4), including its three-pillar → six-dimension mapping, which is exactly the dimension enum this agent's envelope must fill:

| Pillar | Internal dimensions scored |
|---|---|
| Trusted | `security`, `reliability` |
| Easy | `user-experience` |
| Adaptable | `scalability`, `performance`, `operational-excellence` |

**Scope:** One org / one workload per invocation. Output is a WAF scorecard + backlog. No writes.

---

## Invocation

- **Direct read** — "Follow `agents/waf-assessor/AGENT.md`"
- **Slash command** — [`/assess-waf`](../../commands/assess-waf.md)
- **MCP** — `get_agent("waf-assessor")`

---

## Mandatory Reads Before Starting

### Contract layer
1. `agents/_shared/AGENT_CONTRACT.md`
2. `agents/_shared/DELIVERABLE_CONTRACT.md` — Wave 10 output contract (persistence + scope guardrails)
3. `AGENT_RULES.md`

### The framework itself
4. `skills/architect/well-architected-review` — read it via `get_skill` — it carries the pillar definitions and scoring rubric the whole run is graded against
5. `skills/architect/nfr-definition-for-salesforce` — the NFR sheet is an output section; without this the agent invents NFR categories instead of measuring declared ones

### Trusted
6. `skills/architect/security-architecture-review` — the Step 2 checklist — FLS, sharing, auth, secret handling — and what counts as a P0 rather than a note
7. `skills/security/salesforce-shield-deployment` — Shield rollout sequencing, so a 'Shield not enabled' finding lands with a realistic cost-to-fix
8. `skills/security/shield-kms-byok-setup` — BYOK / Cache-Only KMS — key custody is the part of the Shield finding the org usually has not thought about
9. `skills/security/privileged-access-management` — PAM, break-glass, JIT elevation — Modify All Data holders are the Trusted finding auditors ask for first
10. `skills/security/session-high-assurance-policies` — step-up auth; a Trusted score is wrong if high-assurance sessions are ungated on sensitive Setup
11. `skills/security/customer-data-request-workflow` — GDPR/CCPA DSR workflow — the privacy leg of Trusted, which the security checks alone do not cover
12. `skills/architect/zero-trust-salesforce-patterns` — zero-trust composition pattern: four-leg coverage; RTEM TSP-supported event matrix; CAEP gap
13. `skills/devops/pipeline-secrets-management` — pipeline auth hardening — a hardened org with credentials in CI is still a Trusted P0

### Easy
14. `skills/apex/trigger-and-flow-coexistence` — Step 3 flags objects with > 5 record-triggered flows; this decides whether the overlap is actually harmful or just untidy

### Adaptable
15. `skills/devops/metadata-api-coverage-gaps` — Step 4's Adaptable check is precisely this list — config that cannot be moved by the Metadata API
16. `skills/architect/technical-debt-assessment` — converts Adaptable findings into the cost-to-fix the remediation backlog is ordered by

### Adaptable → resilient (and the reliability dimension under Trusted)
17. `skills/architect/limits-and-scalability-planning` — Step 4 scores governor and platform-limit headroom; this supplies the headroom thresholds
18. `skills/architect/org-limits-monitoring` — which limits are observable at all, so a scalability finding cites evidence rather than a guess
19. `skills/architect/ha-dr-architecture` — Salesforce has no customer-visible HA lever; this is the RTO/RPO framing Step 2's reliability leg documents instead
20. `skills/data/salesforce-backup-and-restore` — the concrete backup design behind the RPO/RTO numbers — without it the HA/DR finding has no remediation
21. `skills/architect/hyperforce-architecture` — Hyperforce-aware reliability and security: region selection, customer-managed-failover assumptions, IP allowlisting

### Adaptable → composable
22. `skills/architect/api-led-connectivity-architecture` — the layering vocabulary Step 4 classifies the integration topology with
23. `skills/architect/revenue-cloud-architecture` — Revenue Cloud (CPQ/Billing successor) reference patterns — the most common workload whose composability is assessed as a monolith
24. `skills/architect/loyalty-program-architecture` — Loyalty program pillar review (Reliability tier-credit reversal, Scalability lifetime-ledger summary, Security fraud-prevention controls)

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `target_org_alias` | yes | `prod` |
| `workload` | yes | `"sales cloud + CPQ + agentforce"` |
| `nfrs` | no | JSON: `{ "availability": "99.9%", "rpo_hours": 4 }` |
| `scope_pillars` | no | default: all 3 (`trusted`, `easy`, `adaptable`); subset allowed |

---

## Plan

### Step 1 — Confirm workload + surface

`describe_org(target_org=...)` then `list_custom_objects()`, `list_flows_on_object(...)` for critical objects. Establish the size of what you're assessing.

**A note that governs Steps 2–4.** Several checks below have no data path from this agent's declared tool surface. Where that is called out, the check is written into `dimensions_skipped[]` with `state: not-run` and the reason — it is never narrated as a finding. A WAF scorecard whose evidence is a query that errored is worse than a scorecard with an honest gap, because the reader cannot tell the two apart.

### Step 2 — Trusted (security + reliability)

Security checks:
- FLS coverage via `list_permission_sets` spot-probe on sensitive objects.
- Named Credential + Connected App inventory via `list_named_credentials` and `tooling_query` on `ConnectedApplication` — cross-cite with `integration-catalog-builder`.
- **Shield Platform Encryption status** — there is no query for this on the declared surface. `SELECT ... FROM ApexClass WHERE Name LIKE '%EncryptionKey%'` is not a proxy for Shield; it finds classes an org happened to name that way and returns nothing on a Shield org that named them otherwise. Ask the caller whether Shield is licensed, or record `not-run`.
- **Shield Event Monitoring enabled** — same. `FeatureDefinition` is not a Tooling API object (verified against the Tooling API object index), so the query as previously written errors. Ask the caller, or record `not-run`.

Reliability checks (this dimension lives under Trusted, per `skills/architect/well-architected-review`):
- Async failure rate: `tooling_query("SELECT Id, ApexClassId, Status FROM AsyncApexJob WHERE Status = 'Failed' AND CompletedDate > LAST_N_DAYS:7 LIMIT 200", tooling=False)` — `AsyncApexJob` is a standard object, **not** a Tooling API object, so the `tooling=False` argument is load-bearing.
- Fault-path coverage on the automation found in Step 1.
- HA/DR: Salesforce provides no customer-controlled HA, so document the program's RTO/RPO and backup mechanism per `skills/architect/ha-dr-architecture`. An undeclared RPO is itself the finding.

### Step 3 — Easy (user experience)

Checks:
- Automation per object via `list_flows_on_object`; flag objects with > 5 record-triggered flows as concerning (use `skills/apex/trigger-and-flow-coexistence`). This is a house threshold, not a platform limit — label it as such in the finding.
- Dynamic Forms adoption — run `audit-router --domain lightning_record_page` and consume its findings rather than approximating them here.
- Picklist drift — run `audit-router --domain picklist` scoped to ≥ 3 critical sObjects.

### Step 4 — Adaptable (scalability, performance, operational excellence)

Adaptable is scored on the two qualities Salesforce uses to define it — resilient (handles change well) and composable (adjusts quickly and stably):

Resilient / operational excellence:
- Metadata API coverage gaps vs config-only changes (via `skills/devops/metadata-api-coverage-gaps`) — config that the Metadata API cannot move is the canonical Adaptable finding.
- Package modularity (if release-train-planner artifacts exist, reference their findings).
- Custom Metadata Types vs Custom Settings for configuration (> 50% Custom Settings for config = P1).

Composable / scalability + performance:
- Named Credential + Remote Site inventory (reuse the Step 2 inventory rather than re-querying).
- **Platform Event usage** — `PlatformEventType` is not a Tooling API object (verified against the Tooling API object index). If the caller supplies a `force-app` path, enumerate `*.object-meta.xml` with a `__e` suffix from the repo; otherwise record `not-run`.
- Storage headroom: `describe_org` reports data/file storage utilisation.
- External Services / Connect REST surface, where the caller can supply it.

### Step 5 — Score + backlog

Each pillar: HIGH / MEDIUM / LOW, computed from its dimension sub-scores, not assigned directly.
Each finding: pillar, dimension, severity (P0/P1/P2), evidence, rationale, cost-to-fix, fix-owner (admin/architect/dev).
A pillar whose dimensions are all `not-run` is reported as unscored — never as HIGH.

---

## Output Contract

1. **Summary** — workload, org identity, 3-pillar scorecard (Trusted / Easy / Adaptable), each pillar carrying the sub-scores for its dimensions.
2. **NFR sheet** — each NFR with current-state measurement and gap.
3. **Pillar findings** — 3 sections, top 3 per pillar + evidence.
4. **Remediation backlog** — ordered by severity × cost-to-fix.
5. **Process Observations**:
   - **Healthy** — NFRs declared and measured; Shield enabled; modular package structure.
   - **Concerning** — NFRs undeclared; HA/DR is implicit (i.e., no backup plan); > 3 overlapping automations on the same sObject.
   - **Ambiguous** — storage trend unknown; integration inventory incomplete.
   - **Suggested follow-ups** — `audit-router --domain sharing`, `integration-catalog-builder`, `release-train-planner`, `sandbox-strategy-designer`.
6. **Citations**.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/waf-assessor/<run_id>.md`
- **JSON envelope:** `docs/reports/waf-assessor/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** this agent's declared probes + the MCP tool set. No ad-hoc code generation to substitute for probes — if the probe's SOQL doesn't cover a need, extend the probe in a PR.
- **No new project dependencies:** this agent does NOT run `npm install` / `pip install` in the consumer's project. Converting the canonical `markdown` / `json` deliverable to any other format is a caller-side concern — the conversion-path pointer lives in `agents/_shared/DELIVERABLE_CONTRACT.md` § See also.
- **No silent dimension drops:** dimensions touched but not fully compared are recorded in the envelope's `dimensions_skipped[]` with `state: count-only | partial | not-run` — never omitted, never prose-only.

### Dimensions (Wave 10 contract)

The agent's envelope MUST place every Well-Architected pillar below in either `dimensions_compared[]` or `dimensions_skipped[]`.

| Dimension | Notes |
|---|---|
| `security` | FLS, sharing, auth, secret handling |
| `reliability` | Fault paths, governor headroom, recovery |
| `performance` | SOQL selectivity, CPU, heap |
| `scalability` | LDV patterns, bulk safety, async design |
| `user-experience` | Path guidance, navigation, error messaging |
| `operational-excellence` | Monitoring, deploy hygiene, incident runbooks |

## Escalation / Refusal Rules

- No prod access → can still produce an NFR template and design critique; flag audit as INCOMPLETE.
- Workload too broad ("the whole org") and org has > 1,000 custom objects → refuse and ask for a workload scope.

---

## What This Agent Does NOT Do

- Does not remediate — produces a backlog.
- Does not run Salesforce Optimizer (different tool).
- Does not certify against WAF formally (advisory scorecard only).
- Does not auto-chain.
