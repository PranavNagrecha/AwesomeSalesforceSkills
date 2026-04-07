# Examples — AI Agent to Salesforce Org Integration Architecture

## Example 1: Pattern A — MCP Interactive Assistant Architecture Decision

**Context:** A sales operations team wants to give their team members a Claude Desktop assistant that can look up Account details, check open Cases, and create new Cases without leaving their conversation.

**Problem:** Without an architectural decision process, teams jump straight to implementation and discover mid-project that their auth model is too permissive, their data exposure scope is undefined, or their API call volume exceeds the org's hourly limit.

**Solution:** Architecture decision record for this scenario:

```
Pattern selected: A — MCP via salesforce-mcp-lib
Rationale: Team uses Claude Desktop (MCP-capable). Interactive use case.
  Narrow, well-defined operations (3 tools). Fastest path to working system.

Auth model:
  OAuth flow: Client Credentials
  Run-as user: salesforce-mcp-svc@company.com
  Profile: MCP Service Account (custom — read/write Cases and Accounts, no other objects)
  Connected App scopes: api, refresh_token

Data exposure scope:
  Objects: Account (read), Case (read+create), Contact (read)
  Fields excluded: Account.AnnualRevenue (Finance team only), Contact.SSN__c (PII)
  Record-level: Account sharing = role hierarchy; Case sharing = team sharing rule
  Operations: Read on Account+Contact, Read+Create on Case. NO delete, NO bulk.

Governor limit assessment:
  Team: 15 users, avg 5 tool calls/user/day = 75 calls/day
  Org API limit (Enterprise, 50 users): 720,000 calls/24hr. Well within limit.

Observability:
  API calls logged via Salesforce Event Monitoring (API Event Type)
  Apex debug logs enabled for the service account in sandbox
  Alert: notify admin if service account exceeds 500 API calls/hour
```

**Why it works:** Documenting the decision before implementation catches the data scope gaps (AnnualRevenue, SSN) before a tool exposes them accidentally. The governor limit math confirms the pattern is viable at this team size.

---

## Example 2: Pattern C — Event-Driven AI Classification Architecture

**Context:** A support team wants Case records to be automatically classified (Category, Subcategory, Sentiment) by an LLM pipeline immediately after creation, before an agent picks it up.

**Problem:** Polling-based architectures (the AI pipeline polls for new Cases every minute) are wasteful and introduce up to 60 seconds of latency. An event-driven approach pushes Cases to the AI pipeline as soon as they are created.

**Solution:**

```
Pattern selected: C — Platform Events / Change Data Capture (CometD subscription)
Rationale: Event-driven trigger. AI pipeline is Python-based (not MCP-capable).
  Low-latency classification required before human agent views the Case.

Event source: Change Data Capture on the Case object
  CDC publishes CaseChangeEvent when a Case is created or updated.
  Filter: Python subscriber processes only Create events.

AI pipeline:
  Language: Python (LangChain)
  Subscribes to CometD /data/CaseChangeEvent channel
  On new Case event: calls LLM classification API with Case.Subject + Case.Description
  On classification result: calls Salesforce REST API to update Case.Category__c,
    Case.Subcategory__c, Case.AI_Sentiment__c

Auth model for callback:
  OAuth flow: JWT Bearer (certificate-based, suitable for long-running Python process)
  Run-as user: ai-classifier-svc@company.com
  Profile: AI Classifier Service (update Case Category/Subcategory/Sentiment only)

Governor limit assessment:
  Volume: 2,000 new Cases/day = 2,000 CDC events + 2,000 REST PATCH calls = 4,000 calls/day
  Org API limit: within budget.
  Risk: CDC events have a 24-hour retention window. If the pipeline is down for > 24hr,
    events are lost. Design a recovery job (scheduled Apex or batch) to re-classify
    Cases created in the last 24hr that have no AI classification.
```

**Why it works:** CDC eliminates polling latency. The recovery job design addresses the 24-hour CDC retention limit — a gotcha that catches most event-driven architectures.

---

## Anti-Pattern: Giving the AI Agent System Administrator Profile

**What practitioners do:** Assign a System Administrator profile to the Connected App's run-as user "to avoid permission issues during development."

**What goes wrong:** The service account has unrestricted access to all objects, fields, and records. Any SOQL the AI agent generates (or is tricked into generating via prompt injection) can access any data in the org. DML operations can modify any record. The blast radius of a compromised agent or a misguided LLM response is the entire org.

**Correct approach:** Create a custom profile (or use a base profile + Permission Sets) with only the specific object, field, and record permissions the agent's tools need. Document which permissions are granted and why. Treat the agent's service account the same way you would treat an external integration user — with explicit least-privilege access.
