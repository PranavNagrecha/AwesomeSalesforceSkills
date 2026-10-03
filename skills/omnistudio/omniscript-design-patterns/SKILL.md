---
name: omniscript-design-patterns
description: "Use when designing or reviewing OmniScripts for guided experiences, step structure, branching, save/resume, and the boundary between OmniScript, Integration Procedures, DataRaptors, and custom LWCs. Triggers: 'omniscript design', 'too many steps in omniscript', 'save and resume omniscript', 'branching in omniscript', 'when should this be an integration procedure'. NOT for deep Integration Procedure design — use omnistudio/integration-procedures. NOT for DataRaptor design — use omnistudio/dataraptor-patterns."
category: omnistudio
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
  - Operational Excellence
  - Reliability
tags:
  - omniscript
  - guided-experience
  - save-and-resume
  - branching
  - omnistudio
triggers:
  - "how should i structure an omniscript"
  - "too many steps in my omniscript"
  - "omniscript save and resume strategy"
  - "when to use integration procedure vs omniscript"
  - "custom lwc inside omniscript"
  - "design a guided omniscript for editing an account"
  - "reuse one omniscript inside another omniscript"
inputs:
  - "business journey, personas, and expected step count"
  - "which logic belongs in the guided UI vs backend services"
  - "save/resume, branching, and performance expectations"
outputs:
  - "omniscript design recommendation"
  - "review findings for step structure, branching, and handoff boundaries"
  - "decision on what should stay in omniscript vs move to integration procedures or lwc"
dependencies: []
runtime_orphan: true
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
---

Use this skill when OmniScript is the guided interaction layer for a business journey and the design needs to stay understandable for users and maintainers. The key question is not just how to assemble elements, but how to keep steps, branching, data gathering, and backend calls balanced so the script stays fast and operable.

## Before Starting

- What is the user journey, and how many meaningful steps does it actually require?
- Which logic belongs in the guided script, and which belongs behind it in Integration Procedures, DataRaptors (Data Mappers), or Apex-backed components?
- Does the experience need save and resume, conditional branching, reusable child OmniScripts, custom LWC components, or multilingual versions?
- Which runtime does the org use: Omnistudio for Managed Packages or the standard runtime? Designers, metadata types, and Trailhead content differ.

## Questions to Ask Before Configuring

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| What Type, SubType, and Language will identify this OmniScript? | Only one active OmniScript may have the same Type, SubType, and Language; the metadata unique name is `Type_SubType_Language_VersionNumber`. | A naming scheme that leaves room for variants and languages. | No collision when a second team builds a similar journey. |
| Which parts of the journey are reused elsewhere? | A child OmniScript can be embedded only when it is marked embeddable (`isOmniScriptEmbeddable`). | Small reusable child scripts for shared steps. | One fix updates every journey that embeds the child. |
| How many server calls does each step make, and can one Integration Procedure serve them? | Trailhead calls Integration Procedures the best practice for data input, and an Integration Procedure Action calls "a series of actions" in one request. | One orchestrating IP per user intent. | Fewer round trips and one place to change data logic. |
| Does the journey need save and resume, and what must be re-checked on resume? | Save Options are a script-wide Setup panel setting; backend data can change while a session is paused. | A list of values revalidated on resume. | Resumed sessions don't submit stale eligibility or prices. |
| Which validations must also hold on the server? | Step validation runs in the browser; any caller that reaches the IP or Apex directly skips it. | Server-side checks for every write. | Data rules hold for API callers and guest users too. |
| Will the OmniScript ship as metadata (`OmniScript` type) or as DataPacks? | Enabling Omnistudio metadata can't be undone and is blocked by unique names with spaces or special characters. | A chosen deployment model before naming components. | Clean CLI deploys and diffs. |

## Core Concepts

### OmniScript Is the Guided Experience Layer

OmniScript is strongest at user guidance, step progression, and data collection. Trailhead describes its modular architecture: the JSON structure, stylesheets, and data are kept separate, and Action elements reach data through Integration Procedures, Data Mapper actions, HTTP actions, and other tools. It gets harder to maintain when it also absorbs every transformation and integration rule.

### Element Families

| Family | Use for | Examples |
|---|---|---|
| Actions | Getting, saving, calculating, emailing | Data Mapper Extract Action, Data Mapper Post Action, Integration Procedure Action, HTTP Action, Email Action, Navigate Action |
| Display | Instructions and layout | Text Block, Line Break |
| Functions | Calculations and conditional messages | Formula, Aggregate, Messaging |
| Groups | Grouping on the page | Step, Block, Edit Block, Radio Group, Type Ahead Block |
| Inputs | User entry and selection | Text, Phone, URL, Select, Checkbox, Lookup |
| Omniscripts | Reusable child scripts | Embedded child OmniScript |

Element names must be unique within an OmniScript (Trailhead). Labels need not be unique; Action labels appear in the Action Debugger.

### Step Design Is a UX Decision and an Operations Decision

Each step should be a meaningful chunk of work. Too many tiny steps cause fatigue and operational complexity. Oversized steps cause validation and branching confusion.

### Branching Must Keep a Clear Data Story

Conditional paths are often necessary, but they should still produce a predictable data JSON. Branches that change the data shape without defaults make testing and support much harder.

### Versions and Activation

Only one version of an OmniScript can be active at a time. To change an active OmniScript, create a new version; the active one keeps serving users while you work (Trailhead, "Create a Simple Omniscript").

## Common Patterns

### Thin OmniScript, Rich Backend Services

**When to use:** The journey needs a guided UI, but transformations and integrations are too complex for the script layer.

**How it works:** Keep OmniScript focused on interaction. Put data shaping into one Integration Procedure per user intent, which calls Data Mappers and HTTP actions.

**Why not the alternative:** Backend-heavy scripts become slow, hard to test, and difficult to evolve.

### Milestone-Based Step Design

**When to use:** The journey spans clear milestones such as identify, verify, select, confirm, and submit.

**How it works:** Group fields and decisions by milestone rather than by data model, and align validation with those checkpoints.

### Reusable Child OmniScripts

**When to use:** Several journeys share a block of steps, such as address capture or identity verification.

**How it works:** Build the shared steps as their own OmniScript, mark it embeddable, and embed it with the Omniscripts element. The deployable files and naming are in [references/metadata-examples.md](references/metadata-examples.md).

### Controlled Branching With Stable Defaults

**When to use:** User answers legitimately change later steps.

**How it works:** Keep branches narrow, provide a predictable default path, and keep the resulting data JSON comprehensible for downstream processing.

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Guided multi-step journey with clear checkpoints | OmniScript | Best fit for guided interaction |
| Heavy transformation or integration logic | One Integration Procedure behind the script | Keeps the guided layer thin and the call count low |
| One field from Salesforce | Lookup input | Trailhead's mapping for single-field input |
| Fields from one object | Data Mapper Turbo Action | Simpler and faster for single-object reads |
| Fields from related objects | Data Mapper Extract Action, or an IP | Multi-object reads |
| Shared steps across journeys | Embeddable child OmniScript | One place to fix shared logic |
| Very custom UI dominates the experience | Custom LWC plus services | OmniScript is not always the right UX layer |

## Recommended Workflow

1. Write the journey as milestones and fix the Type, SubType, and Language for each OmniScript and child script.
2. Map each data need to an element using the Decision Guidance table, defaulting to one Integration Procedure Action per user intent.
3. Configure Setup panel options (save options, error messages) and decide what is revalidated on resume.
4. Build steps, test in Preview with a real Context ID, and inspect the Data JSON and the Action Debugger for every action.
5. Retrieve the `OmniScript` metadata and run `python3 skills/omnistudio/omniscript-design-patterns/scripts/check_omniscript_design_patterns.py --source-dir force-app` to flag step and action counts, missing embeddable flags, and non-standard unique names.
6. Activate the new version only after review, and record which version is active per environment.

## Review Checklist

- [ ] Type, SubType, and Language are unique among active OmniScripts; element names are unique within each script.
- [ ] Step count and grouping reflect real user milestones.
- [ ] Each step makes as few server calls as possible, normally one Integration Procedure per user intent.
- [ ] Branches are narrow and leave a stable data JSON.
- [ ] Save/resume behavior has explicit revalidation rules.
- [ ] Every write is validated again on the server.
- [ ] Shared steps live in embeddable child OmniScripts.
- [ ] The team can explain why OmniScript fits better than Flow or a custom LWC for this journey.

## Salesforce-Specific Gotchas

Full write-ups with sources are in [references/gotchas.md](references/gotchas.md).

| Gotcha | One-line summary |
|---|---|
| Identity collision | Only one active OmniScript per Type, SubType, and Language. |
| Version activation | Changing an active script means creating and activating a new version. |
| Embedding | A child must be marked embeddable before another script can embed it. |
| Client-side validation | Step validation is UX, not a server boundary. |
| Call count | Many actions per step multiply round trips; prefer one orchestrating IP. |
| Metadata switch | Omnistudio metadata can't be turned off once enabled. |
| Internal objects | `OmniProcess` and `OmniProcessElement` records are internal; don't edit them with DML. |

## Output Artifacts

| Artifact | Description |
|---|---|
| OmniScript design review | Findings on step count, branching, save/resume, and service boundaries |
| Journey model | Step structure, checkpoints, Type/SubType/Language plan, delegated backend responsibilities |
| Simplification plan | Changes that reduce script sprawl or move logic behind the guided layer |

## Related Skills

- `omnistudio/integration-procedures`: use when the backend service orchestration is the real design focus.
- `lwc/custom-property-editor-for-flow`: use when the problem shifts from guided journey design to custom component implementation.
- `admin/flow-for-admins`: use when a standard Flow may be sufficient and OmniStudio might be unnecessary.
