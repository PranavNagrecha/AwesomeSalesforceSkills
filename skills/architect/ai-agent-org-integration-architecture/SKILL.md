---
name: ai-agent-org-integration-architecture
description: "Use this skill to design and review the architecture for integrating external AI agents (Claude, ChatGPT, LangChain, custom LLM pipelines) with a Salesforce org — covering integration pattern selection (MCP vs. REST vs. Platform Events), auth model design, data exposure scope, org governor limit planning, and Well-Architected tradeoffs. Trigger keywords: AI agent Salesforce integration, agent-to-org architecture, LLM Salesforce access pattern, external AI org connectivity, agentic system org design. NOT for native Agentforce Agent creation inside Salesforce (use agent-topic-design), NOT for implementation-level Apex tool code (use mcp-tool-definition-apex), NOT for ETL or data pipeline design (use sf-to-llm-data-pipelines)."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Scalability
  - Reliability
  - Operational Excellence
triggers:
  - "How should an external AI agent connect to Salesforce to read and write CRM data?"
  - "What is the right architecture for giving Claude or ChatGPT access to my Salesforce org?"
  - "Should I use MCP, REST API, or Platform Events to connect an LLM pipeline to Salesforce?"
  - "How do I design secure, auditable AI agent access to Salesforce without exposing the whole org?"
  - "What are the Well-Architected tradeoffs for different external AI-to-Salesforce integration patterns?"
tags:
  - architecture
  - agentforce
  - mcp
  - ai-agent
  - integration
  - rest-api
  - platform-events
  - oauth
  - well-architected
  - llm
inputs:
  - Org type (production, sandbox, scratch) and Salesforce edition (Enterprise/Unlimited minimum for most AI use cases)
  - AI agent platform being integrated (Claude Desktop, ChatGPT, LangChain agent, custom pipeline)
  - "Use case scope — read-only, read-write, event-driven, batch, or interactive"
  - Security and compliance requirements (data residency, PII handling, audit log requirements)
  - Expected call volume and latency requirements
outputs:
  - Integration pattern recommendation with rationale (MCP via salesforce-mcp-lib, REST API direct, Platform Events, or hybrid)
  - Auth model design (Connected App OAuth scopes, run-as user profile, Permission Set assignment)
  - Data exposure scope definition (which objects, fields, and records the agent can access)
  - Governor limit impact assessment for expected call volume
  - Well-Architected review notes covering Security, Scalability, Reliability, and Operational Excellence pillars
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-07
---

# AI Agent to Salesforce Org Integration Architecture

This skill activates when an architect or senior developer needs to design or review the integration architecture for connecting an external AI agent — Claude Desktop, a ChatGPT plugin, a LangChain/LangGraph pipeline, or a custom LLM system — to a Salesforce org in a secure, auditable, and operationally sustainable way.

The central architectural decision is choosing the right integration pattern for the use case, then designing the auth model and data exposure scope to satisfy security and compliance requirements while staying within Salesforce platform constraints.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Use case classification**: Is the AI agent performing read-only lookups, read-write operations, event-driven reactions, or bulk data processing? The answer determines which integration pattern is appropriate.
- **AI client type**: Is the client an MCP-capable AI (Claude Desktop, Cursor, ChatGPT with MCP support)? A custom LLM pipeline (LangChain, LangGraph, Crew.AI)? A REST consumer? Each has different protocol constraints.
- **Salesforce org edition**: Enterprise or Unlimited is required for Connected Apps with Client Credentials Flow and for Platform Event licenses. Developer Edition supports Connected Apps but has API call limits that make production simulation misleading.
- **Compliance constraints**: Does data leaving the org via the API need to be logged? Are there PII masking requirements? Is the org subject to HIPAA, GDPR, or Salesforce Shield requirements? These constraints filter the viable pattern options significantly.
- **Volume expectations**: Salesforce imposes per-org API call limits based on edition and license count. An interactive assistant making 2-3 API calls per user message scales differently than a batch pipeline making thousands of calls per hour.

---

## Core Concepts

### Three Primary Integration Patterns

**Pattern A — MCP via salesforce-mcp-lib (for MCP-capable AI clients):** Install the salesforce-mcp-lib 2GP Apex package and expose custom tools, resources, and prompts through an Apex REST endpoint. The npm proxy handles OAuth and bridges stdio to HTTPS. Best for interactive AI assistants that need to call specific, well-defined Salesforce operations.

**Pattern B — Direct REST API (for custom LLM pipelines):** The AI pipeline uses Salesforce REST API directly, authenticating with OAuth 2.0 (Client Credentials, JWT Bearer, or Named Credential). The pipeline queries SOQL, reads records, and performs DML via REST. Best for LangChain or custom agents that manage their own HTTP client and tool calls.

**Pattern C — Platform Events / Change Data Capture (for event-driven architectures):** Salesforce publishes events that the AI pipeline subscribes to via CometD or the Pub/Sub API. The agent reacts to data changes rather than polling. Best for pipelines that need to trigger AI processing when Salesforce data changes (e.g., a new Case triggers an AI classification step).

### Auth Model Design

All three patterns require a Connected App. The key design decisions are:

1. **OAuth flow selection**: Client Credentials (service-to-service, no user interaction) vs. JWT Bearer (service-to-service, requires certificate setup) vs. Web Server (user-delegated, requires browser redirect). For AI agent integrations, Client Credentials is the most appropriate for automated systems; Web Server is appropriate for user-facing AI assistants where actions should be attributed to the end user.

2. **Run-as user (for Client Credentials)**: The service account user's profile and Permission Sets define the agent's maximum data access. Apply the principle of least privilege — the agent should only see the objects and fields its tools explicitly need.

3. **Scope restriction**: OAuth scopes on the Connected App restrict which API surfaces are accessible. Use `api` (SOAP/REST), `refresh_token` (token renewal), and specific feature scopes (e.g., `cdp_query_api` for Data Cloud) rather than broad access.

### Data Exposure Scope

The most common architectural failure in AI-to-org integrations is over-broad data exposure. An agent that can query any object with any SOQL is a data exfiltration risk. Design the exposure scope before implementation:

- **Object-level**: Which objects can the agent read? Which can it write?
- **Field-level**: Within each object, which fields are visible? PII fields (SSN, bank account, health data) require explicit justification.
- **Record-level**: Can the agent see all records of a type, or only records related to a specific context (e.g., only Cases assigned to the agent's service account user)?
- **Operation-level**: Read-only vs. read-write vs. delete. Most AI agents should be read-only by default.

---

## Common Patterns

### Pattern: Interactive MCP Assistant (Claude Desktop to Salesforce)

**When to use:** A developer or sales team member is using Claude Desktop and wants to query and update Salesforce data interactively during their workflow.

**How it works:**

1. Install salesforce-mcp-lib Apex package in the org.
2. Design a set of narrow, purpose-specific McpToolDefinition classes covering the specific operations the team needs (e.g., `get_account`, `create_case`, `search_contacts`).
3. Create a Connected App with Client Credentials Flow, run-as user with a custom profile limited to the needed objects and fields.
4. Deploy the Apex REST endpoint with all tools registered.
5. Wire Claude Desktop with the npm proxy config.

Auth model: Client Credentials. All tool calls run as the service account — appropriate for team-shared org access. Not appropriate when individual user attribution is required for audit purposes.

**Why not direct REST:** Direct REST requires the LLM to construct SOQL queries and REST payloads itself, which is error-prone and hard to validate. MCP tools provide a structured, validated interface that constrains what the agent can do.

### Pattern: LangChain/LangGraph Pipeline with Named Credentials

**When to use:** A custom Python LLM pipeline (LangChain, LangGraph, Crew.AI) needs to call Salesforce as part of a multi-step reasoning chain.

**How it works:**

1. Create a Connected App with JWT Bearer Flow (more operationally robust for programmatic pipelines than Client Credentials because the certificate can be rotated without changing the client secret).
2. Use the `simple_salesforce` Python library or the Salesforce REST API directly to implement LangChain tools.
3. Implement SOQL result caching in the pipeline to reduce repeat API calls for the same data.
4. Use Named Credentials in the Salesforce org for any callouts from Salesforce back to the AI pipeline (if bidirectional flow is needed).

### Pattern: Event-Driven AI Processing (Platform Events)

**When to use:** You want AI processing to trigger automatically when a Salesforce record changes — for example, when a new Case is created, an AI step classifies it and updates the Category field.

**How it works:**

1. Define a Platform Event or use Change Data Capture on the relevant object.
2. The AI pipeline subscribes to the event stream via the Pub/Sub API (gRPC) or the CometD Streaming API.
3. On event receipt, the pipeline performs AI inference and calls back to Salesforce REST API to update the record.
4. The Connected App for the callback uses Client Credentials or JWT Bearer.

---

## Decision Guidance

| Situation | Recommended Pattern | Reason |
|---|---|---|
| MCP-capable AI client (Claude, Cursor) | Pattern A: MCP via salesforce-mcp-lib | Native protocol match; validated tool interface; fastest setup |
| Custom LLM pipeline (LangChain, Python) | Pattern B: Direct REST API | Maximum flexibility; no MCP runtime dependency |
| AI should react to Salesforce data changes | Pattern C: Platform Events / CDC | Push model avoids polling; event-driven is more reliable than polling |
| User actions must be auditable per-user | Web Server OAuth flow | Client Credentials runs as a service account; user attribution requires user-delegated tokens |
| High call volume (>1000 calls/hr) | Review API call limits; consider bulk endpoints | Standard Salesforce REST API has per-org hourly limits based on license count |
| PII fields must not leave the org | Field-level security on the run-as user profile | The service account profile should explicitly exclude PII fields |
| Bidirectional flow needed | Pattern B or A + Salesforce External Services | Salesforce → AI pipeline requires an outbound callout pattern |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Classify the integration** — determine AI client type, use case (interactive vs. event-driven vs. batch), and compliance requirements. These three inputs drive pattern selection.
2. **Select the integration pattern** — use the decision table above to choose A (MCP), B (REST), or C (Platform Events). Document the rationale including rejected alternatives.
3. **Design the auth model** — choose OAuth flow, define the run-as user profile with least-privilege permissions, set Connected App OAuth scopes to the minimum required set.
4. **Define the data exposure scope** — list every object, field, and operation the agent needs. Explicitly exclude PII fields and objects outside the agent's mandate. Document the scope definition as a review artifact.
5. **Assess governor limit impact** — estimate expected API call volume per hour, compare against the org's API limit (available via Setup > Company Information), and confirm headroom exists for concurrent human and agent usage.
6. **Design for observability** — identify how agent API calls will be logged (Event Monitoring, Apex Debug Logs, external SIEM), how errors will be surfaced, and how anomalous agent behavior (e.g., unexpected high call volume) will be detected.
7. **Review against Well-Architected pillars** — Security (auth, data scope, PII), Scalability (API limits, governor limits), Reliability (error handling, retry design), Operational Excellence (logging, deployment pipeline for Apex changes).

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Integration pattern selected and rationale documented with rejected alternatives
- [ ] OAuth flow chosen and Connected App design documented with scope list
- [ ] Run-as user profile restricted to minimum necessary object and field permissions
- [ ] Data exposure scope defined: objects, fields, operations, record-level filter
- [ ] Governor limit impact estimated and confirmed within org limits
- [ ] Observability design: audit log mechanism identified, anomaly detection described
- [ ] Well-Architected review completed against Security, Scalability, Reliability, OpEx pillars
- [ ] PII handling addressed (either fields excluded from scope or masking/tokenization mechanism documented)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **API call limits are per-org, not per-user** — Salesforce enforces an hourly API call limit at the org level (sum of all API calls from all users, apps, and agents). A high-volume AI agent can consume API budget that blocks human users from completing their work. Monitor `DailyApiRequests` via the Limits API and set a usage alert before deploying a high-volume agent.
2. **Client Credentials run-as user must have "API Only" login** — The service account used as the Connected App's run-as user should have the "API Only" user attribute set and should not have access to the Salesforce UI. Granting UI access to a service account increases the attack surface if the account is compromised.
3. **Field History Tracking records agent changes without agent attribution** — When the AI agent updates records via the service account, Field History Tracking logs the change attributed to the service account user, not to the human who triggered the agent action. For audit-sensitive use cases (financial records, healthcare), this may be a compliance problem. Design the audit strategy before implementation, not after.
4. **SOQL query results are governed by sharing, even via API** — If the run-as user has restricted sharing access, SOQL via the REST API returns only the records that user can see. An agent that "cannot find" records may simply be hitting a sharing boundary. This is correct security behavior but is frequently mistaken for a bug.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Integration pattern decision document | Selected pattern, rationale, rejected alternatives |
| Auth model specification | OAuth flow, Connected App scopes, run-as user profile requirements |
| Data exposure scope definition | Objects, fields, operations the agent is authorized to access |
| Governor limit impact assessment | Estimated API call volume vs. org limits |
| Well-Architected review notes | Pillar-by-pillar assessment of the proposed architecture |

---

## Related Skills

- salesforce-mcp-server-setup — implementation guide for Pattern A (MCP via salesforce-mcp-lib)
- mcp-tool-definition-apex — Apex implementation of specific tools within Pattern A
- agentforce/sf-to-llm-data-pipelines — data pipeline patterns for batch AI processing use cases
- agentforce/einstein-trust-layer — data masking and AI output filtering capabilities in Salesforce AI Trust Layer
- agentforce/rag-patterns-in-salesforce — retrieval-augmented generation patterns for knowledge-grounded agents

---

## Official Sources Used

- salesforce-mcp-lib GitHub (MIT) — https://github.com/Damecek/salesforce-mcp-lib
- Salesforce Connected Apps OAuth 2.0 Client Credentials Flow — https://help.salesforce.com/s/articleView?id=sf.connected_app_client_credentials_setup.htm
- Salesforce REST API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/
- Salesforce Platform Events Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/
- Salesforce API Limits — https://developer.salesforce.com/docs/atlas.en-us.salesforce_app_limits_cheatsheet.meta/salesforce_app_limits_cheatsheet/
- Agentforce Developer Guide — https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Well-Architected Security — https://architect.salesforce.com/docs/architect/well-architected/guide/security.html
