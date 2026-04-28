---
name: process-flow-as-is-to-be
description: "Documenting As-Is and To-Be business processes for a Salesforce project as swim-lane diagrams with one lane per actor (user, system, integration, customer), explicit decision points, parallel paths, exception/sad-path handling, and per-step automation-tier annotations (Flow / Apex / Approval / Platform Event / Manual / Integration) that drive downstream build decisions. Use when discovery has named a business process and the team needs a structured map before any Flow, Apex, or Approval Process is built. Trigger keywords: As-Is To-Be salesforce process, swim lane salesforce, business process map, automation candidate identification, sad path documentation, process actor mapping, manual residue. NOT for Sales-specific stage design (use sales-process-mapping). NOT for fundraising stewardship process mapping (use fundraising-process-mapping). NOT for FSL appointment scheduling flows (use fsl-scheduling-policies). NOT for actually building the Flow (use skills/flow/* and agents/flow-builder/AGENT.md). NOT for pure UI-side user journeys (use persona-and-journey-mapping-sf)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
  - User Experience
triggers:
  - "We need an As-Is To-Be salesforce process map for the order intake workflow before we touch any Flows"
  - "Stakeholders keep arguing about who does what — we need swim lanes for sales rep vs system vs the integration"
  - "How do we identify automation candidates per step in a To-Be process and pick Flow vs Apex vs Approval?"
  - "The customer experience handoff is invisible in our process doc — we forgot the customer-facing swim lane"
  - "We mapped a happy path but the build keeps surfacing exception paths we never documented"
  - "How do I annotate each To-Be step so the build team knows whether it is Flow, Apex, manual, or an integration call?"
  - "We have a target operating model but no manual residue list — what stays manual on purpose?"
tags:
  - process-mapping
  - as-is-to-be
  - swim-lane
  - automation-candidate
  - bpmn
  - business-analysis
  - exception-paths
  - manual-residue
  - admin
  - discovery
inputs:
  - "Process name and approximate scope (start trigger, end state, deal type or business unit)"
  - "Names of actors involved — internal users by role, automated systems, integrations by name, customer touchpoints"
  - "A walkthrough of the As-Is process, however informal (whiteboard, recording, SOP doc, verbal)"
  - "Known pain points or compliance requirements that constrain the To-Be design"
  - "List of integrated systems and which ones are inbound, outbound, or bidirectional"
  - "Approval requirements (regulatory, financial threshold, manager sign-off) tied to specific decision points"
outputs:
  - "As-Is process map: swim-lane diagram with actor, action, system of record, and pain-point annotation per step"
  - "To-Be process map: swim-lane diagram with each step annotated by automation tier ([FLOW], [APEX], [APPROVAL], [PLATFORM_EVENT], [INTEGRATION], [MANUAL])"
  - "Automation candidate table: one row per To-Be step proposed for automation, with cited automation-selection.md branch and the recommended run-time agent"
  - "Manual residue list: steps that intentionally remain manual, with the reason (judgement call, regulatory, low volume, change cost)"
  - "Exception path catalogue: the sad paths for every decision diamond and every integration handshake"
  - "Handoff JSON for /build-flow, /build-agentforce-action, and /design-object — process_id, as_is_steps[], to_be_steps[] each with actor, description, automation_tier, recommended_agents[]"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# Process Flow As-Is To-Be

This skill activates when a practitioner needs to produce an As-Is and To-Be business process map as the structured input to a Salesforce build. The output is a swim-lane diagram (one lane per actor, not per system or per phase), a decision-tree-anchored automation candidate list, an explicit manual residue list, and a machine-readable handoff JSON consumed by `/build-flow`, `/build-agentforce-action`, `/design-object`, and the `automation-selection.md` decision tree.

This is the generic, domain-agnostic process flow skill. Vertical-specific process mapping (sales stages, fundraising stewardship cycles, FSL scheduling) lives in sister skills.

---

## Before Starting

Gather this context before mapping anything:

- **Confirm the start trigger and end state.** A process map without unambiguous start and end conditions drifts during build. "Lead created" and "Opportunity Closed Won" are start and end. "Improving sales" is not.
- **Enumerate actors.** Each actor becomes a swim lane. The four canonical actor types are: human users by role (AE, manager, deal desk, customer support), the Salesforce system itself (automation, validation, sharing), external integrations by name (NetSuite, MuleSoft, payment gateway), and the customer or external counterparty (when they fill out a form, sign a document, or receive an email).
- **Identify the decision authority for the To-Be design.** The To-Be is a future-state proposal — it requires sign-off from a named owner (process owner, RevOps lead, COO). Map without that owner and the To-Be will not survive contact with the build phase.
- **Establish whether the process is in scope of an existing decision tree.** If the process touches automation tooling choice, read `standards/decision-trees/automation-selection.md` first. If it touches async patterns or integration patterns, read those trees too. The trees are authoritative — the To-Be must cite them for every automated step.
- **Confirm there is no domain-specific sister skill that fits better.** A sales-stage transition map is `sales-process-mapping`. A donor stewardship cycle is `fundraising-process-mapping`. An FSL scheduling policy is `fsl-scheduling-policies`. Use those instead when the domain matches.

---

## Core Concepts

### Swim Lane Per Actor — Not Per System, Not Per Phase

A swim lane represents an actor: who or what is performing each step. The most common mapping mistake is collapsing actors into systems (one lane for "Salesforce", one for "ERP") or splitting by phase (Discovery / Negotiation / Close). Both produce maps that obscure responsibility.

The canonical actor categories are:

- **Human user** — by role, not by name. "Account Executive" not "Jane".
- **Salesforce platform** — for automated steps the platform performs (validation, sharing, record creation, notification).
- **Integration** — one lane per named external system. NetSuite is one lane; MuleSoft is another; Stripe is a third. Lumping integrations into a single "External" lane hides handshake steps.
- **Customer or external counterparty** — when the process includes a step the customer performs (signs a document, fills out a portal form, replies to an email). In B2C contexts this lane is mandatory; B2B teams forget it constantly.

A well-formed As-Is map has 4–7 lanes. More than 7 indicates the process scope is too broad and should be split.

### Decision Diamond Rules

Every decision diamond in the map must:

1. **State the decision as a question** — "Has credit check passed?" not "Credit check".
2. **Have at least two outgoing branches** — typically Yes / No, but multi-way decisions (Tier 1 / Tier 2 / Tier 3) are valid.
3. **Label each branch with the condition that triggered it** — not just the outcome. "No → escalate to manager" not just "→ escalate".
4. **Have an explicit sad-path branch** — what happens when the decision data is missing, ambiguous, or the system that would supply it is down. Maps that show only the happy branch fail at build time when the developer asks "what about when…".

### Parallel Paths and Merge Patterns

When two or more steps run concurrently after a fork (e.g., legal review and finance review both kick off at Proposal), the map must show:

- The fork point — usually a parallel-gateway diamond or a labelled fork node.
- Each concurrent path on its own lane.
- The merge point — the step that cannot proceed until all parallel paths complete (an AND-merge) or any one completes (an OR-merge). This distinction is critical because AND-merge translates to a wait condition or an aggregation flow, while OR-merge translates to a first-wins pattern.

### Exception / Sad-Path Handling

Every external integration handshake, every approval, and every decision diamond must have an exception path documented. The four canonical exception classes are:

- **Timeout** — the upstream system did not respond within the SLA.
- **Validation rejection** — the data submitted did not pass downstream validation.
- **Authorization failure** — the actor performing the step lacks permission.
- **Manual override** — a human consciously bypassed the automated step.

A To-Be map that documents only happy paths is incomplete. The build team will invent exception handling on the fly, and the resulting Flows or Apex services will not be auditable.

### Automation-Tier Annotation Syntax

Every To-Be step must carry exactly one automation tier in square brackets at the end of the step label. The allowed values are:

- `[FLOW]` — a record-triggered, screen, or autolaunched Flow per `automation-selection.md` Q2/Q4/Q5.
- `[APEX]` — Apex trigger, service class, batch, or queueable per `automation-selection.md` Q3/Q6/Q10.
- `[APPROVAL]` — a Salesforce Approval Process per the cheat sheet in `automation-selection.md`.
- `[PLATFORM_EVENT]` — Platform Event publish or CDC subscriber per `automation-selection.md` Q11/Q12.
- `[INTEGRATION]` — a callout, inbound API call, MuleSoft orchestration, or Pub/Sub subscription. Pair with `integration-pattern-selection.md` for the specific pattern.
- `[MANUAL]` — the step is not automated. Required: a "why manual" annotation in the manual residue table.

A step labelled with two tiers is a routing failure. Re-run the decision tree until exactly one tier applies, or split the step into two.

### Handoff JSON Shape

The canonical handoff payload that downstream agents (`/build-flow`, `/build-agentforce-action`, `/design-object`) consume:

```json
{
  "process_id": "order-intake-2026q2",
  "scope": {
    "start_trigger": "Customer submits order form",
    "end_state": "Order activated in NetSuite and customer notified",
    "actors": ["Sales Ops", "Salesforce Platform", "NetSuite", "Customer"]
  },
  "as_is_steps": [
    {
      "step_id": "asis-001",
      "actor": "Sales Ops",
      "description": "Manually re-keys order from email into Salesforce",
      "pain_points": ["double entry", "no audit trail"]
    }
  ],
  "to_be_steps": [
    {
      "step_id": "tobe-001",
      "actor": "Salesforce Platform",
      "description": "Order auto-created from inbound API payload",
      "automation_tier": "INTEGRATION",
      "decision_tree_branch": "automation-selection.md Q11 → REST API + Apex custom endpoint",
      "recommended_agents": ["build-agentforce-action", "object-designer"]
    },
    {
      "step_id": "tobe-002",
      "actor": "Salesforce Platform",
      "description": "Validate credit limit on Account before activation",
      "automation_tier": "FLOW",
      "decision_tree_branch": "automation-selection.md Q2 → Before-save record-triggered Flow",
      "recommended_agents": ["build-flow"]
    }
  ],
  "manual_residue": [
    {
      "step_id": "manual-001",
      "description": "Sales Ops reviews flagged orders > $250k",
      "reason": "Regulatory: financial threshold requires human sign-off"
    }
  ],
  "exception_paths": [
    {
      "decision_id": "credit-check",
      "branches": [
        {"condition": "approved", "next_step": "tobe-002"},
        {"condition": "rejected", "next_step": "manual-001"},
        {"condition": "credit_service_timeout", "next_step": "tobe-fallback-001"}
      ]
    }
  ]
}
```

This shape is enforced by `scripts/check_process_map.py`.

---

## Common Patterns

### Pattern 1: As-Is Walkthrough → To-Be Re-Lane

**When to use:** The business has an existing process they describe verbally or in a flat SOP document. There is no diagrammed As-Is.

**How it works:**
1. Run a 60-minute walkthrough with the process owner and 2–3 front-line operators. Ask them to narrate one real instance end to end.
2. Capture every step on a sticky note (or row in a table). Annotate each with the actor, the action verb, and any system of record touched.
3. Group sticky notes into swim lanes by actor. Resist the temptation to group by phase — that hides responsibility transitions.
4. Mark every cross-lane transition (a handoff). Handoffs are where pain points cluster.
5. Document pain points per step explicitly: double entry, manual lookup, waiting for approval, missing audit trail.
6. Now produce the To-Be by re-laning: ask, for each As-Is handoff, "could the Salesforce platform lane absorb this step?" If yes, add it to the To-Be Salesforce Platform lane and tag it with the appropriate automation tier per `automation-selection.md`.

**Why not skip the As-Is:** A To-Be without an As-Is is not a process map — it is wishful thinking. The As-Is provides the ground truth of what currently happens, and the pain points justify each automation candidate. Skipping the As-Is is the single most common failure mode in process mapping projects.

### Pattern 2: Automation Candidate Annotation Pass

**When to use:** The To-Be diagram is drafted but steps are unannotated. Build team is asking "is this Flow or Apex?".

**How it works:**
1. For each To-Be step, walk through `standards/decision-trees/automation-selection.md` top-to-bottom. Stop at the first decision branch that resolves the technology choice.
2. Annotate the step with the tier in square brackets and the decision-tree branch citation.
3. If the step is a callout, also walk `integration-pattern-selection.md` and add a sub-tier annotation (e.g., `[INTEGRATION:REST]` vs `[INTEGRATION:PE]`).
4. If the step is async or scheduled, walk `async-selection.md` and tag the async pattern.
5. If a step has no clear tier (decision tree gives no answer), flag it as `[OPEN]` and add it to the open questions log. Do not guess.
6. Cross-check that the tier distribution is realistic. A To-Be that is 100% `[FLOW]` is suspicious — most processes have at least one `[APEX]`, `[INTEGRATION]`, or `[MANUAL]` step.

**Why not freestyle:** Without a decision-tree citation, two practitioners will reach different conclusions and the build team will inherit a routing argument. The tree is the tie-breaker.

### Pattern 3: Manual Residue as a First-Class Output

**When to use:** Stakeholders are pushing for "automate everything". The To-Be is starting to look like an unrealistic green field.

**How it works:**
1. List every step that is intentionally manual in the To-Be. Each row gets: step_id, actor, description, and a "why manual" reason chosen from: judgement call, regulatory requirement, low volume (not worth automating), high change cost (process is in flux).
2. Confirm each manual residue row with the process owner. Get an explicit "yes, this stays manual" sign-off.
3. Treat manual residue as a feature, not a gap. The map is honest about what humans still own.
4. Surface the manual residue list to the build agents — they need to know what NOT to attempt to automate.

**Why this matters:** "Automate everything" is the most expensive anti-pattern in Salesforce projects. Steps that involve human judgement, low-volume edge cases, or regulatory sign-off should remain manual. The map is more credible — and the build is faster — when manual residue is documented up front.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Customer fills out a form or signs a contract as part of the process | Add a Customer swim lane | Otherwise the customer-facing handoff is invisible; B2C maps fail without it |
| Two systems exchange data in the process (e.g., SF + ERP) | One swim lane per integration, named after the system | Lumping into one "Integration" lane hides handshake steps and exception paths |
| Decision diamond has only one outgoing branch | Re-frame — it is not a decision | A real decision has ≥2 branches; a single-branch "decision" is a step |
| Step is unclear whether Flow or Apex | Walk `automation-selection.md` until a branch resolves | The tree is authoritative; do not freestyle |
| Stakeholder wants every step automated | Push back with the manual residue concept | Some steps stay manual on purpose; the map must say so explicitly |
| Process spans more than 30 steps | Split into sub-processes with named handoff points | Maps over 30 steps lose readability and cannot be validated |
| External system can fail mid-process | Add an exception path with timeout / fallback | Happy-path-only maps fail at build when the dev asks "what if it times out?" |
| Step requires regulatory sign-off | Tag as `[APPROVAL]`, not `[FLOW]` | Approval Process gives auditability; Flow alone does not |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. **Identify actors and draw the swim lanes.** Confirm the four canonical actor categories: human roles, Salesforce platform, named integrations, customer / external counterparty. Add the customer lane explicitly even if the team did not mention it. Cap at 4–7 lanes; if more, the process scope is too broad and should be split.
2. **Map the As-Is steps and annotate pain points.** For every step, capture actor, action verb, system of record, and any pain point (double entry, waiting, manual lookup, missing audit). Mark every cross-lane transition as a handoff — handoffs are where automation value concentrates.
3. **Map the To-Be steps and annotate each with an automation tier.** For every step, walk `standards/decision-trees/automation-selection.md` top-to-bottom and tag with exactly one tier from the enum: `[FLOW]`, `[APEX]`, `[APPROVAL]`, `[PLATFORM_EVENT]`, `[INTEGRATION]`, `[MANUAL]`. Steps with no clear tier go to `[OPEN]` and the open questions log.
4. **Cite the automation-selection decision-tree branch per candidate.** Each automated step must list the specific tree question that resolved its tier (e.g., "automation-selection.md Q2 → Before-save record-triggered Flow"). This citation is what makes the map auditable — and what lets the build agents validate they followed the correct guidance.
5. **Flag manual residue with reasons.** Every step intentionally left manual gets a row in the manual residue table with one of: judgement call, regulatory, low volume, high change cost. Get explicit process-owner sign-off on each. Resist "automate everything" pressure.
6. **Document exception paths for every decision diamond and integration handshake.** The four canonical exception classes are timeout, validation rejection, authorization failure, manual override. Maps without these are incomplete.
7. **Hand off candidates to the matching run-time agent.** For each `[FLOW]` step, recommend `/build-flow`. For `[APEX]` steps, the appropriate apex builder. For `[APPROVAL]`, the approval-processes skill. For new objects implied by the To-Be, `/design-object`. For agent-driven steps, `/build-agentforce-action`. Produce the handoff JSON with `process_id`, `as_is_steps[]`, `to_be_steps[]`, each step carrying actor / description / automation_tier / recommended_agents[].

---

## Review Checklist

Run through these before marking the process map complete:

- [ ] Every swim lane has an explicit actor (role, platform, named integration, or customer)
- [ ] The customer / external-counterparty lane is present when the process touches a customer
- [ ] Every As-Is step has a pain-point annotation or is explicitly marked "no pain"
- [ ] Every To-Be step carries exactly one automation tier from the enum
- [ ] Every automated step cites the `automation-selection.md` branch that resolved its tier
- [ ] Every decision diamond has ≥2 outgoing branches with conditions labelled
- [ ] Every integration handshake has a timeout / fallback exception path
- [ ] Manual residue table is populated and signed off by the process owner
- [ ] Open questions log is empty (or every item has a named owner and target date)
- [ ] Handoff JSON validates against `scripts/check_process_map.py`
- [ ] Number of lanes is between 4 and 7; otherwise scope is split

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **The "Salesforce Platform" lane is not one thing — it covers Flow, Apex, validation rules, sharing, assignment rules, and approval processes** — Mapping every automated step into a single platform lane loses the tier distinction. Use the `[FLOW]` / `[APEX]` / `[APPROVAL]` annotations to preserve it. The build team needs to know which sub-tool to reach for.
2. **A process map with no `[APPROVAL]` tier is suspicious** — Most non-trivial business processes have at least one approval step (financial threshold, manager sign-off, regulatory review). Maps that show every approval as a `[FLOW]` typically miss the audit-trail and approver-history features the Approval Process gives for free.
3. **Integration steps must be paired with `integration-pattern-selection.md`** — Tagging a step `[INTEGRATION]` is not enough. The choice between REST callout, Bulk API, Platform Event, CDC, Pub/Sub, Salesforce Connect, and MuleSoft is itself a decision that the integration tree resolves. Skipping that resolution leaves the build team to guess.
4. **Backward branches in a decision diamond are silently allowed unless documented** — If a decision diamond's "No" branch loops back to an earlier step (a rework loop), the platform will not warn that this creates a potential infinite loop. The map must call out rework loops explicitly so the build team adds a circuit-breaker (e.g., a max-attempts counter on the record).
5. **Customer-facing steps that depend on email or portal action are not "automated" steps** — A step like "customer signs DocuSign" is the customer's action, not Salesforce's. It belongs in the Customer lane with no automation tier. Tagging it `[INTEGRATION]` because DocuSign is integrated is wrong — the integration is the callout, not the signing.
6. **Process maps drift during build unless versioned** — The most common failure: the As-Is map gets written, the team starts building, the To-Be evolves in conversation, and three weeks later nobody can find the version that drove the build. Commit the JSON handoff to source control alongside the build artifacts.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| As-Is process map | Mermaid swim-lane diagram with actor, action, system of record, and pain-point annotation per step |
| To-Be process map | Mermaid swim-lane diagram with each step annotated by automation tier and decision-tree citation |
| Automation candidate table | One row per automated To-Be step: step_id, actor, description, tier, decision-tree branch, recommended agent |
| Manual residue table | One row per intentionally-manual step: step_id, actor, description, "why manual" reason |
| Exception path catalogue | One row per decision diamond and integration handshake: timeout / validation / auth / override branches |
| Handoff JSON | Machine-readable payload conforming to `scripts/check_process_map.py` schema; consumed by `/build-flow`, `/build-agentforce-action`, `/design-object` |
| Open questions log | Unresolved tier choices or stakeholder disagreements with named owner and target resolution date |

---

## Related Skills

- requirements-gathering-for-sf — broader user-story-driven discovery; this skill produces the process-map artifact that requirements gathering references
- sales-process-mapping — sales-stage-specific variant; use when the process is opportunity stage progression
- fundraising-process-mapping — nonprofit donor stewardship variant
- fsl-scheduling-policies — FSL appointment scheduling variant
- persona-and-journey-mapping-sf — UI-side user journey companion; pair with this skill to cover both process and journey perspectives
- approval-processes — consumed by `[APPROVAL]`-tagged steps in the To-Be
- flow/record-triggered-flows — consumed by `[FLOW]`-tagged steps

## Related Decision Trees

- `standards/decision-trees/automation-selection.md` — primary tree for tier annotation
- `standards/decision-trees/async-selection.md` — for async / scheduled steps
- `standards/decision-trees/integration-pattern-selection.md` — for `[INTEGRATION]` step sub-tier
