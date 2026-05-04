# Well-Architected Notes — Loyalty Program Architecture

## Relevant Pillars

- **Reliability** — A loyalty program's reliability is measured in member trust. Members who watch their balance behave inconsistently (delayed posting, retroactive descalation, points missing after a refund) lose trust permanently. Architecture decisions — DPE schedule, tier-credit reversal pipeline, descalation grace period — directly determine the program's perceived reliability.
- **Scalability** — Lifetime ledgers, partner transactions, and multi-region federation each have data-volume implications that compound over years. The architecture must plan for the program's year-3 state, not the year-1 state. Lifetime status without a rolled-up summary, partner programs without per-partner rate limits, and multi-region without federation each become re-architects under load.
- **Security** — Loyalty programs are fraud targets. Accrual abuse, redemption pooling, tier-credit gaming all require pre-aggregation controls and anomaly thresholds in the architecture, not post-hoc detection scripts.

## Architectural Tradeoffs

- **Generous launch thresholds vs sustainable distribution.** Launching with low thresholds drives sign-ups but inflates tier populations within 24 months. The tradeoff is resolvable only by building the descalation policy into the architecture from Day 1; retrofitting descalation against legacy members is a brand crisis.
- **Currency-ratio asymmetry vs marketing simplicity.** A 1:1 qualifying-to-non-qualifying ratio is "simpler" for marketing to communicate but invites mental collapse and downstream redemption errors. A 1:10+ ratio adds explanation cost but enforces psychological separation between tier and redemption currencies.
- **Real-time tier vs DPE schedule.** True real-time tier upgrades require custom logic outside the supported DPE pipeline. The tradeoff is significant custom work + reconciliation complexity vs accepting a 24-hour SLA on tier promotions. Most programs take the SLA; high-end travel programs (where tier is part of the booking experience) sometimes take the custom path.
- **Hub-and-spoke vs peer-to-peer partner loyalty.** Hub-and-spoke is the supported pattern; peer-to-peer requires custom federation. Most ecosystems work fine in hub-and-spoke; peer-to-peer is justified only for true-equal partnerships (airline alliances).
- **Single program vs federated multi-region.** Single program is operationally simpler but constrained by GDPR data residency. Federation is architecturally heavier but compliance-safe. The decision is regulatory, not operational.
- **Lifetime status mechanics.** Earned-for-life status drives long-term loyalty but creates a forever-growing ledger. The tradeoff is resolved by maintaining a rolled-up summary on the member object rather than re-aggregating raw transactions for tier evaluation.

## Anti-Patterns

1. **Setting tier thresholds without distribution analysis.** Numbers based on competitor benchmarks or marketing intuition rather than the brand's actual customer behavior produce tier distributions that don't match the target.
2. **No descalation rule.** Tier inflation is the single most common program-failure mode. Architect descalation in v1.
3. **Same currency for tier and redemption (no two-currency split).** Conflicts with Loyalty Management's two-currency model and corrupts tier evaluation when redemption rules read the qualifying balance.
4. **Trying to use Marketing Cloud engagement programs as a loyalty engine.** Marketing Cloud is the engagement channel; Loyalty Management is the system of record for tier and points. Don't conflate them.
5. **Promising real-time tier upgrades without custom architecture.** The DPE schedule is the heartbeat; "instant tier" is custom work, not a config switch.

## Official Sources Used

- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html — used for the Reliability / Scalability / Security framing across the architectural tradeoffs
- Salesforce Loyalty Management Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.loyalty.meta/loyalty/loyalty_dev_guide.htm — used for the two-currency model, `LoyaltyProgram` / `LoyaltyProgramPartner` / `LoyaltyMemberCurrency` object semantics, and DPE job names
- Loyalty Management Implementation Guide (Help & Training) — https://help.salesforce.com/s/articleView?id=sf.loyalty_management.htm — used for the qualifying-vs-non-qualifying split, tier-group constraints, and Partner Loyalty configuration model
- Integration Patterns — https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html — used for the multi-region federation pattern (Platform Events as the cross-region earn channel)
- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm — used for object-level semantics referenced in the architecture (LoyaltyMemberCurrency, LoyaltyTier, LoyaltyTierGroup)
