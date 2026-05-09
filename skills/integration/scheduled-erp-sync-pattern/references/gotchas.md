# Gotchas — Scheduled ERP Sync Pattern

Non-obvious Salesforce platform behaviors that bite teams during scheduled-ERP-sync work. Each gotcha has cost real engineering time in real orgs.

---

## Gotcha 1: 100 callouts per transaction — including chained Queueables

**Symptom:** A Queueable with a loop calling the ERP per record throws `LimitException: Too many callouts: 101` once the staged batch reaches 101 records.

**Why:** The Apex governor limit on **HTTP callouts is 100 per Apex transaction**, documented in the Apex Reference Guide under Per-Transaction Apex Limits. Queueable chaining gives you a fresh transaction *per chained job*, but inside any single Queueable's `execute()` you still cap at 100. A Queueable that loops `for (record : 500_records) http.send(...)` will fail at iteration 101 every time.

**Fix:** Two options. (a) Batch the records into a *single* multi-record callout — most ERP REST endpoints accept arrays. Send 100 records in one POST, not 100 POSTs of one record each. (b) Cap the per-Queueable workload at 80 records (leaving headroom for retry/fallback callouts) and chain the next Queueable for the next 80. Never loop callouts unbatched.

---

## Gotcha 2: Named Credential token refresh requires Auth Provider, not just header config

**Symptom:** OAuth-based ERP integration runs fine for an hour, then every callout fails with HTTP 401. The Named Credential is configured with the access token — but only the *initial* token. There is no refresh.

**Why:** A Named Credential's "Generate Authorization Header" checkbox + Auth Provider configuration handles refresh automatically only when the External Credential is set up with an Auth Provider that *supports* the OAuth refresh flow. If the integration was scaffolded by pasting a bearer token into the "Custom Headers" section instead of using an Auth Provider, the token never refreshes — the header is static. You will not notice until the access token TTL elapses (often 1 hour for OAuth client credentials).

**Fix:** Use an External Credential with an OAuth 2.0 Auth Provider configured for the ERP. Verify in Setup → Named Credentials → External Credentials that the Auth Protocol is "OAuth 2.0" and a Principal has authenticated. Test by manually setting the principal's token TTL low and confirming the refresh fires. Salesforce documents this in the "Named Credentials as Callout Endpoints" section of the Apex Developer Guide.

---

## Gotcha 3: Schedulable cannot make callouts directly

**Symptom:** Developer writes `Schedulable.execute()` that calls `http.send()`. Job throws `CalloutException: You have uncommitted work pending` or `CalloutException: Callout from scheduled Apex` at runtime.

**Why:** The Schedulable execution context **does not allow callouts**. This is a documented platform restriction. The historical reason is transactional safety — a long-running callout inside a scheduled job would hold a transaction across an unbounded wait.

**Fix:** Schedulable's `execute()` must `System.enqueueJob(new MyQueueable(...))` and return. The Queueable, with `Database.AllowsCallouts` declared, performs the callout. This is canonical and documented in the Apex Developer Guide ("Using Queueable Apex" → "Callouts in Queueable Jobs").

---

## Gotcha 4: Governor limits reset between Queueable chain steps — but daily totals do not

**Symptom:** A 15-minute sync chains 6 Queueables per cycle, each making 50 callouts = 300 per cycle × 96 cycles/day = 28,800 callouts/day. Suddenly all integrations across the org start failing with `LimitException: Daily callout time exceeded`.

**Why:** Per-transaction limits (100 callouts, 60 sec total callout time) reset between chained Queueables. But the **org-wide daily totals are cumulative across all transactions**. Org-wide governors include daily Apex CPU time, daily callout time, and daily outbound email volume. A polling pattern at high cadence eats org-wide budget, not just per-transaction budget.

**Fix:** Two strategies. (a) Coarsen cadence — does the business actually need 15 minutes, or did they pick 15 minutes by default? Hourly often suffices. (b) Check org-wide daily callout consumption with a Dashboard sourced from `EventLogFile` or by exposing a per-day counter custom object, and budget integrations explicitly. The Salesforce Limits documentation has the up-to-date numbers per edition.

---

## Gotcha 5: Watermark advanced to `Datetime.now()` post-cycle skips records

**Symptom:** The integration runs successfully every cycle. No errors, no DLQ entries. But records modified during the cycle window keep getting missed and only show up in SF days later, if at all.

**Why:** A naive implementation captures the watermark *after* the cycle finishes:

```apex
// WRONG — race window
List<Record> r = pull(priorWatermark, http);
upsert r;
advanceWatermark(Datetime.now());   // <— ERP records modified during pull()
                                    //     have a modifiedDate older than this
                                    //     and will be skipped next cycle
```

The cycle takes 60–120 seconds. Any ERP record modified during that window has a `modifiedDate` between `priorWatermark` and `Datetime.now()` *but* may or may not have been included in the response, depending on ERP read isolation. If excluded, advancing the watermark to `now()` skips it forever.

**Fix:** Capture the cycle-start timestamp at the *beginning* of the Schedulable's execute(), pass it through the entire Queueable chain, and only persist it as the new watermark *after* the entire chain succeeds. Records modified during the cycle then re-appear in the next cycle's window.

---

## Gotcha 6: Custom Setting watermark loses sandbox refresh; Custom Metadata survives

**Symptom:** Production deploy goes fine. Sandbox refresh kills the integration with "watermark missing" error.

**Why:** **Hierarchy / List Custom Settings store data, not metadata** — sandbox refreshes do not preserve their values. Custom Metadata Types **are metadata** — values flow with deployments and survive refreshes. Many integrations were originally written with Custom Settings because Custom Metadata was not yet generally available; the legacy code does not survive modern lifecycle requirements.

**Fix:** Watermarks belong in `ERP_Sync_Watermark__mdt` (Custom Metadata Type), not `ERP_Sync_Settings__c` (Custom Setting). The deploy-via-Apex pattern in `references/examples.md` Example 2 is the documented update mechanism.

---

## Gotcha 7: `Database.upsert(records, ExternalId)` silently inserts duplicates if the field is not `Unique`

**Symptom:** Integration runs for a week, all checks pass. Then someone notices duplicate Accounts where the same ERP customer ID maps to multiple SF rows.

**Why:** `Database.upsert(records, ExternalId__c)` looks at the External ID field to match incoming records to existing ones. If the External ID field is not also marked **Unique** in the field definition, two different inbound payloads with the same ID can both insert as new rows. The upsert documentation specifies that the External ID field "must also be marked as a unique field." Without that, upsert degrades to insert.

**Fix:** Verify in Setup → Object Manager → Field → External ID, the field is *both* "External ID" *and* "Unique" (with "Treat ABC and abc as duplicate" set appropriately for case sensitivity). The field-level metadata XML must have both `<externalId>true</externalId>` and `<unique>true</unique>`.

---

## Gotcha 8: HTTP timeout default of 10s is far too low for ERP endpoints

**Symptom:** Cycles intermittently fail with `CalloutException: Read timed out`. The ERP responds in 8–20 seconds depending on load.

**Why:** `HttpRequest.setTimeout()` defaults to **10,000 ms (10 seconds)**. ERPs under load — particularly during their own batch windows or month-end close — routinely take longer to respond than 10s for queries that touch large tables.

**Fix:** Set `req.setTimeout(120000)` (120 seconds, the platform max) for ERP callouts. The platform max is documented in the HttpRequest Apex Reference. Pair with a circuit-breaker — if a single callout takes >60s, the next cycle should skip the call and write a DLQ entry instead, to avoid stacking long-running callouts.
