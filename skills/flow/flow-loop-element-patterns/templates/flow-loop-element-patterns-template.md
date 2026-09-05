# Flow Loop Element Patterns — Loop Review Worksheet

One worksheet per flow. Fill the inventory from the flow XML (or from
`python3 scripts/check_flow_loop_element_patterns.py --manifest-dir <dir>`), then work the
verdict column. A row is not closed until it names the refactor or the reason none is needed.

## Scope

**Skill:** `flow-loop-element-patterns`
**Flow under review:** `<Flow API name>` · `<apiVersion>` · `<processType>` · `<triggerType>`
**Reviewer / date:**
**Request summary:**

## Answers to the seven questions

Copy the answers, not the questions. An unanswered row is a design decision you are about
to make by accident.

| # | Question | Answer |
|---|---|---|
| 1 | Worst-day size of the input collection | |
| 2 | What the loop body does (edit / write / query / subflow / count) | |
| 3 | Where edited records get written | |
| 4 | Second collection iterated inside the first? | |
| 5 | Does iteration order change the result? | |
| 6 | Behaviour when the collection is empty | |
| 7 | Flow `<apiVersion>`, plus subflows and actions the body calls | |

## Loop inventory

One row per `<loops>` node, in the flow and in every subflow it calls.

| Loop name | `collectionReference` | sObject | `assignNextValueToReference` | `iterationOrder` | `noMoreValuesConnector` wired? | Body classification | Expected iterations | Verdict |
|---|---|---|---|---|---|---|---|---|
| | | | | | | Pure / DML / SOQL / Action / Subflow / Nested | | Keep / Refactor / Delete |

Body classification legend: **Pure** = Assignment and Decision only · **DML** = Create /
Update / Delete inside the body · **SOQL** = Get Records inside the body · **Action** =
Apex invocable or other action · **Subflow** = recurse and re-classify the child ·
**Nested** = a second `<loops>` reachable from this one's `nextValueConnector`.

## Loop-free ladder

Work top to bottom. The first row that applies ends the exercise.

| Rung | Applies? | Note |
|---|---|---|
| Get Records `filters` / `sortField` / `sortOrder` / `limit` (2–20,000, API 63.0+) does it in the database | | |
| Sort processor with `sortOptions` + `limit` (API 51.0+) bounds the working set | | |
| Filter processor (API 53.0+) replaces Loop → Decision → Assignment(Add) | | |
| Map processor `RecommendationMapCollectionProcessor` (API 53.0+) replaces Loop → build → Add | | |
| `AssignCount` (API 43.0+) replaces a counter loop | | |
| `RemoveUncommon` / `RemoveAll` (API 43.0+) replace a two-collection comparison | | |
| A Loop is genuinely required — staged-collection shape below | | |

## Checklist

From SKILL.md § Review Checklist. Tick or record the exception.

- [ ] No Create / Update / Delete Records inside any loop body, directly or via subflow or action
- [ ] No Get Records inside any loop body
- [ ] Every loop-variable edit is paired with an `Add` into a separate collection and one post-loop DML
- [ ] No nested loops, or the inner one is documented as hard-bounded with the Filter alternative rejected in writing
- [ ] Every `<loops>` node has a wired `noMoreValuesConnector`
- [ ] Nothing the post-loop path needs is initialised inside the loop body
- [ ] `iterationOrder` is not standing in for a sort
- [ ] `faultConnector` on the Get Records feeding the loop and on the DML following it
- [ ] Each `collectionProcessors` element carries exactly one of `formula` or `conditions`, matching its `conditionLogic`
- [ ] Any Map processor names an `assignNextValueToReference`
- [ ] `body_elements × iterations` read against 10,000 ms sync CPU, not against a 2,000-element ceiling
- [ ] Subflows called inside a loop inspected for hidden DML / SOQL
- [ ] `python3 scripts/check_flow_loop_element_patterns.py --manifest-dir <dir>` reports no findings
- [ ] A `FlowTest` asserts the staged collection is non-empty and the post-loop DML has no error

## Checker output

```
paste the run here, or "No issues found."
```

## Verification evidence

| Check | Command / query | Result |
|---|---|---|
| Records actually written | the count-by-stage SOQL in `references/metadata-examples.md` § Verification | |
| Real iteration count | `grep -c FLOW_LOOP_DETAIL` on a Workflow-`FINER` debug log | |
| Records per DML element | `grep FLOW_BULK_ELEMENT_DETAIL` | |
| CPU against 10,000 ms | `grep FLOW_INTERVIEW_FINISHED_LIMIT_USAGE` | |

## Deviations

Record any place this flow departs from the staged-collection shape in
`references/metadata-examples.md` §2, and why the departure is safe.
