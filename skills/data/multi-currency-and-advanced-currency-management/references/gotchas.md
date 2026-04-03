# Gotchas - Multi Currency And Advanced Currency Management

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Activation Is One-Way

**What happens:** Teams treat multi-currency like a reversible trial setting.

**When it occurs:** The org has not treated activation as a data-model decision.

**How to avoid:** Make the irreversible nature part of the architecture decision and stakeholder signoff.

---

## Gotcha 2: Bare Decimals Travel Badly

**What happens:** Integrations and Apex DTOs pass amounts around without ISO codes.

**When it occurs:** Developers assume the org's corporate currency is obvious everywhere.

**How to avoid:** Carry `CurrencyIsoCode` with the amount whenever values leave their original record context.

---

## Gotcha 3: Historical Values Surprise Stakeholders

**What happens:** Reports and totals differ from what business users expected once dated exchange rates are involved.

**When it occurs:** ACM was enabled without enough explanation of historical conversion behavior.

**How to avoid:** Document which reports and analytics are affected before rollout.
