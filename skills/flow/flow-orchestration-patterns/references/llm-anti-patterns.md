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
analysis. Any sentence that prints "running orchestrations stay on
the version they started on" as platform law is unsourced — that
claim is not in Help, release notes, or the Object Reference.

---

## Anti-Pattern 10: Evaluation flow that returns `isComplete` / `shouldExit` / anything except the reserved name

**What the LLM generates.** An autolaunched flow with a Boolean
output named `isComplete` or `stageDone`, assigned as the stage
exit evaluation flow.

**Why it happens.** "Return a boolean" is the whole instruction the
model remembers.

**Correct pattern.** Output variable **must** be named
`isOrchestrationConditionMet`. Any other name is discarded
silently. Help: `platform.orchestrator_considerations_evaluation_flows`.

**Detection hint.** An evaluation flow whose Boolean output is not
exactly `isOrchestrationConditionMet`.

---

## Anti-Pattern 11: Assignee as a 15- or 18-character User Id

**What the LLM generates.** `<assignee><stringValue>005…</stringValue></assignee>`
or "assign to `$Record.OwnerId`".

**Why it happens.** Every other Salesforce API takes an Id.

**Correct pattern.** Interactive-step `<stringValue>` assignees are
**usernames**, resolved and `IsActive`-checked at **deploy**. A
User Id is rejected at deploy. `$Record.Owner.ManagerId` can
deploy and fail at run time. Prefer a queue.

**Detection hint.** `005` in orchestration assignee XML, or
`Owner.ManagerId` as the only assignee with no fallback.

---

## Anti-Pattern 12: Dotted `StepName.output` references

**What the LLM generates.** Stage-entry condition
`Evaluate_Deal_Risk.financeReviewRequired`.

**Why it happens.** Subflow / Get-Records dotted paths work in
ordinary Flow.

**Correct pattern.** Capture the step output into an orchestration
variable, then read the variable. A dotted step-output path is
rejected (`element doesn't exist`).

**Detection hint.** Any orchestration expression that dots into a
step API name.

---

## Anti-Pattern 9: Quoting the retired 600-run orchestration entitlement

**What the LLM generates.** "Flow Orchestration is a paid add-on"
or "you get 600 free orchestration runs per org per year (except
flow approvals), then you buy more" — usually offered as the reason
to reject an orchestration design.

**Why it happens.** That usage-based entitlement was real until
Spring '26 (week of 16 February 2026), so it saturates pre-2026
training data — and it's a licensing claim, so repeating it can
cost the customer a design they're already entitled to.

**Correct pattern.** Orchestration runs are included with no
usage-based limitations in the editions Salesforce lists on the
**Flow Orchestration** entitlements page — confirm that page and
the org's entitlement, do not paste the Flow Approval Processes
edition list. Choose orchestration on fit (multi-stage /
multi-human / multi-day), not on a run budget. Do not quote `$1
per run` or `600 runs`; those trace to a pre-GA projection. If
asked whether runs are metered **today**, say you could not
confirm current metering and they should check their own
entitlement.

**Detection hint.** Any answer that prices orchestration, counts
runs against an annual allowance, or carves out "except flow
approvals" is quoting a retired entitlement. Any answer that copies
the **Flow Approval Processes** edition list ("all Einstein 1
editions") onto Orchestration is merging two adjacent Help
sections — Spring '26 Flow Orchestration *Where* clauses list
Enterprise, Performance, Unlimited, and Developer, not
Professional. Confirm the org's own entitlement screenshot before
printing an edition list.
