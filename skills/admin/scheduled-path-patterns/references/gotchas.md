# Gotchas — Scheduled Path Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: The scheduled branch runs against stale field values unless you re-query

**What happens:** A Case Flow schedules "24 hours after creation, if still open, escalate." A rep closes the Case an hour later. The scheduled branch fires the next day and escalates a closed Case, because the record variable the branch evaluates is the snapshot captured when the interview was queued, not the record's current state.

**When it occurs:** Every scheduled path whose condition can change during the wait — which is nearly all of them, since the reason for waiting is usually that something might change.

**How to avoid:** Put a Get Records element at the top of the scheduled branch, re-read the record by Id, and make every decision off the freshly-read variable. Do not branch off `$Record` in a scheduled path. Treat the path's own entry criteria as a coarse pre-filter and the re-read as the actual decision.

---

## Gotcha 2: The offset is computed once, at queue time — editing the source field does not reschedule

**What happens:** A path is configured as "30 days before `Renewal_Date__c`". Sales moves the renewal date out by two months. The reminder still fires on the original schedule, because the interview's execution time was calculated when the interview was created.

**When it occurs:** Any field-anchored path on a date that the business routinely revises — renewal dates, close dates, go-live dates, contract end dates.

**How to avoid:** Add a second record-triggered path on `ISCHANGED(Renewal_Date__c)` that cancels or supersedes the stale reminder, or move the reminder to a scheduled (batch) Flow that re-evaluates all records nightly against the *current* field value. A daily sweep is less elegant than a scheduled path and it is correct under field edits; the scheduled path is not.

Note also that the offset unit vocabulary is fixed. The Metadata API's `FlowScheduledPathOffsetUnit` enumeration documents its "possible values" as "Months, Days, Hours, Minutes" — there is no Weeks and no Seconds, so "two weeks before" is authored as 14 Days.

---

## Gotcha 3: The scheduled branch is a separate asynchronous transaction with different limits

**What happens:** A path that loops over a collection and calls an Apex action works in a low-volume sandbox and then, on a bulk load, fails partway with limit errors. The scheduled branch does not share the triggering transaction's limit budget — it gets its own, and those limits are the *asynchronous* ones.

**When it occurs:** Bulk inserts and data loads, which queue interviews in bulk and resume them in batches.

**How to avoid:** Design the branch against the asynchronous numbers, which are the generous ones for CPU and heap and the tight ones nowhere: 200 SOQL queries (versus 100 synchronous), 150 DML statements, 50,000 records retrieved by SOQL, 12 MB heap (versus 6 MB), and a "Maximum CPU time on the Salesforce servers" of 60,000 milliseconds (versus 10,000 synchronous). The two that actually bite in a resumed path are the DML statement count and the 10,000-record ceiling on "Total number of records processed as a result of DML statements" — both are shared across the whole batch of interviews resumed together, not per interview.

The practical rule: never put an unbounded loop with a DML element inside it in a scheduled branch. Build a collection, commit once.

---

## Gotcha 4: A scheduled path calling invocable Apex can start throwing when that class's `apiVersion` is raised

**What happens:** A path calls an `@InvocableMethod` that has always queried and updated records fine. Someone bumps the Apex class's `apiVersion` in `.cls-meta.xml` from 66.0 to 67.0 as part of routine housekeeping. The path now fails on records the running user cannot see or fields they cannot edit.

**When it occurs:** Only on the class's own version bump. Upgrading the org's release does nothing on its own — the gate is per-class metadata.

**How to avoid:** Know the rule before you bump: "In API version 67.0 and later, Apex runs in user context by default, meaning that the current user's permissions and field-level security (FLS) are enforced during code execution," while "In API version 66.0 and earlier, system mode is the default." The Flow side is unaffected — no class `apiVersion` changes a record-triggered Flow's own execution context. So the failure appears to come from the Flow and originates in the Apex. When raising an invoked class to 67.0+, review every query and DML in it for the permissions the *running user* actually holds, and add explicit `system mode` clauses only where the elevation is deliberate and justified. Canonical table: [`agents/_shared/AGENT_CONTRACT.md` § Apex security idiom by API version](../../../agents/_shared/AGENT_CONTRACT.md#apex-security-idiom-by-api-version).

---

## Gotcha 5: Deleting the record cancels the interview, and deactivating the Flow does not clean up what is already queued

**What happens:** Two symmetrical surprises. Delete a record and its pending scheduled branch never runs — no error, no notification, and any compensating action the branch was going to take (a reminder, a rollup, an integration callout) silently does not happen. Conversely, deactivate or replace a Flow version and the interviews already queued keep executing under the version that queued them, so "we turned that off last week" is not true for anything already in flight.

**When it occurs:** Record merges and cascading deletes for the first case; every Flow version swap for the second.

**How to avoid:** For deletes, do not use a scheduled path for anything that must happen regardless of the record's survival — that work belongs in a Schedulable Apex sweep keyed off a durable record. For version swaps, check Setup → Paused And Waiting Interviews before you deactivate, and either let the queue drain or delete the pending interviews deliberately. Plan the swap as a change with a drain window, not as a save.
