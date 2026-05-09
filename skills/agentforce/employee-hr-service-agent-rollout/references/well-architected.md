# Well-Architected Notes — Employee HR Service Agent Rollout

## Relevant Pillars

### Security

The Employee HR Service agent operates against the most sensitive data the organization holds about its own people — pay, leave, dependents, performance, terminations. The pillar question is not "is the agent secure?" in a generic sense; it is "does the *combination* of the agent, the HRIS connector, the LLM context, and the surface honour an employee-self-only data boundary, with carefully scoped manager-of-team expansion?"

Three concrete requirements:

- **Bind data access to the running user, not to agent inputs.** Agent actions must derive the employee identity from `UserInfo.getUserId()` (or the Slack/Teams-to-Salesforce mapping for chat surfaces) and never accept an employee identifier as an input parameter. This makes prompt-injection attacks ("get the leave balance for user X") structurally impossible to satisfy.
- **Strip non-essential PII before the LLM sees it.** The Einstein Trust Layer adds defense in depth (masking, zero-retention) for the data that does enter the prompt, but the durable security control is to *not put the data in the prompt in the first place*. Action layer return types should contain only the fields the agent will display.
- **Treat the chat transcript as a data class subject to retention controls.** GDPR Article 17 and similar frameworks apply to transcripts that contain employee PII. Transcript retention defaults must be set deliberately, with a documented purge mechanism for departed employees.

### Reliability

Read-only HRIS integration is reliable enough to ship in a pilot quarter; read-write integration is not, unless explicitly engineered for failure. Reliability concerns specific to the rollout:

- **No two-phase commit between Salesforce and the HRIS.** A leave-request submission can succeed in Workday and fail in Salesforce, or vice versa. The local-record-first pattern (write a `PENDING` row in Salesforce, then call HRIS, then update the local row) gives the system a recoverable state machine. Without it, partial failures are silent.
- **Channel deployment surfaces fail independently.** A Slack workspace OAuth re-authorization, a Microsoft Teams app version drift, an Embedded Service CORS misconfiguration — each takes one surface offline while the others continue working. The rollout plan needs a per-surface health check, not a single "is the agent up?" signal.
- **HRIS integrations rate-limit aggressively.** Workday, ADP, and BambooHR all impose API-side rate limits that are lower than Salesforce's. An agent that calls the HRIS on every conversation turn can be blocked by a single high-traffic moment. Cache user-scoped data for the session duration, and design for graceful degradation when the HRIS is rate-limited.

### Operational Excellence

The rollout is not "build and forget"; it's an operational program with a measurement loop. Operational concerns:

- **Measurement from day 1.** Without baseline metrics — pre-launch HR case volume, time-to-first-response, CSAT — there is no honest answer to "is the agent working?" Instrument before launch.
- **Standard topics drift across releases.** Salesforce updates the shipped Employee Service topic content periodically. The org's customizations need to be re-validated each release; a topic that was customized in Spring '25 may need re-merge work in Summer '25.
- **HRIS-side data quality propagates to agent behavior.** A manager assignment that's stale in the HRIS produces a manager-of-team flow that returns the wrong people. Operational excellence treats `User.ManagerId` synchronization with the HRIS as a first-class dependency, not an afterthought.

## Architectural Tradeoffs

| Tradeoff | Why it matters |
|---|---|
| **In-Salesforce console vs Slack-first vs Teams-first** | Most frontline employees do not live in the Salesforce console. Forcing them there for HR self-service guarantees low adoption. Slack and Teams are where employees already are; deploy to where the user is, not where the platform is most native. The cost is a more complex test matrix and dependency on the workspace administrator's cooperation. |
| **Read-only HRIS integration vs read-write back** | Read-only is observably useful within a pilot quarter and has a manageable failure model (HRIS down → agent shows "temporarily unavailable"). Read-write doubles integration effort, requires reconciliation runbooks for failed submissions, and creates compliance complexity (EU works councils may need to consult on automated submissions). Default the pilot to read-only; graduate read-write workflow by workflow. |
| **Salesforce Knowledge grounding vs external retrieval** | Salesforce Knowledge integrates natively, supports Data Category visibility that lines up with the manager-vs-employee split, and uses the platform's existing publish/version model. External retrieval (Confluence, SharePoint via connectors) preserves authoring in HR's existing tools but creates a moving target for grounding quality and a separate access-control model to audit. For a pilot, import to Knowledge; for mature steady state, evaluate external retrieval as authoring stays where HR works. |
| **Standard shipped topics vs net-new authoring** | Shipped topics encode years of conversation-design patterns. Customizing them is faster and more reliable than authoring from scratch; the org's job is to connect them to org data. Net-new is occasionally necessary for highly local workflows (e.g., a country-specific leave program that doesn't fit the shipped leave topic), but should be the minority of pilot effort. |
| **One agent for employees and HRBPs vs split agents** | One agent simplifies authoring but the visibility / data-access model differs sharply between an employee asking about their own data and an HRBP investigating a case. A split with a thin shared layer (persona, tone, common policies) and dedicated topics per audience is operationally cleaner; one agent with role-conditional topics works for smaller orgs but accumulates conditional complexity. |

## Anti-Patterns

1. **Trusting the LLM with the visibility model** — Embedding "you may only show this manager their direct reports" as a prompt instruction is a wish, not a control. The action layer must enforce the boundary by querying with explicit relationship filters and returning only authorized rows. Treat the LLM as a presentation layer; never as an access-control layer.

2. **Passing the full HRIS row into the prompt** — A team that pulls a Workday worker record (containing pay, dependents, manager, performance score) and passes the entire JSON to the agent has just put all of that data into the LLM context, where it is at risk of leaking into responses. Strip to the minimum-necessary fields server-side before the agent ever sees the data.

3. **Treating the agent rollout as a build project, not an operational program** — Launching the agent without baseline metrics, without a measurement cadence, without an operational owner, and without a change-management plan for HR ops creates an artifact that drifts within a quarter. The rollout plan must include a 30/60/90 review cycle and a named owner for ongoing tuning.

4. **Deploying read-write to HRIS in the pilot** — Read-write back to Workday or ADP is technically possible but operationally heavy: idempotency, reconciliation, manager-approval round-trips, EU works-council consultation. Read-only delivers measurable value within a quarter; read-write is a second-phase decision for workflows where the pilot data shows round-tripping through the HRIS UI is the dominant friction.

5. **Skipping the contractor / shadow-user test case** — Pilots typically use full-FTE employees with established SSO. Production traffic includes contractors, recently-onboarded employees with incomplete SSO mappings, and ex-employees whose accounts are still in the workspace. The agent must handle all of these gracefully — not by silently returning the wrong data.

6. **Single-channel test coverage for multi-channel deployment** — Deploying to Slack and Teams and Embedded Service but only testing Slack creates a false-confidence release. Each channel has its own auth, identity-mapping, and rendering behavior. Test every channel before broadcasting any of them.

## Official Sources Used

- Agentforce Developer Guide — https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html — agent topic configuration, action invocation model, channel concepts
- Einstein Generative AI overview — https://developer.salesforce.com/docs/einstein/genai/guide/overview.html — Einstein Trust Layer feature framing, masking, zero-retention semantics
- Agentforce for Slack Help — https://help.salesforce.com/s/articleView?id=sf.agentforce_slack.htm — Slack workspace deployment, OAuth flow, managed app installation
- Salesforce Help — Einstein Trust Layer — https://help.salesforce.com/s/articleView?id=sf.einstein_trust_layer.htm — Trust Layer entitlement and configuration
- Salesforce Help — Salesforce Knowledge Data Category Visibility — https://help.salesforce.com/s/articleView?id=sf.knowledge_data_categories.htm — Data Category Group, channel availability, role-based visibility cascade
- Apex Developer Guide — Named Credentials — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callouts_named_credentials.htm — Named Credential storage and OAuth client credentials grant for HRIS integrations
- Object Reference — `User.ManagerId` — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_user.htm — manager-of-team relationship source of truth on the User record
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html — Trusted (Security, Reliability), Operational Excellence pillar framing
- Salesforce Well-Architected Trusted: Secure — https://architect.salesforce.com/docs/architect/well-architected/guide/trusted/secure.html — Security pillar specifics for AI agents and PII
- Architect — Agentic Patterns Guide — https://architect.salesforce.com/docs/architect/agentic-patterns/guide/overview.html — agentic-pattern decision framing for HRIS-style integrations
