# Well-Architected Notes: Multi Currency And Advanced Currency Management

## Relevant Pillars

- **Reliability**: finance and sales users need currency behavior that stays explainable. Amounts travel with their ISO code, aggregates are labeled as corporate currency, and rate loads are an owned job.
- **Scalability**: currency context must hold across reports, integrations, packages, and Apex. Code guarded with `UserInfo.isMultiCurrencyOrganization()` runs in any org.

## Architectural Tradeoffs

- **Stored currency vs converted currency:** preserve transaction truth versus present the viewer's currency.
- **Multi-currency alone vs ACM:** simpler static rates versus dated rates that apply only to opportunity, line item, and opportunity history amounts.
- **Bare amount fields vs amount plus ISO code:** convenience versus correctness.
- **Setup-maintained rates vs API job:** fewer moving parts versus rates that stay current without a person remembering.

## Anti-Patterns

1. **Hardcoded single-currency assumptions**: they leak into every downstream consumer.
2. **Converted values without a named context**: users do not know which currency they are seeing.
3. **Enabling ACM without scoping it**: users expect every currency field to become historical.

## Official Sources Used

- Metadata API Developer Guide, Summer '26 (262), "CurrencySettings" (`enableMultiCurrency` one-way, `enableCurrencyEffectiveDates`, `isParenCurrencyConvDisabled`, package.xml form). https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Object Reference for the Salesforce Platform, Summer '26 (262), "CurrencyType" and "DatedConversionRate" (supported calls, fields, the `IsActive` default warning) and the `CurrencyIsoCode` field description. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- SOQL and SOSL Reference, Summer '26 (262), "convertCurrency()" and its Considerations and Workarounds. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_soql_sosl.pdf
- Apex Developer Guide, Summer '26 (262), "sObjects That Don't Support DML Operations." https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- Apex Reference Guide, Summer '26 (262), `UserInfo.getDefaultCurrency()`, `UserInfo.isMultiCurrencyOrganization()`, `Database.queryWithBinds()`. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_reference_guide.pdf

### Earlier references kept from version 1.0.0 (checked 2026-10-03: atlas pages return a script shell, help.salesforce.com returns an app shell, and Well-Architected guide pages redirect to the home page, so no claim in this skill rests on these links)

- Salesforce Help, Multi-Currency: https://help.salesforce.com/s/articleView?id=sf.admin_currency.htm&type=5 (help.salesforce.com does not return article text to a fetch)
- Salesforce Help, Advanced Currency Management: https://help.salesforce.com/s/articleView?id=sf.admin_currency_dated_exchange.htm&type=5 (same limitation)
- Currency in Queries (atlas page; the 262 SOQL PDF above was read instead): https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_currency.htm (returned 404 on 2026-10-03)
