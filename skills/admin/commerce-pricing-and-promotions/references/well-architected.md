# Well-Architected Notes — Commerce Pricing and Promotions

## Relevant Pillars

- **Reliability** — Silent limit violations (rank-26+ pricebook exclusion, rank-51+ promotion exclusion, tier gaps) cause incorrect pricing or missing discounts with no error surfaced to buyers or admins. Reliable pricing architecture requires proactive limit audits and explicit monitoring, not reactive debugging.
- **Performance** — The price resolution engine evaluates pricebooks and promotions on every cart interaction. Accumulating orphaned pricebook assignments or retired-but-active promotions increases evaluation overhead unnecessarily. Keeping active records lean improves checkout latency.
- **Scalability** — The `BuyerGroupPricebook` model scales to 50 pricebooks per BuyerGroup and 100 BuyerGroups per pricebook, supporting complex multi-tier pricing without custom code. The `WebStorePricebook` slot limit (5 per store) forces deliberate architectural choices about what needs store-wide vs. segment-specific visibility.
- **Operational Excellence** — Pricing and promotion hygiene (retiring expired promotions, removing development pricebook assignments) is an ongoing operational requirement, not a one-time setup task. Orgs that treat these as set-and-forget configurations eventually hit silent exclusion limits.

## Architectural Tradeoffs

### WebStorePricebook vs. BuyerGroupPricebook for Differentiated Pricing

`WebStorePricebook` is appropriate for pricebooks that should be visible to all buyers in the store (including guest buyers in D2C). Its hard limit of 5 per store makes it unsuitable as the primary mechanism for buyer-tier differentiation at scale.

`BuyerGroupPricebook` is the correct vehicle for segment-specific pricing. It supports up to 50 pricebooks per BuyerGroup and allows the resolution engine to select the right price based on the buyer's group membership. The tradeoff is complexity: the `Priority` field on the junction record must be carefully managed across all BuyerGroup assignments to ensure the intended pricebook wins when a buyer belongs to multiple groups.

### Automatic vs. Coupon-Gated Promotions

Automatic promotions fire for all eligible buyers without input. They are simpler to configure but harder to control — a misconfigured scope or missing `PromotionSegmentBuyerGroup` can inadvertently discount orders for unintended segments. Coupon-gated promotions require buyers to take explicit action, which provides a natural control gate but adds UX friction and requires code distribution outside the platform.

For high-value, targeted promotions, prefer coupon-gated. For broad, time-limited store events (flash sales, site-wide discounts), prefer automatic with explicit `PromotionSegmentSalesStore` scoping.

### Tiered Pricing vs. Promotion-Based Volume Discounts

`PriceAdjustmentSchedule` / `PriceAdjustmentTier` is the preferred mechanism for standing volume discount programs. It runs at price resolution (not checkout) and does not consume promotion evaluation slots.

Promotions can also implement quantity-based discounts through promotion conditions, but they consume one of the 50 available automatic promotion slots at checkout. Use promotions for time-limited or segment-gated volume events; use `PriceAdjustmentSchedule` for permanent product-level tier structures.

## Anti-Patterns

1. **Relying on `Account.Pricebook2Id` for Commerce pricing** — The Commerce engine ignores this Sales Cloud field. All pricebook assignment for Commerce must go through `WebStorePricebook` and `BuyerGroupPricebook`. Using the Account field gives a false sense of configuration completeness with no actual effect on buyer-visible prices.

2. **Activating promotions without verifying the checkout flow** — The `PromotionsCartCalculator` subflow is a non-optional runtime dependency for all promotions. Skipping flow verification is the most common cause of "promotion not working" incidents and the first thing to check before any other debugging.

3. **Accumulating active promotions and pricebook assignments without a retirement process** — Silent exclusion limits (25 pricebooks per resolution call, 50 promotions per evaluate call) are hit gradually and without error signals. Orgs that treat the data model as append-only will eventually see unexpected pricing behavior with no obvious cause. Build a quarterly audit into the operational calendar.

## Official Sources Used

- B2B Commerce Developer Guide — Pricing and Promotions APIs: https://developer.salesforce.com/docs/atlas.en-us.b2b_b2c_comm_dev.meta/b2b_b2c_comm_dev/b2c_comm_dev_pricing.htm
- Promotions Data Model — B2B and D2C Commerce Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.b2b_b2c_comm_dev.meta/b2b_b2c_comm_dev/b2c_comm_dev_promotions_data_model.htm
- Promotions Data Limits: https://developer.salesforce.com/docs/atlas.en-us.b2b_b2c_comm_dev.meta/b2b_b2c_comm_dev/b2c_comm_dev_promotions_limits.htm
- Price Book Data Limits: https://developer.salesforce.com/docs/atlas.en-us.b2b_b2c_comm_dev.meta/b2b_b2c_comm_dev/b2c_comm_dev_pricebook_limits.htm
- Salesforce Help — Set Up a Pricing Strategy in a B2B Store: https://help.salesforce.com/s/articleView?id=sf.comm_b2b_pricing_strategy.htm
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
