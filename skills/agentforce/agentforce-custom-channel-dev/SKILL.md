---
name: agentforce-custom-channel-dev
description: "Use this skill when building custom channel integrations with the Agentforce Agent API or BYOC (Bring Your Own Channel) for CCaaS — covering session lifecycle management, webhook handling, externalSessionKey design, sequenceId sequencing, BYOC Interaction API integration, and conversation state management. NOT for standard channels (Embedded Service, Slack, SMS/MMS via standard Messaging). NOT for agent-channel-deployment (which handles standard channel setup and activation). NOT for custom agent actions or Apex topics."
category: agentforce
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Performance
tags:
  - agentforce
  - agent-api
  - byoc
  - custom-channel
  - webhook
  - session-lifecycle
  - ccaas
  - conversation-state
triggers:
  - "How do I connect my external app to Agentforce via API and manage the conversation session lifecycle"
  - "building a custom webhook for Agentforce agent responses from a mobile app or IVR system"
  - "integrating a CCaaS platform with Agentforce Service Agent using Bring Your Own Channel and Omni-Channel routing"
  - "externalSessionKey UUID format error when creating an Agentforce agent session"
  - "sequenceId error in Agentforce Agent API messages endpoint causing 400 bad request"
  - "how to inject context variables into an Agentforce session at creation and update language mid-session"
inputs:
  - "Target channel surface (mobile app, IVR, CCaaS platform, custom web surface, third-party system)"
  - "Integration pattern — raw Agent API (direct) vs. BYOC for CCaaS (Omni-Channel routing)"
  - "OAuth Connected App credentials (Consumer Key, Consumer Secret)"
  - "Agent ID (from BotDefinition object or Setup > Agentforce Agents)"
  - "External session identifier strategy (UUID generation approach)"
  - "Context variables to inject at session start"
outputs:
  - Session management implementation (create/message/delete lifecycle)
  - externalSessionKey UUID generation pattern
  - sequenceId tracking logic
  - Webhook endpoint design for inbound/outbound message routing
  - BYOC Interaction API integration plan with messagingEndUser record handling
  - Context variable injection strategy
  - Conversation state management approach
dependencies:
  - agentforce/agent-channel-deployment
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-13
---

# Agentforce Custom Channel Dev

This skill activates when a practitioner needs to integrate an external system, application, or communication platform with Agentforce using the Agent API session lifecycle or the BYOC (Bring Your Own Channel) for CCaaS pattern — covering webhook design, session state management, and the sequenceId/externalSessionKey protocol. Use this skill for programmatic, API-driven integrations, not standard channel deployments.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm whether the integration targets the raw Agent API directly (mobile apps, IVR, custom web surfaces) or uses BYOC for CCaaS (routing through Omni-Channel via Interaction API and Establish Conversation API). These use different endpoints, different auth scopes, and different record types.
- The most common wrong assumption: that context variables can be updated mid-session. They cannot. All context variables set at session creation via the `variables` payload are immutable for the entire session lifetime, with the single exception of `Context.EndUserLanguage`.
- Platform constraints: the Agent API requires the `chatbot_api` OAuth scope in addition to the standard `api` scope. Sessions are tied to a single agent and cannot be re-routed mid-session. The `externalSessionKey` must be a valid UUID (RFC 4122 format) — arbitrary strings are rejected. The `sequenceId` must be a monotonically increasing integer per session — gaps or resets cause message ordering errors.

---

## Core Concepts

### Agent API Session Lifecycle

The Agentforce Agent API follows a strict three-phase lifecycle for every conversation:

**1. Session Creation (POST)**

```
POST /services/data/v63.0/einstein/ai-agent/agents/{agentId}/sessions
```

Request body:
```json
{
  "externalSessionKey": "550e8400-e29b-41d4-a716-446655440000",
  "instanceConfig": {
    "endpoint": "https://your-org.salesforce.com"
  },
  "variables": [
    { "name": "Context.Channel", "type": "Text", "value": "custom-mobile-app" },
    { "name": "Context.EndUserLanguage", "type": "Text", "value": "en_US" }
  ],
  "bypassUser": false
}
```

The response returns a `sessionId` (Salesforce-generated UUID) distinct from the `externalSessionKey`. Store both — the `sessionId` is used for all subsequent calls; the `externalSessionKey` is your idempotency key.

**2. Message Exchange (POST with sequenceId)**

```
POST /services/data/v63.0/einstein/ai-agent/agents/{agentId}/sessions/{sessionId}/messages
```

Request body:
```json
{
  "message": {
    "sequenceId": 1,
    "type": "Text",
    "text": "Hello, I need help with my order"
  },
  "variables": []
}
```

The `sequenceId` must start at 1 and increment by 1 for each message in the session. The platform uses this to enforce message ordering — a duplicate or out-of-order `sequenceId` results in a 400 error.

**3. Session Termination (DELETE)**

```
DELETE /services/data/v63.0/einstein/ai-agent/agents/{agentId}/sessions/{sessionId}
```

Always call DELETE when the conversation ends. Failing to do so leaves orphaned sessions that consume platform resources and may interfere with concurrent session limits.

### externalSessionKey and Session Idempotency

The `externalSessionKey` is a caller-supplied UUID that acts as an idempotency key for session creation. If the same `externalSessionKey` is submitted to POST a second time (e.g., after a network timeout), the platform returns the existing session rather than creating a duplicate. This guarantees exactly-once session semantics even in unreliable network conditions.

Requirements:
- Must conform to UUID format (RFC 4122) — e.g., `xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx`
- Must be unique per logical conversation
- Must be generated by the caller (not the platform)
- Recommended: use a UUIDv4 generator; do not use user IDs, timestamps, or sequential integers as the key value

### BYOC for CCaaS — Interaction API vs. Raw Agent API

BYOC (Bring Your Own Channel) for CCaaS is a distinct integration pattern from the raw Agent API. It is designed for Contact Center as a Service (CCaaS) providers that want to route conversations through Salesforce Omni-Channel while leveraging Agentforce Service Agents.

The BYOC flow uses two APIs:

**Establish Conversation API** — initializes the conversation and creates or retrieves a `MessagingEndUser` record in Salesforce. This record represents the end user across Omni-Channel sessions and stores conversation history.

**Interaction API** — sends and receives messages between the external CCaaS platform and the Agentforce Service Agent through the Omni-Channel routing engine.

Key distinctions from raw Agent API:

| Dimension | Raw Agent API | BYOC for CCaaS |
|---|---|---|
| Routing | Direct to agent, no Omni-Channel | Routes via Omni-Channel queue/agent assignment |
| End-user record | No Salesforce record created | Creates/reuses `MessagingEndUser` object |
| Conversation history | External responsibility | Stored in Salesforce Messaging Session |
| Auth scope | `api` + `chatbot_api` | `api` + `chatbot_api` + Omni-Channel permissions |
| Primary API | Agent API sessions endpoint | Establish Conversation + Interaction API |

### Webhook Handling Patterns

When integrating an external system, the integration layer typically acts as a bidirectional webhook bridge:

**Inbound (external system → Agentforce):** The webhook receiver accepts messages from the external channel (IVR DTMF, mobile app text, CCaaS event), translates them to the Agent API message format, increments the `sequenceId`, and posts to the Agent API sessions endpoint.

**Outbound (Agentforce → external system):** The Agent API returns the agent's response synchronously in the POST /messages response body. Parse the `messages` array in the response to extract agent reply text and any structured data (rich content, handoff signals).

For BYOC CCaaS, Agentforce sends responses via the Interaction API push mechanism to a pre-registered webhook endpoint on the CCaaS side.

---

## Common Patterns

### Pattern 1: Direct Agent API Integration for Mobile or IVR

**When to use:** A mobile app, IVR system, or custom web surface needs to interact with an Agentforce agent programmatically without Omni-Channel routing.

**How it works:**

1. Generate a UUIDv4 as `externalSessionKey` when the user starts a conversation.
2. POST to the sessions endpoint with context variables (channel, language, user tier, etc.).
3. Store the returned `sessionId` and initialize a `sequenceId` counter at 0.
4. For each user message: increment `sequenceId`, POST to `/messages`, parse `messages[].text` from the response.
5. On conversation end (user hangs up, session timeout, explicit close): DELETE the session.
6. Handle 409 Conflict on session POST by re-using the existing `sessionId` returned in the conflict response body.

**Why not the alternative:** Using a custom Apex REST endpoint to "wrap" the agent is not supported — Apex endpoints cannot invoke the Agentforce reasoning engine or route through the Einstein Trust Layer.

### Pattern 2: BYOC for CCaaS with Omni-Channel Routing

**When to use:** A CCaaS provider (e.g., Genesys, Amazon Connect, Five9) needs to surface an Agentforce Service Agent with full Omni-Channel routing, escalation to human agents, and Salesforce-side conversation history.

**How it works:**

1. Register a BYOC channel in Salesforce Setup and obtain the channel endpoint credentials.
2. Call the Establish Conversation API from the CCaaS platform when a new customer interaction begins. Salesforce creates or matches a `MessagingEndUser` record based on the provided identifier (phone number, email, or custom external ID).
3. Route the conversation through the Interaction API — send customer messages as `INBOUND_MESSAGE` events, receive Agentforce responses as `OUTBOUND_MESSAGE` events pushed to the registered webhook.
4. When the Agentforce agent determines escalation is needed, Omni-Channel handles the transfer to a human agent queue without additional API calls from the CCaaS side.
5. On conversation close, send an `END_CONVERSATION` event via the Interaction API.

**Why not the alternative:** Using raw Agent API for CCaaS integrations loses Omni-Channel routing, supervisor monitoring, conversation history storage in Salesforce, and the escalation handoff mechanism — all of which are available only through the BYOC pathway.

### Pattern 3: Stateful Conversation Context Design

**When to use:** The integration needs to carry user context (account tier, authenticated identity, preferred language) into the Agentforce session so the agent can personalize responses from the first message.

**How it works:**

Set context variables at session creation in the `variables` array. Common variables:

```json
{
  "variables": [
    { "name": "Context.Channel", "type": "Text", "value": "mobile-ios" },
    { "name": "Context.EndUserLanguage", "type": "Text", "value": "fr_FR" },
    { "name": "Context.AuthenticatedUserId", "type": "Text", "value": "003xx000001GxyzAAC" }
  ]
}
```

Do not attempt to update these mid-session. If the user's language preference changes during the conversation, `Context.EndUserLanguage` is the only variable that can be updated — all others are locked for the session lifetime.

For state that genuinely changes during a conversation (e.g., items added to cart), manage that state externally (in your integration layer or a Salesforce custom object) and surface it to the agent via agent actions, not session variables.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Mobile app or custom web surface connecting directly to Agentforce | Raw Agent API (POST/DELETE lifecycle) | Direct, low-latency path; no Omni-Channel overhead needed |
| CCaaS platform needing Omni-Channel routing and human escalation | BYOC for CCaaS (Establish Conversation + Interaction API) | Omni-Channel routing, `MessagingEndUser` record, supervisor visibility, escalation |
| IVR system sending DTMF or voice-transcribed text to Agentforce | Raw Agent API with context variable for channel type | IVR has no need for Omni-Channel queue; direct API is simpler |
| Need to inject user identity or account tier at start of session | Context variables in session POST `variables` array | Only reliable injection point; variables are immutable post-creation |
| User language changes mid-conversation | Update `Context.EndUserLanguage` only | Only this variable is mutable post-session-creation |
| Network timeout during session creation | Retry POST with same `externalSessionKey` UUID | Platform returns existing session on duplicate key — idempotent |
| Conversation ends (any reason) | Always call DELETE on session | Prevents orphaned sessions and resource leaks |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner building a custom Agentforce channel integration:

1. **Determine integration pattern** — Confirm whether the use case requires raw Agent API (direct, no Omni-Channel) or BYOC for CCaaS (Omni-Channel routing, human escalation, MessagingEndUser records). These use different APIs, endpoints, and data models. Do not mix them.
2. **Configure Connected App and OAuth** — Create or verify a Connected App with OAuth scopes `api` and `chatbot_api`. For BYOC CCaaS, also confirm Omni-Channel permissions. Retrieve the Agent ID from `SELECT Id, DeveloperName FROM BotDefinition WHERE DeveloperName = 'YourAgent'` or Setup > Agentforce Agents > Agent Detail.
3. **Design session management** — Implement a UUIDv4 generator for `externalSessionKey` (one UUID per logical conversation). Initialize a per-session `sequenceId` counter starting at 0. Plan the session creation, message exchange, and DELETE lifecycle. Handle 409 Conflict on session POST by extracting `sessionId` from the conflict response.
4. **Define context variables** — Determine which context variables to inject at session start (`Context.Channel`, `Context.EndUserLanguage`, authenticated user identifiers, account tier). Document that all variables except `Context.EndUserLanguage` are immutable for the session lifetime. Plan external state management for data that changes during a conversation.
5. **Implement webhook or event handling** — For raw Agent API: parse the synchronous `messages` array in POST /messages responses. For BYOC CCaaS: register the inbound webhook endpoint, implement the Establish Conversation API call, and handle `OUTBOUND_MESSAGE` push events from the Interaction API.
6. **Implement graceful session termination** — Ensure DELETE is called on session end in all code paths including timeouts, user drop-offs, errors, and explicit closes. Implement a session registry or TTL-based cleanup job for sessions that did not receive a DELETE.
7. **Test sequenceId sequencing and error handling** — Validate that sequenceId increments correctly with no gaps. Test retry behavior using the same `externalSessionKey`. Verify that context variables injected at creation are present in early agent responses. Test DELETE and confirm the session is no longer accessible.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] `externalSessionKey` is generated as a valid UUIDv4 (not a user ID, timestamp, or sequential integer)
- [ ] `sequenceId` starts at 1 and increments by exactly 1 per message with no gaps or resets within a session
- [ ] Connected App includes both `api` and `chatbot_api` OAuth scopes
- [ ] Context variables are injected only at session creation; no code attempts to update non-language variables mid-session
- [ ] DELETE is called on session termination in all code paths (success, error, timeout, user drop)
- [ ] For BYOC CCaaS: Establish Conversation API is called before any Interaction API messages; `MessagingEndUser` record creation is handled
- [ ] Integration pattern (raw Agent API vs. BYOC CCaaS) is documented and the correct endpoints and auth are used for each
- [ ] Session creation retries use the same `externalSessionKey` UUID (not a new one) to leverage idempotency

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **sequenceId gaps cause 400 errors** — The platform enforces monotonically increasing sequenceIds with no gaps. If message 3 fails to send and the integration retries as message 4 without re-sending message 3, the session is corrupted and subsequent messages will be rejected. Always retry the failed message with the same sequenceId before incrementing.
2. **Context variables are immutable at session start (except EndUserLanguage)** — Variables passed in the `variables` array at session creation cannot be changed for the lifetime of the session. The only exception is `Context.EndUserLanguage`, which can be updated via a subsequent API call. Attempting to "update" other variables mid-session has no effect — the original values are retained.
3. **externalSessionKey must be a UUID** — The platform validates UUID format on session POST. Strings that look like session IDs (e.g., `user-123-conversation-456`, ISO timestamps, numeric IDs) are rejected with a 400 validation error. Use a proper UUIDv4 generator.
4. **BYOC CCaaS uses Interaction API, not raw Agent API** — BYOC integrations do not call the Agent API sessions endpoint directly. They use the Establish Conversation API and Interaction API, which have different base paths, different event schemas, and different authentication requirements. Mixing the two APIs in a single integration causes session state errors and routing failures.
5. **Orphaned sessions from missing DELETE** — Sessions not explicitly closed via DELETE remain active on the platform and count against concurrent session limits. In high-volume integrations (IVR, mobile), failure to call DELETE for dropped calls or timed-out sessions depletes the session pool. Implement a TTL-based background cleanup job.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Session management implementation | Code or pseudocode for session POST, message POST with sequenceId tracking, and session DELETE |
| externalSessionKey generator | UUIDv4 generation snippet with idempotency retry logic |
| Context variable injection plan | List of variables to inject at session creation with types and source data |
| Webhook endpoint design | Inbound/outbound message routing logic for raw Agent API or BYOC Interaction API |
| BYOC integration plan | Establish Conversation API call sequence, MessagingEndUser record handling, Omni-Channel routing config |
| Session cleanup job | TTL-based or event-driven job to DELETE orphaned sessions |

---

## Related Skills

- `agentforce/agent-channel-deployment` — use for standard channel setup (Embedded Service widget, Slack, standard Messaging), NOT for programmatic API integrations
- `agentforce/custom-agent-actions-apex` — use when building Apex-based agent actions that the Agentforce agent calls during a session; this skill handles the session/channel layer, not the action layer
- `agentforce/agentforce-agent-creation` — use for UI-driven agent setup, topic assignment, and activation in Setup before implementing any channel integration
- `integration/api-led-connectivity` — use when the external system connects to Salesforce through MuleSoft or an API gateway layer rather than directly to the Agent API

---

## Official Sources Used

- Agentforce Agent API Session Lifecycle — https://developer.salesforce.com/docs/einstein/genai/guide/agent-api-session-lifecycle.html
- Bring Your Own Channel for CCaaS Agentforce Service Agent — https://developer.salesforce.com/docs/einstein/genai/guide/byoc-ccaas-agentforce.html
- Agentforce Developer Guide — https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html
- Einstein Platform Services — https://developer.salesforce.com/docs/einstein/genai/guide/overview.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
