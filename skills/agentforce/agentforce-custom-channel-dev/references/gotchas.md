# Gotchas — Agentforce Custom Channel Dev

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: sequenceId Must Be Monotonically Increasing With No Gaps Per Session

**What happens:** The Agentforce Agent API enforces strict monotonic ordering of `sequenceId` values within a session. If message 3 fails (network error, timeout, 5xx), and the integration retries by sending message 4 (incrementing past the failed message), the platform rejects message 4 with a 400 error because sequenceId 3 was never successfully acknowledged. The session is now in an inconsistent ordering state.

**When it occurs:** Any retry logic that increments `sequenceId` on failure rather than retrying with the same ID. Also occurs when multiple threads or processes share a session and increment the counter independently without locking.

**How to avoid:** Treat the `sequenceId` as a commit pointer: only increment after a successful 2xx response. On failure, retry the same message with the same `sequenceId`. Use a single-threaded or mutex-guarded counter per session to prevent concurrent increment races.

---

## Gotcha 2: Context Variables Are Immutable for the Session Lifetime (Except Context.EndUserLanguage)

**What happens:** All context variables injected in the `variables` array at session creation are locked for the entire session. Passing variables in a subsequent `POST /messages` call has no effect — the platform silently ignores them and the agent continues using the original values. No error is returned, making this extremely difficult to diagnose.

**When it occurs:** When developers attempt to "refresh" context mid-session (e.g., after completing a login step, after a product is added to cart, after account tier is determined from a slow external lookup). The silence of the failure means the agent silently uses stale data.

**How to avoid:** Gather and resolve all immutable context before the `POST /sessions` call. For data that genuinely changes during the conversation, use agent actions (Apex or Flow actions invoked by the agent) to perform lookups at action-invocation time. `Context.EndUserLanguage` is the only variable that can be changed after session creation.

---

## Gotcha 3: externalSessionKey Must Be a Valid UUID — Arbitrary Strings Are Rejected

**What happens:** The platform validates the format of `externalSessionKey` on session creation. Strings that are not valid RFC 4122 UUIDs (e.g., `"user-12345"`, `"conv-2026-04-13-001"`, `"session_abc"`, numeric strings like `"9001"`) are rejected with a 400 validation error. The error message references the field but does not always clarify that UUID format is required, leading to confusion.

**When it occurs:** When developers treat `externalSessionKey` as an arbitrary session label, using their own ID schemes (database auto-increment IDs, user IDs, conversation hashes, ISO timestamps).

**How to avoid:** Always generate `externalSessionKey` using a UUIDv4 library (e.g., Python's `uuid.uuid4()`, Java's `UUID.randomUUID()`, Node.js's `crypto.randomUUID()`). Generate once per conversation and store it for idempotency retries. Do not construct UUID-shaped strings manually — use a proper generator to guarantee format compliance.

---

## Gotcha 4: BYOC CCaaS Uses Interaction API, Not the Agent API Sessions Endpoint — Different Endpoints, Auth, and Data Model

**What happens:** A developer building a CCaaS integration reads the raw Agent API documentation, implements session POST/DELETE, and then wonders why Omni-Channel shows no activity, supervisor dashboards are empty, and the Agentforce Service Agent escalation actions have no effect. The integration appears to work (agent responds to messages) but the entire Omni-Channel layer is bypassed.

**When it occurs:** When developers use the raw Agent API sessions endpoint (`/einstein/ai-agent/agents/{agentId}/sessions`) for a BYOC CCaaS integration instead of the Establish Conversation API (`/einstein/ai-agent/byoc/conversations`) and Interaction API. The two patterns are documented separately but it is easy to start with the simpler raw API and miss the distinction.

**How to avoid:** Determine the integration pattern before writing any code. If the use case involves routing through Omni-Channel queues, supervisor visibility, human agent escalation, or Salesforce-side conversation history on `MessagingEndUser` records — use BYOC CCaaS APIs exclusively. The raw Agent API cannot be retrofitted to add Omni-Channel routing mid-project.

---

## Gotcha 5: Orphaned Sessions From Missing DELETE Deplete the Session Pool

**What happens:** Sessions not explicitly closed via `DELETE /sessions/{sessionId}` remain active on the platform and count against the org's concurrent session limit. In high-volume environments (IVR integrations handling hundreds of simultaneous calls, mobile apps with high churn), sessions accumulate from dropped connections, app backgrounding, network errors, and server crashes where the cleanup code path is never reached.

**When it occurs:** When session termination (`DELETE`) is only called in the happy-path code (user explicitly closes chat) but not in error handlers, timeout handlers, app lifecycle events (iOS/Android background/foreground transitions), or server restart scenarios.

**How to avoid:** Implement DELETE in a `finally` block or equivalent cleanup handler for all code paths. Additionally, implement a background session registry with TTL tracking — any session older than the expected maximum conversation duration (e.g., 30 minutes for a support chat) should be proactively deleted by a cleanup job. Log all `externalSessionKey` + `sessionId` pairs to a durable store so the cleanup job can issue DELETE even if the original process is gone.

---

## Gotcha 6: 409 Conflict on Session POST Is Not An Error — It Signals an Existing Session

**What happens:** On network timeout or during a retry after a 5xx error, the integration calls `POST /sessions` again with the same `externalSessionKey`. The platform returns a 409 Conflict status. Developers treating 409 as a failure throw an exception and abort the session, losing the existing conversation. The platform returns the existing `sessionId` in the 409 response body — this is the intended idempotency mechanism.

**When it occurs:** Whenever the session creation POST is retried after any non-2xx response, or in distributed systems where two processes may attempt to create a session for the same external conversation.

**How to avoid:** Handle 409 explicitly: extract `sessionId` from the 409 response body and continue using it as if the session was just created. Do not treat 409 as a fatal error. Document this behavior in the integration's error handling spec so that future developers do not inadvertently change the 409 handling to an error path.
