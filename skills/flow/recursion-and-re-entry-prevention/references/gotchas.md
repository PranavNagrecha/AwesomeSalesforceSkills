# Gotchas — Flow Recursion and Re-Entry Prevention

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Flow has no per-transaction static state

**What happens:** An engineer transferring patterns from Apex reaches for the `static Boolean alreadyRan` idiom and finds nothing equivalent in Flow. They assume "the platform must prevent recursion automatically" and ship a Flow that loops at runtime.

**When it occurs:** Any record-triggered Flow whose update DML re-satisfies the entry criteria, directly or via another Flow.

**How to avoid:** Always model recursion prevention as a record-field state (state guard, hash, or lock). The platform's only ceiling is the trigger-depth limit, which is a circuit breaker, not a fix.

---

## Gotcha 2: "Maximum trigger depth exceeded" doesn't tell you which Flow is at fault

**What happens:** The error is thrown at depth 16 by the platform's cascade detector — long after the offending Flow first fired. The error message names the platform-level limit, not a specific Flow node.

**When it occurs:** Any time multiple automations cascade past 16 nested updates. With Apex + Flow + Workflow Rules + Process Builder all wired on the same object, finding the culprit takes triage.

**How to avoid:** Enable Apex + Flow debug logs at FINER and trace the order-of-execution. The offending Flow appears repeatedly in the trace at increasing depth. Map out every automation on the object before changing anything; loops often span layers.

---

## Gotcha 3: `ISCHANGED()` is true even when the Flow's own DML caused the change

**What happens:** A Flow on Account fires when `ISCHANGED(Status__c)` is true. The Flow updates `Status__c` itself. On the next save cycle, `ISCHANGED(Status__c)` is true again — the Flow can't tell its own DML apart from a user's.

**When it occurs:** Whenever the entry criteria predicate matches the field the Flow itself writes.

**How to avoid:** Pair `ISCHANGED` with a state guard (Pattern 1) — `AND(ISCHANGED(Status__c), Status__c <> Last_Tracked_Status__c)` — and update the tracking field at the end of the Flow.

---

## Gotcha 4: Before-save Flows still participate in cross-record cascade loops

**What happens:** An engineer assumes "before-save = no DML, so no recursion." It's true the before-save Flow doesn't perform a separate save on the same record, but it can still update *related* records via in-memory assignment that *do* save and trigger downstream automations.

**When it occurs:** Before-save Flows that modify related-record fields, or that work in a chain where the *next* record save triggers the next Flow.

**How to avoid:** Treat before-save Flows like after-save Flows for the purpose of cross-object cascade analysis. They are safer for self-recursion on the same record, but offer no additional protection for cross-object loops.

---

## Gotcha 5: Process Builder and Workflow Rules are still firing in many production orgs

**What happens:** A team migrates Process Builder logic to Flow but doesn't deactivate the original Process Builder. Both fire on the same save, potentially in different orders, and the Flow's "loop fix" doesn't apply to the Process Builder side.

**When it occurs:** Mid-migration orgs, or orgs where deactivation was pending and forgotten.

**How to avoid:** Audit all automation on the object before designing the recursion fix. `Setup → Workflow Rules` and `Setup → Process Builder` lists must show "Inactive" for migrated logic. The migration audit should be the first step, not the recursion fix.

---

## Gotcha 6: The 16-depth limit is per-record, not per-transaction

**What happens:** A bulk update of 200 records each triggers its own loop. The team assumes "16 across the transaction" and concludes the fix doesn't need to scale. Each record can independently reach depth 16, and bulk operations make the failure more spectacular, not less.

**When it occurs:** Data Loader operations, mass-update flows, batch jobs touching many records.

**How to avoid:** Test the recursion fix with a 200-record bulk DML. If any single record loops, all 200 can.

---

## Gotcha 7: Flow tests don't simulate the full automation save chain

**What happens:** A Flow test passes against a fixture record, but the production loop only manifests when the full automation stack (Apex triggers + other Flows + Process Builder) runs in sequence. The test gives false confidence.

**When it occurs:** Any team relying solely on Flow Builder's built-in test capability to verify recursion fixes.

**How to avoid:** Pair Flow tests with Apex tests that exercise the originating user-facing DML and inspect the full post-condition. The Apex test runs the entire save chain; the Flow test only runs the one Flow.
