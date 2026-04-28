# LLM Anti-Patterns — Data Loader Batch Window Sizing

Common mistakes AI coding assistants make when asked to size a Data Loader / Bulk API job. These help the consuming agent self-check its own output before recommending settings.

---

## Anti-Pattern 1: Recommending higher batch size to "make the load faster"

**What the LLM generates:** "You're loading 5M Accounts and it's slow — try batch size 5,000 or 10,000 in parallel mode to finish faster."

**Why it happens:** the LLM reasons from intuition that bigger batches = fewer round trips = faster, without modelling per-batch CPU consumption, parallel-mode lock contention, or sharing-recalc cost. It also pattern-matches on "make X faster" with "use bigger chunks" from generic batch-processing examples in training data.

**Why it backfires:** for an Account with rich automation, batch=5,000 hits `CPU_TIME_LIMIT_EXCEEDED` immediately (because each 200-row server transaction still pays the CPU cost). For a Private OWD object, parallel mode produces `UNABLE_TO_LOCK_ROW` storms on row-skewed parents. The "faster" recommendation ends up costing more wall clock than starting small-and-serial would have.

**Correct pattern:**

```yaml
# Tier the recommendation to volume + complexity, not "go bigger"
target: Account (Private OWD, role hierarchy, 6 record-triggered Flows)
record_count: 5_000_000
batch_size: 200             # NOT 5000 — trigger CPU is per-200-row server transaction
mode: serial                # NOT parallel — row-skew on migration user OwnerId
trigger_bypass: TriggerControl__mdt for the load user
defer_sharing_calculations: ON during load window
post_load_enrich: separate Batch Apex pass
```

**Detection hint:** any recommendation that raises batch size in response to a CPU error, or recommends parallel mode for Account/Opportunity in a Private OWD org. Both are reverse-direction wrong.

---

## Anti-Pattern 2: Forgetting parallel mode + sharing recalc = catastrophic combination

**What the LLM generates:** "Use Bulk API V2 parallel mode with batch=2,000 for your Account load." (No mention of OWD setting, role hierarchy, sharing recalc, or Defer Sharing Calculations.)

**Why it happens:** the LLM treats batch sizing as a numeric optimisation independent of org configuration. It does not model the interaction between parallel mode (which creates lock contention on parent records) and sharing recalculation (which reads/writes those same parent rows).

**Why it backfires:** parallel mode against a Private OWD object with role hierarchy guarantees three failure modes simultaneously: (1) `UNABLE_TO_LOCK_ROW` on implicit-share row creation, (2) async sharing-recalc tail that runs for hours after the visible job ends, (3) inability to retry failed records in the same job. The recommendation is structurally unsafe.

**Correct pattern:**

```yaml
# Always profile OWD + hierarchy + automation before recommending parallel mode
required_inputs_check:
  - OWD setting for target SObject              # Public R/W vs Private
  - role hierarchy depth                         # 0-3 = mild; 4+ = strong implicit-share fan-out
  - sharing rules count on target                # each one adds recalc work
  - row-skew check (any parent with >10K children)
recommendation_branch:
  if OWD == Private and (hierarchy_depth >= 3 or sharing_rules > 0):
    mode: serial
    batch_size: 200
    defer_sharing_calculations: ON
  else:
    mode: parallel
    batch_size: 1_000-2_000
```

**Detection hint:** any sizing recommendation for Account/Opportunity/Contact that omits OWD setting and Defer Sharing Calculations. Both are first-order inputs.

---

## Anti-Pattern 3: Defaulting to "200 is the safe default for everything"

**What the LLM generates:** "Use batch size 200 — it's the Data Loader default and it's safe for any object."

**Why it happens:** the LLM has seen "200" in countless Data Loader docs and treats it as a universal safe value. The number is correct as a Data Loader UI default; it is wrong as a recommendation, because it is wasteful for simple loads and dangerous for complex ones.

**Why it backfires:** for a 5M-row Lead insert with no triggers, batch=200 = 25,000 batches = ~50,000 API calls consumed. The same load at batch=2,000 = 2,500 batches = ~5,000 API calls consumed and runs in 1/10 the wall clock with zero downside. Conversely, for an Account with 12 triggers, batch=200 still hits CPU limits.

**Correct pattern:**

```yaml
# Tier the recommendation to BOTH volume AND complexity
simple_object_no_triggers_public_rw:        # Lead, Task, simple custom
  batch_size: 2_000-10_000
  mode: parallel
standard_object_with_triggers_public_rw:    # Case in many orgs
  batch_size: 500-1_000
  mode: parallel
private_owd_complex:                         # Account, Opportunity in mature orgs
  batch_size: 200
  mode: serial
row_skewed_shape:                            # any object with skewed parent
  batch_size: 200
  mode: serial    # mandatory
```

**Detection hint:** any single-number recommendation that does not vary with the input profile. The right answer is always a function of (object × volume × complexity), not a constant.

---

## Anti-Pattern 4: Loading 1M+ records without checking field history tracking impact

**What the LLM generates:** "Bulk-update all 1,000,000 Accounts to set the new `Region__c` value — use batch=2,000 parallel mode."

**Why it happens:** the LLM does not model the side-effects of the update (history rows, feed items, platform-event traffic) — it only models the visible DML. Field history tracking is invisible from the outside; the LLM treats the update as if it only writes 1M rows when it actually writes 1M Account rows + 1M `AccountHistory` rows + potentially 1M feed items.

**Why it backfires:** 1M extra `AccountHistory` rows consume measurable storage, clutter the Account feed for users, and (critically) cannot be deleted in production. A second pass to fix a mistake doubles the history cost. Storage allocation is a budget item; this anti-pattern silently consumes it.

**Correct pattern:**

```yaml
# Always check side-effects before mass-update
pre_load_checks:
  - field_history_tracking: which fields are tracked? does the update touch them?
  - feed_tracking: same question
  - duplicate_rules: will they slow the upsert and produce noise?
  - platform_events: do triggers publish events on this update path?
mitigations:
  - temporarily disable field history tracking on touched fields for the load window
  - re-enable after the load
  - DO NOT plan to delete *History rows after the fact (production immutability)
```

**Detection hint:** any mass-update recommendation that omits a field-history-tracking check. Production update sizing without this check is incomplete.

---

## Anti-Pattern 5: Recommending REST Composite for ">200K records because it's simpler than Bulk API"

**What the LLM generates:** "Use REST Composite to upsert your 500K Contacts — it's a simpler API than Bulk and easier to integrate."

**Why it happens:** the LLM optimises for surface-area familiarity (REST is familiar to web devs) over the architectural fit. REST Composite has a hard 200-records-per-request cap; the LLM either does not know this or assumes it can be raised.

**Why it backfires:** 500K records via REST Composite = 2,500 requests minimum, each a synchronous round-trip. The wall-clock cost is an order of magnitude higher than Bulk V2, the API call consumption is identical to Bulk V1, and there is no batch-state machine to recover from partial failure. The "simpler" choice is structurally wrong for the volume.

**Correct pattern:**

```yaml
# Pick the API by volume, not by familiarity
volume_to_api:
  <_5_000_records: REST Composite or Tooling API ok
  5_000-100_000_records: Bulk API V1 (Data Loader) or Bulk V2
  >_100_000_records: Bulk API V2, period
explanation: |
  REST Composite caps at 200 records per request and is intended for
  small-volume, low-latency operations. Bulk V2 is the canonical large-data
  ingestion API; using anything else above 100K records is fighting the
  platform.
```

**Detection hint:** any recommendation that uses REST Composite, REST single-record, or SOAP API for a load over 5K records. The volume crossover to Bulk is not optional.

---

## Anti-Pattern 6: Suggesting "just retry the failed records in parallel" after `UNABLE_TO_LOCK_ROW`

**What the LLM generates:** "Some records failed with `UNABLE_TO_LOCK_ROW` — that's a transient error, just re-run the failure CSV in parallel mode."

**Why it happens:** the LLM has seen "transient error → retry" in generic error-handling training data and applies it without modelling that row-lock contention from row-skew is **structural**, not transient. The same retry hits the same lock.

**Why it backfires:** the second-pass parallel retry hits the same row-lock contention because the underlying shape (row-skewed parent) has not changed. The job produces another failure CSV with overlapping records, and the engineer ends up doing 3-4 retry passes with diminishing yield.

**Correct pattern:**

```yaml
# Detect the shape that caused the lock; switch mode for the retry pass
on_unable_to_lock_row_failures:
  step_1: query SELECT ParentId, COUNT(Id) FROM ChildObject WHERE ... — find row-skew parents
  step_2: re-run the failure CSV in serial mode (NOT parallel)
  step_3: if no row-skew, parallel retry is OK — but verify shape first
explanation: |
  UNABLE_TO_LOCK_ROW under parallel mode is a structural failure when row-skew
  is present. Retry in serial mode for skewed shapes; verify shape before
  retrying in parallel.
```

**Detection hint:** any retry recommendation that keeps the same mode (parallel) without first checking the row-skew shape. Retry-in-parallel without diagnosis is the wrong default.

---

## Anti-Pattern 7: Ignoring trigger bypass for one-time historical loads

**What the LLM generates:** "Run the 5-year-of-Cases historical load through the standard triggers — they should bulkify fine if your handler is well-written."

**Why it happens:** the LLM trusts the "well-written triggers bulkify" platitude without modelling that historical loads have shapes (5-year-old data with unfamiliar values) that trigger code was not designed to handle. The triggers will fire emails, create platform events, and execute validations against records that are conceptually "already done."

**Why it backfires:** historical-load triggers fire emails to long-departed users, create platform-event traffic that downstream systems are not expecting, run sharing logic against records that should not have current-day sharing implications, and consume CPU on validation rules that pass historical data fine but are wasteful. Even when no governor limit is hit, the side effects pollute the org.

**Correct pattern:**

```yaml
# One-time historical loads default to bypass + post-load enrich
one_time_historical_load:
  step_1: design TriggerControl__mdt with Bypass_<Object>__c flag
  step_2: trigger handlers read the CMDT and short-circuit for the load user
  step_3: run the load with bypass ON
  step_4: run post-load enrich Batch Apex to recompute the rollups, sharing,
          and rule-evaluation that the bypassed triggers would have done
  step_5: clear the CMDT flag, verify normal trigger flow works for new records
explanation: |
  Trigger code is designed for one-record-at-a-time UI inserts and
  incremental day-to-day inserts, not for 5-year historical replays.
  Bypass is the correct default for one-time historical loads.
```

**Detection hint:** any one-time historical load plan that does NOT include a trigger-bypass mechanism. The bypass should be a default, not an afterthought.
