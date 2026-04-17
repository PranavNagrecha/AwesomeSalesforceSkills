# Gotchas — Flow and Platform Events

## Gotcha 1: Assumed transactional

**What happens:** Consumer failure rolls back producer — it doesn't.

**When it occurs:** Misunderstanding PE semantics.

**How to avoid:** Compensating transaction pattern; idempotent consumers.


---

## Gotcha 2: Subscriber error silent

**What happens:** Retries exhaust; no alert.

**When it occurs:** Default config.

**How to avoid:** Monitor Setup → Event Delivery Monitoring.


---

## Gotcha 3: PE allocation exceeded

**What happens:** Publish fails with LIMIT_EXCEEDED.

**When it occurs:** Spike load.

**How to avoid:** Capacity-plan; high-volume type for >250k/day.

