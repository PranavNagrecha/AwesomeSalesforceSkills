---
name: omniscript-design-patterns
description: "Use when designing or reviewing OmniScripts for guided experiences, step structure, branching, save/resume, and the boundary between OmniScript, Integration Procedures, DataRaptors, and custom LWCs. Triggers: 'omniscript design', 'too many steps in omniscript', 'save and resume omniscript', 'branching in omniscript', 'when should this be an integration procedure'. NOT for deep Integration Procedure or DataRaptor design when the guided interaction layer is not the main concern."
category: omnistudio
salesforce-version: "Spring '25+'"
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
inputs:
  - "business journey, personas, and expected step count"
  - "which logic belongs in the guided UI vs backend services"
  - "save/resume, branching, and performance expectations"
outputs:
  - "omniscript design recommendation"
  - "review findings for step structure, branching, and handoff boundaries"
  - "decision on what should stay in omniscript vs move to integration procedures or lwc"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-03-13
---

Use this skill when OmniScript is the guided interaction layer for a business journey and the design needs to stay understandable for users and maintainers. The key question is not just how to assemble elements, but how to keep steps, branching, data gathering, and backend calls balanced so the script remains fast and operable.

## Before Starting

- What is the user journey, and how many meaningful steps does it actually require?
- Which logic belongs in the guided script, and which logic belongs behind the script in Integration Procedures, DataRaptors, or Apex-backed components?
- Does the experience need save and resume, conditional branching, custom LWC components, or multilingual reuse?

## Core Concepts

### OmniScript Should Stay The Guided Experience Layer

OmniScript is strongest when it handles user guidance, step progression, and clear data collection. It becomes harder to maintain when it also tries to absorb every transformation, integration rule, and backend dependency directly into the script structure.

### Step Design Is A UX Decision And An Operations Decision

Each step should represent a meaningful chunk of work for the user. Too many tiny steps create fatigue and operational complexity, while oversized steps create validation and branching confusion. Good step design balances the mental model of the user with the maintainability needs of the team.

### Branching Must Keep A Clear Data Story

Conditional paths are often necessary, but they should still produce predictable data shape and progression. Branching that changes the script too dramatically without clear defaults or state rules makes testing and support much harder.

### Save And Resume Need Intentional State Boundaries

Long guided journeys often need save/resume behavior. That means the team has to decide what state is preserved, what can change between sessions, and how to recover when backend context has moved on since the user paused.

## Common Patterns

### Thin OmniScript, Rich Backend Services

**When to use:** The journey needs a guided UI, but transformations and integrations are too complex for the script layer.

**How it works:** Keep OmniScript focused on user interaction and move heavier data shaping into Integration Procedures, DataRaptors, or reusable service layers.

**Why not the alternative:** Backend-heavy scripts become slow, hard to test, and difficult to evolve.

### Milestone-Based Step Design

**When to use:** The journey spans several clear user milestones such as identify, verify, select, confirm, and submit.

**How it works:** Group fields and decisions by milestone rather than by data model alone, and keep validation aligned to those user checkpoints.

**Why not the alternative:** Field-by-field or system-centric grouping produces clumsy user journeys.

### Controlled Branching With Stable Defaults

**When to use:** Different user answers legitimately change later steps.

**How it works:** Keep branches narrow, provide a predictable default path, and ensure the resulting data model stays comprehensible for downstream processing.

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Guided multi-step user journey with clear checkpoints | OmniScript | Best fit for guided interaction flow |
| Heavy transformation or integration logic | Move behind the script into IP/DataRaptor/Apex | Keeps the guided layer thin |
| Many branches with weak defaults | Simplify the journey before building | Support and testing costs rise fast |
| Very custom UI interaction dominates the experience | Consider custom LWC plus services | OmniScript is not always the right UX layer |


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

- [ ] Step count and grouping reflect real user milestones.
- [ ] Branches are narrow, intentional, and leave a stable data model.
- [ ] Save/resume behavior has explicit state boundaries and recovery expectations.
- [ ] Backend-heavy logic is delegated out of the script where appropriate.
- [ ] Custom LWCs are used only where the standard OmniScript experience is insufficient.
- [ ] The team can explain why OmniScript is a better fit than Flow or custom LWC for this journey.

## Salesforce-Specific Gotchas

1. **Too many steps turn maintainability into the real bottleneck** — the script may still work, but support and change velocity suffer.
2. **Branching without stable defaults makes testing explode** — every alternate path increases support burden and data-shape risk.
3. **Save/resume is only useful when the restored context still makes sense** — backend state can drift while the user is away.
4. **Embedding custom LWCs widens the support surface** — OmniScript stays thin only if custom components are used deliberately.

## Output Artifacts

| Artifact | Description |
|---|---|
| OmniScript design review | Findings on step count, branching, save/resume, and service boundaries |
| Journey model | Recommended step structure, checkpoints, and delegated backend responsibilities |
| Simplification plan | Changes to reduce script sprawl or move logic behind the guided layer |

## Related Skills

- `omnistudio/integration-procedures` — use when the backend service orchestration is the real design focus.
- `lwc/custom-property-editor-for-flow` — use when the problem shifts from guided journey design to custom component implementation.
- `admin/flow-for-admins` — use when a standard Flow may be sufficient and OmniStudio might be unnecessary.
