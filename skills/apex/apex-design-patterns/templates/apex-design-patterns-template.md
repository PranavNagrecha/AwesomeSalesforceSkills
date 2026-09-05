# Apex Layering Worksheet

Fill this in before writing a class. Rows 1–7 are the questions from
`SKILL.md` § Questions to Ask Before Configuring; the rest records the decisions
that reviewers otherwise re-litigate.

## 1. Answers That Decide The Design

| Question | Answer | What it decides |
|---|---|---|
| Largest batch this code will ever see (UI save / 200-row trigger chunk / Bulk API job)? | | Recursion-guard shape — `Set<Id>` vs a boolean |
| Must any step be undone if a later step fails? | | Whether a savepoint exists at all |
| Which behaviours vary by business unit / record type / org? | | Whether a strategy interface + `__mdt` is justified |
| Which of these classes is an entry point? | | The sharing keyword per class |
| API version these classes are saved at? | | `apiVersion` in every `.cls-meta.xml` |
| Who owns the field list, and does every caller need it? | | Selector method granularity |
| Which abstractions pay for themselves today? | | The stop line — see § 4 |

## 2. Entry Points

- Trigger:
- Controller / REST / Invocable:
- Scheduler / Async:

## 3. Proposed Layers

| Concern | Class | Extends | Sharing keyword | Notes |
|---|---|---|---|---|
| Trigger adapter | `...Trigger` | — | n/a | one line only |
| Dispatch | `...TriggerHandler` | `templates/apex/TriggerHandler.cls` | | |
| Object-specific rules | `...Domain` | `templates/apex/BaseDomain.cls` | | no SOQL / DML / callouts |
| Data access | `...Selector` | `templates/apex/BaseSelector.cls` | `inherited sharing` | one method per intent |
| Orchestration | `...Service` | `templates/apex/BaseService.cls` | | owns the savepoint |
| Swappable behaviour | `I...Strategy` + impls | — | | one impl per variant |
| Factory / resolver | `...Factory` | — | | `Type.forName` + fallback |

## 4. Unit Of Work

- Public service method that owns the savepoint:
- Objects written inside it:
- What "partial success is acceptable" would mean here (if it is, use `Database.insert(rows, false)` instead):
- Reset hooks called in the `catch` alongside `rollbackTransaction(sp)`:

## 5. Strategy Rows

| `__mdt` record | Key field value | Apex class | Active? | Fallback if missing |
|---|---|---|---|---|
| | | | | |

## 6. Deliberately Not Abstracted

| Thing left concrete | Why | Revisit when |
|---|---|---|
| | | |

## 7. Review Guardrails

- [ ] Entry points are thin adapters
- [ ] Query definitions are centralized where reuse exists
- [ ] Domain rules are not duplicated across entry points
- [ ] Dependency seams avoid `Test.isRunningTest()`
- [ ] Class names match real responsibilities
- [ ] Every class, inner classes included, declares a sharing keyword
- [ ] Every `abstract` / `override` method has an explicit access modifier
- [ ] Exactly one savepoint per service method, rolled back before logging
- [ ] Every static mutable collection has a reset hook
- [ ] Every dynamically-named class is public, top-level, and constructor-free
- [ ] Tests cover 200 records, every strategy row, and the rollback path
