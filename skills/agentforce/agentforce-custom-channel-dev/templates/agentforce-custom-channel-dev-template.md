# Agentforce Custom Channel Dev — Work Template

Use this template when planning or executing a custom Agentforce channel integration.

## Scope

**Skill:** `agentforce/agentforce-custom-channel-dev`

**Request summary:** (fill in what the user asked for)

**Integration pattern:** (circle one)
- [ ] Raw Agent API (direct, no Omni-Channel) — mobile app, IVR, custom web surface, third-party system
- [ ] BYOC for CCaaS (Omni-Channel routing, human escalation, MessagingEndUser records)

---

## Context Gathered

- **Target surface / channel:** (mobile iOS, Android, IVR, CCaaS vendor name, custom web app)
- **Agent ID:** (from `SELECT Id, DeveloperName FROM BotDefinition WHERE DeveloperName = '...'`)
- **Connected App name:** _______________
- **OAuth scopes confirmed:** `api` + `chatbot_api` — Yes / No
- **externalSessionKey strategy:** (UUIDv4 generated per conversation — confirm library used: _______)
- **Context variables to inject at session start:**

| Variable Name | Type | Source / Value |
|---|---|---|
| Context.Channel | Text | (channel identifier string) |
| Context.EndUserLanguage | Text | (locale, e.g., en_US) |
| (custom) | Text | (value or data source) |

- **Known constraints:** (concurrent session limits, expected conversation volume, timeout requirements)
- **Session cleanup plan:** (finally block, background job, TTL: _____ minutes)

---

## Integration Pattern Checklist

### Raw Agent API

- [ ] 1. Connected App created with OAuth scopes: `api`, `chatbot_api`
- [ ] 2. Agent ID confirmed: _______________
- [ ] 3. UUIDv4 generator implemented for `externalSessionKey`
- [ ] 4. Per-session `sequenceId` counter initialized at 0, increments on successful send only
- [ ] 5. Session creation (`POST /sessions`) implemented with context variables
- [ ] 6. 409 Conflict on POST handled — extract `sessionId` from response, continue
- [ ] 7. Message send (`POST /sessions/{sessionId}/messages`) implemented
- [ ] 8. Agent response parsed from `messages[]` array in POST response
- [ ] 9. Session DELETE implemented in finally/cleanup handler (not only happy path)
- [ ] 10. Background cleanup job configured for TTL: _____ minutes

### BYOC for CCaaS

- [ ] 1. BYOC channel registered in Salesforce Setup
- [ ] 2. Channel address identifier obtained: _______________
- [ ] 3. Webhook endpoint registered for outbound Agentforce responses
- [ ] 4. Establish Conversation API call implemented (creates MessagingEndUser record)
- [ ] 5. `externalConversationIdentifier` strategy defined (CCaaS contact/session ID)
- [ ] 6. `endUserClientIdentifier` strategy defined (phone, email, or custom external ID)
- [ ] 7. Inbound message routing via Interaction API (`INBOUND_MESSAGE` event type)
- [ ] 8. Outbound webhook handler implemented (receives `OUTBOUND_MESSAGE` events)
- [ ] 9. END_CONVERSATION event sent on conversation close
- [ ] 10. Omni-Channel queue routing confirmed: _______________

---

## Session Lifecycle Notes

**externalSessionKey:** (paste example UUID here — confirm it's a proper v4 UUID)

**sequenceId tracking:** (describe how the counter is stored and protected from concurrent access)

**Session registry:** (where are active sessions logged? Database table, Redis key, Salesforce custom object?)

**Cleanup trigger:** (what triggers DELETE? User close, timeout, error, all three?)

---

## Context Variable Design

| Variable | Mutable Mid-Session? | Notes |
|---|---|---|
| Context.Channel | No | Set at creation, locked for session lifetime |
| Context.EndUserLanguage | YES — only exception | Can be updated post-creation |
| All other variables | No | Silent ignore if passed in /messages payload |

**Dynamic data strategy:** (how will context that changes mid-conversation be surfaced to the agent?)
- [ ] Agent action (Apex) that queries live data on demand
- [ ] Agent action (Flow) that queries live data on demand
- [ ] Pre-loaded at session creation (only if stable for session lifetime)

---

## Webhook / Event Handling

**Inbound path:** (how does a message from the external channel reach the Agent API?)

**Outbound path:** (how does the agent's response reach the external channel?)

**Error handling:** (what happens if the Agent API returns 4xx/5xx? Retry strategy:)

**Timeout:** (what is the client-side timeout for Agent API calls? Confirm it exceeds expected agent reasoning time of 1–5 seconds)

---

## Deviations From Standard Pattern

(Record any decisions that deviate from the SKILL.md recommended workflow and the reason why.)

---

## Review Checklist

- [ ] `externalSessionKey` is a UUIDv4 (not a user ID, timestamp, or arbitrary string)
- [ ] `sequenceId` starts at 1 per session, increments monotonically, no gaps, retries use same ID
- [ ] Connected App has both `api` and `chatbot_api` OAuth scopes
- [ ] Context variables are injected at session creation only; mid-session updates are only for `Context.EndUserLanguage`
- [ ] DELETE is called on session end in all code paths (success, error, timeout, user drop)
- [ ] Integration pattern is consistent — raw Agent API OR BYOC CCaaS, not mixed
- [ ] For BYOC: Establish Conversation API called before any Interaction API messages
- [ ] Session cleanup job (background TTL DELETE) is implemented for high-volume or unreliable network scenarios
- [ ] 409 Conflict on POST is handled as idempotent success (use returned sessionId, do not error)
- [ ] No PII is logged in plain text (externalSessionKey, endUserClientIdentifier, context variable values)
