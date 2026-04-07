# AI Agent to Salesforce Org Integration Architecture — Work Template

Use this template when designing or reviewing an external AI agent integration with a Salesforce org. Fill in each section before making implementation recommendations.

## Scope

**Skill:** `ai-agent-org-integration-architecture`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Answer the Before Starting questions from SKILL.md before proceeding:

- **Use case classification:** (read-only / read-write / event-driven / batch / interactive)
- **AI client type:** (Claude Desktop, ChatGPT, LangChain, LangGraph, custom pipeline, other)
- **Salesforce org edition:** (Developer / Enterprise / Unlimited — affects Connected App support and API limits)
- **Compliance constraints:** (HIPAA, GDPR, CCPA, Salesforce Shield, data residency, PII masking requirements)
- **Expected call volume:** (estimated API calls per hour/day; compare against org API limit)
- **Audit requirements:** (are agent actions subject to per-user audit? or org-level logging sufficient?)

## Integration Pattern Selection

Which pattern from SKILL.md applies?

- [ ] **Pattern A — MCP via salesforce-mcp-lib** (MCP-capable AI clients: Claude Desktop, Cursor)
- [ ] **Pattern B — Direct REST API** (custom LLM pipelines: LangChain, LangGraph, Python)
- [ ] **Pattern C — Platform Events / Change Data Capture** (event-driven, AI reacts to data changes)
- [ ] **Hybrid** (describe combination)

**Rationale for selected pattern:**

**Rejected alternatives and why:**

## Auth Model Design

| Decision | Selection | Rationale |
|---|---|---|
| OAuth flow | Client Credentials / JWT Bearer / Web Server | |
| Run-as user profile | (custom profile name) | |
| Connected App OAuth scopes | api, refresh_token, ... | |
| Token expiry / rotation strategy | | |

**Least-privilege checklist for run-as user profile:**
- [ ] "API Only" attribute enabled (no Salesforce UI access)
- [ ] Object permissions limited to required objects only
- [ ] Field-level security excludes PII fields not needed by the agent
- [ ] No System Administrator profile; custom profile used

## Data Exposure Scope Definition

| Category | Scope | Justification |
|---|---|---|
| Objects the agent can read | | |
| Objects the agent can write | | |
| PII fields explicitly excluded | | |
| Record-level filter (sharing rule / ownership) | | |
| Operations permitted (read / create / update / delete) | | |

## Governor Limit Impact Assessment

- **Estimated API calls per hour:** ___
- **Org's API limit per hour:** (check Setup > Company Information > API Requests Last 24 Hours)
- **Headroom percentage:** ___
- **Risk if agent volume spikes:** ___
- **Mitigation:** (rate limiting, caching, bulk endpoint usage, etc.)

## Observability Design

- **Audit log mechanism:** (Salesforce Event Monitoring / Apex Debug Logs / external SIEM / all)
- **Agent call identification:** (how are agent API calls distinguished from human calls in logs)
- **Anomaly detection:** (alert mechanism for unexpected high call volume or error rate)
- **Error surfacing:** (how the agent team is notified of integration failures)

## Implementation Checklist

Copy from SKILL.md review checklist:

- [ ] Integration pattern selected and rationale documented with rejected alternatives
- [ ] OAuth flow chosen and Connected App design documented with scope list
- [ ] Run-as user profile restricted to minimum necessary object and field permissions
- [ ] Data exposure scope defined: objects, fields, operations, record-level filter
- [ ] Governor limit impact estimated and confirmed within org limits
- [ ] Observability design: audit log mechanism identified, anomaly detection described
- [ ] Well-Architected review completed against Security, Scalability, Reliability, OpEx pillars
- [ ] PII handling addressed (fields excluded from scope or masking/tokenization documented)

## Well-Architected Pillar Notes

**Security:**
- Connected App scopes restricted to minimum necessary
- Run-as user uses custom least-privilege profile
- PII field exclusions documented
- No secrets in committed code

**Scalability:**
- API call volume estimated and within org limits
- Caching strategy defined for repeated lookups (if applicable)
- Bulk endpoint usage considered for high-volume patterns

**Reliability:**
- Error handling defined at the integration layer
- Retry strategy for transient 5xx responses
- Circuit breaker pattern for sustained org unavailability (if applicable)

**Operational Excellence:**
- Deployment pipeline for Apex changes defined
- Agent behavior observable via logs
- Runbook for common failure scenarios

## Deviations from Standard Architecture

(Record any deviations from the recommended patterns and the reason for each)
