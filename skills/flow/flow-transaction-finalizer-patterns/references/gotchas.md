# Flow Transaction Finalizer — Gotchas

## 1. Flow Has No Native Finalizer

Flow does not provide a System.Finalizer equivalent. For guaranteed
post-outcome logging, you must cross into Apex Queueable.

## 2. Publish-After-Commit vs Publish-Immediate

Platform Events have two publish modes. Only "publish-after-commit"
protects against rollback. Confirm the mode before trusting it.

## 3. Scheduled Path At 0 Minutes Still Has Queue Latency

It's "soon," not instant. If the consumer expects sub-second latency, use
a Platform Event instead.

## 4. Invocable Apex Inside Flow Runs In The Same Transaction

Unless it explicitly enqueues async work, an Invocable Action runs in the
calling transaction and rolls back with it.

## 5. Finalizer Cannot Enqueue New Queueables (Limit)

Apex finalizers can re-enqueue the same Queueable but with depth limits.
Plan for max retry attempts rather than open-ended retry chains.

## 6. Mixed DML In Scheduled Path

A scheduled path running User / Group DML plus a standard object in the
same transaction can still fail Mixed DML. Separate the DML.
