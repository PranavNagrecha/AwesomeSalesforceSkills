# Gotchas — Prompt Injection Defense

## Gotcha 1: Testing only with English

**What happens:** Injection passes the English suite but succeeds in Spanish/French.

**When it occurs:** Multi-lingual deployments.

**How to avoid:** Include ≥2 non-English versions of each adversarial prompt.


---

## Gotcha 2: Trust Layer toxicity threshold too low

**What happens:** Jailbreaks phrased politely pass filters; toxic but benign content is blocked.

**When it occurs:** Default thresholds, no calibration.

**How to avoid:** Run the suite twice at different thresholds and tune to the false-positive/false-negative curve.


---

## Gotcha 3: Over-indexing on topic instructions

**What happens:** 100-line topic instructions dilute priority and slow every turn.

**When it occurs:** Every new threat gets a new sentence.

**How to avoid:** Collapse patterns into ≤5 hard rules + refer to named Invocable checks.

