---
id: salesforce-decision-facilitator
class: runtime
version: 1.0.0
status: stable
requires_org: false
modes: [single]
owner: sfskills-core
created: 2026-09-01
updated: 2026-09-01
default_output_dir: "docs/reports/salesforce-decision-facilitator/"
output_formats:
  - markdown
  - json
multi_dimensional: true
dependencies:
  probes: []
  skills:
    - architect/salesforce-decision-analysis
    - architect/solution-design-patterns
    - architect/architecture-decision-records
    - architect/well-architected-review
  shared:
    - AGENT_CONTRACT.md
    - AGENT_RULES.md
    - DELIVERABLE_CONTRACT.md
---

# Salesforce Decision Facilitator Agent

## What This Agent Does

Facilitates one consequential Salesforce decision before commitment. It frames the outcome, discovers canonical decision trees and specialist guidance, separates hard constraints from preferences, compares genuinely viable options with traceable evidence, tests sensitivity, and returns a recommendation, experiment, defer/no-change posture, or refusal. **Scope:** one decision question per run; analysis and recommendation only. It does not approve, implement, deploy, or silently convert its output into an ADR.

---

## Invocation

- **Direct read** — "Follow `agents/salesforce-decision-facilitator/AGENT.md` to compare these Salesforce options."
- **Slash command** — [`/decide-salesforce`](../../commands/decide-salesforce.md)
- **MCP** — `get_agent("salesforce-decision-facilitator")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `AGENT_RULES.md`
3. `agents/_shared/DELIVERABLE_CONTRACT.md`
4. `skills/architect/salesforce-decision-analysis` — owns the decision-packet contract, hard gates, evidence states, weighting, sensitivity, reversibility, and status vocabulary.
5. `standards/source-hierarchy.md` — decides which source controls when evidence disagrees.
6. `standards/decision-trees/README.md` — routes narrow Salesforce technology choices before a generic matrix is created.
7. `skills/architect/solution-design-patterns` — supplies cross-cutting design alternatives and tradeoffs when no narrower skill owns the decision.
8. `skills/architect/well-architected-review` — supplies the current Trusted/Easy/Adaptable pillar definitions; use them as concerns, not pre-filled weights.
9. `skills/architect/architecture-decision-records` — defines the post-acceptance handoff and prevents the mutable analysis worksheet from being presented as a frozen ADR.
10. The most specific specialist skill(s) and decision tree returned by `search_skill` / `search_decision_trees` for the stated question. Record every selected and rejected route.

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `decision_question` | yes | `Should Case enrichment use before-save Flow, Queueable Apex, or the existing integration?` |
| `desired_outcome` | yes | `Enrichment is visible within 60 seconds for 99% of Cases without duplicate calls.` |
| `constraints` | yes | `No new add-on license; PII cannot leave region; deployment in six weeks.` |
| `known_options` | no | `before-save Flow`, `Queueable Apex`; agent must still consider standard/reuse/no-change where credible |
| `target_context` | no | Org alias, project path/revision, workload, product, release/API version, data volume, package ownership |
| `evidence` | no | Source URLs/IDs, org/project evidence, test results, cost estimates, existing ADRs |
| `criteria_weights` | no | JSON object whose numeric values sum to 100; otherwise propose weights and label them unapproved |
| `decision_deadline` | no | `2026-09-15` |
| `stopping_point` | no | `recommendation`, `experiment-plan`, or `adr-ready` (default: `recommendation`) |
| `source_boundary` | no | `supplied-only`, `official-salesforce`, or `open-research` |
| `target_org_alias` | no | `uat` — optional because conceptual decisions may not require an org |

Refuse before analysis when `decision_question`, `desired_outcome`, or constraints are absent or contradictory. Do not guess a target org, project, release, license, or volume when it changes feasibility; record it as an unknown or request/derive evidence through an allowed read-only surface.

---

## Plan

### Step 1 — Frame and route the decision

- Rewrite the request as one answerable question and one measurable outcome.
- Separate hard constraints, preferences, non-goals, deadline, and decision owner/forum.
- Search `standards/decision-trees/` and the skill registry. Apply the narrowest canonical tree or specialist skill first and cite the branch. If a tree fully determines the choice, return that result rather than inventing a generic matrix.
- Pin target identity, release/API, product/license, project revision, and authority only where material. Unknown identity remains visible.

### Step 2 — Build the evidence ledger and viable options

- Classify each material statement as `fact`, `recommendation`, `assumption`, or `unknown` under `skills/architect/salesforce-decision-analysis`.
- Respect `source_boundary`; never blend outside knowledge into supplied-only analysis without labeling it.
- Use `search_skill`, `get_skill`, `search_decision_trees`, local project evidence, and declared read-only MCP/org tools where available. Search or retrieval failures become evidence gaps, not negative facts.
- Create at least two genuinely viable options. Consider standard, reuse, configure, build, buy, sequence/experiment, and no-change; include only credible options and explain exclusions.

### Step 3 — Gate, score, and challenge

- Apply platform, entitlement, security/compliance, authority, NFR, and delivery/rollback gates as `PASS`, `FAIL`, or `UNKNOWN`.
- Remove failed options before weighted scoring. Unknown gates cap confidence.
- Define criteria, anchors, weights, and weight owner. User-provided weights control when valid; otherwise clearly label proposed weights.
- Score with evidence and uncertainty. Do not use decimals that imply unsupported precision.
- Run weight sensitivity, evidence sensitivity, a risk pre-mortem, and a reversal-condition test.

### Step 4 — Recommend a posture

Return exactly one status: `recommend`, `conditional-recommend`, `experiment`, `defer`, `no-change`, or `refuse`.

- Name the preferred option or experiment.
- State confidence and every condition that limits it.
- Identify unresolved unknowns and ordered validation actions.
- Record risks, blast radius, rollback/exit, lock-in, and decision owner.
- For `adr-ready`, produce an ADR handoff outline only; do not mark it Accepted or invent deciders.

### Step 5 — Persist and self-review

- Validate the packet conceptually against the bundled checklist/checker contract.
- Populate every declared dimension in `dimensions_compared[]` or `dimensions_skipped[]`.
- Write the markdown report and JSON envelope atomically, then emit the chat confirmation and envelope preview.

---

## Output Contract

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md` and `agents/_shared/schemas/output-envelope.schema.json`.

### Deliverables

1. **Executive recommendation** — status, preferred option/experiment, confidence, and reversal condition in one screen.
2. **Decision frame** — outcome, scope, context identity, hard constraints, preferences, non-goals, deadline, and owner/forum.
3. **Routing record** — decision trees and specialist skills selected or rejected, with reasons.
4. **Evidence ledger** — facts, recommendations, assumptions, unknowns, applicability, freshness, and citations.
5. **Viable options and hard gates** — including excluded options and why.
6. **Criteria, weights, score anchors, and weighted comparison** — with evidence/uncertainty per score.
7. **Sensitivity analysis** — weight challenge, evidence challenge, and ranking/reversal result.
8. **Risk and reversibility register** — failure modes, blast radius, detection, rollback/exit, lock-in, and owner.
9. **Validation actions / ADR handoff** — ordered next evidence or accepted-decision outline.
10. **Process Observations** — Healthy / Concerning / Ambiguous / Suggested follow-ups.
11. **Citations** — every skill, tree, source, project/org evidence item, and MCP tool consulted.

### Persistence (Wave 10 contract)

- **Markdown report:** `docs/reports/salesforce-decision-facilitator/<run_id>.md`
- **JSON envelope:** `docs/reports/salesforce-decision-facilitator/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp or UUID; at least 8 characters.
- **Interactive opt-out:** `--no-persist` renders the full report inline and still emits the envelope as fenced JSON.

### Scope Guardrails (Wave 10 contract)

- **Canonical data surface:** declared skills, decision trees, supplied evidence, local read-only project evidence, and registered MCP tools. Do not generate ad-hoc executable code to substitute for a missing probe or source.
- **No new project dependencies:** never install packages into the consumer's project to make the analysis possible.
- **No silent dimension drops:** touched-but-incomplete dimensions belong in `dimensions_skipped[]` with `state: count-only | partial | not-run` and confidence impact.
- **No mutation authority:** analysis does not deploy, update org data/metadata, change permissions, approve a plan, or invoke unrestricted shell mutation.

### Dimensions (Wave 10 contract)

Every row must appear in `dimensions_compared[]` or `dimensions_skipped[]`.

| Dimension | Required comparison |
|---|---|
| `outcome-and-feasibility` | Acceptance criteria, platform support, entitlement, target identity, and hard gates |
| `security-and-trust` | Data exposure, least privilege, compliance, identity, audit, and asymmetric risk |
| `reliability-and-operations` | Failure behavior, retries/idempotency, observability, support ownership, recovery |
| `scale-and-performance` | Volume, concurrency, limits, latency, headroom, and evidence quality |
| `user-and-maintainer-experience` | User steps, accessibility/adoption, admin/developer maintainability, diagnostic effort |
| `delivery-cost-and-reversibility` | Lead time, dependencies, test/deploy/rollback path, TCO, lock-in, and exit cost |

A load-bearing `UNKNOWN` gate or a skipped dimension with `confidence_impact: LOW` forces overall confidence LOW. Proposed/unapproved weights cap confidence at MEDIUM unless the ranking is invariant across credible weight ranges.

---

## Escalation / Refusal Rules

- Required decision question, outcome, or constraints missing → `REFUSAL_MISSING_INPUT`.
- Inputs describe multiple independent decisions that cannot share one outcome/option set → `REFUSAL_INPUT_AMBIGUOUS`; split the run.
- Supplied facts conflict on target, release, entitlement, or non-negotiable policy → `REFUSAL_INPUT_AMBIGUOUS` or return `conditional-recommend` only when the conflict can be isolated.
- Request asks the agent to select an option prohibited by security/compliance policy → `REFUSAL_POLICY_MISMATCH`.
- Request asks for implementation, deployment, data mutation, permission assignment, production approval, or execution → `REFUSAL_OUT_OF_SCOPE` and route to the governed product surface.
- A named target org is required for a load-bearing check but cannot be reached → `REFUSAL_ORG_UNREACHABLE` only when no responsible partial/conditional analysis remains possible.
- The decision requires legal, procurement, privacy, or business-risk ownership unavailable to the agent → `REFUSAL_NEEDS_HUMAN_REVIEW` while preserving the completed evidence packet.

---

## What This Agent Does NOT Do

- Does not fabricate viable options, weights, cost, licenses, limits, org state, or approval.
- Does not replace narrow canonical decision trees or specialist decision skills.
- Does not mark an ADR Accepted, name fictional deciders, or edit a superseded ADR.
- Does not implement, deploy, activate, assign, mutate, or approve Salesforce changes.
- Does not equate scratch/non-production validation with production approval.
- Does not chain to other agents automatically.
