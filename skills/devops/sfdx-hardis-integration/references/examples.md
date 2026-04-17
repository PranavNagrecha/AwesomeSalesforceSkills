# Examples — sfdx-hardis Integration

## Example 1: Daily drift monitor

**Context:** Detect manual prod changes

**Problem:** Previously admins changed flows directly in prod

**Solution:**

Daily `sf hardis:org:monitor:all` pipeline posts Slack alert on diff

**Why it works:** Catches unauthorized change within 24h


---

## Example 2: Smart deploy

**Context:** Reduce deploy failures

**Problem:** Validation errors mid-deploy

**Solution:**

`sf hardis:project:deploy:sources:dx --check` catches 80% pre-deploy

**Why it works:** Faster feedback

