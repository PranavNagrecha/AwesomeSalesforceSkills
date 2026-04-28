---
name: subflows-and-reusability
description: "Use when extracting reusable Flow logic into subflows, defining input and output variables, keeping parent flows maintainable, and sharing common automation contracts across multiple flows. Triggers: 'reuse this flow logic', 'how should subflow variables work', 'too much duplicated flow logic', 'subflow contract design'. NOT for Apex-called Flow execution direction or Flow Orchestration process design."
category: flow
salesforce-version: "Spring '25+'"
well-architected-pillars:
  - Operational Excellence
  - Scalability
  - Reliability
tags:
  - subflows
  - flow-reuse
  - input-output-variables
  - autolaunched-flow
  - maintainability
triggers:
  - "should this logic become a subflow"
  - "how do input and output variables work in a subflow"
  - "too much duplicated logic across flows"
  - "subflow fault handling and contracts"
  - "reusable autolaunched flow pattern"
inputs:
  - "which parent flows repeat the same logic and what outputs they need back"
  - "whether the reusable step is pure calculation, data lookup, mutation, or error handling"
  - "how much of the current flow contract is stable across callers"
outputs:
  - "subflow extraction recommendation with clear input and output contracts"
  - "review findings for over-coupled or under-specified flow reuse"
  - "guidance on when to keep logic inline versus moving it to subflow or Apex"
dependencies: []
version: 2.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

Use this skill when the same Flow logic keeps appearing in more than one place or when one parent flow is becoming too long to reason about safely. A good subflow is a reusable contract with a narrow purpose, explicit inputs, explicit outputs, and predictable side effects. A bad subflow is just a pile of hidden assumptions moved out of sight.

The failure modes this skill prevents: (1) "extract-everything" subflow explosion where every 3-element sequence becomes its own file, (2) god-subflow that accepts 15 input variables and returns 8 outputs because it's trying to be useful to too many callers, (3) shared subflow whose contract drifts because nobody runs regression tests across callers on change.

## Before Starting

Check for `salesforce-context.md` in the project root. If present, read it first.

Gather if not available:
- How many parent flows need the logic today, and is the contract likely to stay stable across them?
- Is the candidate subflow primarily computing a value, centralizing a lookup, or performing side effects such as DML and notifications?
- What should happen when the called flow fails, returns nothing, or needs to evolve later?
- Does the org have existing reusable subflow patterns I should align with?
- Is this subflow going to be callable from Apex too, or Flow-only?

## Core Concepts

Subflows are most valuable when they remove repetition without hiding important behavior. The key design decision is whether the reusable unit has a clean contract. If the parent flow still needs to understand many internal assumptions or pass a long list of loosely related variables, the design is not reusable yet.

### Reuse Requires A Stable Contract

A subflow should expose a small set of clearly named inputs and outputs. Variable names such as `inCaseId`, `inPriority`, and `outQueueDeveloperName` are easier to maintain than generic `text1` or `varRecord`. A caller should understand what to pass and what it gets back without reading the entire child flow.

**Naming convention (recommended):**

| Variable role | Prefix | Example |
|---|---|---|
| Input the caller provides | `in` | `inCaseId`, `inCustomerType` |
| Output the caller reads | `out` | `outRoutingQueue`, `outEscalationNeeded` |
| Internal only, not exposed | `int` or no prefix | `intCandidateList`, `matchedContact` |

Mark "Available for input" + "Available for output" explicitly only on the variables that are part of the contract. Leaving all variables exposed creates a wider contract than intended.

**Contract size heuristic:** if a subflow has more than 5 inputs OR more than 3 outputs, either the subflow is trying to do too much or the caller shape isn't stable enough. Redesign.

### Subflows Share The Parent Transaction Context

Moving logic into a subflow does not magically reset governor limits, rollback behavior, or fault responsibility. If the subflow does repeated queries inside a loop or throws an unhandled error, the parent still pays the cost. Reuse improves maintainability only if the reused logic is already safe.

Shared across parent and subflow:
- Governor limits (SOQL, DML, CPU, heap)
- Transaction boundaries (one commit across both)
- User context (subflow runs as the same user)
- `$Flow.InterviewStartTime` is from the ORIGINAL parent start

NOT shared:
- Local variables (each flow has its own variable scope)
- Record triggers (a subflow can't receive the "triggering record" semantics of the parent unless explicitly passed in)

### Side Effects Should Be Deliberate

The cleanest reusable subflows often perform one well-bounded job: derive data, centralize a lookup, or apply a consistent decision tree. A child flow that creates records, sends emails, and mutates unrelated state for many different callers is harder to reason about and harder to test safely.

Classify subflows by side-effect profile:

| Type | Side effects | Reuse safety |
|---|---|---|
| Pure calculation | None — only reads inputs, returns outputs | Highest; safe to call from anywhere |
| Lookup / derivation | SOQL reads only | High; budget-aware callers needed |
| Single-purpose mutation | One DML operation on one object | Medium; caller should handle fault |
| Multi-purpose mutation | Multiple DML + notifications + external calls | Low; usually not reusable — redesign |

### Activation And Change Management Matter

A reusable child flow becomes a dependency surface. Renaming variables, changing output meaning, or widening side effects can break multiple callers at once. That means subflow changes need release discipline and regression testing across every parent flow that relies on the contract.

**Versioning discipline:**
- Increment subflow version on every contract change.
- Keep the previous active version for at least one release (callers updating gradually).
- Tag the subflow name or description with its contract version (e.g., "v2 — added outEscalationNeeded").
- Maintain a "callers of this subflow" list in the subflow's description field.

## Common Patterns

### Pattern 1: Shared Lookup Or Decision Subflow

**When to use:** Several flows need the same routing rule, owner lookup, or eligibility decision.

**Structure:**
```text
Subflow: Get_Case_Queue_Assignment
  Inputs:
    - inCaseId (Text)
    - inCustomerTier (Text)  
  Outputs:
    - outQueueDeveloperName (Text)
    - outRoutingReason (Text)  [for logging]
  Side effects: None (SOQL read only)
  Internal: Get Records, Decision tree, Assignment
```

**Why not the alternative:** Copying the same decisions into every flow creates drift; the "premium customer routing" rule gets updated in 3 of 5 callers and the other 2 miss the change.

### Pattern 2: Reusable Preparation Step Before Main Work

**When to use:** Multiple parent flows need the same record enrichment or normalization step before continuing.

**Structure:**
```text
Subflow: Enrich_Opportunity_For_Routing
  Inputs: inOpportunityId
  Outputs: outEnrichedOpportunity (Record)
  Side effects: None (read-only enrichment; caller decides whether to commit)

Parent flow:
  [Subflow: Enrich_Opportunity_For_Routing]
  └── [Decision using outEnrichedOpportunity fields]
  └── [Update Records if needed — COMMIT HAPPENS HERE, not in subflow]
```

**Why not the alternative:** Folding parent-specific side effects into the child destroys reuse; each caller commits differently.

### Pattern 3: Subflow For Fault-Handling Macro

**When to use:** Multiple parent flows need the same fault-logging-and-notification behavior when a DML step fails.

**Structure:**
```text
Subflow: Log_Flow_Fault
  Inputs:
    - inFaultMessage (Text)  [receives $Flow.FaultMessage from caller]
    - inElementName (Text)
    - inRecordId (Text)
    - inSeverity (Text: 'P0' | 'P1' | 'P2')
  Outputs:
    - outLogId (Text)
  Side effects: Creates one Application_Log__c record; may send notification based on severity
```

Callers share the same fault-routing without duplicating the Create-Log-then-Notify pattern.

### Pattern 4: Escalate Out Of Flow When Reuse Gets Too Complex

**When to use:** The reusable unit needs deep branching, heavy data work, broad inputs/outputs, or transaction control Flow can't express.

**Signals:**
- Candidate subflow has > 5 inputs or > 3 outputs.
- Subflow logic requires > 3 levels of nested Decisions.
- Subflow needs precise try/catch semantics (Flow's fault connectors are coarser than Apex try/catch).
- Reuse happens from Apex code, not just from other Flows.

**Approach:** Build an invocable Apex method with a clear DTO input/output. Flow callers invoke it as an Action; Apex callers call it directly. The "subflow" becomes an Apex method with stronger type guarantees and easier unit testing.

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Same decision or lookup repeated across 3+ flows | Extract a subflow with explicit inputs/outputs (Pattern 1) | Centralizes logic without duplicating maintenance |
| Logic is unique to one short parent flow | Keep it inline | Extraction adds indirection without enough reuse benefit |
| Reusable step has many side effects and hidden dependencies | Redesign or move to Apex (Pattern 4) | The contract is too wide for healthy Flow reuse |
| Child flow failure needs consistent caller handling | Add clear fault behavior at the call boundary | Subflows do not isolate error design automatically |
| Parent using subflows to avoid bulk/governor review | Reassess the overall architecture | Limits and rollback still apply across the transaction |
| Same fault-handling macro repeated across flows | Build Pattern-3 subflow | One place to update when notification rules change |
| Reused from both Flow and Apex | Build invocable Apex, NOT subflow | Dual-callable unit belongs in code |

## Review Checklist

- [ ] The subflow solves a repeated problem (3+ callers), not a one-off decomposition habit.
- [ ] Input and output variables are small in number (<= 5 inputs, <= 3 outputs) and named as a clear contract.
- [ ] The subflow's side effects are narrow and documented.
- [ ] Parent flows handle subflow failure intentionally.
- [ ] Bulk and transaction behavior were reviewed at the parent-plus-child level.
- [ ] Contract changes are regression-tested across all callers.
- [ ] Subflow description field lists current callers.
- [ ] Version history documented for contract changes.

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Common Patterns above; size the contract per the heuristic
4. Validate — run the skill's checker script and verify against the Review Checklist above
5. Document — record any deviations from standard patterns and update the template if needed

---

## Salesforce-Specific Gotchas

1. **Subflows do not reset limits** — the caller and child still consume the same transaction budget.
2. **Wide variable contracts are a design smell** — if a subflow needs many loosely related inputs, the reusable boundary is probably wrong.
3. **A shared child flow can break many parents at once** — contract changes need versioning discipline and regression tests.
4. **Moving logic out of sight is not the same as simplifying it** — some complex reuse should become Apex instead of another Flow layer.
5. **Subflows cannot receive `$Record` directly from the parent's record-triggered context** — the parent must explicitly pass the record as an input variable.
6. **"Available for input" / "Available for output" must be set explicitly** — missing these makes variables invisible to callers, silent coupling to defaults.
7. **Subflows with record-triggered type CANNOT be called from auto-launched flows** — types must match; a "reusable" record-triggered flow isn't actually reusable in the general case.
8. **Deleting a subflow doesn't error the parent at deploy time** — the parent fails at RUNTIME when the call happens; test deploys DO NOT catch missing subflows.
9. **Managed-package subflows are opaque** — you can call them but can't see internals; contract changes in managed releases can break you silently.
10. **Apex callers of Flows pass inputs differently than Flow callers** — if the subflow needs to be dual-callable (Pattern 4 escape hatch), consider making it Apex to start.

## Proactive Triggers

Surface these WITHOUT being asked:

- **Subflow with > 5 input variables** → Flag as High. Contract too wide; subdivide or redesign.
- **Subflow with mutation + read side effects that callers don't all want** → Flag as High. Split into read-only and mutation subflows.
- **Subflow used by only one parent flow** → Flag as Medium. Not yet reusable; keep inline until a second caller appears.
- **Contract change to a subflow without regression-test plan** → Flag as Critical. Multi-caller break risk.
- **Subflow description field empty or generic** → Flag as Medium. Missing caller list + version history — OpsEx debt.
- **Subflow name not following `<Verb>_<Object>_<Modifier>` convention** → Flag as Low. Naming debt.
- **Parent flow calling > 3 subflows in sequence** → Flag as Medium. Consider whether the parent's logic is really one flow or several.
- **Subflow doing same-transaction DML without explicit fault connector in parent** → Flag as High. Silent failure risk.

## Output Artifacts

| Artifact | Description |
|---|---|
| Subflow boundary recommendation | Guidance on what to extract and what to leave in the parent |
| Contract design | Proposed input and output variable set for the child flow with names + types |
| Reuse review findings | Risks around side effects, failure handling, over-decomposition |
| Versioning plan | How to evolve the subflow contract without breaking callers |

## Related Skills

- **flow/flow-bulkification** — alongside this skill when the shared child logic may still be unsafe under volume.
- **flow/fault-handling** — when the key question is how callers should respond to child-flow failure.
- **flow/record-triggered-flow-patterns** — when the subflow receives context from a record-triggered parent.
- **flow/auto-launched-flow-patterns** — when the subflow itself is auto-launched.
- **apex/trigger-framework** — when the reusable unit has outgrown Flow (Pattern 4).
