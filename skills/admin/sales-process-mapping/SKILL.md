---
name: sales-process-mapping
description: "Eliciting, documenting, and structuring a sales process before it is built in Salesforce: stage sequencing, entry/exit criteria per stage, win/loss analysis requirements, and stage transition rules. Use when a business needs to analyse or formalise its sales methodology before any Salesforce configuration begins. Trigger keywords: sales process design, stage discovery, entry criteria, exit criteria, stage gate, win/loss categorisation, sales methodology, pipeline stages, opportunity stage mapping. NOT for configuring OpportunityStage picklist values, Sales Processes, or record types in Setup (use opportunity-management skill). NOT for Path configuration. NOT for Collaborative Forecasts or quota alignment."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - User Experience
triggers:
  - "We need to figure out what our sales stages should be before we build anything in Salesforce"
  - "The sales team argues about what Closed Won means — how do we define stage exit criteria?"
  - "We want to add a win/loss reason field but aren't sure what categories to use or when to require them"
  - "Our VP of Sales wants a stage gate process documented before we configure Salesforce"
  - "How do we map our existing sales methodology (MEDDIC, SPIN, Challenger) to Salesforce opportunity stages?"
tags:
  - sales-process
  - stage-design
  - entry-exit-criteria
  - win-loss-analysis
  - stage-gate
  - sales-methodology
  - opportunity-stages
  - discovery
  - admin
inputs:
  - "Current sales methodology name and a rough description of the selling motion (transactional, enterprise, channel, renewal)"
  - "Names and rough descriptions of stages used today (whiteboard, spreadsheet, or verbal — any form)"
  - "Which roles participate in the deal at each stage (AE, SE, Legal, Finance)"
  - "Win/loss reason taxonomy if one exists, even informally"
  - "Whether distinct business motions exist (e.g., new logo vs. renewal vs. upsell) that would need separate stage sequences"
outputs:
  - "Stage map document: ordered stage list with definition, entry criteria, exit criteria, and primary owner per stage"
  - "Win/loss reason category list with a recommendation on where and when to capture them in Salesforce"
  - "Stage transition rule table: which transitions are allowed, which require field completion, which require manager approval"
  - "Open questions log for items that need stakeholder resolution before Salesforce configuration begins"
  - "Handoff brief for the opportunity-management skill (stage names, process count, record type needs)"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Sales Process Mapping

This skill activates when a practitioner needs to design or document a sales process as a structured artefact before any Salesforce configuration work begins. It covers discovery interviews, stage sequencing, entry/exit criteria definition, win/loss requirement analysis, and transition rule documentation. The output is a mapping document that the opportunity-management skill then uses as its input specification.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm how many distinct selling motions the business runs (new logo, renewal, upsell, channel). Each motion that diverges meaningfully at more than two stages needs its own stage sequence — and eventually its own Salesforce Sales Process.
- Identify who owns the definition of each stage. In most organisations the VP of Sales or RevOps lead is the decision authority; without their involvement, agreed-on definitions will not be adopted by the sales team.
- Establish whether a named sales methodology (MEDDIC, MEDDPICC, SPIN, Challenger, Value Selling) is in use or intended. Methodology constrains stage names and entry criteria. If the business has no methodology, the mapping exercise will need to establish one — that is a larger consulting engagement than a configuration task.
- Determine whether win/loss analysis is currently tracked anywhere (CRM, spreadsheet, survey tool). If it is, obtain the existing reason taxonomy before proposing a new one. Replacing an established taxonomy breaks trend reporting.
- Ask whether the sales stages are tied to a quoting or CPQ process. If a quote must be sent before a stage can advance, a CPQ dependency exists and must be noted in the transition rules.

---

## Core Concepts

### Stage as a Gate, Not a Label

A stage in a well-designed sales process represents a verified milestone — a point at which the deal has cleared a defined bar — not simply a label that the rep drags the opportunity to when the mood is right. Each stage must have explicit entry criteria (what must be true before the deal enters this stage) and exit criteria (what must be true before the deal can leave). Without both, stage data degrades quickly: reps park deals in whichever stage looks best for the forecast and move on.

In Salesforce terms, entry criteria become the driver for required fields on the record at that stage (enforced via validation rules). Exit criteria become the condition the rep must satisfy before the stage can advance. Documenting both in plain language during discovery is what makes the subsequent validation rule design deterministic rather than guesswork.

### Win/Loss Analysis as a First-Class Requirement

Win/loss analysis is the closed-loop mechanism that tells the business whether its sales process is working. It depends on three design decisions made during the mapping exercise:

1. **Category taxonomy**: what are the allowable win reasons and loss reasons? A good taxonomy has 5–10 mutually exclusive, collectively exhaustive categories per outcome, not a free-text field.
2. **Capture point**: at what stage transition does the rep record the reason? Almost always this is the transition to Closed Won or Closed Lost. Capturing it too early (e.g., at Proposal) means the reason changes; too late means it never gets filled in.
3. **Who owns the data**: is win/loss self-reported by the rep, validated by the manager, or collected via an external survey? Self-reported data has selection bias; external surveys have response rate issues. Document the chosen approach explicitly.

In Salesforce, win/loss reasons are typically implemented as a required dependent picklist on Opportunity (primary picklist: Stage outcome; dependent: specific reason) or as a required custom field enforced by a validation rule on close. The mapping document must specify which approach is needed so the configuration can be designed correctly.

### Stage Transition Rules

A stage transition rule defines which movements are valid, which require field completion, and which require an additional approval or review. Common transition rules include:

- **Linear progression only**: the opportunity must move through stages in order (no skipping).
- **Backward movement restricted**: once past a stage, the opportunity cannot return without manager approval.
- **Required fields per stage**: certain fields must be populated before an opportunity can be saved at or past a given stage.
- **Stage-triggered notifications**: advancing to a specific stage sends an alert to legal, finance, or deal desk.

Documenting these rules in the mapping artefact is critical because Salesforce does not enforce stage order natively — Path is visual only. Enforcement requires validation rules, and those rules are only as good as the transition requirements that were documented during the mapping exercise.

### Mapping to Platform Constraints

During the mapping exercise the practitioner must track which design decisions will hit Salesforce platform limits or constraints. Key constraints to flag:

- **ForecastCategoryName is fixed**: the five platform values (Pipeline, Best Case, Commit, Closed, Omitted) cannot be renamed. Every stage must map to one of these. If the business uses different category names in their forecast process, a translation layer must be documented.
- **Stage picklist values are global**: every stage defined in the mapping becomes a global picklist value. Stage names that are too generic (e.g., "Stage 1") will conflict with other business units if the org is shared.
- **Multiple Sales Processes require multiple Record Types**: if the mapping produces two distinct stage sequences, two Sales Processes and two Record Types are required in Salesforce. The mapping document should flag this dependency explicitly.

---

## Common Patterns

### Discovery-First Stage Mapping

**When to use:** The business has informal stages (whiteboard, verbal, legacy CRM) but no documented entry/exit criteria. The practitioner needs to produce a formal stage map before any Salesforce work can begin.

**How it works:**
1. Run a structured discovery session (60–90 minutes) with the VP of Sales and 2–3 front-line AEs. Use the Stage Map Template (see `templates/`). Ask for each stage: "What has to be true before a deal enters this stage?" and "What has to happen before the deal can leave?"
2. Document every stage with a plain-language definition, entry criteria, exit criteria, and the role responsible for advancing the stage.
3. For each stage, ask which of the five Salesforce forecast categories it should map to. Explain the five values plainly: Pipeline (actively working), Best Case (likely to close), Commit (near-certain), Closed (done), Omitted (not forecast). Let the sales leader assign each stage.
4. Identify all transition rules: which stage jumps are blocked, which require additional fields, which require manager sign-off.
5. Document open questions (anything stakeholders disagree on) separately. Do not proceed to configuration until these are resolved.
6. Produce the Stage Map Document as the output. Hand it to the opportunity-management skill as the specification input.

**Why not skip to configuration:** Configuring stages without agreed-on entry/exit criteria means the rep community will not adopt the process. Re-configuring after go-live is expensive and creates data integrity problems for historical records.

### Win/Loss Reason Design

**When to use:** The business wants to track why deals are won or lost, but has no existing reason taxonomy or has a taxonomy that is too granular to be useful (more than 15 values).

**How it works:**
1. Interview the VP of Sales and at least two deal-experienced AEs separately. Ask each to name the top five reasons they think deals are won and lost, without prompting.
2. Cluster the responses into themes. A healthy taxonomy has 5–8 win reasons and 5–8 loss reasons, each representing a meaningfully distinct cause.
3. For loss reasons, always include a "No Decision / Status Quo" category — deals where the prospect did not choose any vendor. This is the most commonly omitted category.
4. Decide the capture point and enforcement mechanism. Recommend: required picklist on Opportunity, enforced by validation rule only when StageName = 'Closed Won' or StageName = 'Closed Lost'.
5. Decide who validates the data. If managers will review and override rep-entered reasons, document this as a workflow step.
6. Record the final taxonomy and all design decisions in the mapping document.

**Why not use a free-text field:** Free-text win/loss fields produce unusable data within 3 months. Analysis is impossible without normalization. A constrained picklist with a defined taxonomy is always the right choice.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Business has one selling motion | Single stage sequence, single Sales Process | No need to separate processes; keep it simple |
| New logo and renewal have divergent stages past Proposal | Two separate stage sequences, two Sales Processes | Stage names and forecast category mappings differ; a shared process creates confusion |
| Stage names already exist in legacy CRM | Keep names where possible, add entry/exit criteria | Changing stage names mid-cycle creates adoption friction; criteria can be added without renaming |
| Business wants to enforce stage order | Document as transition rule; implement as validation rule — not Path | Path does not block saves; validation rules do |
| Win/loss taxonomy has more than 12 values | Consolidate to 5–8 per outcome | Large taxonomies are not completed consistently; data quality degrades |
| Business uses MEDDIC methodology | Map MEDDIC components to stage entry criteria | MEDDIC identifies what must be confirmed at each stage — use components as entry criteria directly |
| Stakeholders disagree on stage definitions | Document the disagreement, escalate to VP of Sales, do not configure until resolved | Configuration built on disputed definitions requires rework; the mapping exercise forces the decision |
| Stage must trigger a downstream process (e.g., legal review) | Document as a stage-triggered notification or approval requirement | This becomes a Flow or Approval Process requirement passed to the implementation phase |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm scope and motion count.** Identify how many distinct selling motions exist. For each motion, confirm whether it needs its own stage sequence. Document the motion name, deal type, and typical deal size and length for context.
2. **Run stage discovery sessions.** Use the Stage Map Template. For each stage, elicit: definition, entry criteria, exit criteria, primary owner, and approximate probability. Do this with both sales leadership and front-line reps — their views often diverge and the divergence is important signal.
3. **Map stages to platform constraints.** For each stage, assign one of the five ForecastCategoryName values (Pipeline, Best Case, Commit, Closed, Omitted). Flag any stage where stakeholders want a forecast category that does not exist — document the gap and explain the platform constraint.
4. **Document transition rules.** For each stage boundary, record: is forward progression enforced? Is backward movement allowed? Which fields must be populated? Which transitions trigger a notification or approval? Flag transitions that will require validation rules or flows — these become configuration requirements.
5. **Design the win/loss taxonomy.** Run the win/loss interview pattern. Produce a final taxonomy of 5–8 win reasons and 5–8 loss reasons. Decide capture point, enforcement method, and data owner. Document in the mapping artefact.
6. **Log open questions and resolution owners.** Any item stakeholders could not agree on goes into the open questions log with a named owner and a target resolution date. The mapping document is not complete until all questions are resolved.
7. **Produce the handoff brief.** Summarise the stage sequences, motion count, transition rules, and win/loss taxonomy in a one-page handoff brief formatted as input to the opportunity-management skill. Include the stage names exactly as they should appear in Salesforce (this is the source of truth for the global picklist values).

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Every stage has a plain-language definition, entry criteria, and exit criteria documented
- [ ] Every stage is assigned to exactly one of the five ForecastCategoryName values
- [ ] Win/loss reason taxonomy is finalised (5–8 values per outcome), capture point is defined, enforcement method is documented
- [ ] Stage transition rules are documented: which transitions are blocked, which require fields, which require approvals
- [ ] Open questions log has no unresolved items (or all unresolved items have a named owner and target date)
- [ ] Number of distinct sales processes required is confirmed and matches the number of distinct stage sequences
- [ ] Stage names in the handoff brief are the exact strings that should appear as Salesforce picklist values
- [ ] If a named methodology (MEDDIC, SPIN, Challenger) is in use, its components are explicitly mapped to stage entry criteria in the document

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **ForecastCategoryName values cannot be renamed** — The five platform values (Pipeline, Best Case, Commit, Closed, Omitted) are hardcoded. If the business uses different labels in their forecasting process (e.g., "Called" instead of "Commit"), those translations must be documented during mapping. Many mapping exercises skip this and produce stage-to-forecast assignments that confuse reps when they see different labels in the UI than in the mapping document.

2. **Stage picklist values are global across all Opportunity record types** — Every stage name defined in the mapping becomes a global picklist entry visible across the entire org. Generic names like "Stage 3" or "Prospecting" create ambiguity when multiple business units share the org. The mapping exercise must produce stage names that are unambiguous across all business units, not just the one being mapped.

3. **Path adds no enforcement — the mapping document must flag enforcement requirements explicitly** — A common handoff failure is delivering a stage map that lists "required fields" per stage without flagging that Path alone will not enforce them. If the document does not explicitly state that a validation rule is needed, the configuration team may use Path guidance only and leave the enforcement gap open.

4. **Backward movement is silently allowed unless a validation rule blocks it** — Salesforce allows reps to move an opportunity from Closed Won back to Negotiation without any warning. If the mapping exercise documents a rule like "no backward movement past Proposal without manager approval", that rule must be translated into an explicit validation rule or approval process requirement in the handoff brief — the platform will not honour it otherwise.

5. **Win/loss capture point timing affects data completeness** — If the win/loss reason field is required only on close (StageName = Closed Won or Closed Lost), reps often close deals by skipping the requirement via mass update or bulk edit, bypassing the validation rule. The mapping document should note whether the win/loss field needs additional enforcement (e.g., manager-only close permission) to prevent this gap.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Stage map document | Ordered stage list with definition, entry criteria, exit criteria, ForecastCategory assignment, owner, and default probability per stage |
| Win/loss taxonomy table | Final reason categories (win and loss), capture point, enforcement method, and data owner |
| Transition rules table | All stage boundaries with allowed direction, required fields, and notification/approval triggers |
| Open questions log | Unresolved items from discovery with named owner and target resolution date |
| Handoff brief | One-page summary of stage names (exact picklist-ready strings), process count, and transition rule summary formatted as input to the opportunity-management skill |

---

## Related Skills

- opportunity-management — use after this skill completes; it consumes the handoff brief as its input specification and performs the Salesforce configuration
- requirements-gathering-for-sf — use when the sales process mapping is one component of a larger requirements discovery effort
- path-and-guidance — use after opportunity-management to add visual stage guidance layered on top of the configured stages
- record-type-strategy-at-scale — use when the mapping produces multiple sales processes and record type design decisions need to be made at org scale
- collaborative-forecasts — use after opportunity-management when the forecast category assignments from the mapping document need to be wired into Collaborative Forecasting types
