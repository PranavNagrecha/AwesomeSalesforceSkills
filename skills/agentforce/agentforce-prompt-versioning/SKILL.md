---
name: agentforce-prompt-versioning
description: "Version Prompt Templates and agent topic (now subagent) prompts: source-control shape, change review, model-version pinning, A/B, and rollback. Trigger keywords: prompt template versioning, prompt changelog, prompt rollback, A/B prompt test, agentforce prompt release. NOT for the CMDT-backed binding that swaps the live template version without a redeploy — use agentforce/prompt-template-versioning. NOT for authoring the template itself — use agentforce/prompt-builder-templates. NOT for prompt engineering tips, general LLM fine-tuning, or Classify / Einstein Generate studio UI walkthroughs."
category: agentforce
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "version prompt templates"
  - "prompt template source control"
  - "prompt a/b test"
  - "prompt rollback plan"
  - "model version pinning agent"
tags:
  - agentforce
  - prompts
  - versioning
  - devops
inputs:
  - Prompt template inventory
  - Agent topic prompts
  - Model-version strategy (auto / pinned)
outputs:
  - Prompt versioning convention (naming, changelog)
  - Rollback plan per prompt
  - A/B harness for prompt variants
dependencies:
  - agentforce/agentforce-testing-strategy
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-08-14
---

# Agentforce Prompt Versioning

This skill is the **repository lifecycle** for prompt templates: layout, change
records, model pinning, drift detection, and ownership. The runtime flip — how
the live version changes, what rollback costs in wall-clock time, and how to run
two variants concurrently — is `agentforce/prompt-template-versioning`. The two
meet at `activeVersionIdentifier`.

## Why Version Prompts

A prompt is executable configuration whose behaviour cannot be verified by
reading it. That makes the *record* of why a version exists more load-bearing
than for ordinary code, where the code is its own documentation.

## Source Of Truth And File Shape

`GenAiPromptTemplate` lives in `force-app/main/default/genAiPromptTemplates/`
with suffix `.genAiPromptTemplate`, minimum API version 60.0. The fact that
determines everything else about the layout:

> **All versions of a template live in one file.** `templateVersions` is an
> array on the template — not a file per version. `activeVersionIdentifier`
> names the live one.

Per-version fields inside each `GenAiPromptTemplateVersion`: `versionNumber`,
`versionIdentifier`, `status` (`Published`/`Draft`), `content`, `primaryModel`,
`inputs`, `outputSchema`, `responseFormat` (HTML/JSON/MarkDown),
`isCitationEnabled`, and `templateDataProviders`.

So git history is **per template** and the changelog is **per version**. Neither
substitutes for the other.

The repo is authoritative — but state it *and* detect it. Both drift directions
are silent (a UI edit does not fail; the deploy that reverts it does not fail
either), so a convention alone is not a control. See the nightly drift check
below.

## Naming And Version Strategy

- Template developer name reflects purpose and is a **published interface** —
  Flows, Apex, scorers, and agent actions reference it. Rename only as a
  coordinated change; prefer editing `masterLabel`, which is free.
- Versions are `versionNumber` inside the file. **Do not** put version suffixes
  in template names — that creates separate templates and couples every consumer
  to a version number.
- There is no "Revision" field. The compatible-vs-breaking distinction is real
  and belongs in the change record's **Contract impact** section, where it drives
  the deployment shape.

Contract-breaking means: a new `required` input, a changed `responseFormat` or
`outputSchema`, new or removed `templateDataProviders`, or a changed
`primaryModel`. None of these fail at deploy time — a new required input fails at
*invocation*.

## Changelog Convention

`PROMPTS_CHANGELOG.md` at repo root, keyed by `versionIdentifier`. Four sections,
contract impact first because it is the only one a release manager must read:

```markdown
## 2026-08-10 — Sales_Email v4  (versionIdentifier: e5f6g7h8)

### Contract impact: NONE
inputs unchanged · responseFormat unchanged · outputSchema n/a ·
templateDataProviders unchanged · primaryModel unchanged
=> one-field activation flip; no consumer deployment required

### What changed
Removed the "As an AI assistant" preamble; added an instruction to name the
most recent Opportunity stage change; shortened closing guidance to 1 sentence.

### Why
Sales ops sampled 80 drafts (2026-07): reps deleted the opening line in 60%.

### Measured before promotion
Golden suite 48/48 (unchanged) · median draft 214 -> 168 words ·
canary 10% / 5 working days / n=41 reps: send-without-edit 38% -> 51% ·
no adverse latency change

### Rollback
Revert activeVersionIdentifier to a1b2c3d4 (v3), deploy.
Measured 6 min in the 2026-08-04 rehearsal. v3 retained until 2026-10-01.
```

Numbers with sample sizes are the point. "Improved tone" records a belief; a
reader six months later must be able to disagree with the conclusion.

## Model Pinning

The field is **`primaryModel`** on `GenAiPromptTemplateVersion`. Verify any model
identifier against what the org offers — a plausible-but-wrong value deploys and
then behaves unexpectedly.

Pin per template, not per org, and only where reproducibility is a stated
requirement: parsed output, regulated wording, customer-facing copy. Leave the
platform default where a human reviews every output anyway.

**Pinning is a commitment to re-evaluate quarterly.** A stale pin produces no
error — output simply stops improving while the platform default's does. Record
the outcome either way; "evaluated and declined because X, reconsider Q2" is a
completed review.

## A/B And Rollback

**Only one version of a template can be active at a time**, and there is no
platform-level traffic split. Concurrent variants therefore need two templates
plus a resolver you write — the mechanics live in
`agentforce/prompt-template-versioning`. What belongs here is the record: which
variants ran, over what period, with what result.

Rollback availability is a retention decision. Keep at least two prior versions
with a **dated** retirement; an inactive version costs only file size, and the
weeks right after a promotion — when the cleanup instinct fires — are exactly
when the rollback is most likely to be needed.

## Recommended Workflow

1. Inventory templates. Assign **two** owners each in CODEOWNERS — the business
   owner of the wording and the engineer who owns the envelope. The failure modes
   split the same way.
2. One file per template under `genAiPromptTemplates/`, all versions inside.
   Put a structural-diff command in the PR template so envelope changes surface
   before anyone opens a 400-line prose diff.
3. Write the change record with contract impact first and measurements with
   sample sizes.
4. Decide `primaryModel` pinning per template, and schedule the quarterly
   re-evaluation with a named owner. Do not pin without the capacity to review.
5. Inject policy values (`refundWindowDays`) as inputs rather than embedding
   them in prose — unless the exact sentence is itself the reviewed artefact.
6. Run a nightly `sf project retrieve start --metadata GenAiPromptTemplate` plus
   `git diff --exit-code`, with a written resolution rule per drift direction.
   Run it again after every production deploy as release verification.
7. Put `GenAiPromptTemplate` early in `package.xml` — the Metadata API deploys in
   file order and the template must exist before referencing types such as
   `AiAgentScorerDefinition`.

## Official Sources Used

- GenAiPromptTemplate (Metadata API) —
  https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_genaiprompttemplate.htm
- GenAiPromptTemplateActv (Metadata API) —
  https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_genaiprompttemplateactv.htm
- Use Multiple Versions of a Prompt Template —
  https://help.salesforce.com/s/articleView?id=sf.prompt_builder_use_multiple_versions.htm&type=5
- Activate and Deactivate Prompt Templates —
  https://help.salesforce.com/s/articleView?id=sf.prompt_builder_activate_deactivate_templates.htm&type=5
- Manage Prompt Templates —
  https://help.salesforce.com/s/articleView?id=ai.prompt_builder_manage_prompt_templates.htm&type=5
- Create Custom Scorers (deploy ordering) —
  https://developer.salesforce.com/docs/ai/agentforce/guide/testing-api-custom-scorers.html
