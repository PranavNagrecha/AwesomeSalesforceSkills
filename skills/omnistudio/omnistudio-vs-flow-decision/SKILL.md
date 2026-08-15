---
name: omnistudio-vs-flow-decision
description: "Use when choosing between OmniStudio (OmniScript / Integration Procedure / FlexCard / DataRaptor) and Flow / Screen Flow / Apex for a given capability. Triggers: 'omnistudio or flow', 'omniscript vs screen flow'. NOT for general automation selection (use admin/process-automation-selection) — use architect/omnistudio-vs-standard-decision."
category: omnistudio
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
  - Performance
triggers:
  - "should this be an omniscript or a screen flow"
  - "integration procedure or invocable apex"
  - "flexcard vs custom lwc"
  - "dataraptor extract vs soql in flow"
  - "when is omnistudio the wrong choice"
tags:
  - omnistudio
  - flow
  - tool-selection
  - decision-tree
  - architecture
inputs:
  - "capability description and user surface"
  - "licensing and product line context (Industry Cloud vs core)"
  - "team skills and operational model"
outputs:
  - "recommended tool per layer (UI, orchestration, data shaping)"
  - "risks and tradeoffs"
  - "migration notes if replacing existing implementation"
dependencies: []
runtime_orphan: true
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-08-14
---

# OmniStudio vs Flow Decision

## Route first, then read this

This skill does **not** re-derive the automation choice. Two canonical trees own
that, and this skill runs after them:

1. **`standards/decision-trees/automation-selection.md`** — the Flow vs Apex vs
   Agentforce vs Approvals vs Platform Events routing. Read it top to bottom
   first. Its Q1–Q12 will tell you whether the capability is record-triggered
   work, a user-facing form, a scheduled job, or an integration — and that
   classification is what makes the OmniStudio question answerable at all.
2. **`standards/decision-trees/flow-pattern-selector.md`** — once the first tree
   says "Flow", this picks *which* Flow. Its Q1–Q9 and its transaction-boundary
   table are the comparison baseline for anything OmniStudio might replace.

Cite the branch that resolved the choice. If the automation tree lands on
before-save record-triggered Flow, OmniStudio has no equivalent and this skill
has nothing to add — say so and stop.

**What this skill adds** is the layer the trees do not cover: on an org that has
OmniStudio, for the branches where an OmniStudio artifact *could* serve, which
one should. It is a per-layer choice, and it is dominated by operational cost
rather than by capability.

---

## Precondition: three questions before any comparison

The answers change the recommendation more than anything about the capability.

**1. Does the org actually have OmniStudio, and is anyone trained on it?**
An org where one person can maintain an OmniScript has a single point of failure
dressed up as a platform capability. This is a real constraint, not a soft one,
and it should be written down rather than implied.

**2. Which runtime?** The managed package runtime (the Vlocity lineage, custom
data model, `vlocity_*` namespaces, DataPacks) or the standard runtime
(Salesforce standard objects, Metadata API). Migration between them is a
documented three-phase project, now assisted by the Omnistudio Migration
Assistant. The runtime changes deployment, Apex entry points, and the extension
model — so "should we use OmniStudio" has two different answers depending on
which one the org is on.

**3. Is there already an OmniStudio implementation of this capability's
neighbours?** A capability that sits between two existing OmniScripts is a
different proposition from a greenfield one, regardless of which tool is
theoretically better.

---

## Core Concepts

### Three layers, three independent decisions

The most common mistake is treating this as one choice. It is three, and mixed
answers are normal and usually correct.

| Layer | OmniStudio option | Core option | The question that decides it |
|---|---|---|---|
| **UI** | OmniScript, FlexCard | Screen Flow, LWC, Lightning Record Page | How many steps, how much branching, and who maintains the surface |
| **Orchestration** | Integration Procedure | Autolaunched Flow, Invocable Apex | Whether the work is record-triggered, and how much JSON shaping there is |
| **Data shaping** | Data Mapper (Extract / Turbo Extract / Transform / Load) | Get/Update/Create Records, Apex | Whether the shape crossing the boundary is dictated by an external system |

An OmniScript UI in front of an autolaunched Flow is a legitimate design. So is a
Screen Flow that calls an Integration Procedure for one gnarly external payload.
Insisting on one vendor per capability is an aesthetic preference, not an
architectural one.

### What OmniStudio is genuinely better at

Three things, and they are narrower than the enthusiasm suggests:

- **Long, branching, guided journeys.** A twelve-step application with conditional
  sections, save-and-resume, and heavy validation is what OmniScript exists for.
  A Screen Flow can do it and becomes hard to reason about well before step
  twelve.
- **JSON shaping as a first-class artifact.** Data Mappers make the payload
  contract a named, versionable thing. The Transform type is documented as
  performing "intermediate data transformations without reading from or writing
  to Salesforce" — an artifact whose entire job is reshaping. Flow has no
  equivalent, and expressing a nested-JSON reshape in Flow formulas is genuinely
  worse.
- **One capability, several surfaces.** The same OmniScript serving an internal
  console and an Experience Cloud site is real reuse, not a claim.

### What Flow is genuinely better at

- **Anything record-triggered.** OmniStudio has no before-save equivalent, and
  before-save is the cheapest automation on the platform: it writes the field in
  the save the trigger already pays for. If `automation-selection.md` Q2 lands on
  before-save, the discussion is over.
- **Short admin-owned interactions.** One to three screens, changed monthly, by
  people who already work in Flow Builder.
- **Anything the platform will inspect for you.** Flow Trigger Explorer, the
  debugger, and the standard automation surfaces know what a Flow is.

### The operational tax is the actual decision

Capability comparisons rarely decide this. Operating cost does, and it is
asymmetric in ways that do not show up in a demo.

**Deployment.** On the managed package runtime, OmniStudio components move as
DataPacks — a mechanism unlike anything else in the org's pipeline. On the
standard runtime they move through the Metadata API as `OmniProcess`
(OmniScript and Integration Procedure), `OmniDataTransform` (Data Mapper), and
`OmniUiCard` (FlexCard) — but only after the **Omnistudio Metadata** setting is
enabled: "To deploy and retrieve Omnistudio standard objects with Salesforce
Metadata API, enable the Omnistudio Metadata setting."

**Setup surface.** The standard runtime is governed by a set of switches an
architect should know exist before committing, because several are prerequisites
rather than preferences: Omnistudio Metadata API Support, Managed Package Runtime,
Managed Package Designer, Deploy Custom Lightning Web Components, Omnistudio SLDS
2 Theme, Data Mapper Versioning, Omni Global Auto Number, and Enhanced Runtime
Performance — the last documented as making "Omnistudio communicate[] with the
Salesforce Platform with in-platform capabilities instead of through Apex calls".

**Introspection.** `OmniProcess`, `OmniDataTransform`, and `OmniDataTransformItem`
are all documented in the Object Reference as **"For internal use only… Don't
perform any create, edit, or delete operations on this object."** You can read
them for an inventory; you cannot build tooling that rewrites them. Flow metadata
has no such restriction.

**Hiring and handover.** Flow skills are common and transferable. OmniStudio
skills are neither. On a five-year horizon this is frequently the largest cost in
the comparison and the one least often written down.

---

## Common Patterns

### Pattern A — OmniScript UI, Flow side-effects

The journey is OmniStudio; the record-triggered consequences of what it saves are
Flow. This is the default shape on an Industry Cloud org and it respects both
tools' strengths: OmniScript owns the multi-step interaction, and the after-save
work stays where `flow-pattern-selector.md` Q4–Q5 puts it.

### Pattern B — Screen Flow UI, Integration Procedure for one hard payload

The interaction is three screens and admin-owned, so `flow-pattern-selector.md`
Q7 says Screen Flow. One step needs a nested JSON document shaped for a partner
API. An Integration Procedure with a Transform Data Mapper does that better than
any Flow formula. Mixed, and correct.

### Pattern C — Lightning Record Page, not FlexCard, unless a FlexCard feature is needed

Replacing a Lightning Record Page with a FlexCard because the org "is an
OmniStudio org" trades a surface every admin can edit for one that needs an
OmniStudio skillset. Do it when you need FlexCard-specific behaviour — a card
consumed across several surfaces, actions driven from a central designer, an
IP-powered save chain — and not because of house style.

### Pattern D — leave the working thing alone

An existing Screen Flow that does the job is not a migration candidate because
the org bought OmniStudio. Rewrites consume the budget that new capability needed
and reintroduce bugs that were fixed years ago. Migrate on the next substantial
change, not on a platform decision.

### Pattern E — record the mixed-tool boundary as a contract

Where an OmniScript calls a Flow, or a Flow calls an Integration Procedure, the
interface is where this design will break. Write down the input and output shape,
who owns each side, and what happens when one side changes. A boundary nobody
documented is a boundary nobody tests.

---

## Decision Guidance

Apply *after* `automation-selection.md` has classified the capability.

| Situation | Recommended | Reason |
|---|---|---|
| Automation tree lands on before-save record-triggered Flow | Flow — no discussion | OmniStudio has no before-save equivalent |
| Automation tree lands on after-save record-triggered Flow | Flow | Record-triggered is Flow's native context |
| 1–3 screen internal interaction, admin-owned, changes monthly | Screen Flow | Lower operating cost, common skills |
| 8+ step guided journey with branching and save-and-resume | OmniScript | What it exists for; Flow gets hard well before this |
| Same journey needed in a console and an Experience Cloud site | OmniScript | Genuine surface reuse |
| Nested JSON shaped for an external contract | Integration Procedure + Transform Data Mapper | A named, versionable payload artifact |
| Simple record reads and writes | Flow Get/Update/Create Records | Data Mapper adds an artifact for no gain |
| High-volume bulk processing | Apex | `automation-selection.md` Q10; neither tool changes this |
| Replacing a Lightning Record Page | Lightning Record Page, unless a FlexCard feature is required | Simpler operations, wider skill pool |
| Org has OmniStudio but nobody trained | Flow, and say why | One-person capability is a risk, not a platform |
| Managed package runtime, and a migration is planned | Do not build new OmniStudio into the migration scope | You would migrate what you just built |
| Existing Screen Flow that works | Leave it | Rewrites spend budget and reintroduce bugs |
| Capability sits between two existing OmniScripts | OmniStudio | Consistency at the boundary beats tool purity |
| Deployment pipeline cannot carry DataPacks or Omnistudio metadata yet | Fix the pipeline first | An artifact you cannot promote is not a solution |

---

## Recommended Workflow

1. **Route with `automation-selection.md` first** and record the branch that
   resolved it. If it lands on before-save record-triggered Flow, or on Apex for
   volume, this skill adds nothing — say so and stop.
2. **If the answer was Flow, run `flow-pattern-selector.md`** to get the specific
   Flow type. That is the baseline any OmniStudio proposal has to beat, and its
   transaction-boundary table is the comparison you will actually be arguing
   about.
3. **Answer the three preconditions** — does the org have OmniStudio, which
   runtime, and are the capability's neighbours already OmniStudio — before
   comparing anything. These change the answer more than the requirement does.
4. **Split the capability into UI, orchestration, and data-shaping layers** and
   decide each one separately, allowing mixed answers.
5. **Price the operational tax explicitly**: deployment mechanism, the Setup
   switches that are prerequisites, who can maintain it in eighteen months, and
   whether the pipeline can promote it today.
6. **Write the mixed-tool boundaries as contracts** — input shape, output shape,
   owner per side, and what happens when either changes.
7. **Record the decision with its citations** — the tree branches, the runtime,
   and the operational facts — so the next person inherits the reasoning rather
   than only the outcome.

---

## Review Checklist

- [ ] `automation-selection.md` was read first, and the resolving branch is cited
- [ ] `flow-pattern-selector.md` was applied where the answer was Flow
- [ ] The decision is per-layer, and mixed answers were allowed
- [ ] Runtime (managed package vs standard) is identified and recorded
- [ ] Whether the org is mid-migration is known, and new build respects it
- [ ] Team capability is stated honestly, including single-person risk
- [ ] Deployment mechanism is named and known to work in this pipeline today
- [ ] Required Setup switches are listed as prerequisites, not discoveries
- [ ] FlexCard vs Lightning Record Page was decided on FlexCard-specific need
- [ ] No existing working artifact is being rewritten without a separate reason
- [ ] Mixed-tool boundaries are documented as contracts with owners
- [ ] Nothing in the design writes to `OmniProcess` / `OmniDataTransform`
- [ ] Latency and volume expectations are stated, not assumed
- [ ] The decision record cites its sources, so it can be revisited rather than re-argued

---

## Salesforce-Specific Gotchas

Full detail in [`references/gotchas.md`](references/gotchas.md).

1. **Two runtimes** — half of what is "known" about OmniStudio describes only the managed package.
2. **DataPacks are not the standard pipeline**, and the standard-runtime alternative needs a setting enabled first.
3. **The Omnistudio standard objects are internal-use-only** — read, never write.
4. **OmniStudio has no before-save equivalent**, so the cheapest automation on the platform is Flow-only.
5. **Enhanced Runtime Performance is a switch**, not a property of the product.
6. **A one-person OmniStudio capability** is a staffing risk described as an architecture.
7. **FlexCard versus Lightning Record Page** is a separate decision from OmniScript versus Screen Flow.
8. **Building new OmniStudio during a runtime migration** enlarges the migration you are trying to finish.
9. **Managed OmniScripts constrain override**, so a packaged starting point is not a free head start.
10. **Mixed-tool boundaries are where this breaks**, and they are the part nobody documents.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Routing record | The `automation-selection.md` branch, and the `flow-pattern-selector.md` branch where applicable, that classified the capability |
| Precondition record | OmniStudio present? Which runtime? Migration in flight? Who can maintain it? |
| Per-layer decision table | UI / orchestration / data shaping, each with its tool and a one-line reason |
| Operational cost note | Deployment mechanism, prerequisite Setup switches, pipeline readiness, skill availability |
| Boundary contracts | For every mixed-tool seam: input shape, output shape, owner per side, change protocol |
| Migration note | If replacing something that exists: what, why now, and what is deliberately being left alone |

---

## Related Skills

- `standards/decision-trees/automation-selection.md` — the canonical Flow vs Apex
  routing this skill runs after; read it first, always
- `standards/decision-trees/flow-pattern-selector.md` — which Flow type, once the
  first tree says Flow; the baseline any OmniStudio proposal must beat
- `admin/process-automation-selection` — the general automation-selection skill,
  for the cases where OmniStudio is not in scope at all
- `omnistudio/omniscript-design-patterns` — once the choice is OmniScript
- `omnistudio/integration-procedures` — once the choice is an Integration Procedure
- `omnistudio/dataraptor-patterns` — once the choice is a Data Mapper
- `omnistudio/vlocity-to-native-omnistudio-migration` — the runtime move, which
  the precondition questions above may reveal as the real project
- `omnistudio/omnistudio-deployment-datapacks` — the deployment mechanism whose
  cost this skill asks you to price
- `flow/screen-flows` — the Screen Flow patterns this skill compares against
