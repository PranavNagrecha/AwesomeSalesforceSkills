# Gotchas — Session High Assurance Policies

## Gotcha 1: Org-wide HA breaks integrations

**What happens:** API-only integration users fail login.

**When it occurs:** Setting at Org-wide Session Settings.

**How to avoid:** Apply at profile or permission set level; exclude integration profiles.


---

## Gotcha 2: Step-up on report

**What happens:** Users hit the prompt on every refresh.

**When it occurs:** Report folder scoped to HA.

**How to avoid:** Scope HA to the underlying fields not reports; or use a Login Flow that caches HA for the day.


---

## Gotcha 3: Mobile SDK crash

**What happens:** App fails to refresh.

**When it occurs:** Older SDKs.

**How to avoid:** Upgrade to SDK versions that handle HA challenge.

