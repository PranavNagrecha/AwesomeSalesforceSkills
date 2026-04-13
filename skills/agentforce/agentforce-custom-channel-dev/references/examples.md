# Examples — Agentforce Custom Channel Dev

## Example 1: Mobile App Agent API Integration With sequenceId Tracking

**Scenario:** A native iOS/Android app needs to embed an Agentforce agent. Users open a chat screen, send messages, receive agent responses, and close the chat when done.

**Problem:** The developer initializes a new `externalSessionKey` on every message send (treating each POST as stateless), and increments the sequenceId globally across sessions rather than per-session. This causes the platform to create a new session on every message, losing all conversation history, and eventually rejects messages when a sequence gap is detected.

**Solution:**

```python
import uuid

class AgentSession:
    def __init__(self, agent_id: str, base_url: str, access_token: str):
        self.agent_id = agent_id
        self.base_url = base_url
        self.access_token = access_token
        self.session_id = None
        self.external_session_key = None
        self.sequence_id = 0  # per-session counter; reset on new session only

    def start_session(self, channel: str, language: str = "en_US") -> str:
        """Create a new agent session. Returns sessionId."""
        # Generate once per conversation — used as idempotency key
        self.external_session_key = str(uuid.uuid4())
        self.sequence_id = 0  # reset for new session

        payload = {
            "externalSessionKey": self.external_session_key,
            "instanceConfig": {"endpoint": self.base_url},
            "variables": [
                {"name": "Context.Channel", "type": "Text", "value": channel},
                {"name": "Context.EndUserLanguage", "type": "Text", "value": language}
            ],
            "bypassUser": False
        }
        # POST /services/data/v63.0/einstein/ai-agent/agents/{agentId}/sessions
        response = self._post(f"/sessions", payload)

        if response.status_code == 409:
            # Idempotent retry: session already exists for this externalSessionKey
            self.session_id = response.json()["sessionId"]
        else:
            response.raise_for_status()
            self.session_id = response.json()["sessionId"]

        return self.session_id

    def send_message(self, text: str) -> str:
        """Send a message and return the agent's reply text."""
        if not self.session_id:
            raise RuntimeError("Session not started. Call start_session() first.")

        self.sequence_id += 1  # monotonically increasing, never reset mid-session

        payload = {
            "message": {
                "sequenceId": self.sequence_id,
                "type": "Text",
                "text": text
            },
            "variables": []
        }
        # POST /services/data/v63.0/einstein/ai-agent/agents/{agentId}/sessions/{sessionId}/messages
        response = self._post(f"/sessions/{self.session_id}/messages", payload)
        response.raise_for_status()

        messages = response.json().get("messages", [])
        return " ".join(m.get("text", "") for m in messages if m.get("type") == "Text")

    def end_session(self) -> None:
        """Terminate the session. Always call this when the conversation ends."""
        if self.session_id:
            # DELETE /services/data/v63.0/einstein/ai-agent/agents/{agentId}/sessions/{sessionId}
            self._delete(f"/sessions/{self.session_id}")
            self.session_id = None
            self.external_session_key = None
            self.sequence_id = 0
```

**Why it works:** The `externalSessionKey` UUID is generated once per `AgentSession` instance and reused on retries (idempotency). The `sequence_id` counter is per-session-instance and increments monotonically — no gaps, no resets. The `end_session` method always calls DELETE to prevent orphaned sessions.

---

## Example 2: BYOC CCaaS Integration — Establish Conversation and Interaction API Flow

**Scenario:** A CCaaS vendor (e.g., Amazon Connect) is integrating with Salesforce so that when a customer contacts the call center, an Agentforce Service Agent handles the interaction initially, with escalation to a human agent available through Omni-Channel.

**Problem:** The developer uses the raw Agent API sessions endpoint directly instead of the BYOC-specific APIs, so the conversation never routes through Omni-Channel. Supervisor monitoring shows no activity, escalation requests from the agent have nowhere to route, and no `MessagingEndUser` record is created in Salesforce — breaking conversation history and CRM linkage.

**Solution:**

```json
// Step 1: Establish Conversation API
// POST /services/data/v63.0/einstein/ai-agent/byoc/conversations
{
  "channelAddressIdentifier": "your-byoc-channel-address-id",
  "externalConversationIdentifier": "amazon-connect-contact-id-abc123",
  "endUserClientIdentifier": "+15555550100",  // e2e identifier for MessagingEndUser record
  "routingAttributes": {
    "queueDeveloperName": "AgentforceServiceQueue"
  }
}

// Response: Salesforce creates/matches MessagingEndUser record and returns conversationId
{
  "conversationId": "0MHxx0000004CzBGAU",
  "messagingEndUserId": "0MWxx0000008LkjGAE"
}

// Step 2: Send inbound message via Interaction API
// POST /services/data/v63.0/einstein/ai-agent/byoc/conversations/{conversationId}/messages
{
  "messageType": "INBOUND_MESSAGE",
  "message": {
    "id": "amazon-connect-msg-001",
    "text": "I need to check my order status",
    "timestamp": "2026-04-13T10:00:00Z"
  }
}

// Step 3: Receive outbound message at your registered webhook
// Salesforce POSTs to your webhook endpoint:
{
  "messageType": "OUTBOUND_MESSAGE",
  "conversationId": "0MHxx0000004CzBGAU",
  "message": {
    "text": "I can help with that! Could you provide your order number?",
    "timestamp": "2026-04-13T10:00:02Z"
  }
}

// Step 4: End conversation
// POST /services/data/v63.0/einstein/ai-agent/byoc/conversations/{conversationId}/messages
{
  "messageType": "END_CONVERSATION"
}
```

**Why it works:** The Establish Conversation API creates the `MessagingEndUser` record that links the external caller identity to Salesforce CRM. All subsequent messages flow through Omni-Channel routing — enabling supervisor visibility, human escalation through standard Omni-Channel queue assignment, and Salesforce-side conversation history stored on the Messaging Session record. The `END_CONVERSATION` event replaces the DELETE call used in raw Agent API integrations.

---

## Anti-Pattern: Updating Context Variables Mid-Session

**What practitioners do:** After session creation, the developer calls `POST /messages` with a `variables` array containing updated customer context (e.g., updated account tier after a lookup), expecting the agent to see the new values in subsequent responses.

**What goes wrong:** Context variables set at session creation are immutable for the session lifetime (except `Context.EndUserLanguage`). The platform silently ignores variable updates in `/messages` payloads — the agent continues using the original session-start values. This causes the agent to give outdated responses without any error signal, making it very hard to diagnose.

**Correct approach:** Design context that changes during a conversation to be surfaced through agent actions (Apex actions or Flow actions called by the agent) rather than session variables. If language must change, use the dedicated `Context.EndUserLanguage` update mechanism. For all other context, plan data lookups at session creation and inject only stable identity/configuration context as session variables.
