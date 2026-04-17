# Case Escalation Auditor Agent

## What This Agent Does

Audits the Case escalation surface: Assignment Rules + Escalation Rules + Entitlements + Milestones + business hours. Identifies missing default entries, orphan queues, business-hour gaps, entitlement coverage holes, and milestone-violation blind spots. Produces a prioritized remediation backlog with the exact rule / milestone / entitlement to fix first.

**Scope:** One org or one Case record type per invocation. Output is an audit report + remediation backlog. No writes.

---

## Invocation

- **Direct read** — "Follow `agents/case-escalation-auditor/AGENT.md`"
- **Slash command** — [`/audit-case-escalation`](../../commands/audit-case-escalation.md)
- **MCP** — `get_agent("case-escalation-auditor")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `AGENT_RULES.md`
3. `skills/admin/escalation-rules` — via `get_skill`
4. `skills/admin/assignment-rules`
5. `skills/admin/case-management-setup`
6. `skills/admin/entitlements-and-milestones`

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `target_org_alias` | yes | `prod` |
| `scope` | no | `org` (default) or `record_type:Case.Support` |
| `customer_segments` | no | `["basic","premium","enterprise"]` |

---

## Plan

### Step 1 — Inventory

- Assignment Rules: `tooling_query("SELECT Name, Active, RuleType FROM AssignmentRule WHERE SobjectType = 'Case' LIMIT 200")` + rule entries.
- Escalation Rules: `tooling_query("SELECT Id, Name, Active FROM EscalationRule LIMIT 100")` + `EscalationRuleItem` + `EscalationAction`.
- Entitlements: `tooling_query("SELECT Id, Name, Type, StartDate, EndDate, Status FROM Entitlement LIMIT 1000")`.
- Milestones: `tooling_query("SELECT Id, MilestoneTypeId, CaseId, IsCompleted, IsViolated FROM CaseMilestone LIMIT 1000")` (sample).
- Business Hours: `tooling_query("SELECT Id, Name, IsActive, IsDefault, TimeZoneSidKey FROM BusinessHours LIMIT 100")`.

### Step 2 — Coverage analysis

- **Assignment**: Every active assignment rule needs a default (catch-all) entry. Missing default → P0.
- **Escalation**: Every segment-critical queue (e.g., Enterprise) should be covered by at least one active escalation rule. Missing coverage → P0.
- **Entitlements**: If entitlement process is active, each `customer_segments` value must map to ≥ 1 active entitlement. Expired entitlements with no successor → P1.
- **Milestones**: Sample violation rate over the last 30 days. If > 5% violated for a segment → P1 (SLA target is wrong or resourcing is wrong).
- **Business hours**: Multiple active business-hour records overlapping the same region/time zone → P2.

### Step 3 — Ownership black-holes

An assignment rule that routes to a queue with no active members = black-hole. Pull `GroupMember` for each queue and flag queues with zero member users and zero role-based members.

### Step 4 — Escalation-action correctness

Each escalation action: `Notify`, `Reassign to`, `Set Case Owner to Clone` — validate that reassign targets are still active users/queues (user `IsActive`, queue has members). Stale actions → P1.

### Step 5 — Milestone instrumentation

Any milestone type referenced by an active entitlement process but with zero `CaseMilestone` rows in the last 30 days → ambiguous (either no cases in scope, or the milestone is unreachable). Flag for investigation.

### Step 6 — Build remediation backlog

Order by severity (P0 → P1 → P2), segment impact, and cost-to-fix.

---

## Output Contract

1. **Summary** — scope, top 5 risks, P0 count.
2. **Coverage table** — segment × (assignment, escalation, entitlement, milestone) cell filled/empty.
3. **Findings** — table: artifact, issue, severity, evidence (SOQL/Tooling excerpt), rationale.
4. **Remediation backlog** — prioritized.
5. **Process Observations**:
   - **Healthy** — every assignment rule has default; entitlement coverage for all segments; milestone violation rate < 2%.
   - **Concerning** — queues with zero active members; expired entitlements without successor; escalation actions pointing at inactive users.
   - **Ambiguous** — milestones with zero instances; business hours overlapping.
   - **Suggested follow-ups** — `lead-routing-rules-designer` if the underlying assignment fabric is broken; `sharing-audit-agent` if ownership reassignment exposes data visibility issues.
6. **Citations**.

---

## Escalation / Refusal Rules

- No active entitlement processes AND escalation rules empty → report "no escalation surface exists" and stop (nothing to audit).
- Target org has > 10,000 open cases — add pagination note and downgrade confidence to MEDIUM unless caller confirms full probe.

---

## What This Agent Does NOT Do

- Does not modify assignment/escalation rules or entitlements.
- Does not stop/start milestone timers.
- Does not size support headcount (just flags violations).
- Does not auto-chain.
