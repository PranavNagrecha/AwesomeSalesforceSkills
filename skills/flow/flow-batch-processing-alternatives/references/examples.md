# Flow Batch Alternatives — Examples

## Example 1: Chunking Via Platform Event

**Scenario:** Scheduled Flow needs to touch ~30,000 Contacts to recompute a
Next Best Action tag. Runs nightly.

**Pattern:**
- Scheduled Flow 1 queries Contacts with a stale tag, caps to 5,000, publishes
  a Platform Event per 200-record chunk with the Ids.
- Platform-Event-Triggered Flow consumes each event, updates 200 records.
- Chunks run in parallel-ish, staying under per-transaction limits.

**Why it works:** fan-out distributes load across independent transactions.

---

## Example 2: Resume-From-Checkpoint Via Control Record

**Scenario:** One-shot 120,000-record cleanup. Admins can't wait for an Apex
dev.

**Pattern:**
- Custom object `BatchState__c` with `LastProcessedId__c`.
- Scheduled Flow runs every 15 min, grabs next 2,500 records after the
  checkpoint, processes, updates checkpoint.
- Completes over several hours without breaching limits.

**Why it works:** deterministic progress, idempotent.

---

## Example 3: Escalation To Queueable

**Scenario:** Flow has been getting CPU-limit errors on nightly renewal
processing; volume keeps growing.

**Pattern:**
- Replace Flow logic with Queueable Apex using the `BulkTestPattern` base.
- Keep Flow as the scheduler and invoker via Invocable Action.
- Admin visibility preserved; scale improved.

---

## Anti-Pattern: Increase The Scheduled Flow Batch Size

A team raised Scheduled Flow batch size and declared victory. Within a week
new fields joined the flow and CPU limits spiked again. Moral: chunking does
not remove per-transaction cost; it only moves the cliff.
