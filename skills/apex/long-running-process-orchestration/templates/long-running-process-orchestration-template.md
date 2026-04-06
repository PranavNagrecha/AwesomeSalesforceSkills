# Long-Running Process Orchestration — Work Template

Use this template when designing, implementing, or reviewing multi-step async orchestration in Apex.

## Scope

**Skill:** `long-running-process-orchestration`

**Request summary:** (fill in what the practitioner or stakeholder asked for)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md:

- **Process steps and sequencing:** (list each step, its inputs, outputs, and dependencies)
- **Governor limit exposure per step:** (DML count, SOQL count, callout count, CPU estimate per step)
- **Callout steps:** (which steps require `Database.AllowsCallouts`)
- **External participants:** (any steps triggered by external callbacks or human actions)
- **Failure recovery expectations:** (retry count, compensation behavior, dead-letter handling)
- **Progress visibility requirements:** (who needs to see process state, and how — dashboard, record, email)

## Pattern Selection

Which pattern from SKILL.md applies? (check one)

- [ ] Bounded Queueable chain — simple sequential, no external waits, ≤7 steps
- [ ] Platform Event state machine — external participants, time-separated steps, or fan-out
- [ ] Hybrid — Queueable chains within phases, Platform Events between phases
- [ ] Continuation — UI-initiated long callout (LWC/Aura/VF only)

**Rationale:** (explain why this pattern fits the requirements above)

## State Model

Define the process instance state that must survive transaction boundaries:

| Field | Type | Purpose |
|---|---|---|
| (e.g.) `orderId` | Id | Record being processed |
| `currentStep` | Integer or String | Which step is next |
| `retryCount` | Integer | Retry attempts for current step |
| `lastError` | String | Error message from last failure |
| (add fields) | | |

**Custom Object name:** (e.g., `OrderFulfillment__c`)
**Required fields:** Status__c, CurrentStep__c, RetryCount__c, LastError__c, StepUpdatedAt__c

## Step Breakdown

For each step, fill in:

| Step | Queueable Class | Callouts? | Max DML | Finalizer? | Next Step |
|---|---|---|---|---|---|
| 1 — (name) | (ClassName) | Yes/No | (estimate) | Yes/No | 2 or Event |
| 2 — (name) | (ClassName) | Yes/No | (estimate) | Yes/No | 3 or Event |
| (add rows) | | | | | |

## Checklist

Copy from SKILL.md Review Checklist and tick as you complete each item:

- [ ] Each step is a separate Queueable with its own transaction boundary
- [ ] `System.attachFinalizer()` called as the first line of every Queueable `execute()` with side effects
- [ ] `AsyncOptions.MaximumQueueableStackDepth` set on every `System.enqueueJob()` call in the chain
- [ ] `System.AsyncInfo.getCurrentQueueableStackDepth()` used to guard against exceeding the cap
- [ ] State passed through serializable constructor fields — no static variables
- [ ] Custom Object checkpoint record tracks current step, retry count, and error state
- [ ] Finalizer retry logic increments a counter and aborts after configurable maximum
- [ ] Platform Event triggers are thin — delegate heavy work to Queueable workers
- [ ] Callout Queueables implement `Database.AllowsCallouts`
- [ ] Tests verify Custom Object checkpoint state after `Test.stopTest()`

## Deviations And Notes

Record any deviations from the standard pattern and the reason for each:

- (e.g., "Step 3 uses a scheduled batch instead of Queueable because volume exceeds 50K records per run — see batch-apex-patterns skill")
