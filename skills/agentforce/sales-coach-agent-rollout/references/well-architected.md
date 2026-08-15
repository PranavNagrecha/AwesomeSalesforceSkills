# Well-Architected Notes — Sales Coach Agent Rollout

## Relevant Pillars

- **Reliability** — Sales Coach effectiveness depends on the agent's consistency across hundreds of role-play sessions, against a non-deterministic LLM. The reliability discipline here is *grounded* — every methodology claim, objection handling, and value prop comes from a versioned Knowledge article tagged for retrieval. Without grounding, the same rep asking the same question on different days gets contradictory advice. With grounding, the LLM is constrained by your source-of-truth content. Rollout reliability also depends on Opportunity stage hygiene (renamed stages break shipped triggers) and Trust Layer retention configuration (so audit-traceability is consistent).
- **Operational Excellence** — A Sales Coach rollout that ships without a measurement plan is theater. Operational excellence here means defining leading indicators (engagement frequency, session-length distribution) and lagging indicators (win-rate delta within segment, ramp-time delta) before publishing, instrumenting them, and running a structured pilot → measure → iterate cycle on 4-week cadence. The bundled checker, knowledge-grounding tags, and stage-mapping audit are all in service of an operational discipline rather than a one-time configuration push.

## Architectural Tradeoffs

| Tradeoff | Why it matters |
|---|---|
| Use shipped Sales Coach template vs build a bespoke agent | Shipped template covers 80% of opportunity-stage role-play with low maintenance burden — Salesforce updates the underlying behavior on platform releases. Building bespoke buys total control but loses the upstream improvements and adds long-tail maintenance. Default: ship the template, customize via grounded data and subagent-instruction tweaks (subagents were called topics before April 2026); only bespoke if the methodology is so non-standard that retrofitting it onto the template is impossible. |
| Console utility item vs Opportunity record-page component vs separate portal | Utility item: lowest friction, picks up Opportunity context, doesn't compete for record-page real estate. Record component: most context-aware, but burns valuable space on the Opportunity layout. Separate portal: cleanest privacy boundary, highest friction. Default: utility item for the pilot; revisit only if pilot engagement signals demand a different surface. |
| Auto-launch vs opt-in | Auto-launch maximizes top-of-funnel exposure but reads as surveillance to reps and erodes trust. Opt-in slows initial adoption but builds the trust required for honest practice (which is when the coach actually delivers value). Default: opt-in. |
| Methodology in agent instructions vs in grounded Knowledge | Instructions are easy to edit but invisible to admins outside Agent Builder, version poorly, and bleed prompt-token budget. Grounded knowledge is centrally maintained, versioned, accessible to Reports, and updated without re-publishing the agent. Default: instructions describe behavior; grounded knowledge describes the world. |
| Manager visibility into transcripts vs rep privacy | Transcript visibility for managers enables coaching-the-coaching and skill-gap identification but converts a practice tool into a surveillance tool — destroying psychological safety and adoption. Default: manager visibility off; if there's a clear coaching-development use case, opt rep cohorts in explicitly with informed consent. |

## Anti-Patterns

1. **Publishing the shipped template without customization** — Reps experience a generic B-school case study that doesn't match their deals, their methodology, or their objections. Engagement craters by week 3. Always ground methodology and inject ICP seeds before publishing to a real cohort.
2. **Pasting battle cards into agent instructions** — Battle cards belong in Knowledge articles tagged for grounding, not in subagent instructions. Pasting them inflates prompt tokens, makes updates require re-publishing the agent, and prevents Reports from reading the same content. Worse: the battle card content goes stale and contradicts the live Knowledge base.
3. **Comparing coached-opp win rate to global win rate** — Reps who use a coaching tool self-select for engagement and effort, biasing upward. The "coached opps win 18% more" headline is almost always selection effect, not coaching effect. Always compare *within* a segment, ideally with randomized opt-in cohorts.
4. **Hard-coding a methodology in subagent instructions** — Embedding "always evaluate against MEDDIC" in instructions makes the methodology a tribal-knowledge artifact buried in Agent Builder. If the org switches methodologies (or runs more than one), the agent has to be re-edited per subagent. Reference grounded knowledge instead so methodology changes propagate centrally.
5. **Auto-launching the utility item** — Reads as surveillance, kills adoption. Always opt-in.
6. **Skipping the privacy memo** — Conversations contain rep practice content (sometimes including disparaging colleagues, sensitive deal context, etc.). Without a documented data-flow diagram, retention setting, and opt-out path reviewed by legal, the rollout is exposed when the first compliance audit hits.

## Official Sources Used

- Agentforce Sales Coach overview — https://help.salesforce.com/s/articleView?id=sf.agentforce_sales_coach.htm
- Agent Builder overview — https://help.salesforce.com/s/articleView?id=sf.agent_builder_overview.htm
- Einstein Generative AI / Agentforce developer guide — https://developer.salesforce.com/docs/einstein/genai
- Salesforce Help — Set Up Agentforce — https://help.salesforce.com/s/articleView?id=sf.agentforce_setup.htm
- Salesforce Well-Architected — Reliability — https://architect.salesforce.com/docs/architect/well-architected/guide/reliability.html
- Salesforce Well-Architected — Operational Excellence — https://architect.salesforce.com/docs/architect/well-architected/guide/operational-excellence.html
