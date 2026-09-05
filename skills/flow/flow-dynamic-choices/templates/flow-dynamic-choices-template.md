# Flow Dynamic Choices — Work Template

## Scope

**Skill:** `flow-dynamic-choices`

**Request summary:** Describe the specific instance you are working on.

**Flow:** `<API name>` · **processType:** `<Flow | AutoLaunchedFlow | …>` · **apiVersion:** `<n.0>`
· **runInMode:** `<DefaultMode | SystemModeWithSharing | SystemModeWithoutSharing>`

## Context Gathered

- What the user asked for:
- Org/domain constraints relevant here:
- Relevant existing skills or templates:

## Answers to the Seven Questions

| # | Question | Answer |
|---|---|---|
| 1 | Source — picklist value set, query, or collection already held? | |
| 2 | Rows at p99, and the order they should appear in? | |
| 3 | What the user sees (`displayField`) vs what the flow stores (`valueField`)? | |
| 4 | Fields of the selected record needed downstream? | |
| 5 | What happens when the filter matches nothing? | |
| 6 | Does the filter ever need OR / mixed logic? | |
| 7 | Can the user go back and change what this depends on? | |

## Choice Set Register

One row per `<dynamicChoiceSets>` / `<choices>` element.

| Name | Kind (record / picklist / collection / static) | `dataType` | Key fields | `limit` | `sortField` + `sortOrder` |
|---|---|---|---|---|---|
| | | | | | |

## Output Map

`outputAssignments` on each record choice set — the only route to a second field.

| Choice set | `field` | `assignToReference` | Consumed by |
|---|---|---|---|
| | | | |

## Screen Field Register

| Screen | Field name | `fieldType` | `dataType` | `choiceReferences` | `defaultSelectedChoiceReference` | `isRequired` |
|---|---|---|---|---|---|---|
| | | | | | | |

## Checklist

- [ ] Recommended Workflow steps completed
- [ ] Every choice set's `dataType` matches its kind (picklist ⇒ Picklist/Multipicklist; record ⇒ not)
- [ ] Every record choice set has an explicit `limit`, `sortField` and `sortOrder`
- [ ] No `filterLogic` inside a `<dynamicChoiceSets>` element
- [ ] Every screen field's `dataType` is a `FlowScreenField` value (no `Picklist`)
- [ ] Multi-select output lands in a Text or Multipicklist variable, or is decomposed explicitly
- [ ] Every `defaultSelectedChoiceReference` is in that field's `choiceReferences`
- [ ] Empty-set branch exists upstream of the screen
- [ ] `allowBack` / `inputsOnNextNavToAssocScrn` decided rather than inherited
- [ ] `python3 scripts/check_flow_dynamic_choices.py --manifest-dir <tree> --strict` clean
- [ ] Debug-run checklist worked (no `FlowTest` — screen flows are out of its scope)
- [ ] Gotchas reviewed
- [ ] LLM anti-patterns not triggered
- [ ] Official sources consulted

## UNVERIFIED Resolved Against This Org

Anything the guides could not settle that a debug run did. Copy the answer into the flow's
`<description>` so the next author inherits it.

| Claim | How it was tested | Result |
|---|---|---|
| | | |

## Notes
