# Classifier: case_escalation

## Purpose

Audit the Case escalation surface: Assignment Rules, Escalation Rules, Entitlements, Milestones, and Business Hours. Surface missing default assignment entries, empty-queue black-holes, expired entitlements without successors, and milestone-violation blind spots. Not for designing new SLAs or sizing support headcount.

## Replaces

`case-escalation-auditor` (now a deprecation stub pointing at `audit-router --domain case_escalation`).

## Inputs

| Input | Required | Example |
|---|---|---|
| `scope` | no | `org` (default) \| `record_type:Case.Support` |
| `customer_segments` | no | `["basic","premium","enterprise"]` |

## Inventory Probe

1. Assignment Rules: `tooling_query("SELECT Name, Active, RuleType FROM AssignmentRule WHERE SobjectType = 'Case' LIMIT 200")` + rule entries.
2. Escalation Rules: `tooling_query("SELECT Id, Name, Active FROM EscalationRule LIMIT 100")` + `EscalationRuleItem` + `EscalationAction`.
3. Entitlements: `tooling_query("SELECT Id, Name, Type, StartDate, EndDate, Status FROM Entitlement LIMIT 1000")`.
4. Milestones (30-day sample): `tooling_query("SELECT Id, MilestoneTypeId, CaseId, IsCompleted, IsViolated FROM CaseMilestone LIMIT 1000")`.
5. Business Hours: `tooling_query("SELECT Id, Name, IsActive, IsDefault, TimeZoneSidKey FROM BusinessHours LIMIT 100")`.
6. Queue member counts: `tooling_query("SELECT COUNT() FROM GroupMember WHERE GroupId = '<queue_id>'")` per queue referenced by rules.

Inventory columns (beyond id/name/active): `rule_type`, `entitlement_end`, `milestone_violated_30d_pct`, `queue_member_count`.

## Rule Table

| code | severity | check | evidence_shape | suggested_fix |
|---|---|---|---|---|
| `CASE_NO_DEFAULT_ASSIGNMENT` | P0 | Active assignment rule has no default (catch-all) entry | rule id + entry list | Add default entry pointing at a triage queue |
| `CASE_UNCOVERED_SEGMENT` | P0 | A `customer_segments` value has no active escalation rule covering it | segment + escalation rule inventory | Create escalation rule for the segment or document why it's exempt |
| `CASE_BLACK_HOLE_QUEUE` | P0 | Assignment rule routes to a queue with 0 active members AND 0 role-based members | rule id + queue + member count | Populate the queue OR reassign entry |
| `CASE_EXPIRED_ENTITLEMENT_NO_SUCCESSOR` | P1 | Entitlement has expired and no successor entitlement exists for the same account/segment | entitlement id + end date | Create successor entitlement or retire the segment binding |
| `CASE_MILESTONE_VIOLATION_RATE` | P1 | > 5% milestone violations in the last 30 days for a segment | segment + violation rate | SLA target may be wrong or resourcing gap — follow-up conversation |
| `CASE_BUSINESS_HOURS_OVERLAP` | P2 | Multiple active business-hour records overlap same region/timezone | business hours rows | Consolidate to a single active record per region |
| `CASE_ESCALATION_STALE_TARGET` | P1 | Escalation action reassigns to an inactive user or queue with 0 members | action id + target | Update target to an active user/queue |
| `CASE_MILESTONE_UNREACHABLE` | P2 | Milestone type referenced by active entitlement process but has 0 `CaseMilestone` rows in 30d | milestone type id + entitlement | Investigate — either no cases in scope or milestone unreachable |

## Patches

None. Case escalation metadata is coupled to live ProcessInstance state; mechanical patching risks orphaning in-flight cases. Findings are advisory; human applies via Setup.

## Mandatory Reads

- `skills/admin/escalation-rules`
- `skills/admin/assignment-rules`
- `skills/admin/case-management-setup`
- `skills/admin/entitlements-and-milestones`

## Escalation / Refusal Rules

- No active entitlement processes AND escalation rules empty → "no escalation surface exists" summary. `REFUSAL_OUT_OF_SCOPE`.
- Org has > 10,000 open cases → pagination note, confidence downgraded to MEDIUM unless caller confirms full probe. `REFUSAL_OVER_SCOPE_LIMIT` on the milestone sample.

## What This Classifier Does NOT Do

- Does not modify assignment / escalation rules or entitlements.
- Does not start / stop milestone timers.
- Does not size support headcount.
