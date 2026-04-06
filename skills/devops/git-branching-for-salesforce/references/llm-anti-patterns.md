# LLM Anti-Patterns — Git Branching For Salesforce

Common mistakes AI coding assistants make when generating or advising on Git branching strategies for Salesforce projects. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending GitFlow as the Default

**What the LLM generates:** A full GitFlow model with `develop`, `release/*`, `hotfix/*`, and `feature/*` branches for a small Salesforce team with 3-5 developers using scratch orgs.

**Why it happens:** GitFlow is heavily represented in training data as "the" enterprise branching model. LLMs default to it because it appears authoritative and comprehensive. However, Salesforce DX documentation explicitly names trunk-based development as the first recommended model for source-driven projects.

**Correct pattern:**

```text
Default recommendation for source-driven Salesforce teams:
  Trunk-based development with short-lived feature branches.
  Reserve GitFlow/environment branching for teams with 15+ developers,
  compliance-gated releases, or multiple independent release trains.
```

**Detection hint:** Output recommends `develop` branch for a team under 10 developers without citing a specific constraint that requires it.

---

## Anti-Pattern 2: Ignoring Package Version Ancestry Constraints

**What the LLM generates:** A branching model where each feature branch creates its own unlocked package version for testing, with versions merged together later.

**Why it happens:** LLMs treat package versions like Docker images — independently buildable and composable. They do not model the linear ancestry constraint where each new version must descend from the highest promoted version.

**Correct pattern:**

```text
Package versions are created ONLY from the main or packaging branch.
Feature branches test using scratch org deploys, NOT package installs.
Version ancestry: v1.0 → v1.1 → v1.2 (linear, never forked).
```

**Detection hint:** Output includes `sf package version create` in a feature branch CI workflow.

---

## Anti-Pattern 3: Treating Salesforce Metadata Like Application Code for Merge Advice

**What the LLM generates:** "Resolve merge conflicts using standard Git merge or rebase. Use `git mergetool` to handle XML conflicts."

**Why it happens:** LLMs apply generic Git advice without accounting for the fact that Salesforce metadata XML has semantic ordering requirements. A textually valid merge can produce a metadata file that fails to deploy because elements are in an unexpected order or duplicated.

**Correct pattern:**

```text
After merging branches that touch the same metadata types (profiles,
permission sets, custom labels), validate the merge by deploying to
a scratch org: sf project deploy start --source-dir force-app
Standard git mergetool cannot detect Salesforce-specific XML ordering issues.
```

**Detection hint:** Merge conflict advice that does not mention deploying to a scratch org or sandbox for validation.

---

## Anti-Pattern 4: Mapping Every Branch to a Persistent Sandbox

**What the LLM generates:** A branching model that assigns a unique sandbox to each feature branch, integration branch, and release branch — recommending 8-12 sandboxes.

**Why it happens:** LLMs overfit on the concept that branches need org backing. They do not account for sandbox license limits by Salesforce edition. Enterprise Edition typically includes 1 Full Copy, 5 Developer Pro, and limited Partial Copy sandboxes.

**Correct pattern:**

```text
Feature branches → scratch orgs (ephemeral, no license limit beyond Dev Hub)
Integration branch → 1 Developer Pro sandbox
UAT/release branch → 1 Partial Copy sandbox
Production → main branch
Total persistent sandboxes needed: 2-3, not 8-12.
```

**Detection hint:** Output assigns a named sandbox to each feature branch, or recommends more than 5 persistent sandboxes without checking the edition's allocation.

---

## Anti-Pattern 5: Omitting the Hotfix Path

**What the LLM generates:** A clean branching model with feature branches and a main branch, but no documented path for emergency production fixes that must bypass the normal release cycle.

**Why it happens:** LLMs optimize for the happy path. Hotfix workflows are conditionally important and easy to skip in a general recommendation. In Salesforce, hotfixes are common because production orgs can encounter issues from platform updates, data volume changes, or governor limit hits that were not caught in lower environments.

**Correct pattern:**

```text
Hotfix workflow:
  1. Create hotfix/<ticket> from main (or the last production tag)
  2. Deploy to a Full Copy sandbox for reproduction and fix validation
  3. Merge to main AND to develop (or integration branch)
  4. Deploy to production via the expedited pipeline
  5. Tag main with the hotfix version
```

**Detection hint:** Branching model has no `hotfix/*` branch type and no documented emergency path.

---

## Anti-Pattern 6: Recommending Rebase Without Scratch Org Caveats

**What the LLM generates:** "Always rebase feature branches on main before merging to keep a clean linear history."

**Why it happens:** Rebase is standard Git hygiene advice. But in Salesforce DX projects, rebasing rewrites commit history, which breaks scratch org source tracking. The scratch org still tracks the old commits and will produce incorrect push/pull results.

**Correct pattern:**

```text
Rebase is acceptable but requires a follow-up step:
  After rebasing, run a full deploy to the scratch org:
    sf project deploy start --source-dir force-app
  Do NOT rely on source tracking after a rebase or force-push.
  Alternatively, recreate the scratch org after rebasing.
```

**Detection hint:** Rebase advice with no mention of scratch org source tracking impact.
