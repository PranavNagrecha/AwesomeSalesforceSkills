# Gotchas - Sosl Search Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Dynamic Search Text Becomes An Injection Surface

**What happens:** User input is concatenated into dynamic SOSL text.

**When it occurs:** Teams use `Search.query` for convenience without a safety boundary.

**How to avoid:** Prefer static SOSL with bind variables or tightly controlled query construction.

---

## Gotcha 2: Result Shape Surprises Consumers

**What happens:** The caller expects one flat result set and instead receives grouped lists by object.

**When it occurs:** The design copies SOQL assumptions into SOSL consumers.

**How to avoid:** Model the grouped response shape up front.

---

## Gotcha 3: Search UX Overpromises Precision

**What happens:** Stakeholders expect exact report-like behavior from a search experience.

**When it occurs:** Search and filtering requirements were never separated.

**How to avoid:** Be clear about when the flow is discovery and when it transitions to structured retrieval.
