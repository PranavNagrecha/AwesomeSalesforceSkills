# Examples — Scratch Org Pools

## Example 1: Enterprise Team Setting Up First Pool

**Context:** A 12-person development team on an Enterprise Dev Hub runs 6 parallel CI jobs per pull request. Each job creates a scratch org, deploys metadata, runs tests, and deletes the org. Pipeline time is dominated by the 5-minute org provisioning step per job.

**Problem:** 6 parallel jobs each waiting 5 minutes = 30 minutes of idle provisioning time per PR. The team also occasionally hits the 40/day creation limit when multiple PRs are open simultaneously.

**Solution:**

```bash
# Calculate pool size: 6 parallel jobs + 30% buffer = 8 orgs
# Enterprise Dev Hub: 40 daily creates, 20 active — plenty of headroom

# Initial pool creation
cci org pool create dev 8

# Verify
cci org pool list dev
# Output:
# Org Name       Expiration      Status
# pool_dev_001   2026-04-07      Active
# pool_dev_002   2026-04-07      Active
# ... (8 orgs listed)

# In each CI job, replace:
#   sf org create scratch --definition-file config/project-scratch-def.json --alias ci-org --duration-days 1
# With:
cci org pool get dev --org ci_org
```

**Why it works:** Pre-creating 8 orgs during off-peak hours means each CI job claims an org in seconds instead of waiting 5 minutes. The pool uses 8 of the 20 active slots, leaving 12 for developer scratch orgs. Daily replenishment of 8 orgs uses only 8 of the 40 daily creates.

---

## Example 2: Scheduled Replenishment with Monitoring

**Context:** The pool from Example 1 is working, but orgs expire after 1 day and the pool is sometimes empty when the first PR of the morning triggers CI.

**Problem:** Pool replenishment runs at midnight, but orgs are created with 1-day duration and the first CI run is at 9 AM — 9 hours later. Some mornings the pool is already depleted from late-night PR activity.

**Solution:**

```yaml
# .github/workflows/pool-replenish.yml
name: Replenish Scratch Org Pool
on:
  schedule:
    # Run at 4 AM and 4 PM UTC to keep pool fresh
    - cron: '0 4 * * *'
    - cron: '0 16 * * *'
  workflow_dispatch: {}

jobs:
  replenish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install CumulusCI
        run: pip install cumulusci
      - name: Authenticate Dev Hub
        run: |
          echo "${{ secrets.SFDX_AUTH_URL }}" > auth.txt
          sf org login sfdx-url --sfdx-url-file auth.txt --alias DevHub --set-default-dev-hub
      - name: Prune expired orgs first
        run: cci org pool prune dev
      - name: Check current pool size
        id: pool_check
        run: |
          CURRENT=$(cci org pool list dev 2>/dev/null | grep -c "Active" || echo "0")
          echo "current_size=$CURRENT" >> $GITHUB_OUTPUT
      - name: Replenish to target of 10
        run: |
          TARGET=10
          CURRENT=${{ steps.pool_check.outputs.current_size }}
          NEEDED=$((TARGET - CURRENT))
          if [ "$NEEDED" -gt 0 ]; then
            echo "Creating $NEEDED orgs to reach target of $TARGET"
            cci org pool create dev $NEEDED
          else
            echo "Pool already at target size ($CURRENT orgs)"
          fi
```

**Why it works:** Running twice daily with smart replenishment (only creating the delta) avoids wasting daily creates. Pruning before creating ensures accurate counts. The `workflow_dispatch` trigger allows manual replenishment when needed.

---

## Example 3: Dev Hub Allocation Audit Before Pool Setup

**Context:** A team wants to set up pooling but is unsure whether their Dev Hub has enough headroom.

**Problem:** Without checking current usage, creating a pool risks exhausting limits and breaking developer workflows.

**Solution:**

```bash
# Query current active org count
sf data query \
  --query "SELECT COUNT(Id) total FROM ActiveScratchOrg" \
  --target-org DevHub

# Query daily creation history (last 24 hours)
sf data query \
  --query "SELECT COUNT(Id) total FROM ScratchOrgInfo WHERE CreatedDate = TODAY" \
  --target-org DevHub

# Check allocation limits (visible in Dev Hub Setup > Scratch Org Allocations)
# Enterprise: 40 daily / 20 active
# Current: 12 active / 25 created today
# Available for pool: 8 active slots / 15 daily creates remaining
# Recommendation: Pool of 6 orgs, replenished once daily
```

**Why it works:** Auditing before pool setup prevents over-allocation. The team knows exactly how many slots are available and can size the pool accordingly.

---

## Anti-Pattern: Creating Pools on Developer Edition Dev Hub

**What practitioners do:** Team sets up a CumulusCI pool of 5 orgs on a Developer Edition Dev Hub, which has a maximum of 3 active orgs and 6 daily creates.

**What goes wrong:** The pool creation command succeeds for the first 3 orgs but fails for orgs 4 and 5 with an allocation error. The 3 pooled orgs consume all active slots, leaving no room for developer scratch orgs. The team cannot work until pooled orgs expire or are manually deleted.

**Correct approach:** Upgrade the Dev Hub to Enterprise Edition (20 active, 40 daily) or purchase a Scratch Org Add-On before attempting to pool. Developer Edition Dev Hubs are not suitable for pooling.
