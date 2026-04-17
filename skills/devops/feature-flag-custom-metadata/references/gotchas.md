# Gotchas — Feature Flags via Custom Metadata

## Gotcha 1: Random vs. deterministic rollout

**What happens:** Users see feature flicker on/off each page load.

**When it occurs:** Using Math.random().

**How to avoid:** Hash UserId.


---

## Gotcha 2: Dead flags

**What happens:** Codebase accumulates 50 flags, 40 dead.

**When it occurs:** No lifecycle discipline.

**How to avoid:** Quarterly flag audit + deletion.


---

## Gotcha 3: CMDT record shipped with Enabled=true

**What happens:** Feature lights up in prod on deploy.

**When it occurs:** Misconfigured scratch org source.

**How to avoid:** Default-false on the record; enable per-environment post-deploy.

