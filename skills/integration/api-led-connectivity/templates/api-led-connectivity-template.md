# API-Led Connectivity -- Work Template

Use this template when designing or reviewing an API-led integration architecture.

## Scope

**Skill:** `api-led-connectivity`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- Backend systems to connect:
- Consumer channels:
- Reuse requirement (multiple consumers for same backend data?):
- Latency / volume constraints:

## Layer Assignment

| Backend System | System API Name | Notes |
|---|---|---|
| (system) | (sapi name) | (auth method, protocol wrapped) |

| Business Process | Process API Name | System APIs Consumed | Notes |
|---|---|---|---|
| (process) | (papi name) | (list of SAPIs) | (business rules applied) |

| Consumer Channel | Experience API Name | Process APIs Consumed | Notes |
|---|---|---|---|
| (consumer) | (xapi name) | (list of PAPIs) | (data shaping applied) |

## Layers Skipped (if any)

| Layer | Reason for Skipping | Trigger to Add Later |
|---|---|---|
| (Process / Experience) | (justification) | (condition that would require adding it) |

## Salesforce Role

- [ ] Salesforce is a **system-layer endpoint** (other systems consume SF data through a System API)
- [ ] Salesforce is an **experience-layer consumer** (SF calls Process/Experience APIs for external data)
- [ ] Salesforce plays **both roles**

## Checklist

Copy the review checklist from SKILL.md and tick items as you complete them.

- [ ] Every backend system has at most one System API
- [ ] Layer inclusion/exclusion is documented with justification
- [ ] Salesforce's role is explicitly identified
- [ ] API contracts use OpenAPI or RAML specs in a catalog
- [ ] Authentication between layers uses OAuth 2.0 or mutual TLS
- [ ] Latency budget accounts for each network hop
- [ ] Error propagation strategy defined
- [ ] Agentforce agent actions mapped to Experience APIs (if applicable)
- [ ] No consumer calls a backend directly, bypassing the System API

## Notes

Record any deviations from the standard pattern and why.
