# Debug Log Triage Worksheet

Use this worksheet when starting a forensic analysis. Fill it out before reading any log content. It forces Step 1 (triage) and Step 3 (classify the question) from the Recommended Workflow.

## 1. Inventory

| File | Size (bytes) | Start time | Shape | Notes |
|---|---|---|---|---|
| | | | | |
| | | | | |
| | | | | |

Run to populate:

```bash
cd /mnt/user-data/uploads
for f in *.log; do
  start=$(head -3 "$f" | tail -1 | awk '{print $1}')
  size=$(wc -c < "$f")
  entry=$(head -5 "$f" | grep -oE "EXECUTION_STARTED|BATCH_APEX|CRON_|CODE_UNIT_STARTED[^|]*\|[^|]*" | head -1)
  echo "$start  size=$size  $f  entry=$entry"
done | sort
```

## 2. Truncation check

- [ ] No log is within 1 KB of the 20 MB cap (20,000,000 bytes). If any is, note which below.
- [ ] Every log has an `EXECUTION_FINISHED` line. If any does not, note below.

Truncated logs: _________________________________________

## 3. Trace flag inventory

From the header of each log, record the category levels:

| File | APEX_CODE | WORKFLOW | DB | CALLOUT | VALIDATION |
|---|---|---|---|---|---|
| | | | | | |

If `WORKFLOW` is below `FINER`, Flow assignment details will be missing — call this out in the report.

## 4. Cross-log timeline

| Time | Log | Delta to previous | Shape |
|---|---|---|---|
| | | | |

Interval patterns worth noting:
- [ ] Fixed 10–60 s interval → scheduled job or retry loop
- [ ] Fixed multi-minute interval → scheduled flow or cron
- [ ] Tight 1–5 s pairs → single logical operation
- [ ] Shrinking intervals → runaway recursion

## 5. User's question classification

Circle one primary category (load the matching reference):

- Flip-flop / field write attribution → `flows.md`, `apex-and-async.md`, `managed-packages.md`, `recipes.md`
- Flow failure → `flows.md`, `error-codes.md`
- LWC / Aura / Lightning Data Service → `ui-frameworks.md`
- Async (batch, queueable, future, scheduled) → `apex-and-async.md`, `recipes.md`
- Platform event / CDC → `apex-and-async.md`, `integration.md`
- Concurrency (UNABLE_TO_LOCK_ROW, deadlock) → `error-codes.md`, `recipes.md`
- Sharing / FLS / merge / INSUFFICIENT_ACCESS → `security-sharing.md`, `error-codes.md`, `recipes.md`
- Governor limits (SOQL, CPU, heap) → `governor-and-performance.md`, `recipes.md`
- Legacy automation (workflow, PB, approval) → `legacy-automation.md`
- Integration / callout → `integration.md`, `recipes.md`
- Unknown managed package → `managed-packages.md`
- Specialized (Omni-Channel, Einstein, Big Object, etc.) → `specialized-topics.md`

Secondary categories: _________________________________________

## 6. Known unknowns

Before running extractions, list questions the log cannot answer (see `gotchas.md`):

- [ ] Which specific record is the INSUFFICIENT_ACCESS blocker (empty `[]` list)?
- [ ] What ran inside a managed package below `ENTERING_MANAGED_PKG`?
- [ ] What a formula field was "before" (formulas recalculate, no history)?
- [ ] Whether a scheduled job was created by Apex or by Setup?
- [ ] The enqueuing user of an async job (check `AsyncApexJob.CreatedById` outside the log)?

For each checked item, note the concrete next step the user will take outside the log.

## 7. Output plan

Confirm the report will include:

- [ ] Headline (one sentence naming the root cause)
- [ ] Evidence (specific log events with timestamps or line numbers)
- [ ] Timeline (if multi-log, ordered with deltas)
- [ ] Mechanism (how this causes the symptom, in platform terms)
- [ ] What the log cannot tell you (explicit limits + next steps)
- [ ] Recommendations (ordered stop-the-bleeding → long-term fix)
