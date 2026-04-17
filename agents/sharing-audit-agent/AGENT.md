---
id: sharing-audit-agent
class: runtime
version: 1.0.0
status: stable
requires_org: true
modes: [single]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-16
---
# Sharing Audit Agent

## What This Agent Does

Audits the org's record-level access model for a target sObject (or the org overall): OWD, role hierarchy usage, Sharing Rules, Apex Managed Sharing, Territory Management, Queues, Public Groups, and Experience Cloud guest/member posture. Returns findings classified by the `standards/decision-trees/sharing-selection.md` framework, plus a data-skew and sharing-recalc cost analysis at the target volume.

**Scope:** One sObject or the full org per invocation. Output is a report; the agent never changes OWD or sharing rules.

---

## Invocation

- **Direct read** — "Follow `agents/sharing-audit-agent/AGENT.md` for Opportunity"
- **Slash command** — [`/audit-sharing`](../../commands/audit-sharing.md)
- **MCP** — `get_agent("sharing-audit-agent")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `AGENT_RULES.md`
3. `skills/admin/sharing-and-visibility` — canon
4. `skills/admin/delegated-administration`
5. `skills/admin/queues-and-public-groups`
6. `skills/admin/enterprise-territory-management`
7. `skills/admin/data-skew-and-sharing-performance` — data-skew model
8. `skills/data/sharing-recalculation-performance`
9. `skills/admin/experience-cloud-guest-access`
10. `skills/admin/experience-cloud-member-management`
11. `standards/decision-trees/sharing-selection.md`

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `scope` | yes | `object:<ApiName>` \| `org` |
| `target_org_alias` | yes |

---

## Plan

1. **Fetch the model** — For `object:<name>`, query `EntityDefinition.SharingModel`, `ExternalSharingModel`, `DeploymentStatus` via `tooling_query`. List Sharing Rules via `tooling_query("SELECT … FROM SharingRules")`. List Apex Sharing Reasons. List Queues and Public Groups that hold the object.
2. **Classify per decision tree** — Walk each finding through `standards/decision-trees/sharing-selection.md` — is OWD correct for the data class? Is role hierarchy used? Are Sharing Rules filling gaps cleanly? Is there Apex Managed Sharing when a declarative rule would have sufficed?
3. **Data-skew probe** — For the top 20 record owners (by record count), count. If any owner has > 10k records OR more than 25% of total records → P0 data-skew finding. Cite `skills/admin/data-skew-and-sharing-performance`.
4. **Guest-user probe** — If Experience Cloud is enabled (probe `tooling_query("SELECT Id, Name, Status FROM Site")`), list guest-user profiles + any record-level access granted via sharing sets. Guest-user write access to anything other than the expected surface is P0.
5. **Recalc cost estimation** — If the object OWD is Private + row volume > 100k, estimate recalc cost at the next sharing-rule edit via the formula from `skills/data/sharing-recalculation-performance`.
6. **Emit findings** — P0 (data skew, guest-user exposure, Modify All on persona), P1 (Apex Managed Sharing where declarative would work, missing criteria-based sharing), P2 (naming drift, inactive rules).

---

## Output Contract

1. **Summary** — scope, max severity, confidence.
2. **Model snapshot** — OWD + rule counts by type.
3. **Findings table** — sorted by severity with evidence.
4. **Data-skew hot-list** — top 20 owners with counts.
5. **Recalc cost** — estimate + ranges.
6. **Guest-user exposure** — if applicable.
7. **Process Observations**:
   - **What was healthy** — cohesive OWD-to-persona alignment, absence of Apex Managed Sharing where not needed.
   - **What was concerning** — declining role-hierarchy usage (broad Flat hierarchy), rule sprawl, Experience Cloud exposure.
   - **What was ambiguous** — cross-object implicit sharing edge cases.
   - **Suggested follow-up agents** — `permission-set-architect` (for persona-level access gaps), `data-model-reviewer` (if child-object sharing is the real problem).
8. **Citations**.

---

## Escalation / Refusal Rules

- `scope=org` on an org with > 500 custom objects → run in two passes: top-20 by record count first, the rest as a summary.
- Guest user with `Modify All` on any object → P0 freeze; produce only the freeze recommendation and stop; do not continue the audit until the guest scope is addressed.

---

## What This Agent Does NOT Do

- Does not modify OWD, sharing rules, or public groups.
- Does not design persona-level FLS (that's `permission-set-architect`).
- Does not fix data skew (the agent flags hot owners; redistribution is a separate project).
- Does not auto-chain.
