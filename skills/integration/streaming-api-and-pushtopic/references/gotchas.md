# Gotchas — Streaming API and PushTopic

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: PushTopic SOQL Cannot Use Aggregate Functions, Relationship Fields in SELECT, LIMIT, or OFFSET

**What happens:** Attempting to insert a PushTopic with a query like `SELECT COUNT(Id) FROM Account` or `SELECT Contact.Email FROM Case` fails with a DML exception citing an invalid SOQL query for streaming. The error message is often cryptic and does not always clearly state which restriction was violated.

**When it occurs:** At PushTopic creation time (insert DML), not at subscription time. This means a failed PushTopic deploy can silently break a deployment pipeline if the exception is swallowed. Restrictions include: aggregate functions (COUNT, SUM, AVG, MIN, MAX, GROUP BY), relationship traversal in SELECT (`Parent.Field__c`), LIMIT, OFFSET, and semi-joins (IN with a subquery). WHERE clauses may reference relationship fields for filtering (e.g., `WHERE Account.Industry = 'Tech'`) but this is also unreliable across object types.

**How to avoid:** Before inserting a PushTopic, validate the SOQL against the streaming SOQL restrictions documented at https://developer.salesforce.com/docs/atlas.en-us.api_streaming.meta/api_streaming/pushtopic_soql.htm. Use the checker script in `scripts/check_streaming_api_and_pushtopic.py` to scan PushTopic XML metadata for common violations before deployment.

---

## Gotcha 2: 24-Hour Event Retention — Events Are Permanently Lost After the Window

**What happens:** A subscriber that is offline for more than 24 hours reconnects and replays with `-1`, but many events have already been discarded by Salesforce. The subscriber has no way to detect that events were dropped — the replay simply starts from the oldest retained event, not from the event immediately after disconnect.

**When it occurs:** Any time a subscriber is offline for more than 24 hours. Common scenarios: scheduled maintenance windows, bug-induced service crashes, and network partitions. This is particularly dangerous in organizations that assume Streaming API behaves like Platform Events, which has a 72-hour retention window.

**How to avoid:** Confirm the SLA for subscriber uptime vs. the 24-hour window. If events must survive outages longer than 24 hours, switch to Platform Events (`platform-events-integration` skill). If Streaming API must be used, add a secondary reconciliation mechanism (e.g., a scheduled Apex job that queries the sObject for records modified since the last successful event) to detect and backfill any gap.

---

## Gotcha 3: Salesforce Session Expiry Silently Invalidates the CometD Connection

**What happens:** The CometD connection is bound to the OAuth session token that was used during the initial handshake. When that session expires (controlled by the Connected App session policy or org session timeout settings), the server starts returning `401::Authentication required` on the `/connect` long-poll. Clients that only handle `402::Unknown client` (the reconnect error) and not `401` will silently stop receiving events without logging a visible error, depending on the CometD client implementation.

**When it occurs:** For user-context sessions, the default session timeout is often 2 hours. For connected app JWT or OAuth 2.0 flows, the token lifetime depends on the connected app configuration. Sessions can also be revoked administratively (e.g., "Log Out" in Setup > Active Sessions). In sandbox environments, session timeouts are sometimes shorter than production defaults.

**How to avoid:** The CometD client must handle `401` responses by: (1) discarding the current `clientId`, (2) obtaining a fresh OAuth access token via refresh token or re-authentication, (3) performing a new CometD handshake against the new session, and (4) re-subscribing with the persisted `replayId`. The Salesforce EMP Connector supports custom `BayeuxParameters` that can be extended to refresh the token. Ensure the Connected App has the "Refresh Token Policy" set appropriately for long-running daemons.

---

## Gotcha 4: Sandbox Streaming API Uses the Same Channel Names as Production — No Namespace Isolation

**What happens:** When a PushTopic or StreamingChannel is deployed to a sandbox via change set or metadata API, the channel name (e.g., `/topic/OpportunityUpdates`) is identical to production. If developers run integration tests in a sandbox while production subscribers are connected, there is no cross-org contamination (orgs are isolated), but within the same org a subscriber connected to the sandbox cannot distinguish test events from real events on the same channel.

**When it occurs:** QA environments that share a sandbox with automated integration tests. A test that inserts Opportunity records triggers real streaming events on the same channel that QA subscribers are watching.

**How to avoid:** Use environment-scoped channel naming conventions (e.g., `/topic/OpportunityUpdates_QA` vs `/topic/OpportunityUpdates_Prod`) or ensure QA subscribers filter by a flag field in the payload. Automate the convention by parameterizing PushTopic names in deployment scripts.

---

## Gotcha 5: Maximum 100 Simultaneous Clients Per Channel; 1,000 Org-Wide

**What happens:** When a channel reaches 100 simultaneous CometD subscribers, new connection attempts receive a handshake failure or `402::Unknown client` on subscribe. Existing subscribers continue to work, but new ones cannot join. The org-wide limit across all channels is 1,000 concurrent clients; breaching this blocks all new subscriptions across all channels.

**When it occurs:** Organizations that route streaming subscriptions through a fan-out middleware, or that open one CometD connection per browser tab instead of sharing a connection. LWC `empApi` uses one connection per browser session (not per tab), which is efficient. Custom Java or Node services that spawn a thread per subscription are common offenders.

**How to avoid:** Architect the subscriber side to use a single CometD connection per application instance with multiple subscriptions multiplexed on that connection. The EMP Connector uses a single Jetty WebSocket connection per instance. Monitor concurrent client usage via the Streaming Monitor in Setup or via the `StreamingChannel` sObject's `Members` related list.
