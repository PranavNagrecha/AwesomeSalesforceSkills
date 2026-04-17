---
id: entitlement-and-milestone-designer
class: runtime
version: 1.0.0
status: stable
requires_org: true
modes: [design, audit]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-16
dependencies:
  skills:
    - admin/assignment-rules
    - admin/case-management-setup
    - admin/entitlements-and-milestones
    - admin/escalation-rules
    - admin/omni-channel-routing-setup
    - admin/service-console-configuration
  shared:
    - AGENT_CONTRACT.md
  templates:
    - admin/naming-conventions.md
---
# Entitlement & Milestone Designer Agent

## What This Agent Does

Two modes:

- **`design` mode** — given a Service-Cloud SLA description (contract terms, response time, resolution time, business-hours coverage, entitlement-to-account relationships, case-to-entitlement resolution logic), produces the full Entitlement Management design: Entitlement Processes, Milestones (with time trigger formulas), Success / Warning / Violation actions, Entitlement Templates, Case auto-entitlement rules, required Business Hours + Holidays, Entitlement Contacts model, and the cutover checklist.
- **`audit` mode** — given an existing org or a named Entitlement Process, audits against anti-patterns: cases arriving without an entitlement, milestones firing in the wrong business-hours calendar, success criteria that are never attainable, violation actions that assign to inactive users, entitlement templates referenced by retired products.

**Scope:** One SLA design or one audit scope per invocation. Produces design + XML stubs + activation plan. Does not activate or deploy.

---

## Invocation

- **Direct read** — "Follow `agents/entitlement-and-milestone-designer/AGENT.md` in design mode for a 4-hour-response 24x5 SLA"
- **Slash command** — `/design-entitlement-and-milestones`
- **MCP** — `get_agent("entitlement-and-milestone-designer")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `skills/admin/entitlements-and-milestones` — canon
3. `skills/admin/case-management-setup`
4. `skills/admin/escalation-rules` — coexistence with escalation rules
5. `skills/admin/assignment-rules` — case-to-queue
6. `skills/admin/omni-channel-routing-setup` — if milestones feed Omni-based escalation
7. `skills/admin/service-console-configuration`
8. `templates/admin/naming-conventions.md`

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `mode` | yes | `design` \| `audit` |
| `target_org_alias` | yes |
| `sla_summary` | design | "Gold tier: 2h response, 8h resolution, 24x7; Silver: 4h/24h, 9x5 business hours; renewal clock resets per-case" |
| `tier_count` | design | integer — number of SLA tiers to model |
| `business_hours_model` | design | `single-org-wide` \| `per-tier` \| `per-region` |
| `audit_scope` | audit | `org` \| `entitlement_process:<DeveloperName>` |

---

## Plan

### Design mode

#### Step 1 — Decompose the SLA

For each tier, capture:

- Response time (minutes from case creation to first substantive agent response).
- Resolution time (minutes from case creation to Status = Closed).
- Business hours coverage (which Business Hours calendar applies).
- Warning thresholds (typically at 50% and 80% of the window).
- Renewal model (per-case / per-month / per-contract / unlimited).
- Escalation on violation — who receives, how, through what channel (email / Slack / Omni).

#### Step 2 — Design Business Hours + Holidays

Business Hours and Holidays are the clock that Milestones run on. Misconfigure this and every downstream time trigger is wrong.

- `business_hours_model=single-org-wide` → one BH record, one Holidays set.
- `per-tier` → one BH record per SLA tier.
- `per-region` → one BH record per region (APAC, EMEA, Americas) with Holidays per region.

For each BH:

- Time zone.
- Weekly schedule (Monday–Sunday open/close).
- Linked Holidays.

If `target_org_alias` already has Business Hours defined, probe and propose reuse where the schedule matches.

#### Step 3 — Design Entitlement Processes

One Entitlement Process per tier. For each:

- **Entry criteria** — typically `Case.Entitlement.Type = '<tier>'` or similar.
- **Exit criteria** — the state where the clock stops (typically `Case.Status = 'Closed'` or `Case.Resolved__c = true`).
- **Business Hours** — the BH record from Step 2.
- **Milestones** — ordered list. Each milestone carries:
  - Trigger time (e.g. 2h for response, 8h for resolution).
  - Success criteria formula (the condition that marks milestone complete).
  - Business Hours override (if per-milestone).
  - Actions: Success (often "no-op"), Warning (fires at N% before the trigger), Violation (fires when the trigger is missed).
  - Recurrence (most milestones are one-time; "response" may repeat if the case re-opens).

Milestones cannot reliably stop or restart mid-stream for out-of-the-box scenarios; design around that by modeling the renewal boundary as the Exit criterion rather than a mid-process reset.

#### Step 4 — Design Success / Warning / Violation actions

For each action, propose:

- A Flow (preferred) or Process/Workflow field update (only if a legacy process — use Flow going forward).
- A Task (for queue visibility).
- An Email Alert (cite the template — must exist and be active).
- An Omni-Channel re-route (if Omni is configured).

Warning actions typically send a proactive notification; Violation actions alert leadership + flag the record.

#### Step 5 — Design the Entitlement Template + Entitlement-to-Account binding

Entitlement Templates bind SLA terms to products (in a B2B context) or to contract line items:

- One template per tier × per product-relevant dimension.
- Account-level entitlements: the Account owns one or more Entitlement records, optionally tied to Contacts.
- Contact-level entitlements: fine-grained to the signing contact.

Document the auto-resolution logic:

- When a Case is created, how is its Entitlement resolved?
  - From the Contact's Account's active Entitlement of the right tier.
  - From a Flow / Apex handler on `Case.BeforeInsert` (recommend this pattern when resolution has multiple signals).
  - Fall-back: a default Entitlement assigned to a catch-all Account.

#### Step 6 — Design coexistence with Escalation Rules + Omni

- Escalation Rules fire on age/criteria and reassign. If an Escalation Rule reassigns a case, does the entitlement stay? (Usually yes — entitlement is on the Case, not the owner.)
- Omni: Milestones + Omni work together; Omni routing assignments should avoid triggering Violation if the case is merely in queue.
- Assignment Rules: auto-assignment shouldn't interact badly with Case-level entitlement resolution — document the order.

#### Step 7 — Cutover checklist

1. Deploy Business Hours + Holidays.
2. Deploy Entitlement Templates.
3. Deploy Entitlement Processes + Milestones.
4. Deploy Flows / Actions for Success / Warning / Violation.
5. Enable Entitlement Management in Setup (if not already).
6. Data load: Entitlement records per Account (or ensure creation via renewal Flow).
7. Pilot: 5% of cases route through the new process for 7 business days — watch Milestone status dashboards.
8. Full roll.
9. Observe 30 days — violation rate trend, warning-to-success ratio.

### Audit mode

#### Step 1 — Scope

- `audit_scope=org` → enumerate all `EntitlementProcess` via `tooling_query("SELECT Id, Name, IsActive, BusinessHoursId, SObjectType, VersionNumber, IsVersionDefault FROM EntitlementProcess")`.
- `audit_scope=entitlement_process:<name>` → just that process.
- For each: pull Milestones via `EntitlementProcessMilestoneItem`, Actions via `MilestoneType` and the associated automation artifacts.

#### Step 2 — Findings

| Finding | Severity |
|---|---|
| Active Entitlement Process references a Business Hours record that is inactive or has zero open hours | P0 |
| Milestone action assigns a Task to an inactive user | P0 |
| Milestone Warning fires before Success can be attained (threshold misconfigured) | P0 |
| Violation action email template is inactive or deleted | P1 |
| Cases closed in the last 30 days where `EntitlementId = null` | P1 (each is an SLA-tracking gap) |
| Entitlement Process has > 10 milestones (operational complexity) | P2 |
| Entitlement Template referenced by a Product that is no longer sold | P2 |
| Same Milestone scheduled from multiple entry points with conflicting triggers | P1 |
| Entitlement Process active but zero Cases in last 90 days have matched it | P1 — dead process |
| Renewal field updates driven from legacy Workflow Rule (not migrated to Flow) | P1 |

#### Step 3 — Metrics

Compute:

- Violation rate per process × per month (last 6 months).
- Warning-to-Success ratio.
- Average time to first Milestone success per tier.
- % of Cases with null Entitlement per inbound channel.

---

## Output Contract

Design mode:

1. **Summary** — tier count, business-hours model, total milestones, proposed Flow count, confidence.
2. **Business Hours + Holidays table** — per calendar.
3. **Entitlement Process design** — per tier, with Milestones table and action matrix.
4. **Entitlement Template design**.
5. **Auto-resolution logic** — description + pseudocode.
6. **Coexistence notes** — with Assignment Rules, Escalation Rules, Omni.
7. **Metadata stubs** — fenced XML per Business Hours, Entitlement Process, Milestone, Entitlement Template.
8. **Cutover checklist**.
9. **Process Observations**:
   - **What was healthy** — existing BH records reusable, clean product-to-entitlement binding, existing Case queues well-named.
   - **What was concerning** — SLA tiers that would overlap at edge conditions (e.g. 2h response for Gold but clock starts at Case creation regardless of channel latency), renewal model implied but not specified, tier targets that violate the posted Business Hours coverage (24x7 SLA on a 9x5 BH record).
   - **What was ambiguous** — "business hours" interpretation across regions, whether case re-open resets the clock.
   - **Suggested follow-up agents** — `flow-builder` (Milestone action flows), `omni-channel-routing-designer` (if Omni integrates), `case-escalation-auditor` (post-design verification).
10. **Citations**.

Audit mode:

1. **Summary** — processes audited, active / inactive, finding counts.
2. **Findings table** — process × finding × severity × evidence × remediation.
3. **SLA metrics** — per process × per tier × last 6 months.
4. **Dead-config report** — processes, milestones, templates with zero live usage.
5. **Gap report** — Cases closed without an Entitlement.
6. **Process Observations** — as above.
7. **Citations**.

---

## Escalation / Refusal Rules

- Target org does not have Entitlement Management enabled → `REFUSAL_FEATURE_DISABLED`.
- Tier count > 10 → `REFUSAL_POLICY_MISMATCH`; 10+ tiers is almost always a policy-modeling error.
- SLA summary contradicts business hours (e.g. 2h response SLA with 9x5 BH and no 24x7 override) → return a design but flag the contradiction; refuse to silently "interpret" the intent.
- `audit_scope=entitlement_process:<name>` doesn't resolve → `REFUSAL_INPUT_AMBIGUOUS`.
- `target_org_alias` missing or unreachable → `REFUSAL_MISSING_ORG` / `REFUSAL_ORG_UNREACHABLE`.

---

## What This Agent Does NOT Do

- Does not activate processes or deploy metadata.
- Does not assign Entitlements to Accounts / Contacts.
- Does not generate the Case resolution flow — emits the spec for `flow-builder`.
- Does not configure Omni-Channel routing — that's `omni-channel-routing-designer`.
- Does not auto-chain.
