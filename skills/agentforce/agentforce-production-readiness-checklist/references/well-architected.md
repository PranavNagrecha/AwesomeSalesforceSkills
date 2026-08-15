# Well-Architected Notes — Agentforce Production Readiness Checklist

## Relevant Pillars

- **Reliability** — A production-readiness gate exists because reliability is earned at the moment of rollout, not declared at the moment of build-complete. The four-layer model (behavior, trust, operability, rollout) maps directly to the failure modes that compromise reliability: unverified behavior produces silent quality regressions, missing observability hides them, and missing rollback turns a regression into a sustained incident.
- **Security** — Customer-facing agents in particular are an unauthenticated input surface for prompt injection, jailbreak attempts, and tool-misuse exploits. The Trust Layer + adversarial test pass + named-credential scoping combination is what separates "an agent we built" from "an agent we're willing to expose to the public." Security review is a distinct sign-off, not a row inside the builder's checklist.
- **Operational Excellence** — A readiness gate is a feedback loop. The same dashboards and alert thresholds that gate the rollout are the dashboards and alert thresholds that run the agent in production. The readiness investment compounds — every panel built before launch becomes part of ongoing operations. Conversely, every panel skipped before launch tends to stay skipped.

## Architectural Tradeoffs

| Tradeoff | Why it matters |
|---|---|
| Broad rollout vs canary | Broad rollout exposes more users to first-day incidents but generates faster signal; canary contains incidents but slows learning. Canary is correct for net-new agents and material config changes. Broad is acceptable for hot-fixes that have been validated in canary already. The tradeoff is wrong only when the team uses broad rollout because they didn't plan a canary, not because they decided one wasn't needed. |
| Apex action vs Flow action | Apex actions give precise transactional control, explicit error paths, and per-call instrumentation hooks but require dev cycle and permission-set discipline. Flow actions are faster to build and admin-friendly but harder to instrument, harder to enforce least-privilege at the action layer, and easier to ship without the same readiness rigor. Mutating actions tend to belong in Apex; read-only data lookups can be Flow. |
| Prompt template vs custom action | A prompt template is the right answer when the LLM can do the work given enriched context (summarization, classification, drafting). A custom action is the right answer when the answer requires deterministic data, a side-effect, or an external system call. Teams over-rotate to prompt templates because they're faster to ship; they then ship behavior the LLM has to imagine instead of fetch. The readiness gate exists in part to surface "this should be an action, not a template" cases. |
| Real-time alerts vs daily review | Real-time alerts catch acute incidents but produce noise; daily review catches drift but misses fast-moving regressions. The right answer is both, with sharply different thresholds — alerts on hard thresholds (error rate >10%, p95 latency >3s, content-moderation block rate >5%), daily review on trend (slow drift in escalation rate, gradual token-spend creep). |
| Kill-switch granularity (full agent vs single subagent vs single action) | A full-agent kill is broad and clean but disrupts every user. A subagent kill (subagents were called topics before April 2026) is finer but leaves other subagents live. An action kill is finest but requires the action to honor a flag at entry. The right design is to support all three so on-call has the right-sized response per incident type. The readiness gate fails the rollout if only one is implemented. |

## Anti-Patterns

1. **"It worked in build, ship it"** — Build-time tests under a single user are not production validation. The gap is realistic concurrency, realistic prompt diversity, realistic permissions, and realistic data classes. Skipping the gap is the most common cause of week-one incidents.
2. **Treating the readiness checklist as a sign-off ritual** — A checklist with ticks but no evidence is theater. Every row needs an artifact (test ID, query result, screenshot, dashboard link). If the row cannot produce evidence, it cannot be marked PASS.
3. **Building dashboards after launch** — The first incident must not be the user. Dashboards and alerts in place *before* traffic is the difference between "we knew within minutes" and "we found out from a P0."
4. **Skipping rollback rehearsal because the change is small** — Rehearsal is cheap; failed rollback under pressure is expensive. Rehearse for every material config change, not just net-new agents.
5. **Letting the builder run the adversarial test** — The builder has incentive to pass. Adversarial testing belongs to a security reviewer or an independent rotation, not the person who shipped the subagent.
6. **Treating Trust Layer as binary** — "Trust Layer is on" is not a config. Verify each masking category, audit log destination, retention horizon, and content moderation threshold individually.
7. **Using sandbox metadata as production proxy** — Sandbox is a different environment with different named credentials, different data, and possibly different feature licensing. Validate the production-target metadata package, not a stale sandbox copy.

## Official Sources Used

- Salesforce Help — Agentforce Overview — https://help.salesforce.com/s/articleView?id=sf.agent_builder_overview.htm
- Salesforce Help — Einstein Trust Layer — https://help.salesforce.com/s/articleView?id=sf.einstein_trust_layer_overview.htm
- Salesforce Developer — Generative AI / Einstein — https://developer.salesforce.com/docs/einstein/genai
- Salesforce Help — Event Monitoring — https://help.salesforce.com/s/articleView?id=sf.event_monitoring.htm
- Salesforce Architects — Well-Architected Reliability — https://architect.salesforce.com/docs/architect/well-architected/guide/trusted/reliable.html
- Salesforce Architects — Well-Architected Security — https://architect.salesforce.com/docs/architect/well-architected/guide/trusted/secure.html
- Salesforce Architects — Well-Architected Operational Excellence — https://architect.salesforce.com/docs/architect/well-architected/guide/operational-excellence.html
- Salesforce Architects — Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
