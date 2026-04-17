# Gotchas — LWC State Management

## Gotcha 1: Missing message channel

**What happens:** LMS silently no-ops.

**When it occurs:** Channel not deployed.

**How to avoid:** Channel is metadata; deploy with LWC.


---

## Gotcha 2: Race on subscription

**What happens:** First publish missed.

**When it occurs:** Subscriber connects after publish.

**How to avoid:** Keep last value in a small retained cache or use @wire pattern.


---

## Gotcha 3: Redux-style overhead

**What happens:** Bundle bloat, debug complexity.

**When it occurs:** Copying React patterns.

**How to avoid:** Lightweight store tailored to LWC.

