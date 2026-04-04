---
name: custom-metadata-types
description: "Use when designing deployable Salesforce configuration with Custom Metadata Types, especially when choosing between CMTs, Custom Settings, and Custom Objects, protecting packaged defaults, or exposing config to Apex, Flow, and formulas. Triggers: 'custom metadata vs custom settings', 'deployable config', 'protected custom metadata', 'feature flags in Salesforce'. NOT for high-churn transactional data, user-managed business records, or secret storage that should live in Named Credentials."
category: admin
salesforce-version: "Spring '25+'"
well-architected-pillars:
  - Operational Excellence
  - Reliability
  - Security
tags:
  - custom-metadata-types
  - configuration
  - custom-settings
  - feature-flags
  - deployable-config
triggers:
  - "should this be custom metadata or custom settings"
  - "need deployable configuration across orgs"
  - "how do protected custom metadata records work"
  - "can flow or apex read custom metadata"
  - "feature flags in salesforce without hardcoding"
inputs:
  - "who owns the configuration values and how often they change"
  - "whether the values must move through source control, packaging, or CI/CD"
  - "whether the data needs per-user overrides, secrets, reporting, or end-user editing"
outputs:
  - "storage decision between custom metadata, custom settings, custom objects, and named credentials"
  - "configuration design for Apex, Flow, and formula consumption"
  - "review findings for unsafe or non-deployable configuration patterns"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-03-13
---

Use this skill when the org needs configuration that behaves like software, not like business data. Custom Metadata Types are the right answer when values should be versioned, deployed, packaged, and read consistently by Apex, Flow, and formulas without hardcoding environment-specific behavior.

---

## Before Starting

Gather this context before you decide on the storage model:

- Who changes the values, and how often do they change in production?
- Do the records need to travel through source control, packaging, or deployment pipelines?
- Are the values regular configuration, per-user overrides, reportable business data, or secrets such as tokens and passwords?

---

## Core Concepts

Custom Metadata Types are metadata records, not transactional rows. That distinction matters because metadata belongs in source control, deployments, and packaging workflows. If the requirement is "same logic, different environment-safe configuration," CMT is usually the best fit. If the requirement is "users update this every day and report on it," it is usually the wrong fit.

### Deployable Configuration, Not User Data

Use CMT when the value should move between sandboxes, scratch orgs, packaging orgs, and production in a controlled way. This is why routing rules, thresholds, feature toggles, and endpoint path fragments fit well. A Custom Object is better when admins or business users need to add and edit records frequently through the UI and treat the records like business data.

### CMT, Custom Settings, And Custom Objects Solve Different Problems

Hierarchy Custom Settings still matter when behavior varies by user or profile and the override must be cheap to change in production. Custom Objects fit reportable, user-managed records. CMT fits org-level or package-level configuration that should be promoted like code. The wrong decision usually comes from optimizing for today's convenience instead of the future deployment model.

### Protection And Visibility Are Packaging Concerns

Protected custom metadata is useful when a managed package needs internal defaults that subscriber admins should not read or edit. It is not a general-purpose data security boundary for the same org. If the real need is secret management, use Named Credentials or another supported secret store, not public CMT records with masked labels.

### Runtime Access Is Easy; Runtime Mutation Is Not

Apex, Flow, and formulas can read CMT records cleanly, but normal business-transaction DML is not the operating model. That is by design. CMT is meant to stabilize configuration, not to become a hidden editable database.

---

## Common Patterns

### Metadata-Driven Routing Or Threshold Rules

**When to use:** A Flow or Apex service needs environment-safe rules such as queue routing, score thresholds, or feature switches.

**How it works:** Model the rules in a CMT, query them by stable keys such as `DeveloperName`, and keep the business logic reading configuration instead of embedding IDs and values in code.

**Why not the alternative:** Hardcoded IDs, labels, or endpoints create deployment drift and sandbox-specific breakage.

### Packaged Defaults Plus Subscriber-Safe Extensions

**When to use:** A managed package needs safe defaults but also wants limited subscriber configuration.

**How it works:** Keep vendor-owned defaults protected where appropriate, expose only the fields and records that should be subscriber-editable, and separate secrets into Named Credentials.

**Why not the alternative:** Public metadata for internal defaults leaks implementation details and invites unsupported edits.

### Deliberate Migration Off Custom Settings

**When to use:** Existing org logic reads List or Hierarchy Custom Settings even though the values should really be source-controlled and deployed.

**How it works:** Inventory the settings, separate true per-user overrides from deployable org config, move the stable org config into CMT, and update Apex/Flow lookups to use metadata keys instead of record IDs.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Org-wide rules must deploy through Git and CI/CD | Custom Metadata Type | Configuration behaves like metadata and should be promoted with releases |
| Behavior varies by user or profile | Hierarchy Custom Setting | Per-user and per-profile overrides are the primary requirement |
| Admins need frequent UI editing and reporting on the records | Custom Object | The records are business data, not release-managed configuration |
| The value is a password, token, or client secret | Named Credential or supported secret store | CMT is not the right secret boundary |
| Packaged logic needs internal defaults in a managed package | Protected Custom Metadata where appropriate | Keeps package-owned config private while remaining deployable |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] The requirement is truly configuration, not business data with reporting and CRUD needs.
- [ ] The chosen storage model matches the deployment and ownership model, not just developer convenience.
- [ ] Stable keys such as `DeveloperName` are part of the lookup contract.
- [ ] No secrets, passwords, or tokens are being stored in public CMT records.
- [ ] Apex, Flow, and formulas read metadata intentionally and do not depend on environment-specific IDs.
- [ ] Any packaging visibility choice is documented, especially for protected defaults.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **CMT records are metadata, not runtime DML targets** - teams design them like editable rows and then discover the write path does not fit normal transaction logic.
2. **Protected metadata is a package boundary, not an org security model** - it helps managed-package encapsulation but does not replace proper secret handling or field security strategy.
3. **`DeveloperName` becomes part of the contract** - once code, Flow, or formulas key off metadata names, renaming records casually creates breakage.
4. **A deployable model is slower to change by design** - if operations needs hourly production edits by non-release users, the wrong storage type may have been chosen.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Configuration storage decision | Recommendation for CMT vs Custom Setting vs Custom Object vs Named Credential |
| Metadata model | Suggested type, fields, keys, and visibility model for the configuration |
| Refactor findings | Concrete issues such as hardcoded IDs, public secrets, or wrong storage fit |

---

## Related Skills

- `apex/custom-metadata-in-apex` - use when the storage decision is made and the main question is Apex access and caching patterns.
- `admin/change-management-and-deployment` - use when the release process and environment promotion model are the harder problem.
- `admin/process-automation-selection` - use when Flow or Apex design is the main decision and CMT is only one part of the solution.
