# Gotchas — Platform Event Schema Evolution

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Field rename = delete + create

**What happens:** Renaming a field on a Platform Event metadata-deletes the old field and creates a new one. Subscribers reading the old name fail at runtime (Apex) or at deserialization (Pub/Sub).

**When it occurs:** Any time someone uses Setup → Custom Fields → \[Field\] → Edit → change Field Name on a live event.

**How to avoid:** Treat renames as breaking. Use the dual-publish pattern. Never rename in place.

---

## Gotcha 2: Replay window crosses schema changes

**What happens:** Subscriber offline for 12 hours. Comes back. Replays 12 hours of events — some published before yesterday's schema change, some after. Subscriber code mismatched against the older schema crashes.

**When it occurs:** High-volume events have a 72-hour replay window; any subscriber reconnect within that window may receive pre-change events.

**How to avoid:** Subscriber code must tolerate the older schema for at least 72 hours after the publisher schema change. Plan the wait into the migration.

---

## Gotcha 3: Required field on publish breaks Flow publishers silently

**What happens:** A Flow publishing to the event without populating the new required field fails at runtime. Flow run history shows the error; nothing else surfaces it.

**When it occurs:** A previously-optional field is marked required and old Flow publishers don't set it.

**How to avoid:** Search Flow XML for `recordCreate` against the event's API name; update each Flow before flipping the field to required. Or never make event fields required after publish — keep them optional and validate in subscribers.

---

## Gotcha 4: Pub/Sub clients caching a schema ID forever

**What happens:** External client decodes events fine for a year, then fails immediately after the first additive change.

**When it occurs:** Client cached schema ID at deploy time and never calls `GetSchema` for unknown IDs. Each event now carries a new ID the client doesn't recognize.

**How to avoid:** External subscriber code must look up unknown schema IDs via `GetSchema` at runtime. Reject any client implementation that hardcodes a schema ID.

---

## Gotcha 5: No field-history on event metadata

**What happens:** Three months after a schema change, the team can't reconstruct who changed what when. Salesforce keeps no field-level audit trail on Platform Event metadata.

**When it occurs:** Always.

**How to avoid:** Store the event definition in source control. Treat schema changes like code changes: PR, review, audit, change-request ticket linked.
