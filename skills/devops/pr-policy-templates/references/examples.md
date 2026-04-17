# Examples — Pull Request Policy Templates

## Example 1: CODEOWNERS mapping

**Context:** Flow changes route to flow team

**Problem:** Apex devs were rubber-stamping flow PRs

**Solution:**

`/force-app/main/default/flows/ @org/flow-team` in CODEOWNERS

**Why it works:** Right eyes on the right changes


---

## Example 2: Required check: validation deploy

**Context:** Prevent 'works in dev' surprises

**Problem:** Deploy failures 2x/week

**Solution:**

GitHub Action validates against staging on every PR

**Why it works:** Catches metadata issues pre-merge

