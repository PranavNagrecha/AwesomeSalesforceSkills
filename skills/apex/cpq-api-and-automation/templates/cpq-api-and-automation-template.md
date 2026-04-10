# CPQ API and Automation — Work Template

Use this template when working on tasks that require programmatic CPQ operations via SBQQ.ServiceRouter.

## Scope

**Skill:** `cpq-api-and-automation`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record answers to the Before Starting questions from SKILL.md here before writing code.

- **CPQ package installed / accessible:** Yes / No (check SBQQ namespace availability)
- **Operation type:** [ ] Quote creation [ ] Product addition [ ] Re-price [ ] Save [ ] Amendment [ ] Renewal
- **Input record IDs:** Quote ID: ___ / Contract ID: ___ / Product IDs: ___
- **Approximate line count:** ___ (determines sync vs. async calculate decision)
- **Invocation context:** [ ] Apex (sync) [ ] Apex (async/batch) [ ] REST from external system
- **Known constraints:** (governor limits, connected app, running user permissions)

## Loader String Selection

| Required operation | Loader string | Method |
|---|---|---|
| Read existing quote | `QuoteReader` | `ServiceRouter.read()` |
| Load product for adding | `ProductLoader` | `ServiceRouter.read()` |
| Add product to quote model | `QuoteProductAdder` | `ServiceRouter.save()` |
| Price / re-price the quote | `QuoteCalculator` | `ServiceRouter.save()` or `calculateInBackground()` |
| Persist calculated quote | `QuoteSaver` | `ServiceRouter.save()` |
| Create amendment quote from contract | `ContractAmender` | `ServiceRouter.read()` |
| Create renewal quote from contract | `ContractRenewer` | `ServiceRouter.read()` |

**Selected loader string(s) for this task:** ___

## Approach

Which pattern from SKILL.md applies?

- [ ] Programmatic Quote Creation with Products and Calculation
- [ ] Async Calculation for High Line-Count Quotes
- [ ] Contract Amendment via API
- [ ] Contract Renewal via API
- [ ] Other: ___

Why this pattern: ___

## Calculate Strategy

- [ ] Sync (`ServiceRouter.save('QuoteCalculator', model)`) — quote expected to have ≤ ~100 lines
- [ ] Async (`calculateInBackground` + `CalculateCallback`) — high line count or batch context

If async:
- [ ] `CalculateCallback` class is `global`
- [ ] `onCalculated` has a try/catch with explicit error logging
- [ ] Failure logging target identified: ___

## Code Checklist

Copy and use this while writing code:

- [ ] No direct DML on SBQQ pricing fields (`SBQQ__Discount__c`, `SBQQ__NetPrice__c`, etc.)
- [ ] All ServiceRouter calls use recognized loader strings (see table above)
- [ ] QuoteProductAdder step is followed by QuoteCalculator before QuoteSaver
- [ ] Contract status validated as `Activated` before calling ContractAmender or ContractRenewer
- [ ] `CalculateCallback` class (if used) has error handling in `onCalculated`
- [ ] ServiceRouter calls wrapped in try/catch with context-rich error messages
- [ ] REST calls (if applicable) include `Content-Type: application/json` and valid OAuth token

## Post-Build Validation

- [ ] Queried saved `SBQQ__Quote__c` — `SBQQ__NetTotal__c` is non-null and matches expected value
- [ ] Spot-checked quote line `SBQQ__NetPrice__c` — non-zero for all added products
- [ ] If async: confirmed calculation job completed and `onCalculated` was invoked (check logs/custom object)
- [ ] If amendment: new amendment quote exists with correct delta lines
- [ ] If renewal: renewal quote exists with subscription lines from original contract
- [ ] Debug logs reviewed — no unexpected CPU spikes or SOQL N+1 patterns in ServiceRouter calls

## Notes

Record any deviations from the standard pattern and the reason for each deviation.
