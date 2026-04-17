# Gotchas — Clickjack and Frame Protection

## Gotcha 1: Wildcard * allow-list

**What happens:** Any attacker origin can frame the site.

**When it occurs:** Misreading the docs.

**How to avoid:** Enumerate explicit domains.


---

## Gotcha 2: Preview mode bypass

**What happens:** Experience Builder preview frames work, production doesn't.

**When it occurs:** Preview uses salesforce.com, production uses custom domain.

**How to avoid:** Test with real custom domain before go-live.


---

## Gotcha 3: Legacy VF without CSP

**What happens:** Attack via old VF page on force.com domain.

**When it occurs:** Unused VF pages left deployed.

**How to avoid:** Periodic VF cleanup + turn on global clickjack protection.

