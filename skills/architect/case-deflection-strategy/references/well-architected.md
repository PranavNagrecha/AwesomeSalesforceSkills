# Well-Architected Notes — Case Deflection Strategy

## Relevant Pillars

- **Adaptable** — A well-designed deflection program is built to evolve. Topic lists change as product features and customer behavior shift. The architectural pattern must include a regular cadence (60-day ECM refresh, quarterly knowledge audit) that allows the deflection coverage to adapt without a full rebuild. Bots built as rigid menu trees without NLU are difficult to extend; NLU-driven bots trained on ECM clusters are more adaptable as new topics emerge.

- **Easy** — Deflection directly serves the "Easy" pillar: customers resolve their issues without agent involvement, reducing friction and time-to-resolution. However, a deflection program that forces customers through a bot before they can reach an agent, without actually resolving their issue, violates the Easy pillar by adding steps to the customer journey. The architecture must balance containment goals with genuine resolution quality.

- **Trusted** — Knowledge articles surfaced in deflection channels must be accurate, current, and attributable. An article with incorrect information that causes a customer to take the wrong action is a trust failure. Knowledge governance — review cycles, version control, article ownership — is a Trusted-pillar architectural requirement for any knowledge-led deflection program. Data category hygiene also falls here: customers must trust that search results are relevant to their context.

## Architectural Tradeoffs

**Deflection coverage vs. resolution quality.** Maximizing deflection rate by catching more contacts in self-service is straightforward; maintaining a high goal completion rate as more topics are added is harder. Topics at the edge of bot capability (moderately complex, requires account context) are tempting to include in wave 2 but produce abandoned sessions if the bot cannot actually resolve them. The tradeoff: expand coverage incrementally, validating GCR for each new topic before adding the next.

**Front-door bot vs. opt-in self-service.** Requiring all customers to go through a bot before reaching an agent maximizes deflection opportunity but increases friction for customers with complex issues who already know they need a human. An opt-in self-service model (bot is available but agent chat is also directly accessible) improves CSAT for complex-issue customers but reduces deflection rate for contacts that could have been self-served. High-CSAT service orgs often use a hybrid: bot as default entry point with a visible "talk to a person" escape hatch available after the first bot interaction.

**Knowledge investment timeline.** Building deflection channels before knowledge is ready (to show quick delivery) consistently produces poor deflection rates and damages stakeholder confidence in the program. The architectural recommendation is to treat knowledge readiness as a prerequisite gate, not a parallel workstream. This delays initial launch but produces a defensible deflection rate from day one.

## Anti-Patterns

1. **Deflection without topic analysis** — Launching a bot or self-service channel and targeting generic "common issues" without ECM or case volume data produces low deflection rates. The top 5 contact reasons by volume in a specific org are rarely what practitioners guess them to be. ECM-driven topic selection is not optional; it is the foundational step that determines whether the program has any chance of reaching industry benchmark deflection rates.

2. **Treating containment rate as a success metric** — Reporting containment rate (no agent transfer) as the primary deflection KPI obscures whether customers are actually getting their issues resolved. A bot that ends 80% of sessions without agent transfer, but where 60% of those sessions are timeouts (customer abandoned), is not a successful deflection program. Always pair containment rate with goal completion rate and post-deflection case creation rate (customers who used self-service and then submitted a case anyway).

3. **Static deflection topic list** — Building wave 1 bot topics and never revisiting the topic list is the most common cause of deflection program stagnation. Customer contact reasons evolve with product changes, seasonal patterns, and new issue types. A program that reached 25% deflection in its first year and is still at 25% three years later has a static topic list problem. The architecture must include a governance process for topic refresh.

## Official Sources Used

- Deflect Cases with Self-Service — https://help.salesforce.com/s/articleView?id=sf.cases_deflect.htm&type=5
- Einstein Conversation Mining for Case Deflection — https://help.salesforce.com/s/articleView?id=sf.einstein_conversation_mining.htm&type=5
- AI for Admins: Einstein Bots Success — https://help.salesforce.com/s/articleView?id=sf.bots_service_admin.htm&type=5
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Well-Architected: Easy — https://architect.salesforce.com/docs/architect/well-architected/easy/
- Salesforce Well-Architected: Adaptable — https://architect.salesforce.com/docs/architect/well-architected/adaptable/
- Salesforce Well-Architected: Trusted — https://architect.salesforce.com/docs/architect/well-architected/trusted/
