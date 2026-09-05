# Flow Governor Limits Deep Dive — Budget Record

One of these per object + trigger type, not per flow. The meters are per transaction, so the record's
unit has to be the transaction too.

## Scope

**Skill:** `flow-governor-limits-deep-dive`
**Object + trigger type:**
**Flow(s) under review:**
**Requested by / date:**

## Context Gathered

Answers to the seven questions in SKILL.md § Questions to Ask Before Configuring.

| Question | Answer | Source of the answer |
|---|---|---|
| What else is Active on this object, and what does the Apex trigger spend? | | `FlowDefinitionView` / checker W2 / code read |
| p99 records per save, and child rows per record? | | |
| Which meter does the published platform event spend? | | event definition, publish behavior |
| What does the invocable Apex action consume, and its `flowTransactionModel`? | | class read + flow XML |
| Which branches must be atomic with the save? | | business answer, not a technical one |
| Are CPU and heap measured or estimated? | | debug log / `Limits.getCpuTime()` |
| Any managed-package automation, and is the package certified? | | Setup → Installed Packages |

## Budget

Paste the filled worksheet from `references/examples.md`. Arithmetic rows may be filled at review
time; the CPU and heap rows stay blank until a batch has been run.

```text
(paste worksheet here)
```

## Checker Output

```text
python3 skills/flow/flow-governor-limits-deep-dive/scripts/check_flow_governor_limits_deep_dive.py \
  --manifest-dir <source tree>

(paste output here)
```

| Rule | Count | Disposition |
|---|---|---|
| E1 DML in loop | | |
| W1 Get Records in loop | | |
| W2 cross-flow DML total | | |
| A1 apex action without `flowTransactionModel` | | |
| A2 three or more DML, no async path | | |

## Measured Baseline

Workflow log category at `FINER`, at p99 batch size.

```text
FLOW_START_INTERVIEW_LIMIT_USAGE    :
FLOW_INTERVIEW_FINISHED_LIMIT_USAGE :   (note the denominator)
CUMULATIVE_LIMIT_USAGE              :
```

## Decision

- Spend reduced by (loops hoisted, collections staged):
- Moved to `NewTransaction`:
- Moved to `AsyncAfterCommit` (`maxBatchSize` = ):
- Atomicity given up, and the idempotency guard for it:

## Open Questions and Unverified Claims

Record anything the developer guides could not settle, so the next reviewer does not re-derive it:

- Whether the async path was metered at synchronous or asynchronous ceilings (read the denominator):
- Interviews per transaction on the synchronous path (`FLOW_START_INTERVIEWS_BEGIN` request count):
- Any figure taken from help.salesforce.com, and which claim depends on it:
