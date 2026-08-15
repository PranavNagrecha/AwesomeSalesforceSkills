---
name: prompt-template-versioning
description: "Lifecycle management for Prompt Builder templates: version, test, promote, roll back via CMDT-backed bindings. NOT for source-control layout, model-version pinning, or versioning agent topic prompts — use agentforce/agentforce-prompt-versioning. NOT for authoring a template in Prompt Builder — use agentforce/prompt-builder-templates."
category: agentforce
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
triggers:
  - "how do I version a prompt builder template"
  - "rollback a prompt in production"
  - "a/b test a prompt variant"
  - "audit which prompt was live last week"
tags:
  - agentforce
  - prompt-builder
  - lifecycle
  - versioning
inputs:
  - "Prompt template name"
  - "release cadence"
  - "test cases"
outputs:
  - "Versioning policy doc"
  - "promotion checklist"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-08-14
---

# Prompt Template Versioning

This skill covers the **runtime promotion mechanics** of a prompt template: how
the live version changes, what a rollback costs in wall-clock time, and how to
serve two variants at once. The repository shape, changelog, model-pinning
policy, and drift detection live in `agentforce/agentforce-prompt-versioning`.
The two meet at `activeVersionIdentifier` — that skill decides which version
should be live, this one is about the flip.

## Start From What The Platform Already Does

Prompt Builder has **native versioning**. You can create and use multiple
versions of a template and control which one users reach through activation and
deactivation, with **only one version active at a time**. The metadata mirrors
it: `GenAiPromptTemplate` (directory `genAiPromptTemplates`, minimum API 60.0)
holds every retained version in `templateVersions[]` — each with `versionNumber`,
`versionIdentifier`, `status` (`Published`/`Draft`), `content`, `primaryModel`,
`inputs`, `outputSchema`, `responseFormat`, and `templateDataProviders` — and
`activeVersionIdentifier` names the live one.

So "how do I keep a history" is already solved. Two gaps remain, and everything
below addresses one of them:

1. **Promotion latency equals your metadata deploy latency** — an organisational
   property, not a technical one.
2. **Concurrent variants are impossible natively** — a hard platform limit.

## Recommended Workflow

1. Keep versions **inside one template** and have consumers reference the
   template, never a version. Promotion is then a one-field change to
   `activeVersionIdentifier`, and rollback is its inverse — both diffable in git,
   neither touching a Flow or Apex class.
2. Before promoting, run a **structural diff of the version envelope**, not just
   the prose. A new `required` input fails at invocation rather than deploy;
   `responseFormat` and `outputSchema` break parsers silently;
   `templateDataProviders` changes what data reaches the model; `primaryModel`
   invalidates the goldens even when the text is byte-identical.
3. Order the release: **deploy consumers first** (able to handle both versions),
   activate second, observe, retire third on a recorded date. Consumers that
   only handle the new version remove your rollback.
4. **Measure** the rollback wall-clock time in a rehearsal and record it. That
   measurement — not a preference for configurability — is the only good reason
   to add a CMDT slot-binding layer.
5. For a canary, accept that you need **two templates plus your own resolver**:
   bucket deterministically on user id, emit a variant-assignment event *before*
   the ramp starts, ramp 10 → 25 → 50 → 100 with a full working day of
   observation at each step, and delete the scaffolding on completion.
6. Put `GenAiPromptTemplate` **early in `package.xml`** — the Metadata API
   deploys types in file order, and the template must exist before anything
   referencing it (for example `AiAgentScorerDefinition`) can deploy.

## Key Considerations

- A canary with no variant tag produces two populations and no conclusion, and
  attribution cannot be recovered after the conversations end.
- CMDT indirection widens who can change production behaviour. Deploy binding
  records as metadata so a change is still a reviewable commit.
- Retention *is* the rollback plan. Keep at least two prior versions; retire on a
  date, not on a cleanup instinct.
- A grounding change (`templateDataProviders`) is a security event. Agents get no
  Trust Layer masking, so new grounding re-opens the PII register review.

## Worked Examples (see `references/examples.md`)

- *Versions inside one template* — promotion as a one-field change, with the
  wrong version-per-template alternative shown alongside.
- *When indirection earns its keep* — CMDT slot binding, and the honest
  tradeoff table for when not to use it.
- *Canary with attribution* — deterministic bucketing, variant tag, ramp rules.
- *What actually breaks on promotion* — the four envelope fields and their
  failure signatures.

## Common Gotchas (see `references/gotchas.md`)

- **Only one version can be active** — no platform traffic split; concurrent
  variants need two templates and your own resolver.
- **Required-input changes fail at invocation, not deploy** — deploy consumers
  first, always.
- **`primaryModel` changes make the goldens stale** — even with byte-identical
  prompt text.

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- Claiming Prompt Builder has no version history — it does, and designs built on
  the opposite premise solve nothing.
- Inventing a subagent-level `prompt_variants: weight:` traffic split (subagents
  were called topics before April 2026).
- Inventing `<modelVersion>` metadata — the real field is `primaryModel`.

## Official Sources Used

- GenAiPromptTemplate (Metadata API) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_genaiprompttemplate.htm
- Use Multiple Versions of a Prompt Template — https://help.salesforce.com/s/articleView?id=sf.prompt_builder_use_multiple_versions.htm&type=5
- Activate and Deactivate Prompt Templates — https://help.salesforce.com/s/articleView?id=sf.prompt_builder_activate_deactivate_templates.htm&type=5
- Manage Prompt Templates — https://help.salesforce.com/s/articleView?id=ai.prompt_builder_manage_prompt_templates.htm&type=5
- Create Custom Scorers (deploy ordering) — https://developer.salesforce.com/docs/ai/agentforce/guide/testing-api-custom-scorers.html
