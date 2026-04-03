# Currency Design Worksheet

## Org Context

| Question | Answer |
|---|---|
| Multi-currency enabled? | Yes / No |
| ACM enabled? | Yes / No |
| Historical reporting needed? | Yes / No |
| External consumers involved? | Yes / No |

## Currency Handling

- Stored amount fields:
- ISO code propagation:
- Converted value use case:
- Reporting dependencies:

## Guardrails

- [ ] Irreversible activation was acknowledged
- [ ] Amounts are not separated from currency context
- [ ] `convertCurrency()` use is intentional
- [ ] Historical dated-rate behavior is understood
