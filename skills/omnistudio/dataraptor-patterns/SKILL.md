---
name: dataraptor-patterns
description: "Use when designing or reviewing OmniStudio DataRaptors, especially Extract versus Turbo Extract versus Transform versus Load, field mapping strategy, performance tradeoffs, and when to move work into Integration Procedures or Apex. Triggers: 'DataRaptor Extract', 'Turbo Extract', 'DataRaptor Load', 'DataRaptor Transform', 'OmniStudio data mapping'. NOT for overall OmniScript journey design or Integration Procedure sequencing when the main question is not the DataRaptor shape itself."
category: omnistudio
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Reliability
  - Operational Excellence
triggers:
  - "when should I use Turbo Extract instead of Extract"
  - "DataRaptor Load versus Transform decision"
  - "OmniStudio field mapping is getting messy"
  - "should this DataRaptor be moved to Integration Procedure or Apex"
  - "DataRaptor performance review"
tags:
  - dataraptor
  - turbo-extract
  - dataraptor-load
  - dataraptor-transform
  - omnistudio-data-mapping
inputs:
  - "whether the asset is reading, reshaping, or writing data"
  - "object count, response shape, and performance expectations"
  - "whether formulas, complex mappings, or orchestration logic are needed"
outputs:
  - "DataRaptor type recommendation"
  - "mapping and performance review findings"
  - "boundary guidance for DataRaptor versus IP versus Apex"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-03-13
---

# DataRaptor Patterns

Use this skill when OmniStudio data work needs the right DataRaptor shape instead of a generic "just build a DataRaptor" answer. DataRaptors are specialized assets: they read, reshape, or write data. Problems start when teams blur those roles, use Turbo Extract where complex mapping is needed, or pile orchestration logic into mapping layers that were never meant to own it.

The goal is to keep each DataRaptor focused. Extract reads data. Turbo Extract is the faster, simplified path for the right narrow case. Transform reshapes payloads. Load writes data. When the design needs multi-step orchestration, external calls, or complex coordination, that belongs in an Integration Procedure or Apex, not in an overgrown DataRaptor strategy.

---

## Before Starting

Gather this context before working on anything in this domain:

- Is the asset reading Salesforce data, transforming a payload, or writing records back?
- Is the data shape a single-object flat read or a more complex graph with formulas and mapping rules?
- What caller consumes the output: OmniScript, FlexCard, Integration Procedure, or custom Apex?
- Is the main problem mapping, performance, or misuse of DataRaptor for orchestration?

---

## Core Concepts

### Choose The DataRaptor Type Deliberately

Extract is for reading Salesforce data with regular mapping flexibility. Turbo Extract is the simplified, faster option for single-object reads when you do not need formulas or complex field mappings. Transform is for reshaping payloads. Load is for inserting, updating, upserting, or deleting records.

### DataRaptors Are Data Assets, Not Orchestration Engines

If the design needs sequencing, branching, or coordination across several data and service steps, use an Integration Procedure or Apex boundary. Keep DataRaptors narrow and predictable.

### Mapping Discipline Is Part Of Maintainability

Overgrown mappings, unclear names, and weak output contracts make OmniStudio assets hard to reuse. The data shape should be understandable to the caller without reading designer-only tribal knowledge.

### Performance Depends On Matching The Tool To The Shape

Turbo Extract is attractive because it is fast, but it only fits simple cases. Using it in the wrong place or forcing Extract to behave like a transform-and-orchestrate layer creates hidden cost.

---

## Common Patterns

### Turbo Extract For Flat Single-Object Read

**When to use:** The caller needs a simple read from one object with no complex formulas or mapping behavior.

**How it works:** Use Turbo Extract for the narrow read and keep the output intentionally small.

**Why not the alternative:** Standard Extract is more flexible, but unnecessary when the requirement is simple and performance-sensitive.

### Extract Plus Transform Pattern

**When to use:** The read path and the response shape are both needed, but they should remain separate concerns.

**How it works:** Use Extract to fetch the data, then Transform to reshape it for the consumer.

### Load As Explicit Write Boundary

**When to use:** OmniStudio needs a controlled data write with a stable contract.

**How it works:** Keep the input contract narrow, avoid hardcoded IDs, and use Load for the write step instead of hiding write behavior in a loosely defined asset chain.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Single-object flat read with speed sensitivity | Turbo Extract | Simplified and faster fit |
| Read requires richer mapping or formulas | Extract | More flexible read asset |
| Payload must be reshaped without writing | Transform | Clear transformation boundary |
| Records must be inserted or updated | Load | Explicit write behavior |
| Multi-step data logic or orchestration is growing | Integration Procedure or Apex boundary | DataRaptor should not own process sequencing |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] The DataRaptor type matches the actual data responsibility.
- [ ] Turbo Extract is used only for simple single-object read scenarios.
- [ ] Mapping logic is understandable and not overloaded with process behavior.
- [ ] Load assets have clear write contracts and avoid brittle assumptions such as hardcoded IDs.
- [ ] The team rejected Integration Procedure or Apex only for a clear reason.
- [ ] Output shape is stable enough for the caller to depend on safely.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Turbo Extract is not a faster version of every Extract** - it is a narrower asset with less mapping flexibility.
2. **DataRaptor sprawl becomes an operability issue before it becomes a syntax issue** - unclear names and output shapes make change hard.
3. **Using DataRaptor to hide orchestration logic creates brittle OmniStudio flows** - the right boundary is usually an Integration Procedure.
4. **Write behavior deserves the same contract discipline as reads** - a vague Load asset is still a production write surface.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| DataRaptor type recommendation | Extract, Turbo Extract, Transform, or Load guidance |
| Mapping review | Findings on maintainability, contract clarity, and performance fit |
| Boundary recommendation | Advice to keep work in DataRaptor, move to IP, or move to Apex |

---

## Related Skills

- `omnistudio/integration-procedures` - use when sequencing, external calls, or multi-step orchestration are the real issue.
- `omnistudio/omniscript-design-patterns` - use when the caller journey shape is the bigger problem.
- `apex/custom-metadata-in-apex` - use when configuration-driven mapping rules are the real requirement outside OmniStudio.
