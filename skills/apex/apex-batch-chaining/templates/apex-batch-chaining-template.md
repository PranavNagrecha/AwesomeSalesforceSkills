# Apex Batch Chaining — Work Template

Fill this in as you go. It is the record a reviewer reads instead of
re-deriving your design.

## Scope

**Skill:** `apex-batch-chaining`

**Request summary:** _(what the user asked for, in one sentence)_

**Links in the chain:** _(ordered, with the job type of each)_

| # | Class | Type | Object / volume | Scope |
|---|---|---|---|---|
| 1 |  | Batch / Queueable |  |  |
| 2 |  | Batch / Queueable |  |  |
| 3 |  | Batch / Queueable |  |  |

## Answers to the Questions to Ask

Copy the seven questions from SKILL.md and record the answer to each.

| Question | Answer | Consequence for the design |
|---|---|---|
| Failure semantics — proceed / stop / resume? |  |  |
| Who stops it at 2am, with what lever? |  |  |
| What state travels between links, and how big? |  |  |
| Total async executions per full run? |  |  |
| Does any link need to fan out? |  |  |
| Which failures are transient; retry ceiling? |  |  |
| How is a completed run proved tomorrow? |  |  |

## Limits Budget

| Limit | Ceiling | This chain's usage | Source |
|---|---|---|---|
| Concurrent queued/active batch jobs | 5 |  | `apexdev` L17686 |
| Holding jobs in the flex queue | 100 |  | `apexdev` L17687 |
| Async executions / 24 h (shared) | 250,000 or licences × 200 |  | `apexdev` L17689–17693 |
| `enqueueJob` per async transaction | 1 |  | `apexdev` L16175–16177 |
| Finalizer consecutive re-enqueues | 5 |  | `apexdev` L16292–16295 |
| `executeBatch` scope (QueryLocator start) | 2,000 |  | `apexrefguide` L207052–207058 |

## Approach

**Chain architecture:** _(direct `finish()` chain / orchestrator / Queueable coordinator — and why, citing the decision-guidance row in SKILL.md)_

**Kill-switch mechanism:** _(`Chain_Step__mdt` record names, and who can edit them)_

**Terminal condition:** _(step counter / zero-row query / kill-switch)_

**Correlation Id:** _(how a reviewer reconstructs one run from `AsyncApexJob` + logs)_

**Decision-tree branch consulted:** `standards/decision-trees/async-selection.md` Q__

## Checklist

Copy the Review Checklist from SKILL.md and tick as you complete each item.

- [ ] Every hand-off in `finish()` is inside a try/catch
- [ ] Capacity read as two counts, `JobType` filtered
- [ ] Exactly one `enqueueJob` on any async path
- [ ] Cross-link state via constructor or staging sObject
- [ ] Kill-switch read before every advance; `abortJob` in the runbook
- [ ] Terminal condition present
- [ ] `Database.RaisesPlatformEvents` + `BatchApexErrorEvent` subscriber
- [ ] Retry ceiling set below 5, gated on an exception allowlist
- [ ] Tests assert the recorded hand-off request
- [ ] `check_apex_batch_chaining.py --strict` clean or findings adjudicated
- [ ] Correlation Id makes the chain reconstructable

## Checker Output

```text
(paste: python3 skills/apex/apex-batch-chaining/scripts/check_apex_batch_chaining.py --manifest-dir force-app --strict)
```

**Findings adjudicated (advisories and any accepted WARNs):**

| Code | File:line | Why it is acceptable here |
|---|---|---|
|  |  |  |

## Notes

_(deviations from the standard pattern and why; anything an on-call engineer
would need at 2am that is not in the runbook)_
