---
name: feature-flag-custom-metadata
description: "Implement environment-safe feature flags using Custom Metadata Types for Apex, LWC, and Flow. NOT for user-level entitlements or permission sets."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "feature flag salesforce"
  - "custom metadata toggle"
  - "gradual rollout apex"
  - "kill switch feature"
tags:
  - feature-flag
  - custom-metadata
  - release
inputs:
  - "feature name"
  - "rollout criteria"
  - "consuming components"
outputs:
  - "Feature_Flag__mdt record + Apex/LWC/Flow accessor"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-17
---

# Feature Flags via Custom Metadata

Feature flags decouple deploy from release. Custom Metadata Types deploy with the codebase, are queryable from Apex/LWC/Flow without SOQL limits, and can be toggled per environment via the Metadata API or Setup UI. This skill defines a canonical Feature_Flag__mdt layout (Name, Is_Enabled__c, Percent_Rollout__c, Allowed_Users__c, Allowed_Profiles__c) plus a singleton FeatureFlags Apex accessor.

## When to Use

Every non-trivial release that needs a kill switch, a percentage rollout, or a user-population cohort. Not for permanent configuration.

Typical trigger phrases that should route to this skill: `feature flag salesforce`, `custom metadata toggle`, `gradual rollout apex`, `kill switch feature`.

## Recommended Workflow

1. Define Feature_Flag__mdt with Is_Enabled__c, Percent_Rollout__c (0-100), Allowed_Users__c (multi-select), Allowed_Profiles__c.
2. Author an Apex FeatureFlags class with isEnabled(String name) that checks CMDT + rollout hash on UserInfo.getUserId().
3. Expose a @AuraEnabled(cacheable=true) method for LWC; cache in wire service with 5-minute TTL.
4. Ship each new feature wrapped in isEnabled guard; default Is_Enabled__c=false on new CMDT record.
5. Post-release: measure, then either delete the flag (cleanup) or leave disabled (kill switch).

## Key Considerations

- Percentage rollout must be deterministic per user (hash UserId % 100) — not random — so a user's experience is stable.
- Keep flag lifetimes bounded; dead flags rot into permanent dead code.
- CMDT is cached per transaction; no SOQL limit impact.
- Don't use a custom setting for flags — CMDT deploys cleanly across sandboxes.

## Worked Examples (see `references/examples.md`)

- *Apex accessor* — New discount engine
- *LWC toggle via @wire* — New header variant

## Common Gotchas (see `references/gotchas.md`)

- **Random vs. deterministic rollout** — Users see feature flicker on/off each page load.
- **Dead flags** — Codebase accumulates 50 flags, 40 dead.
- **CMDT record shipped with Enabled=true** — Feature lights up in prod on deploy.

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- Custom Setting for flags (doesn't deploy cleanly)
- Random rollout instead of hashed
- Never deleting old flags

## Official Sources Used

- Salesforce DX Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/
- Unlocked Packaging — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_dev2gp.htm
- SF CLI — https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/
- DevOps Center — https://help.salesforce.com/s/articleView?id=sf.devops_center_overview.htm
- Scratch Org Snapshots — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_scratch_orgs_snapshots.htm
- sfdx-hardis — https://sfdx-hardis.cloudity.com/
