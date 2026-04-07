# Well-Architected Notes — CPQ Apex Plugins

## Relevant Pillars

- **Performance** — CPQ plugins execute synchronously inside the managed package's calculation engine. Every SOQL query, heap allocation, and CPU cycle consumed by the plugin competes directly with CPQ's own substantial resource usage. A plugin that adds 2 seconds of CPU time to a 50-line quote will cause governor limit errors at 100 lines. Plugin logic must be minimal: batch any SOQL queries before iterating lines, avoid nested loops over quote lines, and prefer pre-computed lookup maps.

- **Reliability** — Because only one plugin of each type can be registered at a time, a bug in a plugin disables the entire extension point for all users. Plugins must have unit tests covering edge cases (empty line lists, null field values, unexpected product families) and should use try-catch with explicit error logging so a plugin failure produces a visible, actionable error rather than a silent save hang or data corruption.

- **Operational Excellence** — Plugin registration lives in org data, not metadata. Release pipelines must explicitly include post-deployment steps to update `SBQQ__CustomActionSettings__c`. Teams that skip this step discover missing plugins in production only after users report incorrect pricing. Runbooks must document every plugin type registered in each environment.

- **Security** — Apex plugins declared `global` with `with sharing` enforce FLS and record-level sharing on any SOQL they run. Plugins that need to read restricted pricing fields should be declared `without sharing` only if there is an explicit documented business justification, because CPQ's calculation context already runs in a system-mode context within the managed package. Avoid storing sensitive pricing logic inside `SBQQ__CustomScript__c` records without restricting access to the object via profiles and permission sets, as the JS code is stored as plain text in a queryable field.

- **Scalability** — The CPQ calculation engine is invoked on every quote line mutation and on save. A plugin that queries the database per line (rather than in a single pre-loop bulk query) will hit SOQL limits at quote sizes that are common in enterprise deals (50–200 lines). Always bulk-collect the IDs or key values from `quoteLineModels` first, execute a single SOQL query, build a map, then iterate.

## Architectural Tradeoffs

**JS QCP vs. Apex QuoteCalculatorPlugin:** JS QCP is more maintainable for front-end developers and does not require Apex compilation or deployment, but it runs in the browser's JavaScript context and cannot perform server-side DML or callouts directly. The Apex plugin runs server-side and supports callouts via `SBQQ.CalculateCallback`, but requires Apex expertise and is the legacy approach. For new development, JS QCP is preferred unless async server-side logic is strictly required.

**Plugin vs. Price Rule:** Declarative price rules are processed before plugins and require no code. A complex price rule that reads a custom field is always preferable to a plugin that replicates the same logic in code. Plugins should be the last resort after confirming the requirement cannot be expressed declaratively.

**Single Plugin Registration vs. Dispatcher Pattern:** The single-slot registration model forces all logic for a given plugin type into one class. Teams must decide up front whether to use a dispatcher class that delegates to sub-handlers, or to keep a single-purpose plugin. The dispatcher pattern is more maintainable for orgs with multiple business units contributing to a single plugin type, but it increases the cognitive complexity of any individual change.

## Anti-Patterns

1. **Trigger-based calculation overrides** — Using Apex triggers on `SBQQ__Quote__c` or `SBQQ__QuoteLine__c` to modify fields that CPQ's calculation engine owns. CPQ recalculates on save and overwrites trigger-set values. The correct approach is to use the appropriate plugin hook (JS QCP `onAfterCalculate` or Apex `QuoteCalculatorPlugin`) so the mutation happens inside the calculation engine's transaction and is not overwritten.

2. **Per-line SOQL inside plugin loops** — Querying the database inside a `forEach` over `quoteLineModels` or inside a `for` loop over `quoteLines`. This causes N+1 SOQL patterns and hits the 100-SOQL governor limit on medium-sized quotes. The correct approach is to collect all relevant IDs before the loop, execute one query, and use a `Map` for O(1) lookups inside the loop.

3. **Missing Promise return in JS QCP hooks** — Exporting hook functions that do not return a `Promise` in every code path. CPQ awaits the hook's return value; `undefined` causes the calculation engine to hang and the quote save UI to freeze indefinitely without an error message. Every hook must end with `return Promise.resolve()` or equivalent.

4. **Replacing an existing plugin without merging logic** — Overwriting the CPQ Settings registration field with a new class name without reviewing the previously registered plugin. This silently abandons any customizations in the old class. The correct approach is to read the existing registration, incorporate its logic into the new class (or extend the old class), and only then update the Settings field.

## Official Sources Used

- Salesforce CPQ Plugins Developer Guide (Spring '26 v66.0) — https://developer.salesforce.com/docs/atlas.en-us.cpq_dev_plugins.meta/cpq_dev_plugins/cpq_plugins_parent.htm
- CPQ Developer Guide — Quote Calculator Plugin Methods — https://developer.salesforce.com/docs/atlas.en-us.cpq_dev_plugins.meta/cpq_dev_plugins/cpq_plugins_quote_calc.htm
- CPQ Developer Guide — Order Plugin — https://developer.salesforce.com/docs/atlas.en-us.cpq_dev_plugins.meta/cpq_dev_plugins/cpq_plugins_order.htm
- CPQ Developer Guide — Contracting Plugin — https://developer.salesforce.com/docs/atlas.en-us.cpq_dev_plugins.meta/cpq_dev_plugins/cpq_plugins_contracting.htm
- CPQ Developer Guide — Product Search Plugin — https://developer.salesforce.com/docs/atlas.en-us.cpq_dev_plugins.meta/cpq_dev_plugins/cpq_plugins_product_search.htm
- CPQ Developer Guide — Configuration Initializer Plugin — https://developer.salesforce.com/docs/atlas.en-us.cpq_dev_plugins.meta/cpq_dev_plugins/cpq_plugins_config_initializer.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Apex Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm
