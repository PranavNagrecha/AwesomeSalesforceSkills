---
name: prompt-template-versioning
description: "Lifecycle management for Prompt Builder templates: version, test, promote, roll back via CMDT-backed bindings. NOT for authoring initial templates or generic prompt engineering."
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-17
---

# Prompt Template Versioning

Prompt Builder templates drift because authors iterate in Setup without a change-log or rollback plan. This skill defines a three-stage lifecycle (Draft → Candidate → Active) stored as custom-metadata pointers, promoted with a signed-off checklist, and rolled back via the same CMDT.

## When to Use

Any Prompt Builder template that (a) is referenced by a production Flow/Agent or (b) has user-visible output. Not needed for ad-hoc developer experiments.

Typical trigger phrases that should route to this skill: `how do I version a prompt builder template`, `rollback a prompt in production`, `a/b test a prompt variant`, `audit which prompt was live last week`.

## Recommended Workflow

1. Create a CMDT `Prompt_Template_Binding__mdt` with fields DeveloperName, Target_Slot__c (e.g. 'SalesEmail'), Version__c, Active__c.
2. Author new prompt versions in Setup with suffixed DeveloperNames (`SalesEmail_v3`, `_v4`).
3. Update consumers (Flow/Apex/Agent) to read the DeveloperName from `Prompt_Template_Binding__mdt` at invocation — never hardcode the template name.
4. Run the fixture test set against `_v4`; record metrics (accuracy, latency, token cost) in a release note.
5. On promotion: flip Active__c on CMDT from `_v3` row to `_v4` row; on rollback, reverse. Both are deploy-validated CMDT changes — reviewable in git.

## Key Considerations

- Prompt Builder has no native version history — once you save, the old text is gone. The CMDT pointer + named versions give you git-backed history.
- Flow-referenced prompts are bound by DeveloperName; if you rename, the Flow breaks. Use the CMDT layer of indirection.
- Retest whenever the underlying model changes (model upgrades happen transparently).

## Worked Examples (see `references/examples.md`)

- *CMDT-backed template binding* — Sales email prompt updated weekly.
- *Canary rollout via user-hash bucketing* — Shipping `_v4` to 10% of reps before going full.

## Common Gotchas (see `references/gotchas.md`)

- **Setup UI 'Save' loses the prior text** — You can't compare v3 vs v4 without an external copy.
- **Model silently upgrades** — Identical prompt, different output next week.
- **Bound variable schema change** — v4 needs a new {{record.Field__c}} that doesn't exist in your sandbox.

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- Hardcoding template DeveloperName in Flow/Apex — rollback requires redeploy.
- Editing prompts in place — no diff, no rollback.
- Skipping fixture tests 'because the change is small' — prompts amplify small changes.

## Official Sources Used

- Agentforce Developer Guide — https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html
- Einstein Trust Layer — https://help.salesforce.com/s/articleView?id=sf.generative_ai_trust_layer.htm
- Invocable Actions (Apex) — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_classes_invocable_action.htm
- Agentforce Testing Center — https://help.salesforce.com/s/articleView?id=sf.agentforce_testing_center.htm
