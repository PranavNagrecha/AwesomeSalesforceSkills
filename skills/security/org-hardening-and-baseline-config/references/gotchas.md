# Gotchas - Org Hardening And Baseline Config

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Trusted-Site Sprawl Feels Invisible

**What happens:** CSP and CORS exceptions accumulate with no review.

**When it occurs:** Teams optimize for short-term unblock and never return to cleanup.

**How to avoid:** Treat every trust exception as a tracked risk decision with an owner.

---

## Gotcha 2: Release Updates Get Deferred Forever

**What happens:** Security-related release settings pile up until the org is surprised by a forced change or brittle dependency.

**When it occurs:** Release management and hardening are treated as separate concerns.

**How to avoid:** Put critical updates on a recurring operational review cadence.

---

## Gotcha 3: Session Controls Are Underestimated

**What happens:** Password and session policy stay overly permissive because they are less visible than app features.

**When it occurs:** Hardening is framed only as browser configuration.

**How to avoid:** Review session and authentication settings as baseline controls, not as optional cleanup.
