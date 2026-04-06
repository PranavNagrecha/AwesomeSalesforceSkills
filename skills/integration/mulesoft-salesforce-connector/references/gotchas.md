# Gotchas — MuleSoft Salesforce Connector

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Mule 4 Removed the Built-In Watermark Element

**What happens:** Flows migrated from Mule 3 that reference `<watermark variable="lastTimestamp" default-expression="...">` inside a `<poll>` scope fail at deployment on Mule 4 runtime with a cryptic XML parsing error. There is no deprecation warning — the element simply does not exist in the Mule 4 schema.

**When it occurs:** Any Mule 3 to Mule 4 migration of polling-based Salesforce sync flows. This is extremely common because the Mule 3 watermark element was the standard pattern documented in hundreds of blog posts and training materials.

**How to avoid:** Replace the `<watermark>` element with explicit Object Store operations. Read the watermark at the start of the flow (`<os:retrieve>`), process records, then store the new high-water mark at the end (`<os:store>`). This gives finer control over when the watermark advances and prevents accidental advancement on partial failures.

---

## Gotcha 2: Bulk API Query Results Expire After 7 Days

**What happens:** Bulk API 2.0 query jobs store results server-side. If the Mule flow does not retrieve the results within 7 days, the result set is purged. The connector's `query` operation with Bulk API enabled handles retrieval automatically, but if the flow fails between job creation and result retrieval (e.g., Mule app crash), the job results may expire before the flow is restarted and the watermark will not have advanced — causing a full re-query on restart.

**When it occurs:** Environments with unreliable Mule runtime uptime or extremely long-running batch jobs. Also occurs when Mule workers are scaled down during weekends and bulk jobs were submitted Friday evening.

**How to avoid:** Monitor Bulk API job status through Anypoint Monitoring or Salesforce Setup > Bulk Data Load Jobs. Set alerts on jobs in `JobComplete` state that have not been retrieved. Keep Mule runtime uptime SLA well within the 7-day window.

---

## Gotcha 3: Streaming API Replay Window is 72 Hours (Not Unlimited)

**What happens:** Salesforce retains Platform Event and Change Data Capture messages for 72 hours (for standard retention) or 24 hours (for legacy PushTopic events). If the Mule subscriber is offline for longer than this window, events published during the gap are permanently lost — the connector's replay-from-stored-ID will receive an error and fall back to the stream tip.

**When it occurs:** Extended maintenance windows, failed deployments that take multiple days to fix, or disaster recovery scenarios where the Mule application is down for > 72 hours.

**How to avoid:** Design a fallback reconciliation mechanism. After subscriber recovery, run a watermark-based polling query to detect records modified during the gap. Treat the streaming subscription as best-effort real-time and the polling query as the durability guarantee.

---

## Gotcha 4: Connected App "Admin Approved" Bypass for JWT Bearer

**What happens:** A JWT Bearer flow returns `invalid_grant` even though the Connected App, certificate, and consumer key are all correct. The issue is that the Connected App's "Permitted Users" is set to "All users may self-authorize" (the default) instead of "Admin approved users are pre-authorized." JWT Bearer requires pre-authorization — there is no interactive consent step.

**When it occurs:** Every first-time setup where the admin creates the Connected App but does not change the Permitted Users policy and does not assign the Connected App to the integration user's profile or permission set.

**How to avoid:** After creating the Connected App: go to Setup > Connected Apps > Manage > click the app > Edit Policies > set Permitted Users to "Admin approved users are pre-authorized." Then add the integration user's profile under the Profiles or Permission Sets related list. Test the JWT Bearer token exchange with a cURL command before configuring the Mule connector.

---

## Gotcha 5: SOAP API Query-More Cursor Expiration Under Load

**What happens:** When a SOAP API query returns more than 2,000 records, the connector uses `queryMore()` with a server-side cursor (query locator). This cursor has a 15-minute inactivity timeout. If the Mule flow performs heavy transformation or writes to a slow external system between pages, the cursor expires and the query fails with `INVALID_QUERY_LOCATOR`.

**When it occurs:** Flows that use SOAP API for medium-volume queries (2,000 - 50,000 records) with per-record transformation logic that takes more than ~450ms per record (15 minutes / 2,000 records per page).

**How to avoid:** For any query that might return > 2,000 records, either switch to Bulk API (which writes all results to a file, eliminating the cursor) or fetch all pages into memory/disk first, then process. If SOAP API must be used, increase `fetchSize` to the maximum (2,000) and minimize per-page processing time.
