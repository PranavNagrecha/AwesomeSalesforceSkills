---
name: org-edition-and-feature-licensing
description: "Use when evaluating which Salesforce features are available in a given org edition, determining whether a planned solution requires an add-on license, or investigating why a feature is unavailable in the current org. Triggers: 'feature not available in our edition', 'does Enterprise include Einstein', 'Unlimited vs Performance edition differences', 'we need Flow Orchestration but do not have it', 'what license do we need for Agentforce'. NOT for user license seat count planning (use capacity-planning), NOT for AppExchange package licensing (use appexchange-management)."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Scalability
  - Reliability
triggers:
  - "feature is not available in our current Salesforce edition"
  - "does Enterprise Edition include sandbox environments or do we pay extra"
  - "what is the difference between Unlimited and Performance edition"
  - "we need Einstein Copilot but do not know if our license covers it"
  - "Flow Orchestration is not showing up in our org — which edition includes it"
  - "planning an org upgrade from Professional to Enterprise edition"
  - "which features require add-on licenses even in Unlimited edition"
tags:
  - architect
  - editions
  - licensing
  - enterprise
  - unlimited
  - performance
  - add-on
  - feature-availability
inputs:
  - "Current org edition (Professional / Enterprise / Unlimited / Performance / Developer)"
  - "Features the solution requires"
  - "Whether the org has any add-on licenses already"
outputs:
  - "Edition-to-feature availability mapping for the required features"
  - "List of add-on licenses needed for features not included in the current edition"
  - "Upgrade path recommendation if current edition cannot support the solution"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Org Edition and Feature Licensing

Use this skill when a solution design depends on features that may not be available in the org's current Salesforce edition or license tier — or when a feature is missing in production and the root cause may be edition or licensing rather than configuration.

---

## Before Starting

Gather this context before advising on edition or licensing:

- Confirm the current org edition: Setup > Company Information > Salesforce Edition.
- Check the org's add-on licenses: Setup > Company Information > Feature Licenses section.
- Know the specific feature the solution requires — feature names can be ambiguous between marketing names and platform feature names.
- Check whether the missing feature has been enabled in Setup (some features are available in the edition but not enabled by default).

---

## Core Concepts

### Salesforce Edition Hierarchy

Salesforce Sales Cloud, Service Cloud, and Platform editions follow a standard hierarchy:

| Edition | Key Characteristics |
|---|---|
| **Essentials** | Limited to 10 users; basic CRM only; no custom profiles, no Apex, no API access |
| **Professional** | Full CRM; no Apex triggers, no custom Flows (declarative automation is limited), no API by default (available as add-on), 2 sandboxes not included |
| **Enterprise** | Full platform capability; Apex, Visualforce, unlimited custom Flows, API, 1 Full sandbox + unlimited partial sandboxes; no free Agentforce/Einstein |
| **Unlimited** | Enterprise features + 24/7 support, additional storage, more sandboxes (multiple Full sandboxes included), some AI/Einstein features at no extra cost |
| **Performance** | Unlimited features + additional Einstein Activity Capture, CRM Analytics, Salesforce Anywhere; optimized for high-growth orgs |
| **Developer** | Full Enterprise-equivalent feature set for development/testing; not licensed for production use |

### Feature Licensing (Add-Ons)

Many features are not included in any base edition and require separate add-on licenses:

| Feature | Availability Without Add-On | Add-On Required |
|---|---|---|
| Agentforce (AI Agents) | Not included in any base edition | Agentforce add-on (per conversation or flat fee) |
| Einstein Copilot (Einstein for Sales/Service) | Unlimited/Performance include some Einstein features | Einstein 1 add-on for full Copilot |
| Flow Orchestration | Enterprise+ | Included in Enterprise+ (no add-on required) |
| Shield (Platform Encryption + Event Monitoring) | Not included | Salesforce Shield add-on |
| Salesforce CRM Analytics (Tableau CRM) | Not included in Enterprise; partial in Unlimited | CRM Analytics add-on |
| Salesforce Functions | Not included | Functions add-on (currently in limited availability) |
| Large Data Volumes sandbox (Full Sandbox) | 1 included in Enterprise | Additional Full sandboxes are add-ons |
| API Access | Included in Enterprise+ | Add-on required for Professional |
| Apex Triggers | Not available in Essentials/Professional | Requires Enterprise+ |

### Feature Availability vs. Feature Enablement

Some features are **available** in an edition but must be **enabled** before they can be used:

- **Flow Orchestration**: Available in Enterprise+ but must be enabled in Setup > Process Automation Settings.
- **Einstein Activity Capture**: Available in certain editions but must be enabled per user.
- **Territory Management**: Available in Enterprise+ but requires Setup > Territory Management > Enable.
- **High Velocity Sales / Sales Engagement**: Available as a feature but requires explicit enablement.

When a feature is "missing," always check whether it is an edition/licensing issue (feature not available) or an enablement issue (feature available but not turned on) before concluding that an upgrade is needed.

### Sandbox Types and Edition Inclusion

| Sandbox Type | Professional | Enterprise | Unlimited |
|---|---|---|---|
| Developer Sandbox | 10 included | 25 included | Unlimited |
| Developer Pro Sandbox | Not included | 1 included | Additional available |
| Partial Copy Sandbox | Not included | Included | Included |
| Full Sandbox | Not included | 1 included | Multiple included |

---

## Common Patterns

### Diagnosing "Feature Not Available" in a Production Org

**When to use:** A user or admin reports that a feature they expected is missing or greyed out in Setup.

**Steps:**
1. Go to Setup > Company Information > confirm Salesforce Edition.
2. Check the feature against the edition table above to determine if it is included.
3. If included in the edition, check Setup for the feature's enable toggle — many features require an explicit enable step.
4. If the feature requires an add-on, check Setup > Company Information > Feature Licenses to see if the license is allocated.
5. If the add-on is present but not assigned to the user, check User record > Permission Set License Assignments.

### Evaluating an Edition Upgrade

**When to use:** A planned solution requires features that exceed the current edition.

**Steps:**
1. List all features the solution requires.
2. Map each feature to its minimum edition or add-on requirement.
3. Determine whether the gap can be addressed by add-ons without upgrading the edition (cheaper and less disruptive), or whether a full edition upgrade is needed.
4. For Professional → Enterprise upgrades: consider all dependent changes — profile/permission set structure, sandbox availability, API access, Apex trigger enablement.
5. Account for sandbox costs in the upgrade plan — Full sandboxes are often the deciding factor for Enterprise → Unlimited upgrades.

---

## Decision Guidance

| Scenario | Recommendation |
|---|---|
| Feature is available in current edition but not showing | Check Setup for the enable toggle before concluding a license issue |
| Feature requires Enterprise, org is on Professional | Enterprise upgrade required — add-ons alone cannot add Apex to Professional |
| Need Agentforce in an Enterprise org | Add Agentforce license add-on — does not require edition upgrade |
| Need additional Full sandboxes beyond the included one | Purchase additional Full Sandbox add-ons — no edition upgrade needed |
| Need Salesforce Shield for encryption | Shield add-on required — available on Enterprise+ |
| Professional org needs API access | API Access add-on available for Professional without edition upgrade |

---

## Recommended Workflow

1. **Confirm the org edition** — Setup > Company Information > Salesforce Edition.
2. **List the required features** from the solution design — be specific about the platform feature name, not just the marketing name.
3. **Check each feature against the edition matrix** — determine if it is included, requires enablement, or requires an add-on.
4. **Check Feature Licenses in Setup** — confirm whether add-on licenses are already provisioned.
5. **Check enablement for included features** — if a feature is in the edition but missing, find its Setup enable toggle.
6. **Determine gap** — if add-ons can close the gap, recommend add-ons. If the edition is the blocker (e.g., Apex on Professional), recommend an edition upgrade.
7. **Document the licensing requirements** for the solution in the technical design so procurement and renewal teams can plan accordingly.

---

## Review Checklist

- [ ] Current org edition confirmed from Setup > Company Information
- [ ] All required features mapped to their edition or add-on requirement
- [ ] Feature Licenses section checked for existing add-ons
- [ ] Enable toggles checked for features that are included but not active
- [ ] Edition upgrade impact assessed (sandbox counts, profile limits, Apex availability)
- [ ] Licensing requirements documented in the solution design

---

## Salesforce-Specific Gotchas

1. **Marketing names and platform features are not 1:1** — "Einstein Copilot," "Agentforce," and "Einstein for Sales" are related but distinct platform components with different licensing models. Always verify the specific platform feature name against the current edition guide.
2. **Feature availability changes with each release** — Features that were add-ons in one release may be included in a base edition in a subsequent release (e.g., some Flow features moved from Enterprise-only to Professional). Always check the current edition comparison page for the active release, not a cached version.
3. **Developer Edition orgs have Enterprise-equivalent features but cannot run production workloads** — Developer Edition is not a free tier of production capability. Solutions designed on Developer Edition may reference features not available in the customer's actual edition.
4. **Permission Set Licenses (PSLs) grant feature access per user within an edition** — Some add-on features are provisioned as PSLs and must be explicitly assigned to users, even when the org-level license is active. A feature "not working" for one user but working for another is often a PSL assignment issue.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Feature availability matrix | Table mapping required features to edition requirement and current gap |
| Licensing recommendation | List of add-ons or edition upgrade required to support the solution |
| Enablement checklist | Setup steps to enable available-but-inactive features in the current edition |

---

## Related Skills

- limits-and-scalability-planning — edition-level limits (sandbox count, API request limits, storage)
- security-architecture-review — Shield, encryption, and security feature requirements
- agentforce-observability — Agentforce-specific licensing and feature availability
