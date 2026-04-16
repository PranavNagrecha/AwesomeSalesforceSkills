# Well-Architected Notes — Loyalty Management Setup

## Relevant Pillars

- **Reliability** — DPE batch jobs are the backbone of tier processing. They must be activated, scheduled, and monitored. Failed DPE jobs stop tier advancement silently. Set up DPE job failure alerts and monitor execution history.
- **Scalability** — Large programs with high transaction volumes may approach Batch Management record limits. Review official limits documentation before go-live for high-volume programs. Partner loyalty DPE performance scales with number of partner transactions.
- **Operational Excellence** — Loyalty programs require ongoing DPE job management, promotion rule governance, and tier threshold tuning. Establish operational runbooks for DPE job failures, tier recalculation requests, and partner ledger corrections.

## Architectural Tradeoffs

**Single Currency vs. Two-Currency Architecture:** A single currency approach simplifies initial setup but creates irreversible limitations: you cannot reset tier progress without clearing redemption balances, and you cannot model different earning rates for status vs. reward points. Always use the two-currency architecture.

**Manual vs. DPE-Driven Tier Assessment:** DPE batch jobs drive tier recalculation on a schedule. Real-time tier assessment requires custom code (Apex or Flow triggered by transaction recording). For most programs, DPE batch is sufficient. High-frequency retail programs that need immediate tier upgrade upon reaching thresholds may require custom real-time tier calculation.

**Multiple Experience Cloud Sites for Multiple Programs:** Each loyalty program requires its own Experience Cloud site. This adds infrastructure cost but ensures program independence. Evaluate whether a unified multi-program portal experience (requiring custom LWC development) is worth the development investment vs. separate sites.

## Anti-Patterns

1. **Single Currency for Both Tier and Redemption** — Irreversible design decision that prevents independent management of tier qualification and reward redemption. Always separate into qualifying and non-qualifying currencies.

2. **Forgetting to Activate DPE Jobs** — Program goes live with no DPE job activation, tier processing never runs, members never advance. This is the most common post-go-live issue.

3. **Partner Loyalty with Partial DPE Activation** — Activating only one of the two required partner DPE definitions (Create Partner Ledgers or Update Partner Balance) leaves partner balance tracking non-functional.

## Official Sources Used

- Loyalty Management Basics: Set Up a Loyalty Program — https://trailhead.salesforce.com/content/learn/modules/loyalty-management-basics/set-up-loyalty-program
- Tier Processing and Points Expiration — https://trailhead.salesforce.com/content/learn/modules/loyalty-rules-management-and-processing/review-the-tier-processing-and-points-expiration-processes
- Loyalty Management Standard Invocable Actions — https://developer.salesforce.com/docs/atlas.en-us.loyalty.meta/loyalty/loyalty_mgt_actions_parent.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
