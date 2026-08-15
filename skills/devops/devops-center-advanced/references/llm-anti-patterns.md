# LLM Anti-Patterns — DevOps Center Advanced Workflows

Mistakes AI assistants reliably make when asked about DevOps Center pipelines.

---

## Anti-Pattern 1: Answering About the Managed Package When the Org Is on Next-Gen

**What the LLM generates:** setup and troubleshooting steps that begin with
installing or upgrading the DevOps Center managed package, regardless of which
product the user is on.

**Why it happens:** the managed-package product has years of documentation,
blogs, and community answers behind it; the native next-generation product is
recent and thinly represented. The model answers from the larger corpus.

**Correct pattern:** establish which product first. Next-generation DevOps Center
is a native platform capability with no package install, adds Bitbucket (beta)
alongside GitHub, surfaces change tracking through DX Inspector inside the org,
and carries governance policies covering coding agents. Salesforce documents the
two separately.

**Detection hint:** any instruction to install a package, or a reference to
configuring "the DevOps Center app," in an answer about an org that mentions DX
Inspector, agent governance, or Bitbucket.

---

## Anti-Pattern 2: Recommending Parallel Git and DevOps Center Workflows

**What the LLM generates:** "developers can continue using their existing branch
workflow while admins use DevOps Center" — presented as a benefit rather than a
hazard.

**Why it happens:** it is a genuinely appealing compromise and it sounds like
respecting both populations' tooling. The model does not model the promotion
semantics that make it break.

**Correct pattern:** both populations promote through work items. Developers keep
every tool they have — CLI, local tests, their editor — and commit to the
work-item branch instead of one they created. The enforceable rule is negative:
no branch that is not a work-item branch is merged into a pipeline branch.

**Detection hint:** the words "in parallel," "alongside," or "developers can
continue to" in a description of two writers on the same repository.

---

## Anti-Pattern 3: Improvising an Emergency Bypass on Request

**What the LLM generates:** a direct `sf project deploy start --target-org prod`
in answer to "we need to hotfix production now," with no pre-state capture, no
validation, and no reconciliation step.

**Why it happens:** the prompt is urgent and the model optimizes for the
immediate ask. Reconciliation is the part with no visible payoff in the moment.

**Correct pattern:** capture the pre-state, `deploy validate` with an explicit
test level, `deploy quick` the validated job, then cascade the change *down* the
pipeline so the next normal promotion does not revert it. The cascade is the step
that prevents the second incident, and it is the step that gets skipped.

**Detection hint:** a production deploy command with no preceding retrieve and no
following reconciliation task.

---

## Anti-Pattern 4: Omitting `--test-level`

**What the LLM generates:** `sf project deploy start --target-org prod` with no
test level, sometimes with a comment that the default is fine.

**Why it happens:** the flag is optional, so the shortest correct-looking command
omits it. Examples in the wild omit it too.

**Correct pattern:** without `--test-level` the behaviour comes from the target
org's defaults, so the same command behaves differently against different orgs —
which defeats the point of a pipeline. Set it explicitly everywhere, and use
`deploy validate` → `deploy quick --job-id` for production so the tests run once,
ahead of the window.

**Detection hint:** any `sf project deploy start` targeting production without
`--test-level`.

---

## Anti-Pattern 5: Suggesting a Manual Merge for a Flow Conflict

**What the LLM generates:** conflict-resolution guidance that walks through
reconciling the two versions of the flow XML hunk by hunk, often with a plausible
merged fragment.

**Why it happens:** merge-conflict resolution is a well-worn task in the training
data and XML looks like text the model can reason about. It usually can, at the
syntax level — which is exactly what makes the output dangerous.

**Correct pattern:** never hand-merge flow XML. Accept one side wholesale,
re-apply the other change in Flow Builder in a sandbox, commit that result, and
verify on the canvas before promoting. A syntactically valid hand-merge can point
a connector at the wrong element and deploy without error.

**Detection hint:** a diff containing `locationX` or `locationY` in a proposed
manual resolution.

---

## Anti-Pattern 6: Treating a Permission Set Commit as Additive

**What the LLM generates:** a work item that captures only the newly added field
permissions, described as "adding access."

**Why it happens:** the change *is* additive from the author's point of view, and
delta-shaped commits are the norm for source code.

**Correct pattern:** the Metadata API replaces the whole `PermissionSet`
document. Anything in the target org that is not in the deployed XML is removed,
silently. Retrieve the target's current state, merge, commit the merged document.
See `devops/permission-set-deployment-ordering`.

**Detection hint:** a `PermissionSet` metadata file in a commit containing
markedly fewer `<fieldPermissions>` or `<objectPermissions>` entries than the
target org has.

---

## Anti-Pattern 7: Presenting Beta Capabilities as Production-Ready

**What the LLM generates:** a CI pipeline built on `sf project deploy pipeline
start`, or a migration plan that assumes Bitbucket support, with no mention of
beta status.

**Why it happens:** the commands and the provider appear in official
documentation, and the model does not weight the beta label the way a release
manager would.

**Correct pattern:** name the status. The `sf project deploy pipeline` family is
beta and can change without a GA deprecation cycle; Bitbucket support is beta.
Both are the right direction and both belong in a pilot before a release runbook.
Pin the CLI version in CI rather than installing latest.

**Detection hint:** a production runbook referencing a `pipeline` subcommand or
Bitbucket without the word "beta" anywhere near it.

---

## Anti-Pattern 8: Skipping the Edition and Region Check

**What the LLM generates:** a full migration plan to next-generation DevOps
Center that never asks what edition or region the org is in.

**Why it happens:** availability constraints are boilerplate at the bottom of a
help page and read as low-information to a model summarizing capability.

**Correct pattern:** check first. Next-generation DevOps Center requires
Professional Edition with API access or higher and Lightning Experience, and is
not available in Government Cloud Plus or the EU Operating Zone. An org in an
excluded region has no decision to make, and finding that out after the
assessment is wasted work.

**Detection hint:** a migration recommendation with no availability section.
