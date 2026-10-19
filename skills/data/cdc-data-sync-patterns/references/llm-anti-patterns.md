# LLM Anti-Patterns — CDC Data Sync Patterns

Common mistakes AI coding assistants make when generating or advising on CDC data replication pipelines. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Processing Gap Events as Normal Change Events

**What the LLM generates:** A handler that copies fields from every event body (`record.Name = event["Name"]`) with no branch on `changeType`.

**Why it happens:** Tutorials show happy-path change events; gap events rarely appear in examples.

**Correct pattern:**

```python
GAP_TYPES = {"GAP_CREATE", "GAP_UPDATE", "GAP_DELETE", "GAP_UNDELETE"}
header = event["ChangeEventHeader"]
if header["changeType"] == "GAP_OVERFLOW":
    start_entity_resync(header["entityName"], event["replay_id"])
elif header["changeType"] in GAP_TYPES:
    for rid in header["recordIds"]:
        mark_dirty_and_queue(rid, header["commitTimestamp"])
else:
    buffer_by_transaction(event)
```

**Detection hint:** A CDC handler with no reference to `GAP_`, or one that reads body fields before checking `changeType`.

---

## Anti-Pattern 2: Lumping `GAP_OVERFLOW` In With the Other Gap Types

**What the LLM generates:** `if change_type.startswith("GAP_"): query records by recordIds`.

**Why it happens:** The shared prefix suggests one handling path.

**Correct pattern:** The CDC guide treats `GAP_OVERFLOW` as an overflow event: header only, entity name, and the dummy record ID `000000000000000AAA`. Re-sync the whole entity from the overflow event's replay ID; use record lookups only for the four true gap types.

**Detection hint:** A `startswith("GAP_")` branch that reads `recordIds` without first testing for `GAP_OVERFLOW`.

---

## Anti-Pattern 3: Hard-Coding a Replay Option on Every Connect

**What the LLM generates:** `replay_preset=EARLIEST` (or CometD `-2`) on every start, or `LATEST`/`-1` on every restart, with no stored position. A variant claims "Salesforce never tracks subscriber position."

**Why it happens:** Models carry over broker-managed offsets from other systems, or overcorrect against them.

**Correct pattern:** With `Subscribe`, store the replay ID (as bytes) after each committed transaction and resume with `CUSTOM`. Save the `replay_id` from empty keepalive responses too. `ManagedSubscribe` (Beta) is the server-side alternative that commits the replay ID for you.

```python
stored = store.load_bytes("cdc_replay_id")
if stored is None:
    run_day0_then_subscribe()
else:
    pubsub.subscribe(topic="/data/ChangeEvents", replay_preset="CUSTOM", replay_id=stored)

def on_transaction_committed(last_event):
    store.save_bytes("cdc_replay_id", last_event["replay_id"])
```

**Detection hint:** A subscribe call whose replay option is a literal constant and no write of `replay_id` anywhere in the subscriber.

---

## Anti-Pattern 4: Inventing a Replay-Expired Exception

**What the LLM generates:** `except ReplayIdExpiredError: run_resync()` as the only long-outage detection.

**Why it happens:** Models assume a typed error exists for every failure mode.

**Correct pattern:** Decide from elapsed time. Retention is 3 days, and Salesforce doesn't guarantee events beyond 72 hours (purging can also start later, so a replay that happens to work proves nothing). Store the last processed `commitTimestamp`; if it is more than 3 days old, re-sync before subscribing. Test what your client actually reports for an old replay ID instead of coding to an assumed exception.

**Detection hint:** Recovery logic that only triggers on a named exception and never compares the last processed time with a 3-day window.

---

## Anti-Pattern 5: Ordering by Timestamp Instead of by Transaction

**What the LLM generates:** Sorting all events by `commitTimestamp` (or arrival time) and applying them one by one.

**Why it happens:** Timestamp ordering is the default mental model.

**Correct pattern:** Follow the guide's transaction-based approach: buffer events in a map keyed by `transactionKey`, order each buffer by `sequenceNumber` (which starts at 1 within the transaction), and commit the transaction when the next event has a different key. Expect `sequenceNumber` gaps when some objects in the transaction aren't enabled for CDC.

```python
buffers = {}
def on_event(e):
    h = e["ChangeEventHeader"]
    if buffers and h["transactionKey"] not in buffers:
        (prev_key, prev_events), = buffers.items()
        commit(sorted(prev_events, key=lambda x: x["ChangeEventHeader"]["sequenceNumber"]))
        buffers.clear()
    buffers.setdefault(h["transactionKey"], []).append(e)
```

**Detection hint:** Ordering code with no reference to `transactionKey`, or completeness checks that fail on non-contiguous `sequenceNumber`.

---

## Anti-Pattern 6: Logging and Skipping Gap Events

**What the LLM generates:** A gap branch that only logs (`logger.info("gap event")`) and continues.

**Why it happens:** The model recognizes the event is special and treats it as noise.

**Correct pattern:** A gap event is a real change whose details were not sent. Mark the records dirty, ignore later change events for them until reconciled, retrieve them through the API, save, and clear the flag.

**Detection hint:** A `GAP_` branch containing only logging or `continue`, with no retrieval call.
