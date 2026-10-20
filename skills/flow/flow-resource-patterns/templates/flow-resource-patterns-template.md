# Flow Resource Patterns — Work Template

Use this template when choosing or reviewing the resources in a flow's data layer.

## Scope

**Skill:** `flow-resource-patterns`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Questions to Ask Before Configuring table in SKILL.md.

- Value fixed at design time, or record-dependent:
- Formulas referenced repeatedly inside a Loop:
- Variables exposed to a parent flow, page or Visualforce (`isInput`, `isOutput`):
- Choice components that must remember a selection:
- Picklist values or record list as the choice source:
- `dataType` declared on each Choice:
- Run context (`runInMode`):

## Approach

Which resource type from the decision table applies (Variable, Constant, Formula, Collection Variable, SObject Variable, Text Template, Choice, Picklist Choice Set, Record Choice Set, Collection Choice Set), and why.

## Checklist

- [ ] No duplicated literals; repeated values promoted to Constants
- [ ] Constants hold literals only, no merge fields
- [ ] Derived values computed by Formulas, not Assignments
- [ ] Collection variables typed correctly (SObject versus primitive)
- [ ] SObject field references null-guarded
- [ ] Record Choice Sets have a filter and a limit of at most 200
- [ ] Input and output flags documented for every variable a caller uses
- [ ] `check_flow_resource_patterns.py --manifest-dir` run with no ERROR

## Notes

Record any deviation from the standard pattern and why.
