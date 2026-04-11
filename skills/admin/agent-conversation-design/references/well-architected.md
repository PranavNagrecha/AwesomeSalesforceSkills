# Well-Architected Notes — Agent Conversation Design

## Relevant Pillars

- **User Experience** — Conversation design is the primary UX surface of a bot deployment. Poorly authored utterances, single-stage fallbacks, and internal-jargon escalation messages directly degrade the experience quality. Every output of this skill is an investment in measurable customer satisfaction (CSAT) and deflection rate. Well-Architected User Experience requires that self-service interactions be designed around the user's vocabulary and intent, not the system's internal structure.
- **Operational Excellence** — Utterance sets and fallback copy are operational assets that require maintenance. A conversation design that lacks a structured utterance expansion process becomes outdated as user language evolves. Operational Excellence principles require that the conversation corpus be treated as living documentation: versioned, reviewable, and updated on a defined cadence using conversation analytics data.
- **Reliability** — Fallback handling is the reliability story for conversational AI. A bot that has no progressive clarification pattern produces dead ends — interactions that fail to resolve and cannot self-recover. The three-stage fallback pattern described in this skill is the reliability mechanism that prevents total deflection loss when the NLU model misses.
- **Security** — Escalation criteria are a security boundary. Condition-based escalation rules (e.g., escalate if account is flagged for fraud review) must be defined and documented so that the platform configuration correctly implements them. Conversation design outputs that omit or vaguely state escalation criteria can cause sensitive cases to remain in bot self-service when they require human review.
- **Performance** — Response length and dialog depth directly affect perceived performance. A bot that generates long explanatory responses on every turn adds latency and increases the chance of rendering issues on low-bandwidth mobile channels. Well-Architected Performance requires that each dialog turn deliver value in the fewest characters appropriate for the channel.

## Architectural Tradeoffs

**Coverage depth vs. maintenance cost:** A larger utterance set produces better NLU accuracy but increases the maintenance burden when vocabulary evolves. The tradeoff is managed by prioritizing mining over manual authoring — case-mined utterances are more representative and require less ongoing manual curation than hand-written sets. Aim for a minimum viable set (20–50 utterances) at launch and plan a quarterly expansion review using conversation analytics data.

**Specificity vs. deflection rate:** Highly specific topic descriptions in Agentforce reduce routing errors but may also exclude edge cases the bot could handle, increasing escalation rate. Overly broad descriptions reduce escalations to the fallback but increase misroutes. The correct balance is to write specific descriptions with exclusion clauses for the cases that genuinely require human handling, and to leave genuinely borderline topics with catch-all safety nets that escalate rather than miscategorize.

**Persona consistency vs. channel adaptability:** A single voice that works across all channels requires either accepting register mismatches (formal web chat language on mobile) or investing in per-channel dialog variants. For deployments with two or more channels with meaningfully different audiences, per-channel variants are the correct investment. For single-channel deployments, a consistent single voice is the more maintainable choice.

## Anti-Patterns

1. **Writing escalation copy using internal queue labels** — Exposing Salesforce queue names (e.g., "Tier2_Billing_EN_US") in customer-visible transfer messages signals system internals to users, erodes trust, and becomes stale when queues are renamed. Always use functional, user-facing team names in escalation copy.
2. **Single-stage fallback with no clarification offer** — A fallback that only says "I didn't understand" with no guidance forces users to restart the conversation blindly. This is the most common cause of high fallback-to-escalation rate in Einstein Bot deployments. Replace with the progressive clarification pattern described in this skill.
3. **Using topic descriptions as a substitute for utterance investment in Einstein Bots** — Topic descriptions are a routing signal in Agentforce, not in Einstein Bots. In the dialog/intent model, the NLU model requires a training utterance set. Attempting to describe an intent in the description field instead of building utterances produces an intent that will never be selected with sufficient confidence.

## Official Sources Used

- Einstein Bots Overview — https://help.salesforce.com/s/articleView?id=sf.bots_service_intro.htm
- Agentforce Overview — https://help.salesforce.com/s/articleView?id=sf.agentforce_overview.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Help: Bot Dialog and Fallback Behavior — https://help.salesforce.com/s/articleView?id=sf.bots_service_dialog_overview.htm
- Salesforce Help: Create and Manage Topics for Agentforce — https://help.salesforce.com/s/articleView?id=sf.agentforce_topics.htm
