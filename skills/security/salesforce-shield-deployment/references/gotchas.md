# Gotchas — Salesforce Shield Deployment

## Gotcha 1: SOQL LIKE on probabilistic encrypted field

**What happens:** Returns zero rows silently.

**When it occurs:** Field encrypted after code was written.

**How to avoid:** Inventory queries before encrypting; switch to deterministic or refactor.


---

## Gotcha 2: Unbounded FHR storage

**What happens:** Storage bill balloons.

**When it occurs:** Every field audited.

**How to avoid:** Audit only regulated fields; archive to S3 via Data Pipeline.


---

## Gotcha 3: Real-time events dropped

**What happens:** Consumer lagging.

**When it occurs:** High-volume orgs.

**How to avoid:** Use Pub/Sub API with replay IDs + checkpoint offsets.

