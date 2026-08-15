# Gotchas — Agentforce Prompt Versioning

---

## 1. All versions live in one file, so `git log` on a version is meaningless

**What happens:** a reviewer runs `git log` expecting a history of v3 and gets
the history of the whole template, including every other version's edits.

**Why:** `templateVersions` is an array on `GenAiPromptTemplate`. The file is the
unit of version control; the version is a block inside it
([GenAiPromptTemplate](https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_genaiprompttemplate.htm)).

**How to avoid:** treat the changelog as the per-version record and git as the
per-template record. They answer different questions and you need both. The
changelog's `versionIdentifier` is what links an entry to a block in the file.

---

## 2. Diffs are large and the dangerous part is the small bit

**What happens:** adding a version appends a 150-line `<templateVersions>` block.
The reviewer skims, approves, and misses that `required` was added to an input —
three lines inside the block.

**How to avoid:** review the envelope separately from the prose. Put a
structural-diff command in the PR template so the breaking-change candidates are
surfaced before anyone opens the full diff:

```bash
git diff origin/main -- force-app/main/default/genAiPromptTemplates/ \
  | grep -E '^[+-].*(<required>|<apiName>|responseFormat|outputSchema|templateDataProviders|primaryModel|activeVersionIdentifier)'
```

An empty result means the change is prose-only and reviews in a minute. A
non-empty result means it is a coordinated release.

---

## 3. `modelVersion` is not a field — `primaryModel` is

**What happens:** a template is authored with `<modelVersion>` pinning a specific
model. It fails to deploy, or is silently ignored.

**How to avoid:** the documented field on `GenAiPromptTemplateVersion` is
`primaryModel`. Verify the model identifier against what the org actually offers
before writing it — a plausible-but-wrong value that deploys and then behaves
unexpectedly is worse than leaving the field out.

---

## 4. Pinning a model is a commitment to re-evaluate

**What happens:** three templates are pinned during a compliance push. Eighteen
months later they are still on the same model, quality has drifted behind the
platform default, and nobody noticed because nothing broke.

**Why it is invisible:** a stale pin produces no error. Output simply stops
improving while everything around it does.

**How to avoid:** a quarterly review per pinned template, with a recorded outcome
either way. "We evaluated the newer model and declined because X, reconsider in
Q2" is a completed review. An unrecorded review is one that did not happen.

---

## 5. Adding a variable is backwards-compatible; making it required is not

**What happens:** v4 adds an input and marks it `required` for safety. Every
consumer that does not supply it now fails — at invocation, not at deploy.

**How to avoid:** additive and optional is compatible with both versions and
keeps promotion a one-field flip. If the input genuinely must be required, the
release is coordinated: consumers deploy first, activation second. Record it in
the change record's "Contract impact" section so the release manager sees it in
the first two lines.

---

## 6. Renaming a template breaks every reference

**What happens:** `Sales_Email` is renamed to `Sales_Followup_Email` for clarity.
Flows, Apex, scorers, and agent actions that referenced the old developer name
break.

**How to avoid:** template developer names are a published interface. Rename only
as a deliberate, coordinated change with every reference updated in the same
release — and prefer changing `masterLabel` (the human-facing name) instead,
which is free.

---

## 7. Deploying to sandbox and forgetting production inverts your comparison

**What happens:** a prompt change is deployed to a sandbox during development
and omitted from the production release. The agent now behaves differently in
the two orgs, so every comparison used to sign off the release was measuring
different systems.

**How to avoid:** prompt templates go in the standard release train, not in an
ad-hoc developer deploy. Verify with a post-deploy drift check against
production — running the detector after the deploy turns it from monitoring into
release verification.

---

## 8. UI edits and repo deploys silently overwrite each other

**What happens:** a typo is fixed in Prompt Builder in production before a demo.
Three weeks later a routine deploy reverts it. Neither operation failed.

**How to avoid:** a nightly `sf project retrieve start --metadata
GenAiPromptTemplate` plus `git diff --exit-code`, and a written policy for each
drift direction (`references/examples.md` Example 4). Restricting Prompt Builder
edit rights in production is the structural fix; the detector is the safety net
for the exceptions.

---

## 9. `GenAiPromptTemplate` must precede its consumers in `package.xml`

**What happens:** a release deploying a template and a scorer together fails with
a reference error that reads like a permissions problem.

**The rule:** the Metadata API deploys types in the order they appear in the
manifest, and the template must exist before a referencing
`AiAgentScorerDefinition` can deploy.

**How to avoid:** put `GenAiPromptTemplate` early as a standing convention.
Templates are a dependency of agents, scorers, Flows, and Apex — never the
reverse.

---

## 10. Deleting a superseded version removes the rollback

**What happens:** v3 is cleaned up the day v4 is promoted. Two weeks later v4
needs reverting.

**How to avoid:** two-version retention with a dated retirement. An inactive
version costs file size and nothing else, and the weeks immediately after a
promotion are exactly when the rollback is most likely to be needed. Record the
eventual removal in the changelog so a reader can see the policy was followed
rather than forgotten.

---

## 11. Policy text embedded in the prompt binds two release cadences together

**What happens:** the prompt contains *"the refund window is 30 days"*. Policy
changes to 45 days. Now a policy update requires a prompt version, a review, a
canary, and a deploy.

**How to avoid:** inject policy as an input (`refundWindowDays`) sourced from
Custom Metadata or a record, so the prompt describes *how* to use the value and
the data supplies *what* it is. This also makes the policy auditable in one place
rather than embedded in prose across several templates.

The counter-case: when the policy statement *is* the wording being tested — for
instance a legally-reviewed disclosure — embedding is correct, because the exact
sentence is the artefact under version control. Decide per value, and write down
which case you are in.

---

## 12. A change record without numbers records a belief

**What happens:** the changelog says "improved tone". Six months later a
regression is suspected and nobody can tell whether v4 was better than v3,
because "improved" was an opinion at the time and is unfalsifiable now.

**How to avoid:** every entry carries measurements with sample sizes — golden
pass rate, the canary's primary metric with `n`, and any latency change. A reader
must be able to disagree with the conclusion, which requires the evidence to be
present.

---

## 13. In-flight sessions can reference a version you are removing

**What happens:** a version is deleted while conversations that selected it are
still open.

**How to avoid:** deactivate first, observe for a defined window, then delete.
The dated retirement schedule handles this as a side effect — the observation
window between deactivation and removal exists partly for rollback and partly for
in-flight drain.

---

## 14. Two owners, or no owner

**What happens:** the prompt's wording is owned by sales ops and its metadata
envelope by engineering. With no explicit split, either both defer or both edit.

**How to avoid:** CODEOWNERS with both parties on the template path. The failure
modes are genuinely split — a bad sentence is a business problem, a changed
`outputSchema` is an engineering one — so the ownership should be too. A single
owner means one of the two review lenses is missing.
