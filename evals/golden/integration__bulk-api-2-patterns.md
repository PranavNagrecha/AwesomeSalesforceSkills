# Eval: integration/bulk-api-2-patterns

- **Skill under test:** `skills/integration/bulk-api-2-patterns/SKILL.md`
- **Priority:** P0
- **Cases:** 3
- **Last verified:** 2026-04-16
- **Related templates:** None directly — Bulk API is server-side.
- **Related decision trees:** `standards/decision-trees/integration-pattern-selection.md`

## Pass criteria

The AI must choose Bulk API 2.0 for the right volume thresholds, use
External Id upserts instead of pre-lookups, handle the async job status
lifecycle, and avoid REST composite or per-record REST for the scenarios
below.

## Case 1 — Choosing between REST composite, Bulk API, and Platform Events

**Priority:** P0

**User prompt:**

> "External system writes 2 million rows per night to Salesforce Contacts.
> Currently they loop POSTs one at a time. What should they do?"

**Expected output MUST include:**

- Bulk API 2.0 (not 1.0) — explicitly recommended for any new ingest work.
- Upsert on a Contact `External_Id__c` — never lookup-first-then-PATCH.
- CSV ingest via `POST /services/data/vXX.X/jobs/ingest` then
  `PUT .../batches`, then `PATCH .../state = UploadComplete`.
- Poll `GET /services/data/.../jobs/ingest/<id>` for `state = JobComplete`.
- Retrieve successful / failed records via
  `.../jobs/ingest/<id>/successfulResults` and `/failedResults`.
- Batch size note — Bulk API 2.0 handles batching for you; 10k records per
  POST body is a reasonable chunk but not mandatory.
- Reference `integration-pattern-selection.md` Q5.

**Expected output MUST NOT include:**

- REST Composite for 2M/day (wrong tier).
- Platform Events for bulk ingest (wrong primitive).
- Per-record POSTs with retry loop (status quo).
- Bulk API 1.0 (superseded).

**Rubric (0–5):**

- **Correctness:** Bulk API 2.0 chosen with named reasons.
- **Completeness:** Full lifecycle (job create → upload → state → poll → results).
- **Bulk safety:** No per-record callouts.
- **Security:** OAuth 2.0 via Named Credential on SF side, External Credential with rotation policy on external side.
- **Citation of official docs:** Links to Bulk API 2.0 Developer Guide.

**Reference answer (gold):**

"2M/night = Bulk API 2.0 territory. REST Composite tops out practically at ~1M/day before you spend more time batching than importing. Per-record POSTs at this volume are a non-starter.

Flow:

1. Pre-requisite: add `External_Id__c` to Contact as a unique External Id field. This lets you upsert without a prior SELECT.
2. External system calls `POST /services/data/vXX.X/jobs/ingest` with body `{ "object": "Contact", "operation": "upsert", "externalIdFieldName": "External_Id__c", "contentType": "CSV" }` — receives a job Id.
3. Uploads CSV body with `PUT /jobs/ingest/<id>/batches` (content-type `text/csv`). Break the 2M rows into ~10k-row chunks and issue multiple PUTs against the same job; the platform batches them into 10k or smaller internally.
4. `PATCH /jobs/ingest/<id>` with `{ "state": "UploadComplete" }` to kick off processing.
5. Poll `GET /jobs/ingest/<id>` every ~30s until `state = JobComplete` or `Failed`.
6. Pull `GET /jobs/ingest/<id>/successfulResults` and `/failedResults` as CSV for downstream reconciliation.

Security: authenticate via OAuth 2.0 Client Credentials — not user:password. Rotate the external credential from Salesforce-side External Credentials quarterly.

Tree reference: `integration-pattern-selection.md` Q5 — 2M/day falls into the Bulk API 2.0 row."

## Case 2 — Failed records from a Bulk load

**Priority:** P0

**User prompt:**

> "My Bulk API 2.0 upsert finished with 1,200 failed records out of 500k.
> What do I do with them? Can I tell why they failed?"

**Expected output MUST include:**

- `GET /jobs/ingest/<id>/failedResults` returns CSV with error column.
- Common causes: validation rules, required fields missing, triggers
  throwing, FLS / CRUD.
- Never retry blindly — classify errors (transient vs permanent).
- Transient errors (row-lock, UNABLE_TO_LOCK_ROW): retry with backoff,
  possibly in a smaller batch.
- Permanent errors (validation rule, missing required field): route to
  a data-quality review queue — do NOT auto-retry.
- The job also emits `GET /jobs/ingest/<id>/unprocessedRecords` if upload
  was incomplete — different endpoint, different meaning.

**Expected output MUST NOT include:**

- "Just rerun the whole job" (data-integrity risk).
- Assuming all 1,200 are the same root cause.

**Rubric (0–5):**

- **Correctness:** Distinguishes failed vs unprocessed.
- **Completeness:** Error classification + retry strategy.
- **Bulk safety:** Retries operate on the filtered failed subset.
- **Security:** Same credentials, same rotation.
- **Citation of official docs:** Links to results endpoints in Bulk API 2.0.

**Reference answer (gold):**

"Pull `GET /jobs/ingest/<jobId>/failedResults` — CSV with `sf__Id`, `sf__Error`, plus every original column.

Classification rules:

- `UNABLE_TO_LOCK_ROW`, `REQUEST_RUNNING_TOO_LONG`, `CONCURRENT_REQUESTS` → transient. Queue for retry with exponential backoff (30s, 2m, 8m). Rerun as a smaller Bulk job.
- `REQUIRED_FIELD_MISSING`, `FIELD_CUSTOM_VALIDATION_EXCEPTION`, `DUPLICATE_VALUE`, `INSUFFICIENT_ACCESS` → permanent. Push to a `Load_Exception__c` object for human triage.
- Trigger-side custom errors (e.g. `'Invoice must have a parent Account'`) → permanent, but surface them to the data owner with the row's payload for context.

Do NOT rerun the full job — you'd re-upsert 498,800 good rows unnecessarily and potentially re-fire downstream automation.

Separately, `/unprocessedRecords` is different: those are rows you uploaded but the job was closed (or failed) before Salesforce processed them — rerun these as a new job, they never hit validation."

## Case 3 — Security + credential rotation for Bulk API

**Priority:** P0

**User prompt:**

> "How should we authenticate the external system to Salesforce for Bulk API
> calls? We're using a service account with username + password right now."

**Expected output MUST include:**

- Username + password is DEPRECATED for integrations — OAuth 2.0 Client
  Credentials Flow is the current recommendation for server-to-server.
- Configure on Salesforce: Connected App → OAuth Settings → enable
  `Client Credentials Flow`, select "Run As" user (a dedicated integration user).
- External system stores Consumer Key + Consumer Secret; exchanges them
  for access tokens at runtime.
- Rotate Consumer Secret at least every 90 days; never embed in source.
- Integration user follows principle of least privilege — permission sets
  grant only the objects/fields the job needs.
- Mention that Salesforce is moving toward enforcing MFA on logged-in users
  but Client Credentials is exempt by design (no interactive login).

**Expected output MUST NOT include:**

- Keep username + password "because it works".
- Use the admin's personal account.
- Store secrets in Custom Setting or Custom Metadata.

**Rubric (0–5):**

- **Correctness:** OAuth 2.0 Client Credentials named.
- **Completeness:** User, permission sets, rotation, storage all addressed.
- **Bulk safety:** N/A — score 5.
- **Security:** Lead criterion — only 5 if least-privilege integration user is specified.
- **Citation of official docs:** Links to OAuth 2.0 Client Credentials Flow docs.

**Reference answer (gold):**

"Move off username + password — Salesforce is progressively restricting it and you inherit the human user's MFA + session policies. For server-to-server, use OAuth 2.0 Client Credentials Flow:

Salesforce side:

- Create a Connected App with OAuth enabled, and under `OAuth Policies` enable `Client Credentials Flow`. Select a dedicated integration user as `Run As` (not a real human).
- Grant that user the minimum permission set: just CRUD on Contact (and any lookup targets), no more. No `View All Data`, no `Modify All Data`.
- Set `Permitted Users = Admin approved users are pre-authorized` and assign only the integration user's profile.

External side:

- Store Consumer Key + Consumer Secret in a secret manager (AWS Secrets Manager, HashiCorp Vault, etc.) — never in source.
- Exchange them at job start via `POST /services/oauth2/token` with `grant_type=client_credentials`.
- Use the returned access token on Bulk API calls.

Rotation:

- Consumer Secret: 90-day rotation, orchestrated by the secret manager.
- Run-As user password: N/A in Client Credentials (no password in flow), but keep the user's profile locked down and audited.

Salesforce-side inbound callers: if your architecture uses Named Credentials on Salesforce TO call an external system, use External Credentials for credential rotation — never hardcode."
