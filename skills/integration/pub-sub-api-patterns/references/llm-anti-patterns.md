# LLM Anti-Patterns — Pub/Sub API Patterns

## Anti-Pattern 1: Recommending CometD/EMP Connector for New Integrations

**What the LLM generates:** "Use the EMP Connector (Java) or CometD protocol to subscribe to Salesforce Platform Events in your integration."

**Why it happens:** LLMs are trained on large bodies of Salesforce Streaming API documentation from before Pub/Sub API GA (Summer '22). CometD/EMP Connector was the primary streaming integration pattern for years.

**Correct pattern:** As of Summer '22, Pub/Sub API gRPC is the recommended path for new external streaming integrations. CometD/EMP Connector is legacy — it remains supported for existing integrations but should not be recommended for new development. Use `grpc` clients with the Pub/Sub API proto.

**Detection hint:** Recommendations to use "CometD", "EMP Connector", or "Streaming API" for new external subscriber integrations should prompt evaluation of Pub/Sub API gRPC instead.

---

## Anti-Pattern 2: Treating 100-Event FetchRequest Cap as an API Rate Limit

**What the LLM generates:** "The Pub/Sub API has a hard limit of 100 events per request — for higher throughput, you need multiple consumer instances."

**Why it happens:** LLMs conflate per-request batch size limits with throughput rate limits. The 100-event cap applies per FetchRequest, not across the connection.

**Correct pattern:** `num_requested = 100` is the maximum events the server will deliver per FetchRequest. The client sends successive FetchRequests to continue consuming events — there is no per-second or per-minute rate limit on the number of FetchRequests. Consumer throughput scales by reducing per-event processing time, not by adding consumer instances.

**Detection hint:** Claims of a "100 event per second limit" or recommendations to scale consumers to increase event throughput due to a "rate limit" are incorrect.

---

## Anti-Pattern 3: Using 15-Character Org ID as tenantid

**What the LLM generates:** "Set the `tenantid` header to your Salesforce Org ID, which you can find in Setup > Company Information."

**Why it happens:** LLMs don't distinguish between 15-character and 18-character Org ID formats. The Setup UI sometimes displays 15 characters.

**Correct pattern:** The `tenantid` header requires the **18-character** Org ID. Use SOQL `SELECT Id FROM Organization` to retrieve the 18-character version reliably. Verify the string is exactly 18 characters before use.

**Detection hint:** Instructions that copy the Org ID from the Setup URL or Setup UI without specifying "18-character format" or "from SOQL" may produce the wrong value.

---

## Anti-Pattern 4: Closing Subscribe Stream on Token Refresh

**What the LLM generates:** Token refresh logic that closes the gRPC Subscribe connection and reopens it every 2 hours when the OAuth token is renewed.

**Why it happens:** LLMs model the 2-hour session timeout as closing all connections. In reality, the timeout affects idle PublishStream connections but not active Subscribe streams.

**Correct pattern:** Active Subscribe streams persist beyond the 2-hour token expiry — they do not need to be closed and reopened for token refresh. Implement token refresh in the background and update the token on future metadata calls. Close and reopen Subscribe only if the stream itself errors.

**Detection hint:** Token refresh implementations that explicitly close the Subscribe stream (`.cancel()` or `channel.close()`) every 2 hours are unnecessarily disruptive.

---

## Anti-Pattern 5: Ignoring Event Bus Retention in Consumer Downtime Design

**What the LLM generates:** "You can resume event consumption from where you left off by replaying from your stored replay ID, regardless of how long the consumer was offline."

**Why it happens:** Replay ID-based resumption is a real feature, but LLMs don't model the 3-day retention window constraint.

**Correct pattern:** Replay from a stored replay ID is only possible if the events are still in the 3-day retention window. If consumer downtime exceeds 3 days, events older than 3 days are no longer available for replay. Design consumers with monitoring that alerts before the 3-day window is exceeded. For compliance use cases requiring longer replay horizons, archive events to durable storage (S3, BigQuery) as they arrive.

**Detection hint:** Any claim that replay ID-based resumption works "regardless of how long" the consumer was offline ignores the 3-day retention window.
