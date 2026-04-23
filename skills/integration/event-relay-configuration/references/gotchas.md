# Event Relay — Gotchas

## 1. Retention Is 72 Hours, Not Forever

Events not relayed within 72h are gone. If the relay is paused longer, you
have data loss — plan backfill via another channel.

## 2. Standard Platform Events Don't Relay Well At Scale

Use High-Volume Platform Events for relay; standard PE storage is tight.

## 3. IAM Must Use External ID

Without an external id, the IAM trust policy has a confused-deputy
problem. Always set and rotate.

## 4. Filter Language Is Limited

Filters are field-level equality / comparison, not arbitrary expressions.
Complex filtering belongs downstream.

## 5. One Region Per Connection

A relay targets one EventBridge bus in one region. Multi-region requires
multiple configs.

## 6. Order Is Per-Partition

At-least-once delivery preserves order within a partition but not across.
Consumers must be order-tolerant.

## 7. "Paused" Status Auto-Clears On Transient Errors

Persistent errors stay paused and require manual resume. Monitor the
state.
