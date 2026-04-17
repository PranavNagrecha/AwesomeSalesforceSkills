# Examples — SFDX Monorepo Patterns

## Example 1: Three-package layout

**Context:** Sales + Service + Agentforce

**Problem:** Previous single-dir repo had 800 metadata files mixed

**Solution:**

Split into `packages/sales-core`, `packages/service-core`, `packages/ai-actions`, each with its own README and tests

**Why it works:** Teams own their package; cross-package changes visible in diff


---

## Example 2: Change-detection CI

**Context:** Push touches only sales package

**Problem:** Previous CI deployed all three

**Solution:**

`git diff --name-only origin/main... | awk -F/ '/^packages/ {print $2}'` → matrix builds only affected packages

**Why it works:** Cuts CI time 60%

