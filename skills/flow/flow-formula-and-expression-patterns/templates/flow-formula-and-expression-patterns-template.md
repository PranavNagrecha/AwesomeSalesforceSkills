# Flow Formula And Expression Patterns — Work Template

Fill this in as you go. Every row exists because skipping it produced a defect that
deployed cleanly — the cross-references point at the gotcha that documents each one.

## Scope

**Skill:** `flow-formula-and-expression-patterns`

**Request summary:**

**Flow API name / file path:**

**Flow type:** Screen / Autolaunched / Record-triggered (before-save / after-save) / Scheduled

## 1. The contract (answers to the Questions table in SKILL.md)

| Question | Answer |
|---|---|
| Return type, and is `<dataType>` written in the XML? | |
| `<scale>` needed (Number/Currency only)? | |
| Which operands can be null on a real record? | |
| Entry condition: `filterFormula` or `filters` + `filterLogic`? | |
| Prior-value test needed? `doesRequireRecordChangedToMeetCriteria` or `$Record__Prior`? | |
| Picklist fields touched, and comparison rewritten to `ISPICKVAL` / `INCLUDES`? | |
| Reference count × worst-case loop iterations | |
| Target org's Process Automation Settings match source? | |

## 2. Resource inventory

| Resource name | dataType | scale | Referenced by (elements) | Inside a Loop? |
|---|---|---|---|---|
| | | | | |

## 3. Null-guard ledger

| Operand | Nullable? | Guard applied | Compound field? (Gotcha 47) |
|---|---|---|---|
| | | | |

## 4. Grounding

Function-semantics claims made in this work that rest on the unfetchable Formula Operators
and Functions help article, each needing an `UNVERIFIED (<date>)` marker where it is stated:

-

Result of `SELECT Function.Name FROM FormulaFunctionAllowedType WHERE Type = 'FLOW' AND
Function.Name IN (...)` against the target org:

-

## 5. Checklist

Copy the Review Checklist from SKILL.md and tick as you go. The mechanical half is:

```bash
python3 scripts/check_flow_formula_and_expression_patterns.py \
  --manifest-dir <retrieved source> --strict
```

- [ ] Checker exits 0
- [ ] `FlowTest` written and asserts the guarded value, not the arithmetic
- [ ] Every `{!name}` resolves within the flow
- [ ] No numeric platform limit stated without a guide line beside it

## 6. Deviations

Record anything done differently from the patterns in SKILL.md, and why. Undocumented
tokens used (`$Record__Prior`, `$Flow.FaultMessage`, an inline formula-mode decision rule)
belong here with an explicit acceptance.
