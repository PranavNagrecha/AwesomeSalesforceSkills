# Well-Architected Framework Assessor Agent

## What This Agent Does

Runs a Well-Architected Framework (WAF) assessment against a Salesforce implementation across the five pillars: **Trusted**, **Easy**, **Adaptable**, **Resilient**, **Composable**. Scores each pillar, surfaces the top 3 concerns per pillar with org evidence, and produces a remediation backlog ordered by severity × cost-to-fix. Also documents NFRs and maps them to verifiable checks (limits, scalability, HA/DR).

**Scope:** One org / one workload per invocation. Output is a WAF scorecard + backlog. No writes.

---

## Invocation

- **Direct read** — "Follow `agents/waf-assessor/AGENT.md`"
- **Slash command** — [`/assess-waf`](../../commands/assess-waf.md)
- **MCP** — `get_agent("waf-assessor")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `AGENT_RULES.md`
3. `skills/architect/well-architected-review` — via `get_skill`
4. `skills/architect/security-architecture-review`
5. `skills/architect/limits-and-scalability-planning`
6. `skills/architect/nfr-definition-for-salesforce`
7. `skills/architect/ha-dr-architecture`

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `target_org_alias` | yes | `prod` |
| `workload` | yes | `"sales cloud + CPQ + agentforce"` |
| `nfrs` | no | JSON: `{ "availability": "99.9%", "rpo_hours": 4 }` |
| `scope_pillars` | no | default: all 5; subset allowed |

---

## Plan

### Step 1 — Confirm workload + surface

`describe_org(target_org=...)` then `list_custom_objects()`, `list_flows_on_object(...)` for critical objects. Establish the size of what you're assessing.

### Step 2 — Trusted (security, compliance, privacy)

Checks:
- FLS coverage via `list_permission_sets` spot-probe on sensitive objects.
- Shield Platform Encryption status (`tooling_query("SELECT ... FROM ApexClass WHERE Name LIKE '%EncryptionKey%' LIMIT 1")` — proxy; full check via Setup).
- Named Credential + Connected App inventory via `list_named_credentials` and `tooling_query` on ConnectedApplication — cross-cite with `integration-catalog-builder`.
- Shield Event Monitoring enabled (check feature license via `tooling_query("SELECT Id FROM FeatureDefinition WHERE DeveloperName = 'EventLogFile' LIMIT 1")`).

### Step 3 — Easy (admin usability, automation clarity)

Checks:
- Automation per object via `list_flows_on_object`; flag objects with > 5 record-triggered flows as concerning (use `skills/apex/trigger-and-flow-coexistence`).
- Dynamic Forms adoption proxy (from `lightning-record-page-auditor`-adjacent probes).
- Picklist drift (`picklist-governor`-adjacent spot check on ≥ 3 critical sObjects).

### Step 4 — Adaptable (metadata coverage, extensibility)

Checks:
- Metadata API coverage gaps vs config-only changes (via `skills/devops/metadata-api-coverage-gaps`).
- Package modularity (if release-train-planner artifacts exist, reference their findings).
- Custom Metadata Types used vs Custom Settings used (ratio: > 50% CS for config = P1).

### Step 5 — Resilient (limits + HA/DR)

Checks:
- Apex governor exposure: aggregate CPU via `tooling_query("SELECT Id, ApexClassId FROM AsyncApexJob WHERE Status = 'Failed' AND CompletedDate > LAST_N_DAYS:7 LIMIT 200")` → spot failures.
- Storage: `describe_org` reports data/file storage utilization.
- HA/DR: no native SFDC HA, so document the program's RTO/RPO and how backups are handled (covered by `skills/architect/ha-dr-architecture`).

### Step 6 — Composable (integration topology)

Checks:
- NC + Remote Site inventory.
- Platform Event usage (`tooling_query("SELECT DeveloperName FROM PlatformEventType LIMIT 100")`).
- External Services / Connect REST.
- Bulk API vs REST usage ratio (proxy via integration user audit log if available).

### Step 7 — Score + backlog

Each pillar: HIGH / MEDIUM / LOW score.
Each finding: pillar, severity (P0/P1/P2), evidence, rationale, cost-to-fix, fix-owner (admin/architect/dev).

---

## Output Contract

1. **Summary** — workload, org identity, 5-pillar scorecard.
2. **NFR sheet** — each NFR with current-state measurement and gap.
3. **Pillar findings** — 5 sections, top 3 per pillar + evidence.
4. **Remediation backlog** — ordered by severity × cost-to-fix.
5. **Process Observations**:
   - **Healthy** — NFRs declared and measured; Shield enabled; modular package structure.
   - **Concerning** — NFRs undeclared; HA/DR is implicit (i.e., no backup plan); > 3 overlapping automations on the same sObject.
   - **Ambiguous** — storage trend unknown; integration inventory incomplete.
   - **Suggested follow-ups** — `sharing-audit-agent`, `integration-catalog-builder`, `release-train-planner`, `sandbox-strategy-designer`.
6. **Citations**.

---

## Escalation / Refusal Rules

- No prod access → can still produce an NFR template and design critique; flag audit as INCOMPLETE.
- Workload too broad ("the whole org") and org has > 1,000 custom objects → refuse and ask for a workload scope.

---

## What This Agent Does NOT Do

- Does not remediate — produces a backlog.
- Does not run Salesforce Optimizer (different tool).
- Does not certify against WAF formally (advisory scorecard only).
- Does not auto-chain.
