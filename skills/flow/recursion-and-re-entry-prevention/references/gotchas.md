# Gotchas — Flow Recursion and Re-Entry Prevention

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Flow has no per-transaction static state (UNVERIFIED 2026-10-20)

**What happens:** An engineer transferring patterns from Apex reaches for the `static Boolean alreadyRan` idiom and finds nothing equivalent in Flow. They assume "the platform must prevent recursion automatically" and ship a Flow that loops at runtime.

**When it occurs:** Any record-triggered Flow whose update DML re-satisfies the entry criteria, directly or via another Flow.

**How to avoid:** Always model recursion prevention as a record-field state (state guard, hash, or lock). The only documented ceiling is the stack-depth limit of 16 (apexdev 264 L19762), which is a circuit breaker, not a fix. UNVERIFIED (2026-10-20): "Flow has no static state" itself is not in the corpus.

---

## Gotcha 2: A depth-limit failure doesn't tell you which Flow is at fault

**What happens:** The failure comes at depth 16 (apexdev 264 L19762), long after the offending Flow first fired. UNVERIFIED (2026-10-20): the error text `Maximum trigger depth exceeded` and what it names are not in the corpus.

**When it occurs:** Any time multiple automations cascade past 16 nested updates. With Apex + Flow + Workflow Rules + Process Builder all wired on the same object, finding the culprit takes triage.

**How to avoid:** Enable debug logs (Apex Code accepts FINER, api_meta 264 L13295) and trace the order-of-execution. The offending Flow appears repeatedly in the trace at increasing depth. Map out every automation on the object before changing anything; loops often span layers.

---

## Gotcha 3: `ISCHANGED()` is true even when the Flow's own DML caused the change

**What happens:** A Flow on Account fires when `ISCHANGED(Status__c)` is true. The Flow updates `Status__c` itself. On the next save cycle, `ISCHANGED(Status__c)` is true again — the Flow can't tell its own DML apart from a user's.

**When it occurs:** Whenever the entry criteria predicate matches the field the Flow itself writes.

**How to avoid:** Pair `ISCHANGED` with a state guard (Pattern 1) — `AND(ISCHANGED(Status__c), Status__c <> Last_Tracked_Status__c)` — and update the tracking field at the end of the Flow.

---

## Gotcha 4: Before-save Flows re-run inside cascades started elsewhere

**What happens:** An engineer assumes "before-save = no DML, so no recursion." It's true the before-save Flow doesn't perform a separate save on the same record, but it runs again on every later save of that record. The metadata describes it as making "more updates to that record before it's saved" (api_meta 264 L75266-75268), so it does not itself update related records; the earlier claim that it can do so "via in-memory assignment" is CONTRADICTED by that line and removed.

**When it occurs:** A cascade started by an after-save Flow, an Apex trigger or other DML saves the record again, and the before-save Flow runs again with the new values.

**How to avoid:** Include before-save Flows in the cross-object cascade map, because they re-run on every save in the chain. They are safer for self-recursion on the same record, but offer no protection for cross-object loops.

---

## Gotcha 5: Process Builder and Workflow Rules are still firing in many production orgs

**What happens:** A team migrates Process Builder logic to Flow but doesn't deactivate the original Process Builder. Both fire on the same save, potentially in different orders, and the Flow's "loop fix" doesn't apply to the Process Builder side.

**When it occurs:** Mid-migration orgs, or orgs where deactivation was pending and forgotten.

**How to avoid:** Audit all automation on the object before designing the recursion fix. Workflow Rules and Process Builder processes must show "Inactive" for migrated logic (a workflow field update re-runs triggers, not flows, apexdev 264 L15659-15662). The migration audit should be the first step, not the recursion fix.

---

## Gotcha 6: The 16 is a stack depth, not a record count

**What happens:** A bulk update of 200 records each triggers its own loop. The limit counts nested trigger invocations (apexdev 264 L19762); UNVERIFIED (2026-10-20): whether each record's loop is counted independently is not documented. Bulk operations still make the failure more spectacular, not less.

**When it occurs:** Data Loader operations, mass-update flows, batch jobs touching many records.

**How to avoid:** Test the recursion fix with a 200-record bulk DML. If any single record loops, all 200 can (UNVERIFIED 2026-10-20: inference).

---

## Gotcha 7: Flow tests don't simulate the full automation save chain

**What happens:** A Flow test passes against a fixture record, but the production loop only manifests when the full automation stack (Apex triggers + other Flows + Process Builder) runs in sequence. The test gives false confidence.

**When it occurs:** Any team relying solely on Flow Builder's built-in test capability to verify recursion fixes.

**How to avoid:** Pair Flow tests with Apex tests that exercise the originating user-facing DML and inspect the full post-condition. The Apex test runs the entire save chain; the Flow test only runs the one Flow.
