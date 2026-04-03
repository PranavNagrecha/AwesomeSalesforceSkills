# Well-Architected Notes - Multi Currency And Advanced Currency Management

## Relevant Pillars

- **Reliability** - finance and sales users need currency behavior that remains explainable and historically correct.
- **Scalability** - currency context must scale across reports, integrations, and Apex, not just one screen.

## Architectural Tradeoffs

- **Stored currency vs converted currency:** preserve transaction truth versus present user-friendly projections.
- **Multi-currency alone vs ACM:** simpler model versus historically correct dated-rate behavior.
- **Bare amount fields vs amount plus ISO code:** convenience versus correctness.

## Anti-Patterns

1. **Hardcoded single-currency assumptions** - they leak into every downstream consumer.
2. **Using converted values without naming the context** - users do not know what number they are seeing.
3. **Enabling ACM without business education** - historical discrepancies become support incidents.

## Official Sources Used

- Multi-Currency - https://help.salesforce.com/s/articleView?id=sf.admin_currency.htm&type=5
- Advanced Currency Management - https://help.salesforce.com/s/articleView?id=sf.admin_currency_dated_exchange.htm&type=5
- Currency In Queries - https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_currency.htm
