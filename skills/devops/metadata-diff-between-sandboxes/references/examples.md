# Examples — Metadata Diff Between Sandboxes

## Example 1: Pre-deploy diff between UAT and Prod

**Context:** Friday afternoon deploy from UAT to Prod. UAT has been the staging environment for two weeks; Prod has not been touched.

**Problem:** Prior deploys have failed mid-flight on missing custom fields and stale permission sets that exist in UAT but not Prod.

**Solution:**

```bash
# Retrieve both orgs against the same manifest
sf project retrieve start -o uat  -x manifest/scope.xml -r out/uat
sf project retrieve start -o prod -x manifest/scope.xml -r out/prod

# Categorized diff
git diff --no-index --name-status out/uat out/prod \
  | python3 .ci/categorize_diff.py \
      --source out/uat --target out/prod \
      --ignore .forceignore --ignore diff-ignore.txt \
      > diff-report.md

# Build deployable manifest from source-only items
python3 .ci/diff_to_manifest.py diff-report.md > to-deploy/package.xml

sf project deploy preview -o prod -x to-deploy/package.xml
```

**Why it works:** Symmetric retrieves give a clean diff. `--name-status` is the only flag needed for categorization (added / deleted / modified maps to source-only / target-only / changed). The deploy preview catches dependencies that the diff itself can't see.

---

## Example 2: Destructive-changes manifest from a cleanup PR

**Context:** Quarterly tech-debt PR removes 14 deprecated custom fields and 3 unused Apex classes from the repo.

**Problem:** The repo no longer contains the items, but Prod still does. Without destructiveChanges.xml, the deploy is a no-op for the deletions.

**Solution:**

```bash
# Retrieve fresh from Prod
sf project retrieve start -o prod -x manifest/scope.xml -r out/prod

# Diff repo source against retrieved
git diff --no-index --name-status force-app out/prod/force-app \
  | python3 .ci/categorize_diff.py \
      --source force-app --target out/prod/force-app \
      > diff.md

# Target-only items become the destructive manifest
python3 .ci/diff_to_destructive.py diff.md > destructive/destructiveChanges.xml
```

Then a human reviews `destructive/destructiveChanges.xml` before any deploy. Field deletions are irreversible against the data; review is non-negotiable.

**Why it works:** Repo-as-source-of-truth makes "the field is gone in source" the right signal for "delete in target."

---

## Anti-Pattern: full-retrieve for a one-flow diff

**What practitioners do:** "Just retrieve everything from both orgs and diff." 30 minutes per side, plus an hour of git noise on profile XML.

**What goes wrong:** The diff is now 50,000 lines, dominated by profile churn the team doesn't care about. The actual flow change is hidden.

**Correct approach:** Scope the retrieve to the type and name you care about — `-m Flow:Lead_Routing` retrieves one flow per side in seconds. Add scope incrementally only if drift is found.
