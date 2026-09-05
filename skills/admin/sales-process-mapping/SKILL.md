---
name: sales-process-mapping
description: "Eliciting and documenting a sales process before it is built in Salesforce: stage sequencing, entry/exit criteria per stage, win/loss analysis requirements, and stage transition rules. Trigger keywords: sales process design, stage discovery, entry criteria, exit criteria, stage gate, win/loss categorisation, sales methodology, pipeline stages, opportunity stage mapping, stage ladder, probability ladder, forecast category mapping, required fields per stage, stage swim lane, discovery workshop, handoff brief. NOT for configuring OpportunityStage, Sales Processes or Path in Setup — use admin/opportunity-management. NOT for cross-functional swim-lane maps — use admin/process-flow-as-is-to-be."
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
  - "map a sales process before anyone configures opportunity stages"
  - "define entry and exit criteria for every opportunity stage"
  - "reps park deals in one stage and the forecast has stopped meaning anything"
  - "decide whether new logo and renewal need separate sales processes"
  - "work out which fields must be required at each sales stage"
  - "design win and loss reason picklist values for closed opportunities"
  - "run a sales process discovery workshop with the VP of Sales"
  - "build a stage-by-stage swim lane showing who does what in Salesforce"
  - "produce a handoff brief the admin can configure opportunity stages from"
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
  - "Machine-readable stage map (YAML or CSV) that scripts/check_sales_process_mapping.py --map lints"
  - "Handoff brief for the opportunity-management skill (stage names, process count, record type needs)"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
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

## Questions to Ask Before Configuring

Ask these before anyone opens Setup. Each one exists because a specific platform
behaviour punishes the default answer; the right-hand column is what the answer
changes in `templates/sales-process-mapping-template.md`.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Walk me through the last deal you lost at proposal — what happened first?" | Stated criteria are aspirational; loss narratives expose the gate that actually existed | Rewrites one exit criterion into something observable, and usually one required field |
| "Who is allowed to move a deal into Negotiation, and who actually does?" | The platform allows backward and skipped moves silently — only a rule stops it | The owner per stage, and either a validation-rule row or a decision not to enforce |
| "Do renewals run these same stages, or does the CSM run something else?" | Two sequences means two Sales Processes, and `businessProcess` is required on an Opportunity record type (api_meta.txt:45007–45014) | The record type count — the largest cost line in the handoff brief |
| "When a deal closes, who has to know, and what do they need from the record?" | The Closed Won exit obligations (onboarding Case, Contract, booking) get built by nobody unless they are stage requirements | The Sales → Service and Sales → Finance handoff rows and their fields |
| "Which team must *not* see the other team's pipeline?" | Record types and business processes do not govern read access (api_meta.txt:42960–42962, 44974–44980) | Moves the requirement out of the stage map into `standards/decision-trees/sharing-selection.md` |
| "What does the board pack call each forecast bucket?" | Only the documented `ForecastCategoryName` values exist (object_reference.txt:195492–195504) | The internal-label ↔ platform-value translation table, or a separate forecast session |
| "How do deals actually get closed — rep in the UI, manager bulk edit, or a load?" | Close-path assumptions decide whether a validation rule is sufficient enforcement | The enforcement mechanism per rule, rather than "validation rule" by reflex |

What a proper configuration adds over just doing it: the stage ladder ships with an owner, an observable exit condition and a field requirement per stage, so the forecast means something on day one and the Service and Finance handoffs exist before the first deal closes.

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

| Rule | Behavior |
|---|---|
| Linear progression only | The opportunity must move through stages in order (no skipping). |
| Backward movement restricted | Once past a stage, the opportunity cannot return without manager approval. |
| Required fields per stage | Certain fields must be populated before an opportunity can be saved at or past a given stage. |
| Stage-triggered notifications | Advancing to a specific stage sends an alert to legal, finance, or deal desk. |

Documenting these rules in the mapping artefact is critical because Salesforce does not enforce stage order natively — Path is visual only. Enforcement requires validation rules, and those rules are only as good as the transition requirements that were documented during the mapping exercise.

### Mapping to Platform Constraints

During the mapping exercise the practitioner must track which design decisions will hit Salesforce platform limits or constraints. Key constraints to flag:

- **ForecastCategoryName is a fixed, documented value set**: `Best Case`, `Closed`, `Commit`, `Most Likely`, `Omitted`, `Pipeline` (object_reference.txt:195492–195504). They cannot be renamed, and the deployed metadata spells them differently again — see `references/gotchas.md` Gotcha 6. Every stage must map to one of these; if the business uses different category names in its forecast process, a translation layer must be documented.
- **Stage picklist values are global**: every stage defined in the mapping becomes a global picklist value. Stage names that are too generic (e.g., "Stage 1") will conflict with other business units if the org is shared.
- **Multiple Sales Processes require multiple Record Types**: if the mapping produces two distinct stage sequences, two Sales Processes and two Record Types are required in Salesforce. The mapping document should flag this dependency explicitly.

---

## Common Patterns

### Discovery-First Stage Mapping

**When to use:** The business has informal stages (whiteboard, verbal, legacy CRM) but no documented entry/exit criteria. The practitioner needs to produce a formal stage map before any Salesforce work can begin.

**How it works:**
1. Run a structured discovery session (60–90 minutes) with the VP of Sales and 2–3 front-line AEs. Use the Stage Map Template (see `templates/`). Ask for each stage: "What has to be true before a deal enters this stage?" and "What has to happen before the deal can leave?"
2. Document every stage with a plain-language definition, entry criteria, exit criteria, and the role responsible for advancing the stage.
3. For each stage, ask which Salesforce forecast category it should map to. Explain the values plainly: Pipeline (actively working), Best Case (likely to close), Commit (near-certain), Most Likely (available to orgs using the extra tier), Closed (done), Omitted (not forecast). Let the sales leader assign each stage.
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

1. **Count the motions, then open the template.** Copy `templates/sales-process-mapping-template.md` and fill the Selling Motions table first. Every motion that diverges at more than two stages becomes its own stage sequence — and, because `businessProcess` is required on an Opportunity record type, its own record type. Get that number agreed before booking discovery time.
2. **Run the discovery sessions off the question table.** Use `## Questions to Ask Before Configuring` above and §6 of `references/worked-examples.md` as the agenda. Interview sales leadership and front-line AEs separately; where their answers diverge, that gap is the finding, not noise.
3. **Write the ladder as a machine-readable map, not prose.** Fill the stage map in the shape of §2 of `references/worked-examples.md` — one entry, one exit, a `ForecastCategoryName` value, a probability, an owner persona and at least one required field per stage, terminal stages included.
4. **Lint it before anyone reads it.** `python3 scripts/check_sales_process_mapping.py --map <your-map>.yaml` (or `--manifest-dir <design-dir>` to lint every map plus a retrieved stage value set). Fix every ERROR: a missing exit criterion, a non-monotonic probability, two stages exiting on the same condition and a stage with no required field are all design defects, not formatting complaints.
5. **Turn transition rules into enforcement intent.** For every restriction, write the row shape in §3 of `references/worked-examples.md`: where it fires, the condition in words, the rep-facing message. Decide once — in the mapping — how "at or past stage X" will be represented, because `StageName` is a picklist and gives you no ordering for free.
6. **Design the win/loss taxonomy and its capture path.** 5–8 values per outcome, always including "No Decision / Status Quo", plus the answer to how deals actually get closed. Run the narrative document through `python3 scripts/check_sales_process_mapping.py --doc <document>.md` to catch an oversized taxonomy, a catch-all "Other", a free-text fallback or Path-enforcement language.
7. **Read `references/gotchas.md`, then produce the handoff brief.** Close the open-questions log, and hand `admin/opportunity-management` the exact picklist strings, the process and record type count, the per-record-type stage availability matrix, and the validation rules the ladder implies.

## Review Checklist

Run through these before marking work in this area complete:

- [ ] The stage map exists as a machine-readable artefact and `python3 scripts/check_sales_process_mapping.py --map <map>` reports no ERROR
- [ ] Every stage has a plain-language definition, entry criteria, and exit criteria documented
- [ ] Every stage is assigned to exactly one documented `ForecastCategoryName` value, spelled as the label and not as the metadata token
- [ ] Win/loss reason taxonomy is finalised (5–8 values per outcome), capture point is defined, enforcement method is documented
- [ ] Stage transition rules are documented: which transitions are blocked, which require fields, which require approvals
- [ ] Open questions log has no unresolved items (or all unresolved items have a named owner and target date)
- [ ] Number of distinct sales processes required is confirmed and matches the number of distinct stage sequences
- [ ] Stage names in the handoff brief are the exact strings that should appear as Salesforce picklist values
- [ ] If a named methodology (MEDDIC, SPIN, Challenger) is in use, its components are explicitly mapped to stage entry criteria in the document
- [ ] The handoff brief carries a per-record-type stage availability matrix, not just a flat stage list — see `references/gotchas.md` Gotcha 7
- [ ] Any visibility requirement voiced in the workshop has been moved out of the stage map and routed to `standards/decision-trees/sharing-selection.md`

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **ForecastCategoryName values cannot be renamed** — The documented value set (`Best Case`, `Closed`, `Commit`, `Most Likely`, `Omitted`, `Pipeline`) is fixed. If the business uses different labels in their forecasting process (e.g., "Called" instead of "Commit"), those translations must be documented during mapping. Many mapping exercises skip this and produce stage-to-forecast assignments that confuse reps when they see different labels in the UI than in the mapping document.

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

## Reference Files

| File | Read it when |
|---|---|
| `references/worked-examples.md` | Building the artefacts — a B2B SaaS swim lane, the stage ladder in YAML and CSV, validation-rule intent, the record-type decision, the deployable stage value set, and the workshop question set |
| `references/gotchas.md` | Before finalising a stage map — nine platform behaviours that turn a plausible mapping document into a broken configuration |
| `references/examples.md` | Two worked engagements: new-logo vs renewal separation, and MEDDIC components used as stage entry criteria |
| `references/well-architected.md` | Pillar mapping, the tradeoffs behind one process vs many, and the sources every platform claim in this package rests on |
| `references/llm-anti-patterns.md` | Self-checking generated output — the six ways an assistant gets sales process mapping wrong |
| `templates/sales-process-mapping-template.md` | Running the engagement: motions, stage map, transition rules, win/loss taxonomy, open questions, handoff brief |
| `scripts/check_sales_process_mapping.py` | Linting the stage map (`--map`), the narrative document (`--doc`), or a whole design directory (`--manifest-dir`) |

---

## Related Skills

- admin/opportunity-management — use after this skill completes; it consumes the handoff brief and owns the `BusinessProcess`, `RecordType` and `PathAssistant` XML
- admin/picklist-and-value-sets — owns the `OpportunityStage` standard value set once the stage names are agreed
- admin/validation-rules — turns the §3 enforcement intent into formulas, including the `PRIORVALUE` backward-movement pattern
- admin/record-types-and-page-layouts — the record type and layout work that a second sales process forces
- admin/record-type-strategy-at-scale — use when the mapping produces multiple processes and the org's record type budget is already tight
- admin/path-and-guidance — use after opportunity-management to layer visual guidance on the configured stages
- admin/process-flow-as-is-to-be — use for the step-anchored As-Is/To-Be swim lane with exception paths; this skill only maps the stage-anchored lane
- admin/pipeline-review-design — use once the ladder is live, to inspect the distribution across the stages it created
- admin/collaborative-forecasts — use when the forecast category assignments need wiring into forecast types and rollups
- admin/quote-to-cash-process — owns the Quote → Contract handoff that the Closed Won exit criterion points at
- admin/case-management-setup — owns the onboarding Case that the Sales → Service handoff creates
- admin/requirements-gathering-for-sf — use when this mapping is one component of a larger requirements discovery effort
