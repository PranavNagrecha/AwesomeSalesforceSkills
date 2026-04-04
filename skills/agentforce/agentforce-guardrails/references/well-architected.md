# Well-Architected Notes — Agentforce Guardrails

## Relevant Pillars

### Security

Guardrails are the primary mechanism for controlling what an Agentforce agent can disclose, what actions it can execute, and which subjects it will engage with. Customer-facing agents without properly configured restricted topics, action filters, and fallback instructions represent a direct information disclosure and unauthorized action execution risk. The principle of least privilege applies directly: action filters and topic filters should grant only the minimum action access the agent needs for each topic. Abuse prevention patterns (declarative fallback, restricted topics, pre-handoff message before escalation) reduce the attack surface for adversarial prompt injection from untrusted users.

### Reliability

The Escalation topic and fallback system instructions are reliability constructs. A customer-facing agent without a working escalation path and an explicit fallback response will either stall silently or produce off-policy output when conversation inputs fall outside the designed topic set. Both of these outcomes degrade user experience and erode trust in the agent deployment. Instruction Adherence monitoring is the primary operational reliability signal: a sustained low adherence score indicates the agent is not behaving predictably, which is a reliability risk before it becomes a security risk.

### Operational Excellence

Instruction Adherence monitoring, conversation log review, and restricted topic match analysis are the ongoing operational practices for this skill area. Without a cadence for reviewing these signals, guardrail drift occurs: instructions become stale as user behavior evolves, restricted topic entries miss new phrasings, and action filters become overly broad or narrow as the action library changes. Operational excellence in this domain means treating agent instructions as living configuration artifacts that require periodic review, not one-time setup.

### Performance

Overly long system instructions and Scope fields add latency to LLM reasoning. While Salesforce abstracts most of this, instructions that cause repeated reasoning loop re-evaluations (due to imperative instruction conflicts) directly increase turn latency. Declarative, concise instructions improve both reliability and perceived performance.

---

## Architectural Tradeoffs

### Defense-in-Depth vs. Configuration Complexity

Running all four guardrail layers (restricted topics, agent-level instructions, topic Scope, action filters) provides the strongest behavioral control but also increases configuration complexity and the risk of over-filtering (blocking legitimate agent behavior). The tradeoff: start with restricted topics and a fallback system instruction as the minimum viable guardrail set. Add topic Scope refinements and action filters only where specific risk has been identified.

### Pre-Classification vs. Post-Classification Controls

Restricted topics are the only pre-classification guardrail. All other controls (Scope, system instructions, action filters, topic filters) operate after topic selection. For high-risk subjects (legal advice, medical advice, competitor information), pre-classification controls (restricted topics) are the appropriate choice because they do not rely on the LLM routing the conversation correctly first. For nuanced in-topic boundaries (e.g., "this topic processes standard returns but not policy exceptions"), post-classification Scope controls are appropriate.

### Explicit Fallback vs. Implicit Agent Behavior

If no fallback system instruction is written, the agent's behavior for unmatched inputs is determined by the base LLM's general-purpose behavior — which is to attempt a helpful response using general knowledge. This creates unpredictable policy exposure. Explicit fallback instructions make the no-match behavior deterministic and policy-compliant. The tradeoff is marginal authoring cost against significant risk reduction.

---

## Anti-Patterns

1. **Single-Layer Guardrail Configuration** — Relying solely on topic Scope fields to enforce all behavioral boundaries. Scope is a post-classification control. Pre-classification threats (adversarial inputs, off-topic requests that partially match a topic's Classification Description) bypass Scope. Defense requires at least restricted topics (pre-classification) and a fallback system instruction (no-match handling).

2. **Imperative Instruction Stacking** — Writing system instructions or Scope fields as lists of "must not" and "never" commands copied from compliance policy documents. This pattern causes LLM reasoning loop instability, is harder to maintain as policy changes, and produces lower Instruction Adherence scores. Declarative boundary language ("This agent addresses X only. Other requests receive: [canned response].") is more stable and achieves equivalent policy enforcement.

3. **Unverified Escalation Topic Deployment** — Configuring the Escalation topic in Setup and treating it as done without an end-to-end handoff test. The Escalation topic requires Omni-Channel infrastructure that is frequently incomplete at time of agent launch. Silent escalation failures damage user trust and create support blind spots.

---

## Official Sources Used

- Agentforce Guardrails (Help) — https://help.salesforce.com/s/articleView?id=sf.copilot_guardrails.htm
- Agentforce Developer Guide (Get Started) — https://developer.salesforce.com/docs/einstein/genai/guide/agent-get-started.html
- Agentforce Developer Guide (Overview) — https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html
- Einstein Platform Services Overview — https://developer.salesforce.com/docs/einstein/genai/guide/overview.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Agentic Patterns (Salesforce Architects) — https://architect.salesforce.com/decision-guides/agentic-patterns
