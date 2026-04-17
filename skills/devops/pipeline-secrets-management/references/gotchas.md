# Gotchas — Pipeline Secrets Management

## Gotcha 1: Auth URL committed

**What happens:** Anyone with repo read owns the org.

**When it occurs:** Developer cached `sf org login web` output.

**How to avoid:** Pre-commit hook + secret scanning.


---

## Gotcha 2: Shared Connected App

**What happens:** Blast radius includes all pipelines.

**When it occurs:** Single app reused.

**How to avoid:** One app per stage.


---

## Gotcha 3: Expired certificate

**What happens:** Pipelines fail silently at midnight.

**When it occurs:** 3-year self-signed cert.

**How to avoid:** Alert 30 days before expiry; automate rotation.

