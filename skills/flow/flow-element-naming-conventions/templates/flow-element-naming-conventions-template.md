# Flow Element Naming Conventions — Rename Decision Record

Use this template to record one rename pass on one Flow: what exists today, what
it becomes, and how risky each rename is, before anyone touches Flow Builder.

## Scope

**Skill:** `flow/flow-element-naming-conventions`

**Flow API Name:** (the Flow being renamed or authored)

**Request summary:** (new Flow, audit of an existing one, or a Process Builder /
Workflow Rule migration?)

## 1. Inventory (Recommended Workflow step 1)

Pull the Flow XML (`sf project retrieve start --metadata Flow:<FlowName>`) and
list every element whose current name does not match the pattern table in
SKILL.md's Decision Guidance section.

| Current API Name | Element Type | Label | Referenced by (formula / fault path / subflow caller) | Conforms? |
|---|---|---|---|---|
| | | | | |

## 2. Rename Risk Classification (step 2)

Classify each non-conforming name using SKILL.md's three risk tiers:

- **High** — Subflow input/output variable; a parent flow calls it by name and will
  fail at runtime with no save-time warning (Gotcha 1 / Gotcha 2).
- **Medium** — Choice variable bound to a Picklist field; renaming requires a re-bind.
- **Low** — Internal element with no formula reference; safe to rename immediately.

| Current Name | Proposed Name | Risk Class | Why |
|---|---|---|---|
| | | | |

## 3. Proposed Names (step 3)

Apply the Decision Guidance table (`<Verb>_<Object>[_<Qualifier>]` for elements,
type-token prefixes for resources). Keep API Names <= 80 chars; trim the
qualifier first if a name runs long.

## 4. Decision Outcomes (step 4)

List every Decision element in scope. Every outcome gets an affirmative
business-condition name; every Default outcome gets an explicit name — never a
blank `<defaultConnectorLabel>` and never bare `Yes` / `No`.

| Decision | Outcome (old) | Outcome (new) | Default outcome name |
|---|---|---|---|
| | | | |

## 5. Subflow Contract Changes (step 5, if any High-risk items above)

- Version bump plan (per `flow/flow-versioning-strategy`):
- Parent flows that call this Subflow and must be updated:
- Cutover plan (add the new name alongside the old, migrate callers, then retire):

## 6. Process Builder Migration Cleanup (step 6, if this is a PB/Workflow migration)

List every auto-generated name (`myWaitEvent_4`, `myDecision_2`, `myRule_1_A1`, …)
and its replacement. Do not defer this to "cleanup later" — SKILL.md Gotcha 5.

| Auto-generated name | Replacement |
|---|---|

## 7. Verification (step 7)

- [ ] `python3 skills/flow/flow-element-naming-conventions/scripts/check_flow_element_naming_conventions.py --manifest-dir <retrieved metadata path>` exits 0 (add `--strict` if the team has decided WARNs block the build)
- [ ] Flow tests pass (`flow/flow-testing`)
- [ ] Every fault path still routes to its `LogFault_<ParentElementName>` target
- [ ] Metadata diff shows only the rename — no unintended structural changes

## Review Checklist

Copy of SKILL.md's Review Checklist — tick each as you confirm it:

- [ ] Every element API Name matches `<Verb>_<Object>[_<Qualifier>]`; no `Get_Records_3`-style auto-names remain
- [ ] Every variable carries a type prefix (`var`, `coll`, `map`, `formula`, `choice`, `constant`)
- [ ] Every Decision outcome has an explicit, business-readable name; no bare `Yes`/`No`; Default outcome is named
- [ ] Every Subflow input/output uses `input`/`output` and is documented in the Flow Description
- [ ] Every fault-path target is named `LogFault_<ParentElementName>`
- [ ] No API Name exceeds 80 characters, contains spaces, or uses reserved words (`null`, `true`, `false`, `Id`)
- [ ] Orchestration stages are `Stage_<BusinessProcess>` and steps are `Step_<Stage>_<Action>`

## Notes

Record any deviation from the standard pattern here, and why (for example: the
org has adopted a different house prefix table per the "Questions to Ask"
answer, so a specific WARN code is an accepted exception rather than a defect).
