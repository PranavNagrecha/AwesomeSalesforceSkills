# Well-Architected Notes — Loyalty Management Setup

## Relevant Pillars

- **Reliability**: Cloned DPE definitions keep balances current, reset qualifying points, and expire points; they run only when a flow calls them. Tier changes come from the generated Change Tier process (real time or Batch Management). Monitor both: a stopped flow or batch job silently freezes balances or tiers. Each DPE run can be tracked in Monitor Workflow Services.
- **Scalability** — Large programs with high transaction volumes may approach Batch Management record limits. Review official limits documentation before go-live for high-volume programs. Partner loyalty DPE performance scales with number of partner transactions.
- **Operational Excellence** — Loyalty programs require ongoing DPE job management, promotion rule governance, and tier threshold tuning. Establish operational runbooks for DPE job failures, tier recalculation requests, and partner ledger corrections.

## Architectural Tradeoffs

**Single Currency vs. Two-Currency Architecture:** A single currency approach simplifies initial setup but creates irreversible limitations: you cannot reset tier progress without clearing redemption balances, and you cannot model different earning rates for status vs. reward points. Always use the two-currency architecture.

**Real-Time vs. Batch Tier Assessment:** The generated Change Tier process can run in real time as a child of a Transaction Journal process, or in batches through Batch Management with Select Members for Tier Assessment Automatically. Real time gives immediate upgrades at the cost of work per transaction; batch suits high volumes. An earlier version of these notes said real-time tier assessment needs custom code; the Loyalty guide documents the real-time child-process option.

**Multiple Experience Cloud Sites for Multiple Programs:** Each loyalty program requires its own Experience Cloud site. This adds infrastructure cost but ensures program independence. Evaluate whether a unified multi-program portal experience (requiring custom LWC development) is worth the development investment vs. separate sites.

## Anti-Patterns

1. **Single Currency for Both Tier and Redemption** — Irreversible design decision that prevents independent management of tier qualification and reward redemption. Always separate into qualifying and non-qualifying currencies.

2. **Forgetting to Clone, Activate, and Schedule DPE Templates**: Program goes live with templates that nothing calls, so balances, resets, and expirations never run.

3. **Partner Loyalty Without the Partner Ledger Definition**: The single Create Partner Ledgers and Update Partner Balances definition must be cloned, activated, and run, or partner ledgers and balances never update.

## Official Sources Used

Fetched and read on 2026-10-03 unless marked.

- Loyalty Management, Spring '26 (loyalty.pdf): Loyalty Program Currencies, Tier Assessment and Configure a Tier Assessment Process, Select Members for Tier Upgrade Automatically, Data Processing Engine Definitions (Point Balance Calculation, Reset Qualifying Points, Expire Fixed Non-Qualifying Points, Create Partner Ledgers and Update Partner Balances, Clone the Template Data Processing Engine Definitions), Loyalty Member Portal and Associate the Experience Cloud Site with a Loyalty Program. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/loyalty.pdf
- Loyalty Management Developer Guide object reference: LoyaltyMemberCurrency, LoyaltyProgramCurrency, LoyaltyTierGroup, LoyaltyProgramPartner, TransactionJournal. https://developer.salesforce.com/docs/atlas.en-us.loyalty.meta/loyalty/sforce_api_objects_loyaltymembercurrency.htm (read through the get_document_content endpoint, as were the sibling pages sforce_api_objects_loyaltyprogramcurrency.htm, sforce_api_objects_loyaltytiergroup.htm, sforce_api_objects_loyaltyprogrampartner.htm, sforce_api_objects_transactionjournal.htm)
- Loyalty Management Developer Guide resources: Transaction Journals Execution and Eligible Promotions List (POST). https://developer.salesforce.com/docs/atlas.en-us.loyalty.meta/loyalty/connect_resources_loyalty_program_realtime.htm and https://developer.salesforce.com/docs/atlas.en-us.loyalty.meta/loyalty/connect_resources_eligible_promotions.htm
- Loyalty Management Standard Invocable Actions. https://developer.salesforce.com/docs/atlas.en-us.loyalty.meta/loyalty/loyalty_mgt_actions_parent.htm
- Metadata API Developer Guide, Version 67.0: LoyaltyProgramSetup (fields, LoyaltyProgramProcess, action types, sample, package.xml note). https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Salesforce Well-Architected Overview, archived 2026-06-16. http://web.archive.org/web/20260616115029/https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Listed by an earlier version of this skill and not re-read (Trailhead units): Loyalty Management Basics, Set Up a Loyalty Program https://trailhead.salesforce.com/content/learn/modules/loyalty-management-basics/set-up-loyalty-program and Tier Processing and Points Expiration https://trailhead.salesforce.com/content/learn/modules/loyalty-rules-management-and-processing/review-the-tier-processing-and-points-expiration-processes
