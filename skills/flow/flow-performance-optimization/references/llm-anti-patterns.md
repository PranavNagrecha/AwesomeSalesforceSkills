# LLM Anti-Patterns — Flow Performance Optimization

## Anti-Pattern 1: Tuning without measuring

**What the LLM generates:** "Add this optimization, it'll be faster."

**Why it happens:** LLMs pattern-match on "optimizations" without benchmarking.

**Correct pattern:** Benchmark before, tune, benchmark after. Commit measurements in the PR.

---

## Anti-Pattern 2: Optimizing the wrong thing

**What the LLM generates:** Refactors 10 Decision elements while ignoring a SOQL-in-loop that dominates cost.

**Why it happens:** LLMs don't profile — they generalize "cleaner code = faster".

**Correct pattern:** Profile first. The biggest cost dominates. Fix it; everything else is rounding error.

---

## Anti-Pattern 3: Recommending an asynchronous path for all heavy work

**What the LLM generates:** "Move the heavy work to an asynchronous path."

**Why it happens:** LLMs treat async as a performance panacea.

**Correct pattern:** Async helps transaction-isolation, not per-record cost. An asynchronous path with SOQL-in-loop still meets the SOQL limit (apexdev 264 L19747 gives 100 synchronous, 200 asynchronous), only at a higher count.

---

## Anti-Pattern 4: Micro-optimizations with no measurable impact

**What the LLM generates:** Combining two Assignments into one; removing an empty Decision branch.

**Why it happens:** LLMs over-apply "simplify" patterns.

**Correct pattern:** Skip if the measured delta is under noise. Keep readable flow structure when perf gains are < 5%.

---

## Anti-Pattern 5: Selecting all fields in Get Records

**What the LLM generates:** Default Get Records that returns all fields.

**Why it happens:** LLMs default to "just grab everything".

**Correct pattern:** Explicitly list the fields needed (`queriedFields`, api_meta 264 L73623-73625). UNVERIFIED (2026-10-20): the heap and CPU saving is not quantified in the corpus.

---

## Anti-Pattern 6: Unbounded loop accumulation

**What the LLM generates:** Loop that appends to a collection without size bound.

**Why it happens:** Natural accumulation pattern.

**Correct pattern:** Bound collection size; chunk processing at 2000-5000 records. UNVERIFIED (2026-10-20): the 2000-5000 chunk size is a rule of thumb, not a corpus figure.

---

## Anti-Pattern 7: Ignoring per-element cost

**What the LLM generates:** "Flow elements are cheap."

**Why it happens:** LLMs don't model per-element overhead.

**Correct pattern:** Each Assignment, Decision, Loop has non-zero CPU cost. At high scale, count them. UNVERIFIED (2026-10-20): per-element CPU cost is not described in the corpus.
