# Gotchas — Prompt Template Versioning

## Gotcha 1: Setup UI 'Save' loses the prior text

**What happens:** You can't compare v3 vs v4 without an external copy.

**When it occurs:** In-place edits.

**How to avoid:** Always create a new DeveloperName (`_vN+1`) rather than edit in place.


---

## Gotcha 2: Model silently upgrades

**What happens:** Identical prompt, different output next week.

**When it occurs:** Major-version model swap by Salesforce.

**How to avoid:** Re-run the fixture suite on the first of each month; alert on ≥5% metric drift.


---

## Gotcha 3: Bound variable schema change

**What happens:** v4 needs a new {{record.Field__c}} that doesn't exist in your sandbox.

**When it occurs:** Consumer deployed without the dependency.

**How to avoid:** Track dependencies in the CMDT record; validate-all before promotion.

