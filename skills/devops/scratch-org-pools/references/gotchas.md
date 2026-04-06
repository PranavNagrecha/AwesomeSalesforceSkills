# Gotchas — Scratch Org Pools

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Pool Orgs Count Against Active Limits Even When Idle

**What happens:** A pool of 15 orgs consumes 15 of the Dev Hub's active scratch org slots regardless of whether any CI job has claimed them. If the Dev Hub has a 20-org active limit (Enterprise), only 5 slots remain for developer use.

**When it occurs:** Teams create large pools without auditing current active org usage. Developers start getting "maximum number of active scratch orgs" errors when trying to create personal orgs.

**How to avoid:** Always query `SELECT COUNT(Id) FROM ActiveScratchOrg` before sizing the pool. Reserve at least 30-40% of active slots for non-pool developer use.

---

## Gotcha 2: Failed Org Creations Still Burn Daily Limit

**What happens:** If a pool creation batch includes orgs that fail provisioning (e.g., due to an unsupported feature in the definition file), the failed attempts still count against the daily creation limit. A bad definition file can burn through 40 daily creates producing zero usable orgs.

**When it occurs:** The scratch org definition file references a feature not available in the chosen edition, or the Dev Hub has a transient provisioning error. The pool creation command reports partial failure but the daily limit is depleted.

**How to avoid:** Test the scratch org definition file by creating a single org manually before running pool creation. Monitor `ScratchOrgInfo` records with `Status = 'Error'` to detect systematic failures early.

---

## Gotcha 3: CumulusCI Pool State Is Local to the Machine

**What happens:** CumulusCI stores pool state in its local keychain. If the replenishment job runs on CI Runner A and the claim job runs on CI Runner B, Runner B cannot see the pool created by Runner A.

**When it occurs:** Teams set up pool replenishment on one GitHub Actions runner and expect a different runner to claim orgs. The claim fails with "no orgs available in pool" even though orgs exist.

**How to avoid:** Ensure all pool operations (create, claim, prune) either share the same CumulusCI keychain via persistent storage, or use a shared service account and Dev Hub state that all runners can access. In GitHub Actions, this typically means using a shared cache or artifact for the CumulusCI keychain directory.

---

## Gotcha 4: Pool Orgs Expire Silently

**What happens:** Pooled orgs have the same expiration rules as any scratch org. If orgs are created with `--duration-days 1` and not claimed within 24 hours, they expire. CumulusCI does not automatically notify when pool orgs expire — the pool just becomes empty.

**When it occurs:** Weekends and holidays. The Friday replenishment creates 10 orgs with 1-day duration. By Monday morning, all have expired. The first CI run falls back to on-demand creation (or fails if there is no fallback).

**How to avoid:** Use `--duration-days 3` or higher for pools that must survive weekends. Alternatively, skip pool replenishment on Fridays and schedule it for early Monday instead. Always implement fallback-to-create logic in CI jobs.

---

## Gotcha 5: Pooled Orgs Are Bare — Initialization Adds Time at Claim

**What happens:** CumulusCI pool orgs are created but not initialized. When a job claims an org via `cci org pool get`, CumulusCI runs the initialization flow (e.g., `dev_org` or `ci_org`), which deploys metadata and may load data. This initialization can take 3-10 minutes depending on the project.

**When it occurs:** Teams expect "instant" org availability after claiming from the pool. The provisioning step (2-8 minutes) is eliminated, but the initialization step still runs. Total time savings may be less than expected.

**How to avoid:** Set accurate expectations: pooling saves provisioning time, not initialization time. For projects with heavy initialization, the total claim-to-ready time might still be 5-10 minutes — but that is better than 10-18 minutes (provisioning + initialization) without pooling.
