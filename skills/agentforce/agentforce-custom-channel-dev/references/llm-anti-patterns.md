# LLM Anti-Patterns — Agentforce Custom Channel Dev

Common mistakes AI coding assistants make when generating or advising on Agentforce custom channel integrations.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using Non-Sequential or Resetting sequenceIds

**What the LLM generates:** Code that uses `Date.now()` (timestamp), a random integer, or a global counter shared across sessions as the `sequenceId` for Agent API messages. Sometimes also generates code that resets `sequenceId` to 1 at the start of each message batch or on retry.

**Why it happens:** LLMs associate "message ID" with common patterns like timestamps or UUIDs used in messaging systems (Kafka offsets, message queue IDs). The Agentforce-specific requirement for a per-session monotonically increasing integer starting at 1 is non-obvious and frequently hallucinated away.

**Correct pattern:**

```python
class AgentSession:
    def __init__(self):
        self._sequence_id = 0  # per-session, reset only when session restarts

    def next_sequence_id(self) -> int:
        self._sequence_id += 1  # only increment AFTER successful send
        return self._sequence_id

    def send_message(self, text: str) -> dict:
        seq = self._sequence_id + 1  # preview next value without committing
        response = post_message(seq, text)
        if response.ok:
            self._sequence_id = seq  # commit increment only on success
        return response
```

**Detection hint:** Flag any code where `sequenceId` is set to `time.time()`, `random.randint()`, `uuid.uuid4()`, or any expression that does not reference a per-session incrementing counter. Also flag code where `sequenceId` is reset to 0 or 1 mid-session outside of a new session creation.

---

## Anti-Pattern 2: Attempting to Update Context Variables Mid-Session

**What the LLM generates:** Code that passes a `variables` array in the `POST /messages` request body to "update" context (e.g., after authenticating the user mid-conversation, after a product is selected, after an account lookup completes).

**Why it happens:** LLMs model context variables as a mutable session state store, analogous to HTTP session cookies or Redux store updates. The immutability constraint is not inferable from the API structure alone — the `/messages` endpoint accepts a `variables` field, so LLMs assume it is writable.

**Correct pattern:**

```json
// At session creation: inject all stable context
POST /services/data/v63.0/einstein/ai-agent/agents/{agentId}/sessions
{
  "variables": [
    { "name": "Context.Channel", "type": "Text", "value": "mobile-ios" },
    { "name": "Context.EndUserLanguage", "type": "Text", "value": "en_US" },
    { "name": "Context.AccountTier", "type": "Text", "value": "Gold" }
  ]
}

// Mid-session: only Context.EndUserLanguage can be updated
// For all other dynamic context — use agent actions (Apex/Flow) to fetch live data
// The variables array in POST /messages is effectively ignored for non-language fields
```

**Detection hint:** Flag any code that passes a non-empty `variables` array in `POST .../messages` payloads for fields other than `Context.EndUserLanguage`. This is almost always incorrect.

---

## Anti-Pattern 3: Conflating BYOC CCaaS with Raw Agent API (Using Sessions Endpoint for CCaaS)

**What the LLM generates:** A BYOC CCaaS integration that calls `POST /einstein/ai-agent/agents/{agentId}/sessions` directly, then sends messages to `POST .../sessions/{sessionId}/messages`, exactly as in the raw Agent API pattern — without using the Establish Conversation API or Interaction API.

**Why it happens:** The raw Agent API is simpler, better documented in general resources, and appears earlier in search results. LLMs default to the simpler pattern even when the user's description mentions CCaaS, Omni-Channel routing, or human escalation — context that should trigger the BYOC pattern.

**Correct pattern:**

```
// BYOC CCaaS flow (not raw Agent API):
1. POST /einstein/ai-agent/byoc/conversations          (Establish Conversation API)
   -> Returns conversationId + messagingEndUserId

2. POST /einstein/ai-agent/byoc/conversations/{id}/messages   (Interaction API — inbound)
   { "messageType": "INBOUND_MESSAGE", "message": { ... } }

3. Receive OUTBOUND_MESSAGE at registered webhook (push — not polling)

4. POST /einstein/ai-agent/byoc/conversations/{id}/messages   (Interaction API — end)
   { "messageType": "END_CONVERSATION" }
```

**Detection hint:** Flag any code that uses the `/einstein/ai-agent/agents/{agentId}/sessions` endpoint when the user description mentions CCaaS, Omni-Channel, supervisor, escalation, human agent, MessagingEndUser, or a named CCaaS vendor (Genesys, Amazon Connect, Five9, NICE).

---

## Anti-Pattern 4: Using Arbitrary Strings for externalSessionKey Instead of UUID

**What the LLM generates:** Session creation code that sets `externalSessionKey` to a user ID (`"user_12345"`), a composite string (`"conv-" + userId + "-" + timestamp`), a numeric string (`"9001"`), or an ISO timestamp string (`"2026-04-13T10:00:00Z"`).

**Why it happens:** The field name `externalSessionKey` suggests a "key" in the general sense — like a session cookie or API key. LLMs default to meaningful, human-readable identifiers. The UUID requirement is a Salesforce-specific validation constraint not inferable from the field name.

**Correct pattern:**

```python
import uuid

# Always use a proper UUIDv4 generator
external_session_key = str(uuid.uuid4())
# Result: "550e8400-e29b-41d4-a716-446655440000"

# WRONG — these are all rejected with 400:
# external_session_key = f"user-{user_id}"
# external_session_key = str(int(time.time()))
# external_session_key = hashlib.md5(user_id.encode()).hexdigest()  # not UUID format
```

**Detection hint:** Flag any `externalSessionKey` value that is not generated by a UUID library call. Specifically flag string concatenation patterns, integer-to-string conversions, hash hex digests (wrong format), and hardcoded string literals.

---

## Anti-Pattern 5: Forgetting DELETE to Terminate Sessions (Causing Orphaned Sessions)

**What the LLM generates:** An integration that creates sessions (POST) and exchanges messages (POST /messages) but has no `DELETE /sessions/{sessionId}` call. The session cleanup is either omitted entirely or placed only in the "user clicked close" happy path, with no cleanup in error handlers, timeouts, or server shutdown code.

**Why it happens:** LLMs model conversations as stateless request-response exchanges. The concept of an explicit "close session" API call is not intuitive when the agent response is already returned in the POST /messages response. The DELETE is easy to omit because the integration appears to work correctly without it — the failure mode (orphaned sessions depleting the session pool) is delayed and systemic rather than immediate.

**Correct pattern:**

```python
session = AgentSession(agent_id, base_url, access_token)
try:
    session.start_session(channel="mobile-ios")
    reply = session.send_message("Hello")
    # ... conversation continues ...
finally:
    # Always execute, even on exception or timeout
    session.end_session()  # calls DELETE /sessions/{sessionId}

# Additionally: implement a background cleanup job for sessions
# that never reached the finally block (process crash, network partition)
```

**Detection hint:** Flag any Agent API integration code that has `POST .../sessions` without a corresponding `DELETE .../sessions/{id}` in a finally/cleanup path. Also flag integrations with no session registry or TTL-based cleanup mechanism for high-volume use cases.

---

## Anti-Pattern 6: Mixing Interaction API and Agent API Concepts in a Single Integration

**What the LLM generates:** A hybrid integration that uses the Establish Conversation API to create the conversation (BYOC path) but then switches to `POST .../sessions/{sessionId}/messages` (raw Agent API path) to send messages, or vice versa — mixing endpoint namespaces, request schemas, and auth patterns from both APIs.

**Why it happens:** LLMs synthesize from multiple documentation sources and do not always track which API family each endpoint belongs to. The two APIs appear in the same domain (Agentforce Agent API) and serve similar logical purposes, making cross-contamination likely.

**Correct pattern:**

```
// Pick ONE integration path and stay on it:

// PATH A — Raw Agent API (no Omni-Channel):
POST   /einstein/ai-agent/agents/{agentId}/sessions
POST   /einstein/ai-agent/agents/{agentId}/sessions/{sessionId}/messages
DELETE /einstein/ai-agent/agents/{agentId}/sessions/{sessionId}

// PATH B — BYOC CCaaS (with Omni-Channel):
POST   /einstein/ai-agent/byoc/conversations
POST   /einstein/ai-agent/byoc/conversations/{conversationId}/messages
// (receive outbound via registered webhook — no polling endpoint)

// NEVER mix PATH A endpoints with PATH B endpoints in the same conversation lifecycle
```

**Detection hint:** Flag any code that calls both `/agents/{agentId}/sessions` (raw Agent API) AND `/byoc/conversations` (BYOC CCaaS) endpoints in the same conversation lifecycle. These are mutually exclusive integration paths.
