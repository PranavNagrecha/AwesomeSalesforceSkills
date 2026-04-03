# Examples - Permission Set Groups And Muting

## Example 1: Shared Sales Bundle With Muted Export

**Context:** Sales managers and account executives need almost the same access, but only managers should keep export capability.

**Problem:** Teams consider cloning two almost-identical permission bundles.

**Solution:** Create a shared PSG for the common bundle and use a muting strategy for the narrower persona.

**Why it works:** The model reuses the common access bundle instead of multiplying near-duplicate permission sets.

---

## Example 2: Profile-Minimization Migration

**Context:** An org has many profiles with embedded feature permissions and frequent access drift.

**Problem:** Every change touches profiles and is hard to reason about.

**Solution:** Move feature-level permissions into focused permission sets, compose PSGs by persona, and leave profiles as thinner bases.

**Why it works:** Access becomes more modular, auditable, and easier to evolve.

---

## Anti-Pattern: PSG As A Junk Drawer

**What practitioners do:** They keep adding unrelated permission sets into one PSG because it is convenient.

**What goes wrong:** Access review and muting logic both become confusing.

**Correct approach:** Keep permission sets and PSGs coherent and named for real bundles.
