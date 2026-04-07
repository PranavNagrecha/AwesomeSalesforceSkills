# LLM Anti-Patterns — AI Agent to Salesforce Org Integration Architecture

Common mistakes AI coding assistants make when generating or advising on AI Agent to Salesforce Org Integration Architecture.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending System Administrator Profile for the Service Account

**What the LLM generates:** "For ease of setup, assign the System Administrator profile to the Connected App's run-as user to avoid permission errors."

**Why it happens:** LLMs often optimize for reducing friction in the setup process. Sysadmin profile eliminates permission errors immediately. The security tradeoff is not visible in the immediate context of "make it work."

**Correct pattern:**

```
Never assign System Administrator profile to a service account used by an AI agent.
Instead:
1. Create a custom profile based on "Minimum Access - Salesforce" (or equivalent)
2. Grant only the specific object and field CRUD/FLS permissions required by each tool
3. Document why each permission was granted
4. Assign the profile to the service account user
5. Use Permission Sets for any additional access that is context-specific
```

**Detection hint:** Any recommendation that includes "Assign System Administrator" to the run-as user or Connected App service account is the anti-pattern.

---

## Anti-Pattern 2: Ignoring the Per-Org API Call Limit

**What the LLM generates:** Architecture designs or agent configurations that make no mention of API call volume, API limits, or limit monitoring.

**Why it happens:** LLMs are trained on many REST API integration examples that assume unlimited API access. The Salesforce per-org API limit is a platform-specific constraint that is underrepresented in general API integration training data.

**Correct pattern:**

```
Before deploying any AI agent integration, estimate API call volume:
  - Calls per user interaction x concurrent users x peak hours
  - Compare against org limit: GET /services/data/vXX.0/limits/ → DailyApiRequests.Max
  - Ensure agent call volume < 20% of daily limit to leave headroom for humans + other integrations
  - Set up monitoring: alert when DailyApiRequests.Remaining < 10% of Max
```

**Detection hint:** Any AI agent architecture recommendation that does not mention API call limits or volume estimation should be flagged for a limit impact review.

---

## Anti-Pattern 3: Recommending Username-Password OAuth for AI Agent Integrations

**What the LLM generates:** Instructions to configure the npm proxy or Python LangChain tools using the OAuth 2.0 Resource Owner Password Credentials (ROPC) / Username-Password flow with a username and password.

**Why it happens:** Username-Password flow is the simplest OAuth flow to explain and has broad training data coverage. LLMs default to it when asked for "simple" Salesforce authentication.

**Correct pattern:**

```
For AI agent service-to-service authentication, use:
  Option A: OAuth 2.0 Client Credentials Flow (simpler setup, client ID + secret)
  Option B: OAuth 2.0 JWT Bearer Flow (more secure, certificate-based, no secret to rotate)

Do NOT use Username-Password flow because:
  - It transmits the user's actual password to the OAuth endpoint
  - It is disabled by default in orgs with stricter security policies
  - Salesforce is deprecating it for new Connected Apps in some editions
  - It conflates a human user's credentials with a service account
```

**Detection hint:** Any configuration that includes `grant_type=password` or requires a Salesforce user's password as part of the agent configuration is the wrong flow.

---

## Anti-Pattern 4: Conflating Agentforce Agents with External AI Agent Integrations

**What the LLM generates:** Instructions to use Setup > Agents > Create Agent to build a "Salesforce MCP server" or to use Agentforce Topics and Actions as the integration point for an external LLM pipeline.

**Why it happens:** "Agentforce" and "AI agents connecting to Salesforce" sound similar. LLMs conflate native Agentforce (first-party Salesforce AI agent framework running inside the org) with external AI agent integration (third-party AI systems connecting to Salesforce via API).

**Correct pattern:**

```
Two distinct patterns — choose based on where the AI runs:

1. Native Agentforce (AI runs inside Salesforce):
   - Setup > Agents > Create Agent
   - Use Topics, Agent Actions, and Prompt Templates
   - No external API calls from the AI system to Salesforce

2. External AI agent integration (AI runs outside Salesforce):
   - AI system (Claude, ChatGPT, LangChain) calls Salesforce REST API or MCP endpoint
   - Requires Connected App + OAuth authentication
   - Covered by THIS skill (ai-agent-org-integration-architecture)
```

**Detection hint:** If the recommended setup involves Salesforce Setup menus for configuring an external AI client (Claude Desktop, ChatGPT), it is conflating the two patterns.

---

## Anti-Pattern 5: No Mention of PII or Data Exposure Scope in Architecture Recommendations

**What the LLM generates:** An end-to-end architecture for connecting an AI agent to Salesforce with no consideration of which objects, fields, or records the agent can access.

**Why it happens:** LLMs optimize for making the integration "work" and focus on technical connectivity. Data governance and scope definition are organizational concerns that LLMs often treat as out-of-scope for a technical architecture recommendation.

**Correct pattern:**

```
Every AI agent integration architecture must include a data exposure scope definition:
  1. Object-level: List every Salesforce object the agent can access (read/write/delete)
  2. Field-level: List excluded fields — especially PII (SSN, bank account, health data, email where restricted)
  3. Record-level: Define sharing/record-level filter (all records vs. specific subset)
  4. Operation-level: Read-only vs. read-write. Most agents should be read-only by default.

Document this scope before implementation, not after.
Review the scope with the data steward or security team before go-live.
```

**Detection hint:** Any AI-to-Salesforce integration architecture that does not explicitly define data exposure scope (objects, fields, operations) is incomplete.
