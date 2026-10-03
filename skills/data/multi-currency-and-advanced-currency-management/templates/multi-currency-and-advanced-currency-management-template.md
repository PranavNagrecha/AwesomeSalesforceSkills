# Currency Design Worksheet

## Org Context

| Question | Answer |
|---|---|
| Multi-currency enabled? (`enableMultiCurrency` cannot be turned off) | Yes / No |
| ACM enabled? (`enableCurrencyEffectiveDates`) | Yes / No |
| Corporate currency | |
| Historical reporting needed? On which objects? | |
| External consumers involved? | Yes / No |
| Code that must also run in single-currency orgs? | Yes / No |

## Currency Handling

- Stored amount fields:
- ISO code propagation (amount plus `CurrencyIsoCode` in every payload):
- Converted value use cases (`convertCurrency()` in SELECT only):
- Aggregates labeled as corporate currency:
- Amounts that get dated rates (opportunity, line item, opportunity history):
- Amounts that use static rates (everything else):
- Rate-load owner, schedule, and API job:

## Guardrails

- [ ] Sign-off on the permanent switch recorded after a sandbox rehearsal
- [ ] Amounts are not separated from currency context
- [ ] No `convertCurrency()` in WHERE or ORDER BY, and none around aggregates
- [ ] No Apex DML on `CurrencyType` or `DatedConversionRate`
- [ ] `CurrencyType` updates send every field, including `IsActive`
- [ ] `python3 scripts/check_multi_currency_and_advanced_currency_management.py --manifest-dir force-app` reviewed
