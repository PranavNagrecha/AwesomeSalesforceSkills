# Agentforce Agent Creation — Planning Template

Use this fill-in-the-blank template to plan a new agent or to document an existing agent's configuration for review.

---

## Agent Identity

| Field | Value |
|---|---|
| Agent Label | |
| Agent API Name | *(immutable after creation — choose carefully)* |
| Agent Type | Agentforce Service Agent / Custom Agent |
| Salesforce Org | *(sandbox / production / scratch org name)* |
| Target Salesforce Version | *(e.g., Spring '25, Summer '25)* |

---

## Business Purpose

**What problem does this agent solve?**
(1–3 sentences describing the business job and the user population it serves.)

**What is explicitly out of scope for this agent?**
(List at least two things the agent must not do or handle.)

---

## Prerequisites Checklist

Before creation:

- [ ] Einstein Setup toggle is On in the target org.
- [ ] Agentforce feature toggle is Active (Setup > Agentforce Agents).
- [ ] Einstein Trust Layer reviewed: data masking and ZDR settings confirmed.
- [ ] EinsteinServiceAgent User exists and has the Einstein Agent User permission set assigned.
- [ ] Experience Cloud site exists and is published (if using Embedded Service channel).
- [ ] Omni-Channel is configured with a routing configuration and queue (if using Messaging for Web channel).

---

## Agent Definition

### Role (system persona statement)

```
(Write the Role field value here — 2–4 sentences describing the agent's
function, the organization it represents, and its service philosophy.)
```

### Company Context

```
(Write the Company field value here — name, industry, and any context
that shapes how the agent should interact with users.)
```

### Agent Instructions (system-level constraints)

```
(Write the agent-level instructions here. Include:
  - Tone and communication style
  - What the agent should always do
  - What the agent must never do
  - How to handle requests it cannot fulfill
  - Escalation or fallback behavior)
```

---

## Agent User Configuration

| Field | Value |
|---|---|
| Agent User Name | EinsteinServiceAgent User (or custom) |
| Permission Set Name | |
| Objects agent user can Read | |
| Objects agent user can Read/Write | |
| Any fields with FLS restrictions | |

---

## Topic Inventory

*(List topics here at a high level. Each topic is designed in detail using the agent-topic-design skill.)*

| Topic Label | Classification Description (one sentence) | Primary Actions |
|---|---|---|
| | | |
| | | |
| | | |

---

## Channel Configuration

**Primary channel type:**

- [ ] Embedded Service Deployment (Experience Cloud / external site)
- [ ] Messaging for In-App and Web (Omni-Channel)
- [ ] Agent API (custom or third-party integration)
- [ ] Standard footer (internal Salesforce app)

**Channel-specific details:**

| Field | Value |
|---|---|
| Channel Name | |
| Routing Configuration | |
| Fallback Queue | |
| Experience Cloud Site URL (if applicable) | |
| Agent API Connected App (if applicable) | |

---

## Lifecycle And Environment Promotion

| Stage | Target Org | Planned Activation Date | Notes |
|---|---|---|---|
| Development | | | |
| QA / UAT | | | |
| Staging / Full Sandbox | | | |
| Production | | | |

**Production activation owner:** *(name or role)*

**Embedded Service republish required after production activation?** Yes / No

---

## Testing Plan

| Test Type | Tool | Pass Criteria |
|---|---|---|
| Conversation Preview | Agentforce Builder preview panel | Agent completes each topic's happy path |
| Edge case / out-of-scope | Conversation Preview | Agent falls back or escalates cleanly |
| Permission verification | Agent user login / data access test | Agent retrieves only scoped records |
| Channel smoke test | Live channel (post-activation) | Widget appears, agent responds within SLA |

---

## Risk Register

| Risk | Likelihood | Mitigation |
|---|---|---|
| API Name chosen incorrectly | Low | Review naming convention before first save |
| Activation skipped in production | Medium | Include activation step in release runbook |
| Embedded Service not republished | Medium | Add republish step to release checklist |
| Agent user over-provisioned | Low | Scope permission set review as a prerequisite |
| Trust Layer not configured for data grounding | Medium | Complete einstein-trust-layer skill review before activation |

---

## Notes And Deviations

*(Record any deviations from the standard agent creation pattern and the reason for each.)*
