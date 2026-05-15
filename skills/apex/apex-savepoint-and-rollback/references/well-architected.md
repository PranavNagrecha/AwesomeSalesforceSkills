# Well-Architected Notes — Apex Savepoint and Rollback

## Relevant Pillars

Savepoint/rollback sits at the intersection of correctness and
governor-limit management. The mechanism is straightforward; the
mistakes are about what's *outside* its scope (side effects,
queries, async work).

- **Reliability** — Savepoint is the only mechanism in Apex that
  delivers true multi-DML atomicity within a single transaction.
  Without it, partial-failure states leave orphan records that
  downstream automation will act on incorrectly. The reliability
  win is real but conditional: it only covers DML, not callouts,
  Platform Events, emails, or async enqueues.
- **Operational Excellence** — Code that uses savepoint correctly
  is easier to reason about: the atomicity boundary is visible at
  the service-layer method, and the recovery path is a single
  `rollback` + structured rethrow. Code that misuses savepoint (per
  row loops, nested savepoints, savepoint-across-callout) is among
  the hardest Apex to debug because the failures only manifest
  under bulk load or specific timing.
- **Performance** — `setSavepoint` and `rollback` each consume one
  of the 150 DML statements per transaction. That sounds cheap until
  you place them inside a loop or repeat them across a chain of
  service calls. The cost is real and the limit is hard.

The pillars that *don't* apply meaningfully here are Security
(savepoint has no FLS/CRUD implications — it's transaction
control) and Scalability (it doesn't help with bulkification;
it sometimes hurts).

## Architectural Tradeoffs

The dominant decision is **savepoint vs. `Database.insert(records,
false)`** for multi-step DML:

| Dimension | Savepoint + try/catch | `Database.insert(..., false)` |
|---|---|---|
| Atomicity | All-or-nothing | Per-row success/failure |
| Error visibility | Single `DmlException` | `Database.SaveResult[]` per row |
| Compose with parent-child | Natural | Requires two-pass logic |
| Governor cost | 2 DML statements | 0 extra |
| Best for | "Order must include both customer + line items" | "Migrate 10k records, skip the broken ones" |

A second tradeoff: **where in the call stack should the savepoint
live?** Three options, with concrete consequences:

1. **At the entry point** (`@HttpPost`, `@AuraEnabled`, or trigger
   handler). Atomic boundary matches the user's request. Sub-services
   stay savepoint-free. **Recommended default.**
2. **In a service-layer method.** Useful when the same service is
   called from multiple entry points and each needs its own
   atomicity boundary. Forces the entry point to NOT also place its
   own savepoint (otherwise: nested savepoints, see
   `gotchas.md` § 3).
3. **In a domain/selector class.** Almost always wrong — domain and
   selector classes should be composable and stateless. Savepoint
   ownership at this layer breaks the templates-canonical
   architecture and prevents the caller from composing multiple
   domain operations into one atomic transaction.

A third tradeoff: **savepoint vs. compensating action**. For flows
that *must* include side effects (callout, email, async enqueue),
savepoint cannot help — the platform forbids rollback after callout,
and rolling back after a queued async job is irrelevant because the
job is already enqueued. The alternative pattern is a compensating
action: a separate Queueable that runs on failure and explicitly
undoes the side effects (recall webhook, send retraction email,
flag the queued job for skip). Compensating actions are more code
but the only correct option once side effects are in scope.

## Anti-Patterns

1. **Savepoint inside a loop.** Burns 2 DML statements per iteration
   on bookkeeping. See `examples.md` anti-pattern for the corrected
   shape.
2. **Savepoint inside a sub-service when the caller already owns
   one.** Produces nested savepoints with surprising cleanup
   semantics (see `gotchas.md` § 3). Service methods should throw
   on failure and trust the caller's atomicity boundary.
3. **Rollback as a "panic button."** Some code rolls back at the
   first sign of trouble — including in catch blocks for exceptions
   that don't actually invalidate the transaction (e.g., a
   non-fatal `QueryException` for a "lookup might fail" probe).
   Rollback should be reserved for cases where the transaction's
   business outcome is genuinely impossible to deliver.
4. **Treating savepoint as a time-travel mechanism.** It rolls back
   DML, not side effects. Code that publishes a Platform Event,
   sends an email, or enqueues an async job before the rollback
   will *not* unsend or unqueue those operations. See `gotchas.md`
   §§ 1 and 5 for the failure modes.
5. **Savepoint when `Database.insert(records, false)` would do.**
   For migrations and bulk-load patterns, per-row partial success
   is usually the right semantic. Savepoint provides all-or-none
   atomicity, which is the *wrong* tool when the business
   requirement is "load what you can, log what you can't."

## Official Sources Used

- Apex Developer Guide — Transaction Control:
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_transaction_control.htm
- Apex Developer Guide — DML and Loops:
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/langCon_apex_dml.htm
- Apex Reference — `Database.setSavepoint` / `Database.rollback`:
  https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_methods_system_database.htm
- Apex Developer Guide — Execution Governors and Limits:
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm
- Salesforce Well-Architected — Trusted (Reliability):
  https://architect.salesforce.com/well-architected/trusted/reliable
