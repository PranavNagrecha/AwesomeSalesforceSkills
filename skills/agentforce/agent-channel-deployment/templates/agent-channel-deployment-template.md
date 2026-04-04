# Agent Channel Deployment — Work Template

Use this template when planning or executing an Agentforce agent channel deployment.

## Scope

**Skill:** `agentforce/agent-channel-deployment`

**Request summary:** (fill in what the user asked for)

**Target channel(s):** (circle or list)
- [ ] Embedded Service (web chat widget — Experience Cloud or external site)
- [ ] Slack (internal Slack workspace)
- [ ] Agent REST API (mobile app, custom surface, third-party integration)
- [ ] Salesforce Mobile (standard mobile app)
- [ ] Multi-channel (list all targets above)

---

## Pre-Deployment Checklist

Complete all items before starting channel configuration.

### Agent Readiness
- [ ] Agent name and API name confirmed:
- [ ] Agent is in **Active** state (Setup > Agentforce Agents):
- [ ] Agent has at least one topic with at least one action:
- [ ] Agent instructions and role description finalized:
- [ ] Einstein Trust Layer reviewed for this channel's audience (internal / external):

### Channel Prerequisites — Embedded Service
- [ ] Target domain origins collected (all environments):
  - Production: `https://`
  - Staging: `https://`
  - Other: `https://`
- [ ] Experience Cloud site identified (if applicable):
- [ ] CORS Allowed Origins to be added:
- [ ] CSP Trusted Sites to be configured:
- [ ] Page or component where snippet will be embedded:

### Channel Prerequisites — Slack
- [ ] Slack Workspace Admin identified and available:
- [ ] Workspace name:
- [ ] Target Slack channels (for channel-mention mode):
- [ ] DM mode enabled: Yes / No

### Channel Prerequisites — Agent REST API
- [ ] Connected App name:
- [ ] OAuth scopes confirmed: `api`, `chatbot_api`
- [ ] Authentication method: OAuth 2.0 / Session ID
- [ ] Named Credential configured: Yes / No
- [ ] Calling application platform: (Mobile / Web / Backend)
- [ ] Agent ID retrieved: (BotDefinition DeveloperName or record ID)

---

## Deployment Steps

### Embedded Service Deployment

- [ ] 1. Setup > Embedded Service Deployments > **New**
- [ ] 2. Select **Messaging for In-App and Web**
- [ ] 3. Enter deployment name: _________________ and API name: _________________
- [ ] 4. Select target Experience Cloud site (or None for external):
- [ ] 5. On Messaging tab: select agent: _________________
- [ ] 6. Configure branding and pre-chat fields
- [ ] 7. On Security tab: add CORS Allowed Origins:
  - `https://`
  - `https://`
- [ ] 8. Add CSP Trusted Sites (Setup > CSP Trusted Sites):
  - `https://<org-domain>.my.salesforce.com` (connect-src)
  - `https://static.lightning.force.com` (connect-src, frame-src)
- [ ] 9. Click **Publish**
- [ ] 10. Copy snippet and add to target page OR add Embedded Messaging component in Experience Builder
- [ ] 11. Republish Experience Cloud site (if applicable)
- [ ] 12. Wait 10 minutes, then test on live domain

### Slack Deployment

- [ ] 1. Setup > Agentforce > Slack Deployment > **Connect to Slack**
- [ ] 2. Coordinate with Slack Workspace Admin to approve OAuth installation
- [ ] 3. Confirm OAuth scopes granted: `chat:write`, `channels:read`, `app_mentions:read`, `im:read`
- [ ] 4. Select agent: _________________
- [ ] 5. Configure mode:
  - [ ] DM mode
  - [ ] Channel mode — add channel IDs: _________________
- [ ] 6. Click **Publish**
- [ ] 7. Test: DM the Salesforce app in Slack / @mention in configured channel

### Agent REST API

- [ ] 1. Create Connected App with OAuth scopes: `api`, `chatbot_api`
- [ ] 2. Note Consumer Key: _________________ (store securely)
- [ ] 3. Retrieve agent ID:
  ```
  SELECT Id, DeveloperName FROM BotDefinition WHERE DeveloperName = '<agent-api-name>'
  ```
  Agent ID: _________________
- [ ] 4. Test session creation:
  ```
  POST /services/data/v63.0/einstein/ai-agent/agents/{agentId}/sessions
  Body: {"externalSessionKey": "<unique-id>", "instanceConfig": {"endpoint": "<instanceUrl>"}}
  ```
- [ ] 5. Test message send:
  ```
  POST /services/data/v63.0/einstein/ai-agent/agents/{agentId}/sessions/{sessionId}/messages
  Body: {"message": {"text": "test message", "sequenceId": 1, "type": "StaticContent"}}
  ```
- [ ] 6. Test session close:
  ```
  DELETE /services/data/v63.0/einstein/ai-agent/agents/{agentId}/sessions/{sessionId}
  ```
- [ ] 7. Confirm response format matches calling application's expectations

---

## Production Promotion Checklist

- [ ] Agent metadata deployed to production (Bot, BotVersion, GenAiPlannerBundle, GenAiPlugin, GenAiFunction)
- [ ] Agent manually activated in production (does not carry from sandbox)
- [ ] Each Embedded Service deployment republished in production after activation
- [ ] Slack deployment reconfigured in production (if different Slack workspace)
- [ ] Agent API Connected App deployed or recreated in production
- [ ] Channel-specific tests run in production (not just Builder preview)
- [ ] Enhanced Event Logs enabled in production
- [ ] CDN propagation confirmed (10 min after Embedded Service publish)

---

## Post-Deployment Validation

For each deployed channel:

| Channel | Test Action | Expected Result | Actual Result | Pass/Fail |
|---|---|---|---|---|
| Embedded Service | Open widget on live domain | Widget loads, agent responds | | |
| Embedded Service | Submit a query | Agent responds within 5 seconds | | |
| Slack DM | DM the Salesforce app | Agent responds in Slack | | |
| Slack channel | @mention app in channel | Agent responds in thread | | |
| Agent API | POST to /sessions | HTTP 201, sessionId returned | | |
| Agent API | POST message to session | HTTP 200, response messages returned | | |

---

## Notes And Deviations

Record any deviations from standard patterns and reasons:

---

## Change Management Log

| Date | Channel | Change Made | Republished? | Tested? |
|---|---|---|---|---|
| | | | | |
