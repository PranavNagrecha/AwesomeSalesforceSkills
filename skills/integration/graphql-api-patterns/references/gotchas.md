# Gotchas - Graphql Api Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: One Endpoint Hides Over-Fetching

**What happens:** Teams assume a single GraphQL endpoint automatically means efficient traffic.

**When it occurs:** The selection set grows with nested objects and optional fields that the UI does not actually render.

**How to avoid:** Review selection sets like you would review SOQL fields or REST payloads.

---

## Gotcha 2: Partial Success Needs Real Client Logic

**What happens:** The response contains `data` and `errors`, but the client only handles one branch.

**When it occurs:** Error handling is copied from simpler REST assumptions.

**How to avoid:** Design the client for partial data and surfaced field-level or subquery errors.

---

## Gotcha 3: Adapter Choice Gets Cargo-Culted

**What happens:** Teams use `lightning/uiGraphQLApi` by default.

**When it occurs:** Someone saw an example and never re-evaluated the offline requirement.

**How to avoid:** Make `lightning/graphql` the default and justify `uiGraphQLApi` only when offline matters.
