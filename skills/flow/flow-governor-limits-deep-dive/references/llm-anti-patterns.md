# LLM Anti-Patterns — Flow Governor Limits Deep Dive

## Anti-Pattern 1: SOQL inside a Loop

**What the LLM generates:** Loop over records with Get Records inside.

**Why it happens:** Single-record mental model.

**Correct pattern:** Hoist the Get Records outside the loop with an IN-clause.

---

## Anti-Pattern 2: DML inside a Loop

**What the LLM generates:** Loop with Update Records inside.

**Why it happens:** Natural "for each record, update it" pattern.

**Correct pattern:** Build a collection inside the loop; single Update Records outside with the collection.

---

## Anti-Pattern 3: Assuming limits scale with org size

**What the LLM generates:** "Enterprise orgs get more SOQL." No — limits are per-transaction, same for all editions.

**Why it happens:** LLMs assume tier-based scaling.

**Correct pattern:** Design for 100 SOQL max synchronous, regardless of edition.

---

## Anti-Pattern 4: Nominal-limit math

**What the LLM generates:** "We use 80 SOQL, safe under 100."

**Why it happens:** LLMs don't account for shared transactions.

**Correct pattern:** Target 70% headroom. Plan against shared pool, not nominal limit.

---

## Anti-Pattern 5: Ignoring heap in unbounded collections

**What the LLM generates:** Accumulate all 50,000 rows in a collection.

**Why it happens:** LLMs don't model heap cost.

**Correct pattern:** Process in chunks; don't hold large collections.

---

## Anti-Pattern 6: "More async fixes limits"

**What the LLM generates:** Routes everything to Scheduled Paths to solve limit problems.

**Why it happens:** LLMs treat async as a silver bullet.

**Correct pattern:** Async gives fresh limits but doesn't fix bulk-unsafe code. A Scheduled Path with SOQL-in-loop breaks at the same iteration count — just with a 5-minute delay.

---

## Anti-Pattern 7: No benchmark assertion in tests

**What the LLM generates:** Tests for correctness, not for limit consumption.

**Why it happens:** LLMs treat limit math as separate from testing.

**Correct pattern:** Every bulk-sensitive flow test asserts `Limits.getQueries() < budget` and `Limits.getDMLStatements() < budget`.
