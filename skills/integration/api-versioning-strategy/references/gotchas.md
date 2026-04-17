# Gotchas — API Versioning Strategy

## Gotcha 1: No version on v1

**What happens:** First breaking change forces coordinated migration.

**When it occurs:** v1 published without version prefix.

**How to avoid:** Version from day one.


---

## Gotcha 2: Logic in controller

**What happens:** Cannot reuse across versions.

**When it occurs:** Business logic in @HttpGet method.

**How to avoid:** Keep controllers thin; delegate to service layer.


---

## Gotcha 3: Silent deletion

**What happens:** Consumer breaks without warning.

**When it occurs:** No traffic monitoring.

**How to avoid:** Instrument + sunset header.

