---
name: multi-currency-and-advanced-currency-management
description: "Use when designing or reviewing Salesforce multi-currency behavior, especially irreversible activation, `CurrencyIsoCode`, `convertCurrency()`, dated exchange rates, and Advanced Currency Management tradeoffs. Triggers: 'multi currency', 'advanced currency management', 'CurrencyIsoCode', 'dated exchange rate', 'convertCurrency'. NOT for ordinary numeric field calculations with no currency conversion or reporting concern."
category: data
salesforce-version: "Spring '25+'"
well-architected-pillars:
  - Reliability
  - Scalability
tags:
  - multi-currency
  - advanced-currency-management
  - currencyisocode
  - convertcurrency
  - dated-exchange-rates
triggers:
  - "should we enable multi currency in Salesforce"
  - "advanced currency management and dated exchange rates"
  - "CurrencyIsoCode handling in Apex"
  - "convertCurrency in SOQL"
  - "roll up summary and ACM currency issues"
  - "advanced currency management vs standard multi-currency for Sales Cloud"
  - "standard multi-currency versus advanced currency management comparison"
inputs:
  - "whether multi-currency or ACM is already enabled"
  - "objects and reports involved"
  - "query, rollup, or Apex behavior that must respect currency context"
outputs:
  - "currency architecture recommendation"
  - "review findings for conversion and reporting risks"
  - "query and Apex guidance for currency-aware behavior"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-03-13
---

# Multi Currency And Advanced Currency Management

Use this skill when currency is no longer just a formatting concern. Multi-currency and Advanced Currency Management change how data is stored, queried, reported, and explained to the business. The most important design rule is to respect currency context instead of smuggling in hardcoded assumptions about one corporate currency.

---

## Before Starting

Gather this context before working on anything in this domain:

- Is multi-currency already enabled, and if not, has the team understood that activation is irreversible?
- Does the requirement involve Opportunity reporting, forecasting, rollups, or Apex calculations that depend on exchange rates?
- Does the consumer need the stored transaction currency, the user's currency, or dated historical conversion?

---

## Core Concepts

### Activation Changes The Data Model

Once multi-currency is enabled, currency context becomes part of the record model through `CurrencyIsoCode` and exchange-rate behavior. Teams should stop assuming every `Amount` field is implicitly the same currency everywhere.

### `CurrencyIsoCode` Is Not Optional Context

When Apex or integrations move money-like values around, the ISO code matters. A number without its currency context is usually incomplete business data.

### `convertCurrency()` Serves A Different Need

`convertCurrency()` is for returning values converted into the running user's currency context in SOQL. It is different from preserving the stored transactional currency and should be chosen intentionally.

### Advanced Currency Management Adds Time Dimension

ACM uses dated exchange rates for supported use cases such as opportunity reporting. That improves historical correctness, but it also changes reporting and summary expectations. Designs that ignore the time dimension eventually confuse finance and sales users.

---

## Common Patterns

### Currency-Aware Query Pattern

**When to use:** Apex or reporting logic must display both amount and currency context clearly.

**How it works:** Query `CurrencyIsoCode` with the amount fields you expose and use `convertCurrency()` only when the user-currency projection is the actual requirement.

**Why not the alternative:** Returning bare amounts encourages silent conversion mistakes downstream.

### Historical Reporting With ACM

**When to use:** The business needs dated exchange-rate behavior for historical opportunity analysis.

**How it works:** Enable ACM deliberately and document which reports and summaries change meaning under dated rates.

### Integration DTO With Currency Context

**When to use:** Money values leave Salesforce through Apex or integration payloads.

**How it works:** Include both the amount and the ISO code rather than sending a bare decimal.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Org needs multiple transactional currencies | Multi-currency | Core platform support for currency context |
| Historical opportunity reporting needs dated conversion | ACM | Adds time-aware exchange-rate behavior |
| Apex exposes money values externally | Include `CurrencyIsoCode` with amount | Prevents silent interpretation errors |
| User-facing query wants viewer-currency projection | `convertCurrency()` | Returns user-context converted values |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Activation and irreversibility implications are understood.
- [ ] Apex and integrations preserve currency context, not just numeric values.
- [ ] `CurrencyIsoCode` is queried or propagated where needed.
- [ ] `convertCurrency()` is used only when user-currency projection is intended.
- [ ] ACM implications for reporting, rollups, and finance users are documented.
- [ ] Hardcoded single-currency assumptions are challenged.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Multi-currency activation is irreversible** - teams must treat it as an architectural decision, not a casual setting toggle.
2. **Amounts without ISO context are misleading** - Apex and integrations often lose meaning when they move only decimals.
3. **`convertCurrency()` is not the same as preserving stored currency** - it serves a different consumer need.
4. **ACM changes historical reporting expectations** - the business must understand why values differ over time.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Currency design review | Findings on activation, conversion, reporting, and Apex handling |
| Query guidance | Pattern for stored-currency versus converted-currency retrieval |
| ACM decision | Recommendation for when dated exchange rates are justified |

---

## Related Skills

- `data/roll-up-summary-alternatives` - use when parent totals and rollups become the main implementation issue.
- `apex/custom-metadata-in-apex` - use when exchange-rate or currency-routing config belongs in metadata-driven logic.
- `integration/oauth-flows-and-connected-apps` - use when the main blocker is external finance-system authentication rather than currency semantics.
