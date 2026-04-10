# Gotchas — Marketing Integration Patterns

Non-obvious Salesforce Marketing Cloud platform behaviors that cause real production problems in this domain.

## Gotcha 1: Journey Injection Requires `eventDefinitionKey` — Not Journey ID, Not Entry Source Name

**What happens:** The Event API (`POST /interaction/v1/events`) returns HTTP 400 with `"Event Definition not found"` even when the Journey is live and the credentials are valid.

**When it occurs:** When the caller uses the Journey ID (visible in the Journey Builder URL), the Journey name, or the Entry Source display name as the identifier in the `EventDefinitionKey` field. The Journey ID and the `eventDefinitionKey` are completely different identifiers — the `eventDefinitionKey` is a UUID generated specifically for the REST API Entry Source component.

**How to avoid:** In Journey Builder edit mode, click the REST API Entry Source, open its properties panel, and copy the `eventDefinitionKey` value (formatted `APIEvent-<UUID>`). Store this key in the external system's configuration, not the Journey ID. If the Journey is rebuilt or the Entry Source is re-created, the `eventDefinitionKey` changes and integrations must be updated.

---

## Gotcha 2: Async Batch Injection Hard Cap Is 100 Contacts Per Request

**What happens:** The `/interaction/v1/events/async` endpoint returns HTTP 400 when the `contacts` array contains more than 100 entries. The error message references a payload validation failure, not a clear "too many contacts" message.

**When it occurs:** When a caller builds a batch injection loop and does not enforce the per-request cap. A common mistake is assuming the endpoint will internally split large batches or queue excess entries.

**How to avoid:** Enforce chunking in the caller before the request is sent. Split the full contact list into slices of ≤ 100 and send each slice as a separate request. The synchronous `/interaction/v1/events` endpoint handles exactly one contact per call — do not use it for batch enrollment.

---

## Gotcha 3: All REST API Patterns Require an Installed Package with API Integration — No Alternative Auth

**What happens:** REST API calls return HTTP 401 `"Unauthorized"` or fail at token acquisition if the caller attempts to authenticate using Marketing Cloud SOAP credentials (username/password/token), FTP credentials, or a legacy API key.

**When it occurs:** When teams familiar with the SOAP API attempt to use SOAP credentials for REST calls, or when they inherit an integration built before Installed Packages were the standard approach. Marketing Cloud REST APIs exclusively use OAuth 2.0 client credentials from an Installed Package API Integration component.

**How to avoid:** Always create an Installed Package in Marketing Cloud Setup > Platform Tools > Apps > Installed Packages. Add an API Integration component. The API Integration generates the `clientId` and `clientSecret` needed for OAuth 2.0 token acquisition. Each integration context (production vs. sandbox, different permission scopes) should use a separate Installed Package.

---

## Gotcha 4: Triggered Send Definition Must Be in Active Status — Paused or Inactive TSDs Return 400, Not 503

**What happens:** When a Triggered Send Definition is in Inactive or Paused status, the REST send endpoint returns HTTP 400 Bad Request. The response does not clearly indicate that the TSD needs to be activated — it looks like a payload or credential error.

**When it occurs:** After Marketing Cloud sends reach a volume threshold and the TSD auto-pauses, after a marketing team manually pauses a TSD for maintenance, or when the TSD was never activated after creation. Developers spend time debugging credentials and payloads when the real issue is TSD status.

**How to avoid:** Build a startup check in the integration: after obtaining the auth token, call the TSD status endpoint (`GET /messaging/v1/messageDefinitionSends/key:<ExternalKey>`) and verify the status is `Active` before proceeding. Set up an alert if the TSD transitions to Paused status. Document that TSD status is an operational concern, not just a development-time setting.

---

## Gotcha 5: SFTP Import Column Headers Are Case-Sensitive and Must Match Data Extension Field API Names Exactly

**What happens:** The Import Activity runs without error, the file appears to be processed, but records in the target Data Extension are empty or partially populated. No error is surfaced in the Automation Studio activity log.

**When it occurs:** When the CSV file header row uses a different casing or spacing than the Data Extension field API name. For example, the file has `Email_Address` but the DE field API name is `EmailAddress`. The Import Activity silently skips unmatched columns rather than failing.

**How to avoid:** Before configuring the Import Activity, export the Data Extension field list from Marketing Cloud and compare API names character-by-character against the file headers. Use a column-mapping review step in the Automation Studio Import Activity wizard to confirm each column maps correctly. Include a record-count validation step after import (SQL Activity querying row count) to catch silent import failures.

---

## Gotcha 6: MC Connect Synchronized Data Extensions Are Read-Only in Marketing Cloud

**What happens:** SQL Activities or Import Activities that attempt to write to a Synchronized Data Extension fail with a permissions or lock error. Data written externally does not appear in the SDE.

**When it occurs:** When architects assume SDEs work like standard writable Data Extensions and design Marketing Cloud-side processes (SQL transforms, Journey personalization lookups) that write to them. SDEs are CRM-sourced read replicas — they are refreshed by the MC Connect sync process and cannot be written to from within Marketing Cloud.

**How to avoid:** Use SDEs only as source tables in SQL Activities (SELECT from SDE, INSERT into a standard DE). Never use an SDE as the target in an Import Activity or a SQL Activity INSERT/UPDATE. For data that Marketing Cloud needs to write back to Salesforce (e.g., email open events), use the standard MC Connect data sync or a REST API callout from Automation Studio to Salesforce — not SDE manipulation.
