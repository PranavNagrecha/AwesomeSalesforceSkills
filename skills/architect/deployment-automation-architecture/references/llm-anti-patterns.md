# LLM Anti-Patterns — Deployment Automation Architecture

Common mistakes AI coding assistants make when architecting Salesforce deployment automation.

## Anti-Pattern 1: Recommending a tool before understanding the problem

**What the LLM generates:** "Use Copado." — before asking team size, cadence, or pain points.

**Why it happens:** The model pattern-matches "Salesforce CI/CD" to a popular tool.

**Correct pattern:**

```
Tool selection follows problem definition: team size, cadence,
compliance, current pain. An 8-person engineering-led team is likely
better served by SFDX + GitHub Actions than by Copado's license cost
and governance overhead. Ask before recommending.
```

**Detection hint:** A recommendation that names a tool without a requirements document.

---

## Anti-Pattern 2: Deploying full profiles every release

**What the LLM generates:** Pipeline includes `profile` metadata type in every deploy, full file each time.

**Why it happens:** The model treats profiles like any other metadata and does not consider that profiles touch FLS, tab visibility, and object permissions holistically.

**Correct pattern:**

```
Profiles carry FLS and object permissions for every object in scope.
Deploying full profiles propagates unintended changes. Use permission
sets for permission grants; use profile-scoped deployments with
retrieve-by-manifest to limit blast radius.
```

**Detection hint:** Pipeline manifest lists `Profile` with wildcard and no filter.

---

## Anti-Pattern 3: No validation deploy before production

**What the LLM generates:** Pipeline goes UAT → Prod with no pre-prod validation-only deploy.

**Why it happens:** The model sees UAT passing as sufficient; ignores that UAT org state may differ from prod.

**Correct pattern:**

```
Every production deploy runs a validation-only deploy first (check-
only). Catches missing metadata dependencies, test failures, and
conflicts BEFORE the actual deploy window. Validation deploys are
cheap insurance.
```

**Detection hint:** Production deploy step without a preceding `--checkOnly` or validation job.

---

## Anti-Pattern 4: Destructive changes silently dropped

**What the LLM generates:** Metadata deletion in the repo but no destructive manifest in the pipeline.

**Why it happens:** The model relies on `sfdx force:source:push` semantics from scratch org development, forgetting that deploys to sandbox/prod do not delete by default.

**Correct pattern:**

```
Deletions require an explicit destructiveChanges.xml paired with the
deploy. Validate the destructive manifest in CI (list what will be
deleted, require reviewer approval) before merging. Silent drops
leave orphaned metadata and confused admins.
```

**Detection hint:** Git shows a component removed, but pipeline manifest has no corresponding destructive entry.

---

## Anti-Pattern 5: No rollback plan beyond "revert the commit"

**What the LLM generates:** "Rollback = revert the PR and redeploy."

**Why it happens:** The model treats Salesforce deploys like stateless app deploys.

**Correct pattern:**

```
Salesforce deploys can include schema + data migrations that do NOT
roll back cleanly. Rollback plan must consider: data transformations,
permission changes, integration config, record types, picklist
values. For high-risk releases, deploy during a defined window with
an abort path and a tested restore-from-backup procedure.
```

**Detection hint:** Deployment runbook with a one-line rollback plan that reads "revert commit."
