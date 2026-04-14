# API-Led Connectivity Architecture — Work Template

Use this template when designing or reviewing an API-led connectivity architecture for Salesforce integrations.

## Scope

**Skill:** `api-led-connectivity-architecture`

**Request summary:** (fill in what the user asked for)

---

## Context Gathered

Answer these before assigning API tiers:

- **Backend systems:** (list each system that needs an API abstraction)
- **Consumers:** (list each consumer type: Salesforce apps, mobile, Agentforce agents, partners)
- **Orchestration needs:** (which integrations span multiple backend systems?)
- **Consumer differentiation:** (do consumers need different response shapes or rate limits?)
- **Agentforce involvement:** (which agents need to call external backends?)
- **Governance maturity:** (is there an Exchange catalog? Versioning policy? Deprecation process?)

---

## Integration Inventory

| Integration | Backend System | Consumer(s) | Orchestration? | Tier Assignment |
|---|---|---|---|---|
| (example: order sync) | ERP | Salesforce CRM, mobile | Yes (ERP + billing) | System + Process + Experience |
| (example: product catalog read) | Warehouse | Salesforce CRM only | No | System only (ADL entry required) |

---

## API Layer Assignment

### System APIs

| API Name | Backend System Abstracted | Notes |
|---|---|---|
| system-[system]-[domain]-api | [backend] | |

### Process APIs

| API Name | Systems Orchestrated | Business Process |
|---|---|---|
| process-[business-process]-api | [system1], [system2] | |

### Experience APIs

| API Name | Consumer Type | Source Process/System API | Auth Client |
|---|---|---|---|
| experience-[consumer]-[domain]-api | [consumer type] | [process or system api] | [dedicated client ID] |

---

## Layer-Skip Decisions

For any integration where Process or Experience layers are skipped:

```
Integration: [name]
Layers skipped: [Process / Experience / both]
Rationale:
  - Consumer count: [number]
  - Anticipated new consumers: [yes/no — explain]
  - Orchestration requirement: [yes/no]
  - Response shaping requirement: [yes/no]
Re-evaluation trigger: [condition that requires revisiting this decision]
```

---

## Rate Limit Design (Top-Down)

| API | Consumer / Source | Limit (req/min) | Basis |
|---|---|---|---|
| experience-[x]-api | [consumer type] | | Peak consumer traffic estimate |
| process-[x]-api | Sum of Experience APIs | | Sum × 1.10 headroom |
| system-[x]-api | Sum of Process APIs | | Sum × 1.10 headroom |
| Backend system | System API | | Backend published capacity — validate fits |

---

## Governance Checklist Per API

For each API (copy this block):

```
API: [api-name]
- [ ] Exchange catalog entry: name, description, owner, SLA, contact
- [ ] Versioning policy: MAJOR.MINOR.PATCH; MAJOR = breaking change
- [ ] Deprecation timeline: 90-day notice to all registered consumers before decommission
- [ ] Rate limit policy configured in Exchange
- [ ] Consumer notification mechanism for MAJOR version bump
```

---

## Agentforce Integration Points

| Agent | Experience API | Auth Client | Rate Limit | Agent Fabric Route |
|---|---|---|---|---|
| [agent name] | experience-agent-[domain]-api | [dedicated client ID] | [req/min] | Agent Fabric → Experience API |

---

## Review Checklist

- [ ] Every integration assigned to a tier — or layer-skip documented in ADL
- [ ] One System API per backend system (not per consuming team)
- [ ] Separate Experience APIs for consumers with different response shape, rate limit, or auth
- [ ] Agentforce agents routed via Agent Fabric with dedicated OAuth client per agent
- [ ] Rate limits designed top-down (Experience → Process → System → validate against backend)
- [ ] Exchange catalog entry defined for every API
- [ ] Versioning policy defined (semantic versioning, MAJOR = breaking)
- [ ] Deprecation timeline documented (minimum 90 days) for any API being decommissioned
- [ ] No undocumented layer-skipping
- [ ] Salesforce System API designed for any external system that reads Salesforce data

---

## Notes

(Record any deviations from the standard pattern and the rationale)
