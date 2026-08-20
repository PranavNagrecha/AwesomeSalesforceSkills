# SFAEF-070 — Agent taxonomy, delegation, and handoffs

## Taxonomy

1. **Core execution agents** — context, project, org, evidence, policy, and resumption roles reused by products.
2. **Product agents** — own one user job and final domain synthesis.
3. **Catalog specialists** — existing Salesforce domain agents invoked deliberately; not automatically exposed as host subagents.
4. **Maintainer agents** — build, validate, refresh, or package the corpus; never auto-routed for end-user jobs.
5. **QA agents** — evaluate outputs under a controlled rubric; cannot alter labels or pass criteria.

## When an agent earns isolation

SFAEF-070-001. A host-native subagent MUST have a clear isolated-context benefit: noisy exploration, tool-specific evidence gathering, independent review, or specialized synthesis.

SFAEF-070-002. A one-step formatting or deterministic task SHOULD remain code, a skill, or a command rather than a subagent.

SFAEF-070-003. Default host packages MUST expose a small curated set of proven subagents, not the full catalog.

## Agent contract

Each agent MUST declare:

- purpose and non-goals;
- typed input and output;
- permitted modes and tools;
- required/prohibited evidence;
- context budget;
- failure/refusal behavior;
- collaborators and handoff shape;
- success criteria;
- deterministic and behavioral tests;
- host limitations.

SFAEF-070-010. Agents MUST NOT acquire tools outside the active run plan.

SFAEF-070-011. Agents MUST NOT infer permission from a natural-language prompt.

SFAEF-070-012. Product agents MUST distinguish observations, inferences, recommendations, and unknowns.

## Structured handoff

SFAEF-070-020. Every cross-agent handoff MUST validate against `handoff.schema.json`.

SFAEF-070-021. A handoff MUST contain only task, facts, evidence references, hypotheses, unknowns, requested next action, and context metrics.

SFAEF-070-022. Full transcripts, hidden reasoning, credentials, and unbounded raw tool output MUST NOT be transferred.

SFAEF-070-023. Receiving agents MUST validate referenced evidence and MUST not trust a sending agent's confidence without support.

## Independent review

SFAEF-070-030. The evidence reviewer MUST receive the draft claims, evidence index, product policy, and output schema—but not the drafting agent's hidden transcript.

SFAEF-070-031. The reviewer MUST be able to block completion, downgrade claims, require unknowns, and flag unsafe recommendations.

SFAEF-070-032. Reviewer agreement alone is not proof; deterministic evidence lint remains mandatory.
