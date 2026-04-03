# Gotchas — Recursive Trigger Prevention

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Static Boolean Guards Hide Skipped Work

**What happens:** The loop stops recursing, but some legitimate records never receive required processing.

**When it occurs:** One flag controls the whole transaction.

**How to avoid:** Use record-aware guards or delta checks instead of a single global Boolean.

---

## Not All Re-Entry Is Accidental

**What happens:** A guard prevents a second pass that was actually part of the intended design.

**When it occurs:** Teams assume every repeated execution is a bug.

**How to avoid:** Identify which re-entry paths are legitimate before installing the guard.

---

## The Trigger Might Not Be The Only Source

**What happens:** Teams blame the trigger while surrounding automation or related-object updates are causing the extra pass.

**When it occurs:** The order of execution is not traced fully.

**How to avoid:** Map the full automation chain before deciding where the guard belongs.

---

## Guard Placement Matters

**What happens:** A guard exists, but it runs after the self-DML path has already been queued.

**When it occurs:** The guard is added late in the method rather than before the recursive branch.

**How to avoid:** Place the guard directly ahead of the self-triggering operation.
