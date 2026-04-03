# Gotchas - Permission Set Groups And Muting

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Muting Does Not Fix Bad Bundle Design

**What happens:** Teams use muting to patch an overly broad group instead of redesigning the bundle.

**When it occurs:** PSG composition was never normalized around clear feature sets.

**How to avoid:** Keep the base group coherent and use muting only for small, intentional subtractions.

---

## Gotcha 2: Profile Bloat Cancels PSG Benefits

**What happens:** The org adopts PSGs but still carries most feature permissions in profiles.

**When it occurs:** Migration stops halfway.

**How to avoid:** Treat profile minimization as part of the PSG strategy, not an optional follow-up.

---

## Gotcha 3: Access Testing Is Skipped

**What happens:** Bundles look correct on paper but users inherit unexpected combinations.

**When it occurs:** Composed access is never tested with real personas.

**How to avoid:** Validate effective access for the main persona combinations before rollout.
