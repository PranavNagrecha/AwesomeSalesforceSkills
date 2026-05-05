# LLM Anti-Patterns — Flow Orchestration Patterns

Mistakes AI coding assistants commonly make when advising on Flow
Orchestration.

---

## Anti-Pattern 1: Recommending orchestration for single-decision approvals

**What the LLM generates.** "Build a Flow Orchestration with one
stage containing a screen-flow Work Item assigned to the manager."

**Why it happens.** Orchestration is the newest hammer; the LLM
reaches for it.

**Correct pattern.** Single-decision approvals → Approval Process
or a screen flow on the record page. Reach for orchestration only
when ≥ 2 stages OR ≥ 2 humans involved at different steps.

**Detection hint.** Any "single-stage, single-step" orchestration
recommendation is overengineering.

---

## Anti-Pattern 2: Sequential stages where parallel-within-stage was wanted

**What the LLM generates.** Three steps in three sequential stages,
when the requirement was "all three happen in parallel".

**Why it happens.** Top-to-bottom visual reading of a process
diagram suggests sequential stages.

**Correct pattern.** Steps within a stage run in parallel by
default. Parallel work goes in the same stage; sequential work goes
in separate stages.

**Detection hint.** Any orchestration where "stages run in parallel"
is the architectural intent — wrong by construction; that's
"steps", not "stages".

---

## Anti-Pattern 3: Specific-user assignee on a multi-week step

**What the LLM generates.** "Assign the step to the user
`finance.approver@acme.com`."

**Why it happens.** "The finance approver" is a known person;
hardcoding feels right.

**Correct pattern.** For long-running steps, queue-based
assignment. The queue's membership can change over time; the
orchestration doesn't break when the named user leaves.

**Detection hint.** Any specific-user assignment on a step that may
take days is a brittleness landmine.

---

## Anti-Pattern 4: Formula-derived assignee with no null fallback

**What the LLM generates.**

```
Assignee: {!$Record.Account.Owner.ManagerId}
```

**Why it happens.** Formula handles 90% of cases; the LLM doesn't
surface that null managers / inactive users break the step.

**Correct pattern.** `IF(NOT(ISBLANK(...)), ..., <fallback>)` where
the fallback is a default-approver custom-setting value or a queue.

**Detection hint.** Any formula assignee without an `ISBLANK` /
fallback is going to leave Work Items stuck on edge cases.

---

## Anti-Pattern 5: Background-step flows without fault paths

**What the LLM generates.** Background steps that are autolaunched
flows with the default fault behavior (the org-default exception
recipient).

**Why it happens.** "Just write the autolaunched flow" — the LLM
doesn't transfer the orchestration's silent-failure-mode awareness.

**Correct pattern.** Every background step's flow follows
`flow/flow-error-notification-patterns` — fault paths publish to
`Flow_Error_Event__e` or insert into `Flow_Error_Log__c`, with
admin notification cadence.

**Detection hint.** Any orchestration with background steps that
doesn't reference fault-path patterns is silently failing somewhere.

---

## Anti-Pattern 6: No cancel pathway

**What the LLM generates.** Multi-stage orchestration design with
no mechanism to cancel an in-flight orchestration.

**Why it happens.** "How do I cancel" isn't part of the requirement
the user stated; the LLM doesn't volunteer it.

**Correct pattern.** Every orchestration design includes a cancel
pathway — `Cancelled__c` flag on source record, every step /
evaluation flow checks it and short-circuits. Document the admin
action that triggers cancel.

**Detection hint.** Any orchestration design that doesn't include
"how to cancel" is missing the operational answer to "we need to
abort this".

---

## Anti-Pattern 7: Treating orchestration as Process Builder replacement

**What the LLM generates.** Multi-stage orchestration where each
stage is a single background step doing a single field update or
notification.

**Why it happens.** Process Builder deprecation; the LLM picks the
nearest "newer" tool without weighing fit.

**Correct pattern.** Process Builder's actual replacement is
record-triggered flow (single-transaction, all actions in one flow).
Orchestration is for multi-human / multi-day; using it for
single-transaction automation adds asynchronous boundaries with no
benefit.

**Detection hint.** Any "migrate Process Builder to orchestration"
recommendation should default to "migrate to record-triggered flow"
and only suggest orchestration if the original Process Builder spans
human input and time delays.

---

## Anti-Pattern 8: Editing orchestration metadata while orchestrations are in flight

**What the LLM generates.** "Update the orchestration to add a new
stage; deploy."

**Why it happens.** Iterative-development mental model — the LLM
doesn't surface that in-flight orchestrations don't migrate.

**Correct pattern.** Schema changes to orchestrations during a quiet
period. Or accept that in-flight orchestrations will continue with
old behavior; document the mismatch for support; possibly migrate
manually for high-stakes orchestrations.

**Detection hint.** Any orchestration metadata change advice that
doesn't address in-flight orchestrations is missing the impact
analysis.
