# Well-Architected Notes — Recursive Trigger Prevention

## Relevant Pillars

### Reliability

Recursion bugs commonly surface as rollbacks, duplicate actions, or silently skipped work. Preventing them is primarily a reliability concern.

Tag findings as Reliability when:
- the same logical work executes multiple times unexpectedly
- an overbroad guard skips required processing
- trigger re-entry causes data corruption or duplicate side effects

### Scalability

Recursive behavior multiplies transaction cost and can explode SOQL, DML, and CPU usage.

Tag findings as Scalability when:
- self-DML amplifies limit consumption
- a broad guard was chosen because the volume behavior was not understood
- multi-record transactions behave unpredictably under recursion

### Operational Excellence

Teams need a shared, explainable recursion pattern instead of ad hoc static flags.

Tag findings as Operational Excellence when:
- recursion prevention logic is duplicated or inconsistent
- frameworks and handlers use different guard rules
- support teams cannot explain why some records were skipped

## Architectural Tradeoffs

- **Broad static guard vs narrow record-aware guard:** broad is quick, narrow is usually correct.
- **Delta check vs explicit recursion state:** delta checks remove unnecessary work, while guard state protects genuine self-DML loops.
- **Local fix vs framework fix:** centralized guards help large teams when a framework already exists.
- **Guard vs bypass:** a guard shapes work that should still happen; a `TriggerControl` bypass stops it.
  A data load wants the bypass. Using a guard as a bypass produces the worst outcome — the automation
  looks enabled and does nothing.
- **Three layers, three jobs:** `TriggerControl` (should this handler run at all), `TriggerHandler`'s
  depth counter (has this become a runaway loop), `RecursionGuard` (have I already done this work for
  this record with these values). Collapsing them into one static is how the `hasRun` flag gets born.

## Anti-Patterns

1. **Global static Boolean** — suppresses more than the bug.
2. **Guard installed before root cause is known** — may hide the wrong issue.
3. **No distinction between valid re-entry and accidental loops** — correctness suffers.
4. **Guard state inferred from governor-limit counters** — limits and statics reset on different
   schedules under Bulk API, so the inference is wrong exactly where it matters.
5. **Relying on the stack-depth ceiling as the guard** — 16 is a crash barrier, not a design.

## Official Sources Used

- Apex Developer Guide, Version 67.0 (Summer '26), "Using Static Methods and Variables" — L3738–3743
  (a static variable is scoped to the Apex transaction and persists across the trigger invocations
  inside it; a recursive trigger can use a class variable to exit recursion) and L3761–3763 (a static
  declared *in a trigger* does not retain its value between trigger contexts). Grounds the whole
  "why `hasRun` is wrong" section of SKILL.md and the first three gotchas.
  <https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf>
- Apex Developer Guide, "Trigger Context Variables" — L14990–15033 (`isExecuting`, `isBefore`/`isAfter`,
  `oldMap` availability, `operationType` and the `System.TriggerOperation` enum values, and
  `Trigger.size`: "DML operations that include over 200 records are processed in batches, and the
  trigger is invoked for each batch"). Grounds the per-operation-type scoping in `RecursionGuard` and
  the 200-record chunking gotcha.
- Apex Developer Guide, "Triggers and Order of Execution" — L15414–15415 (a recursive save skips steps
  9 through 17), L15455–15460 (a workflow field update re-runs before-update and after-update triggers
  "one more time (and only one more time)"), L15468 (a flow's DML sends the record through the save
  procedure), L15494–15498 (`Trigger.old` after a workflow field update holds the pre-update values),
  L15499–15501 (partial-success DML refires triggers with static class variables not reset), and
  L15502–15504 (two triggers on the same event have no guaranteed order). Grounds the workflow re-fire,
  Apex↔Flow ping-pong, and one-trigger-per-object material.
- Apex Developer Guide, "Execution Governors and Limits" — L19559 (total stack depth for any Apex
  invocation that recursively fires triggers = 16, synchronous and asynchronous) with the footnote at
  L19638–19648 explaining why a trigger-spawning recursion is charged against a tighter ceiling than an
  in-invocation recursive call; L17856 lists `LimitException` among the uncatchable Apex exceptions.
  Grounds the stack-depth gotcha and the "the ceiling is not your guard" position.
- Apex Developer Guide, "Bulk DML Exception Handling" — L9056–9080 (the three partial-save attempts, the
  "Too many batch retries in the presence of Apex triggers and partial failures" error, governor limits
  reset between attempts, and "triggers are refired on this subset of records"). Grounds the
  partial-success gotcha and the warning against switching the example's DML to `allOrNone = false`.
- Apex Developer Guide, "Using Savepoints" — L8689–8693 (savepoint references cannot cross trigger
  invocations; static variables are not reverted during a rollback). Grounds the rollback gotcha.
- Apex Developer Guide, "Testing and Code Coverage" / test setup methods — L41032–41035 ("the static
  context of the test class is reinitialized before each transaction begins… static variable
  initializers and static blocks are executed fresh at the start of every test method"). Corrects the
  widely repeated claim that guards leak between test methods, and grounds the test design in
  `references/code-examples.md`.
- Apex Developer Guide, "Debugging Apex" — debug log code units — L38178–38190 (`CODE_UNIT_STARTED` and
  `CODE_UNIT_FINISHED` delimit units of code, a trigger is one unit, and the log line names the trigger
  and its event). Grounds the debug-log invocation-counting verification step.
- Metadata API Developer Guide, `Flow` — L68438–68441 (`triggerOrder`, int 1–2,000, API 54.0+) and
  L72322–72325 (`doesRequireRecordChangedToMeetCriteria`, API 50.0+, "conditions evaluate to true only
  if the record didn't meet the required conditions before the triggering update but now meets the
  conditions after the update"). Grounds the Flow-side half of the ping-pong fix.
  <https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf>
- Salesforce Well-Architected — reliability, scalability, and operational-excellence framing for the
  pillar tagging above.

The `sf project deploy start` / `sf apex run test` / `sf apex tail log` invocations in
`references/code-examples.md` are Salesforce CLI syntax and are not defined in any of the PDFs above.
UNVERIFIED (2026-09-05): CLI flag spellings could not be checked against an official source in this
environment; verify with `sf <command> --help` before scripting them.
