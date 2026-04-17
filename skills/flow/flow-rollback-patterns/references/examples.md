# Examples — Flow Rollback Patterns

## Example 1: Atomic opportunity + line items creation

**Context:** Sales process requires creating an Opportunity with OpportunityLineItems in one declarative flow. If any line item fails, the entire operation should roll back.

**Problem:** Without rollback, a failing line item leaves an orphan Opportunity in a half-created state — reporting looks wrong, admin cleanup is required.

**Solution:** Fault connector on the line-item Create Records element routes to Rollback Records. The Opportunity is undone too.

**Why it works:** Rollback is transaction-scoped. One rollback undoes everything in the current transaction, regardless of how many prior elements committed.

---

## Example 2: Screen flow cancellation with undo

**Context:** Multi-step screen flow creates a Case and attaches several Case Comments. User reaches the confirmation screen and clicks "Cancel".

**Problem:** The Case and Comments have already been DML'd. Without rollback, "Cancel" leaves garbage.

**Solution:** Route the "Cancel" decision branch directly to Rollback Records. All DML performed during the flow run is undone.

**Why it works:** The screen-flow transaction spans from flow entry to Finish. Rollback before Finish undoes all writes in that span.

---

## Example 3: Compensating Platform Event

**Context:** Flow creates a Subscription (local DML) and publishes `Subscription_Created__e` (Publish Immediately) to notify an external billing system. A later Update Account element faults.

**Problem:** Rollback undoes the local DML but the external billing system has already received the event and charged the customer.

**Solution:** Fault path: Rollback + Publish `Subscription_Cancelled__e`. The external subscriber compensates by refunding.

**Why it works:** Local state stays consistent via Rollback; external state stays consistent via compensation. Use Publish After Commit whenever possible to avoid needing compensation.

---

## Anti-Pattern: Rollback on logging failure

Authors route the fault path of the "log success" element back to Rollback. A logging hiccup then erases the business work. **Correct approach:** logging failures take a Silent End, not Rollback.

---

## Anti-Pattern: Rollback after external callout

Callout completes, then a fault triggers Rollback. The local records are undone, but the external side thinks the work happened. **Correct approach:** perform the callout AFTER all local DML + commit, or design for external-side compensation.
