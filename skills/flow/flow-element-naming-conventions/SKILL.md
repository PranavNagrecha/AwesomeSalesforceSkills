---
name: flow-element-naming-conventions
description: "Canonical naming conventions for Flow elements (Get_/Update_/Decision_/Loop_/Assignment_), resource variables (var/coll/map/formula/choice/constant/stage/screen), Decision branch outcomes, Stage/Step labels in Orchestrations, Subflow input/output contracts, and fault-path target names. NOT for object/field naming — see admin/naming-conventions or templates/admin/naming-conventions.md."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
tags:
  - flow-element-naming-conventions
  - naming-conventions
  - flow
  - api-name
  - readability
  - subflow-contract
  - orchestration
triggers:
  - "what should I name my Flow elements"
  - "API name vs label for flow variables"
  - "naming convention for Decision branch outcomes"
  - "rename flow subflow input variable safely"
  - "Process Builder migrated flow has ugly element names"
  - "stage and step naming convention for orchestration"
  - "fault path target naming pattern"
inputs:
  - Flow design or Flow XML to be named/audited
  - List of existing Flow elements + their current API names
  - Subflow input/output signatures (if reviewing subflow contracts)
outputs:
  - Renamed elements + variables that follow the canonical pattern
  - Decision branch outcome rename list (with Default outcome named explicitly)
  - Subflow input/output rename + version-bump recommendation
  - Audit table of non-conforming element names with proposed replacements
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-27
---

# Flow Element Naming Conventions

Activate when designing a new Flow, auditing an existing one for readability, or migrating a Process Builder / Workflow Rule (which leaves auto-generated element names like `myDecision_4`). This is the canonical reference cited by `agents/flow-builder/AGENT.md` Step 3 (element decomposition), `agents/flow-analyzer/AGENT.md` (audit signal), and `agents/flow-orchestrator-designer/AGENT.md` (stage/step naming).

---

## Before Starting

Gather this context before working on anything in this domain:

- **What naming exists in the org today?** Run `list_flows_on_object(<sObject>)` (or query `FlowDefinitionView`) and pull the Flow XML for one or two representative flows. Look at the element `<name>` values — are they `Get_OpenCases_ByOwner` or `Get_Records_2`? The status quo dictates how much rename work is in front of you.
- **Is this Flow already deployed to production or referenced in a managed/unlocked package?** Element API names become part of the metadata contract. After a package install, renaming an element that is referenced by formula, fault path, or another flow's subflow call is a breaking change.
- **Common wrong assumption:** practitioners think "API Name doesn't matter, only Label is shown." False — API Name is what serializes into Flow XML, what shows up in metadata diffs in Git, what appears in fault email subjects, and what every Subflow / formula reference resolves against. The Label is throwaway; the API Name is the contract.
- **Limits in play:** API Name max 80 characters, must start with a letter, alphanumeric + underscore only (Salesforce auto-replaces spaces and special chars with `_`). Reserved words (`null`, `true`, `false`, `Id`) must not be used as variable API names — they will silently shadow built-ins or refuse to save.

---

## Core Concepts

### Concept 1 — VerbObject element naming

Every Flow element is a verb acting on a noun. The API Name encodes that:

```
<Verb>_<Object>[_<Qualifier>]
```

- `Get_OpenCasesByOwner` — Get Records element fetching open cases scoped to the running user.
- `Update_OpportunityStageToClosedWon` — Update Records element with a clear post-condition.
- `Create_ChildAccount` — Create Records.
- `Decision_HasActiveContract` — Decision element framed as a yes/no question on the noun.
- `Loop_OverContacts` — Loop element iterating a known collection.
- `Assignment_AccumulateTaskList` — Assignment that builds a collection variable across iterations.

The verb maps to the element type (Get, Update, Create, Delete, Decision, Loop, Assignment, Screen, Action, Subflow). The noun is the primary record or domain concept. The qualifier disambiguates when more than one element of the same type acts on the same noun in the same flow.

Why this matters: a fault email reads `Element "Get_Records_3" failed.` The on-call admin has to open the flow, find element 3, and reverse-engineer what it was doing. With `Get_OpenCasesByOwner`, the email is self-describing.

### Concept 2 — Resource prefix discipline

Flow resource variables are typed, but the type is invisible at the call site (e.g. inside a formula, inside an Assignment). Encode the type in the API Name:

| Prefix | Resource type | Example |
|---|---|---|
| `var` | Single-value variable | `varAccountId`, `varCustomerName` |
| `coll` | Collection variable (List) | `collOpenCases`, `collContactsToInsert` |
| `map` | Apex-defined / map-shaped variable | `mapAccountById`, `mapErrorsByRecordId` |
| `formula` | Formula resource | `formulaFullName`, `formulaIsHighValue` |
| `choice` | Choice / Picklist Choice resource | `choiceTaskType`, `choiceCountryList` |
| `constant` | Constant | `constantMaxRetries`, `constantApiVersion` |
| `stage` | Stage (legacy stages or Orchestration stage label) | `stage_LegalReview`, `stage_FinanceApproval` |
| `screen` | Screen-level variable | `screenInputContactInfo` |
| `decisionOutcome` | Outcome label inside a Decision (when needed in formulas) | `decisionOutcome_HasActiveContract` |

Type-disambiguation: when two variables represent the same logical thing in different shapes, encode the shape in the suffix too.

```
varOpportunityId          // primitive ID
varOpportunityIdString    // explicitly the string form, used inside a formula
collOpportunityIds        // a collection of IDs
mapOpportunityById        // map keyed by ID
```

Explicit > clever. The reader six months later will thank you.

### Concept 3 — API Name is immutable in the contract sense

Once a Flow is deployed and referenced, the API Names of its public surface (Flow API name itself, Subflow input/output variables, Choice values bound to picklists) are part of the contract. Renaming them does NOT cause a save-time validation error — Salesforce will let you save the rename and only blow up at runtime in the parent flow that referenced the old name.

This is the single most expensive naming mistake. Treat the public contract as you would treat a public API method signature: name it deliberately the first time, and bump the Flow version (per `flow-versioning-strategy`) if you must rename.

---

## Common Patterns

### Pattern 1 — VerbObject Element Name

**When to use:** every element in every flow.

**How it works:** API Name = `<Verb>_<Object>[_<Qualifier>]`. Label may be more human-readable ("Get open cases owned by current user") but the API Name stays canonical.

```
Element type: Get Records
API Name:     Get_OpenCasesByOwner
Label:        Get open cases owned by current user

Element type: Update Records
API Name:     Update_OpportunityStageToClosedWon
Label:        Update opportunity stage → Closed Won
```

**Why not the alternative:** `Get_Records_1`, `Update_2`, `Decision_3` (Salesforce defaults) carry zero information. Fault emails become unreadable, Git diffs become noise, and every audit takes 4× longer.

### Pattern 2 — Resource Type Prefix

**When to use:** every variable, formula, constant, and choice resource you create.

**How it works:** prefix the API Name with the type token (`var`, `coll`, `map`, `formula`, `choice`, `constant`). Suffix with the noun and (optionally) the shape.

```
varAccountId            (single record ID)
collOpenCases           (List<Case>)
mapAccountById          (Map<Id, Account>)
formulaFullName         (Formula returning Text)
constantMaxRetries      (Constant Number)
choiceTaskType          (Choice resource)
```

**Why not the alternative:** without the prefix, a formula that says `{!AccountId}` is ambiguous — is it a single ID or a collection? Authors then add casts or duplicate variables to disambiguate, and the flow turns into spaghetti.

### Pattern 3 — Default Branch Naming

**When to use:** every Decision element. Salesforce requires a Default outcome but lets you leave its name blank — never do this.

**How it works:**
- Name every outcome with the **affirmative business condition** it represents.
- Name the Default outcome explicitly (`Default`, `NoMatch`, `NoActiveContract_Default`, `Otherwise`).
- Never use bare `Yes` / `No` — they don't survive being read out of context (e.g. in a fault email or a metadata diff).

```
Decision_HasActiveContract
  ├── Outcome:  HasActiveContract           (condition: Account.Active_Contract__c = TRUE)
  └── Default:  NoActiveContract_Default    (no rule — fires when nothing above matched)
```

**Why not the alternative:** unnamed default outcomes show up as `myDecision.outcome2` in fault diagnostics and as a blank cell in the Flow XML — and a future editor has to re-read every other outcome to figure out what the default is supposed to catch.

### Pattern 4 — Subflow Input/Output Contract Naming

**When to use:** any Subflow that is `Available for use as a subflow` (i.e., publicly callable).

**How it works:** treat input/output variable API Names as a published API. Name them once, document them in the Flow's Description, and bump the version on rename.

```
Subflow:       Account_RollupChildContactsCount
  Input:       inputAccountId           (Available for input,  Text)
  Input:       inputContactStatusFilter (Available for input,  Text, default 'Active')
  Output:      outputContactCount       (Available for output, Number)
  Output:      outputLastContactDate    (Available for output, DateTime)
```

Use the `input` / `output` prefix to make the direction obvious to the parent-flow author. Document the contract at the top of the Flow Description so changes are visible in metadata diffs.

**Why not the alternative:** silently renaming `inputAccountId` → `inputAcctId` saves cleanly in the subflow but breaks every parent flow at runtime with `The flow couldn't find a referenced variable.` See `references/gotchas.md` Gotcha 2.

### Pattern 5 — Fault-Path Target Naming

**When to use:** every fault connector that routes to a logging or alerting sub-path.

**How it works:** name the fault-path target after the parent element so the visual diagram shows the route clearly:

```
Element:  Update_OpportunityStageToClosedWon
  fault → LogFault_Update_OpportunityStageToClosedWon
            └── Create Records: Integration_Log__c
```

**Why not the alternative:** generic names like `LogError`, `FaultLogger`, `Handle_Error_1` re-converge every fault path into a blob. When two faults fire in the same interview, you can't tell which originated where. See `flow-error-monitoring` for the broader fault-path skeleton.

---

## Decision Guidance

| Element / Resource Type | Naming Pattern | Example |
|---|---|---|
| Get Records | `Get_<Object>[_<Filter>]` | `Get_OpenCasesByOwner` |
| Update Records | `Update_<Object>_<PostCondition>` | `Update_OpportunityStageToClosedWon` |
| Create Records | `Create_<Object>[_<Qualifier>]` | `Create_ChildAccount` |
| Delete Records | `Delete_<Object>[_<Qualifier>]` | `Delete_StaleTasks` |
| Decision | `Decision_<Question>` (yes/no framed) | `Decision_HasActiveContract` |
| Decision Outcome | `<AffirmativeCondition>` or `Default` / `NoMatch` | `HasActiveContract`, `NoActiveContract_Default` |
| Loop | `Loop_Over<Collection>` | `Loop_OverContacts` |
| Assignment | `Assignment_<Verb><Object>` | `Assignment_AccumulateTaskList` |
| Screen | `Screen_<PurposeOrStep>` | `Screen_CollectShippingAddress` |
| Action / Apex Action | `Action_<VerbObject>` | `Action_SendDocuSignEnvelope` |
| Subflow Call | `Subflow_<CalledFlowName>` | `Subflow_Account_RollupChildContactsCount` |
| Variable (single) | `var<Noun>[<ShapeSuffix>]` | `varAccountId`, `varAccountIdString` |
| Collection variable | `coll<NounPlural>` | `collOpenCases`, `collContactsToInsert` |
| Map / Apex-defined map | `map<Noun>By<Key>` | `mapAccountById` |
| Formula | `formula<Noun>` | `formulaFullName` |
| Constant | `constant<Noun>` | `constantMaxRetries` |
| Choice | `choice<Noun>` | `choiceTaskType` |
| Orchestration Stage | `Stage_<BusinessProcessName>` | `Stage_LegalReview` |
| Orchestration Step | `Step_<Stage>_<Action>` | `Step_LegalReview_AssignToCounsel` |
| Fault target element | `LogFault_<ParentElementName>` | `LogFault_Update_OpportunityStageToClosedWon` |

---

## Recommended Workflow

1. **Inventory current names.** Pull the Flow XML (`sf project retrieve start --metadata Flow:<FlowName>`) and grep for `<name>` values inside `<decisions>`, `<recordLookups>`, `<recordUpdates>`, `<assignments>`, `<loops>`, `<variables>`. List every element whose API Name does not match the pattern table above.
2. **Classify the rename risk.** For each non-conforming name, mark whether it is referenced externally:
   - Subflow input/output variable → high risk (parent flows will break at runtime).
   - Choice variable bound to a Picklist field → medium risk (re-bind required after rename).
   - Internal element with no formula reference → low risk (safe to rename).
3. **Apply names from the Decision Guidance table.** Use the canonical verb + noun + qualifier shape. Keep API Name <= 80 chars; trim qualifier first if needed.
4. **Rename Decision outcomes.** Replace bare `Yes` / `No` with affirmative condition names. Name every Default outcome explicitly (`Default`, `NoMatch`, or `<NegativeCondition>_Default`).
5. **For Subflows:** if you must rename a public input/output, bump the Flow version per `flow-versioning-strategy` and update every parent Subflow call. Do NOT rely on save-time validation to catch missed callers — it won't.
6. **For Process Builder migrations:** auto-generated names like `myWaitEvent_4`, `myDecision_2` are red flags. Plan a rename pass as part of the migration, not "later" — see `process-builder-to-flow-migration`.
7. **Re-deploy and verify.** Run the flow's tests (per `flow-testing`) and check that fault paths still route to the correct `LogFault_<...>` targets. Confirm metadata diff shows only the rename, not unintended structural changes.

---

## Review Checklist

- [ ] Every element API Name matches the `<Verb>_<Object>[_<Qualifier>]` pattern; no `Get_Records_3`-style auto-names remain.
- [ ] Every variable carries a type prefix (`var`, `coll`, `map`, `formula`, `choice`, `constant`).
- [ ] Every Decision outcome has an explicit, business-readable name; no bare `Yes` / `No`; Default outcome is named (not blank).
- [ ] Every Subflow input/output uses `input` / `output` prefix and is documented in the Flow Description.
- [ ] Every fault-path target is named `LogFault_<ParentElementName>` so the route is visually obvious.
- [ ] No API Name exceeds 80 characters, contains spaces, or uses reserved words (`null`, `true`, `false`, `Id`).
- [ ] Orchestration stages are `Stage_<BusinessProcess>` and steps are `Step_<Stage>_<Action>` — never `S1`, `Step2`.

---

## Salesforce-Specific Gotchas

1. **API Name is effectively immutable post-deployment.** Salesforce permits the rename in Flow Builder, but every Subflow caller, formula reference, and fault path that referenced the old name will fail at runtime — there is no save-time validation across flow boundaries. Treat public surfaces (Subflow inputs/outputs) as a published contract.
2. **Max 80 characters for API Names.** Long verb-object-qualifier names get silently truncated by tools that ingest Flow XML. Aim for <= 60 chars in practice.
3. **Spaces and special chars are auto-replaced with underscores.** Typing `Get Open Cases` as the API Name yields `Get_Open_Cases` — but the Label keeps the spaces. Don't fight the platform; type underscores from the start so the API Name and your intent stay aligned.
4. **Renamed elements break formulas at runtime, not save time.** A formula resource referencing `{!Get_Records_3.Id}` will save fine after you rename `Get_Records_3` to `Get_OpenCases`, but it will throw `Couldn't find an Element` at the next interview. There is no global rename tool — you must update every formula manually.
5. **Process Builder → Flow migrations inherit ugly auto-generated names** like `myWaitEvent_4`, `myDecision_2`, `myRule_1_A1`. The migration tool does not rename these. If you skip the rename pass, the resulting flow is harder to maintain than the Process Builder it replaced. Bake the rename into the migration plan.
6. **Reserved words silently shadow built-ins.** Naming a variable `Id` or `null` causes formulas to behave unexpectedly. Salesforce will sometimes refuse to save and sometimes save and fail at runtime — never rely on the save-time check.
7. **Decision outcome order matters when names are weak.** If two outcomes are both named `Yes`, the first one matched wins, and a refactor that re-orders outcomes silently changes routing. Strong, distinct outcome names eliminate this class of bug.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Renamed Flow XML | The Flow with element + variable API Names normalized to the canonical pattern |
| Decision outcome rename map | Old name → new name, including explicit Default names |
| Subflow contract document | Inputs / outputs with API Name + Type + Description, ready to paste into the Flow Description field |
| Audit table | Non-conforming element names + proposed replacement + rename risk class (high / medium / low) |
| Migration cleanup list (PB→Flow) | List of `myWaitEvent_<n>` / `myDecision_<n>` style names with target replacements |

---

## Related Skills

- `flow/flow-versioning-strategy` — bump the version when renaming Subflow inputs/outputs (the contract change requires a version bump).
- `flow/flow-error-monitoring` — defines the broader fault-path skeleton; this skill names the fault-path target elements consistently with that skeleton.
- `flow/process-builder-to-flow-migration` — migration pass should include a rename step using this skill's patterns.
- `flow/flow-resource-patterns` — companion skill on choosing the right resource type; this skill governs how to name them once chosen.
- `flow/orchestration-flows` — Stage / Step naming conventions in this skill apply to Orchestration designs.
- `admin/naming-conventions` (and `templates/admin/naming-conventions.md`) — canonical naming for objects, fields, and metadata outside Flow Builder.

---

## Official Sources Used

- Salesforce Help — Flow Builder Element Reference: https://help.salesforce.com/s/articleView?id=platform.flow_ref_elements.htm
- Salesforce Help — Flow Concepts and Terms (API Name vs Label): https://help.salesforce.com/s/articleView?id=platform.flow_concepts_terms.htm
- Salesforce Help — Flow Resource Reference: https://help.salesforce.com/s/articleView?id=platform.flow_ref_resources.htm
- Salesforce Help — Subflow Element: https://help.salesforce.com/s/articleView?id=platform.flow_ref_elements_subflow.htm
- Salesforce Help — Orchestration Stage and Step: https://help.salesforce.com/s/articleView?id=platform.orchestrator_create_stage.htm
- Salesforce Architects — Well-Architected Operational Excellence: https://architect.salesforce.com/well-architected/trusted/resilient
