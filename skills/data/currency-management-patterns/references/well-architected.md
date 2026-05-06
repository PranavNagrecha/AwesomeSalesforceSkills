# Well-Architected Notes — Currency Management Patterns

## Relevant Pillars

- **Reliability** — Reports, dashboards, formula fields, and roll-up
  summaries can disagree on the same record's value because they
  consult different rate tables. Documented rate-source-per-surface
  is what makes financial reporting trustworthy.
- **Operational Excellence** — Exchange-rate maintenance is an
  ongoing operational task. Without an automated rate-update
  process, rates drift and finance teams paste-load corrections.
- **Security / Compliance** — Audit trails must show which rate
  applied to which record on which date. ACM provides this
  implicitly via `DatedConversionRate`; basic multi-currency does
  not.

## Architectural Tradeoffs

- **Single-currency vs multi-currency org.** Single-currency is
  vastly simpler. Multi-currency is irreversible and adds
  complexity to every report, formula, and integration. Enable only
  when the business genuinely transacts in multiple currencies.
- **Basic multi-currency vs ACM.** ACM is required for any
  financial-reporting use case where historical rates matter. Basic
  multi-currency is acceptable for display-only contexts.
- **Constrain children to parent currency vs allow mixed.** Mixed
  currencies on related records produce surprising roll-ups and
  formulas. For most CRM use cases, constraining children to share
  the parent's currency simplifies downstream reporting at the cost
  of forcing data-entry decisions earlier.
- **Roll-up summary vs Apex calculation.** Roll-up summary is fast
  and declarative but uses static rates. Apex with explicit dated-
  rate lookup is more work but is the only way to get exactness for
  financial-period reporting in mixed-currency rollups.

## Anti-Patterns

1. **Treating `convertCurrency()` as ACM-aware.** It uses static
   rates only.
2. **Inserting `DatedConversionRate` with `NextStartDate`.** Field
   is platform-computed.
3. **Filtering on a currency-field threshold without naming the
   currency.** Filter operates on the native value.
4. **Formula arithmetic across different `CurrencyIsoCode` values.**
   Auto-conversion does not happen in formulas.
5. **Disable-multi-currency expectation.** Not supported.

## Official Sources Used

- Multiple Currencies Overview — https://help.salesforce.com/s/articleView?id=sf.admin_about_enabling_multicurrency.htm&type=5
- Advanced Currency Management — https://help.salesforce.com/s/articleView?id=sf.admin_currency.htm&type=5
- DatedConversionRate Object — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_datedconversionrate.htm
- CurrencyType Object — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_currencytype.htm
- SOQL `convertCurrency()` — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_select_convertcurrency.htm
- Salesforce Well-Architected Trustworthy — https://architect.salesforce.com/well-architected/trusted/secure
