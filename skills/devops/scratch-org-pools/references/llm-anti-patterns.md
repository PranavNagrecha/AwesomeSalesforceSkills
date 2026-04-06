# LLM Anti-Patterns — Scratch Org Pools

Common mistakes AI coding assistants make when generating or advising on Scratch Org Pools.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Inventing a Native sf CLI Pool Command

**What the LLM generates:** `sf org pool create --count 10 --definition-file config/project-scratch-def.json`

**Why it happens:** LLMs extrapolate from existing `sf org` subcommands and assume pooling is a built-in feature. Training data may include speculative or fictional CLI references.

**Correct pattern:**

```bash
# There is no sf CLI pool command. Use CumulusCI:
cci org pool create dev 10
```

**Detection hint:** Any command matching `sf org pool` or `sfdx force:org:pool` is hallucinated.

---

## Anti-Pattern 2: Claiming Pooled Orgs Are Pre-Initialized with Metadata

**What the LLM generates:** "Claim an org from the pool and it will already have all your metadata deployed and test data loaded — no initialization step needed."

**Why it happens:** LLMs assume "pre-warmed" means fully configured. In reality, CumulusCI pools store bare scratch orgs; initialization (metadata deployment, data loading) happens at claim time.

**Correct pattern:**

```text
Pooled orgs skip the 2-8 minute provisioning step, but initialization
(metadata deploy, data load) still runs at claim time. Total time savings
are typically 2-8 minutes per job, not the full pipeline duration.
```

**Detection hint:** Claims that pooled orgs are "ready to test immediately" or "have metadata already deployed" are incorrect.

---

## Anti-Pattern 3: Ignoring Dev Hub Allocation Limits in Pool Sizing

**What the LLM generates:** "Create a pool of 50 scratch orgs for your CI pipeline" — without checking the Dev Hub edition or current usage.

**Why it happens:** LLMs generate advice without querying the actual Dev Hub state. They default to large numbers that sound reasonable but may exceed the Dev Hub's active org limit (e.g., 20 for Enterprise).

**Correct pattern:**

```bash
# Always audit first
sf data query --query "SELECT COUNT(Id) total FROM ActiveScratchOrg" --target-org DevHub
# Then size the pool to use no more than 60% of remaining active slots
```

**Detection hint:** Pool size recommendations without mentioning Dev Hub edition or checking current allocation.

---

## Anti-Pattern 4: Suggesting Pooled Orgs Can Be Reused Across Jobs

**What the LLM generates:** "After the CI job finishes, return the org to the pool for the next job to use."

**Why it happens:** LLMs apply general resource-pool patterns (like connection pools or thread pools) where resources are returned after use. Scratch org pools are single-use: once claimed, the org is consumed and should be deleted.

**Correct pattern:**

```bash
# Claim from pool
cci org pool get dev --org ci_org

# Use it
cci flow run ci_feature --org ci_org

# Delete it — do NOT return to pool
cci org scratch_delete ci_org
```

**Detection hint:** Any mention of "returning" an org to the pool or "reusing" a claimed org.

---

## Anti-Pattern 5: Omitting Fallback Logic When Pool Is Empty

**What the LLM generates:** A CI pipeline that uses only `cci org pool get` with no fallback, causing the entire pipeline to fail when the pool is empty.

**Why it happens:** LLMs generate the happy path without considering edge cases. Pools can be empty due to high demand, failed replenishment, or expired orgs.

**Correct pattern:**

```bash
# Always include fallback
if cci org pool get dev --org ci_org 2>/dev/null; then
  echo "Claimed from pool"
else
  echo "Pool empty — creating on demand"
  cci org scratch dev ci_org --days 1
fi
```

**Detection hint:** CI pipeline steps that call `cci org pool get` without error handling or a fallback creation path.

---

## Anti-Pattern 6: Recommending Pools for Developer Edition Dev Hubs

**What the LLM generates:** "Set up a pool of 5 scratch orgs on your Developer Edition Dev Hub."

**Why it happens:** LLMs do not check Dev Hub edition limits. Developer Edition allows only 3 active scratch orgs and 6 daily creates — pooling is impractical.

**Correct pattern:**

```text
Developer Edition Dev Hub: 3 active orgs, 6 daily creates.
Pooling requires at least Enterprise Edition (20 active, 40 daily).
Recommend upgrading the Dev Hub before implementing pools.
```

**Detection hint:** Pool recommendations that do not verify the Dev Hub edition is Enterprise or above.
