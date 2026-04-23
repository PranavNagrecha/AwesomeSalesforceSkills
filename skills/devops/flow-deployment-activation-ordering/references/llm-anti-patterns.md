# LLM Anti-Patterns — Flow Deployment & Activation

## Anti-Pattern 1: Redeploy For Rollback

**What the LLM generates:** "to rollback, deploy the prior source."

**Why it happens:** rollback-as-redeploy is the generic DevOps pattern.

**Correct pattern:** flip `FlowDefinition.ActiveVersion` to the previous
version id. Redeploying creates a new version.

## Anti-Pattern 2: Delete Old Versions As Cleanup

**What the LLM generates:** "purge flow versions older than N days."

**Why it happens:** cleanliness impulse.

**Correct pattern:** retention must align with paused-interview lifetime.

## Anti-Pattern 3: Caller Before Callee

**What the LLM generates:** deploy in alphabetical order.

**Why it happens:** no dependency awareness.

**Correct pattern:** subflows before their callers.

## Anti-Pattern 4: Ignore Warnings

**What the LLM generates:** `--ignore-warnings` to push past deploy
failures.

**Why it happens:** fastest path to green.

**Correct pattern:** inspect the warning; silent inactive deploys bite
later.

## Anti-Pattern 5: No Pre-Deploy Inventory

**What the LLM generates:** jump to deploy without listing active
versions or paused interviews.

**Why it happens:** time pressure.

**Correct pattern:** capture pre-state — it becomes the rollback plan.
