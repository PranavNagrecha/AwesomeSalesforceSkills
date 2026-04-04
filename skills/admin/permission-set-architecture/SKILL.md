---
name: permission-set-architecture
description: "Use when designing or refactoring Salesforce access architecture around minimal profiles, permission sets, permission set groups, muting, and assignment governance. Triggers: 'profile sprawl', 'permission set strategy', 'PSG architecture', 'access bundle design', 'least privilege'. NOT for record-sharing model design or CRUD/FLS enforcement inside Apex."
category: admin
salesforce-version: "Spring '25+'"
well-architected-pillars:
  - Security
  - Operational Excellence
  - Reliability
tags:
  - permission-set-architecture
  - least-privilege
  - permission-set-groups
  - profiles
  - access-governance
triggers:
  - "too many custom profiles to manage safely"
  - "how should we structure permission sets and groups"
  - "profile sprawl is making access changes risky"
  - "need a least privilege access bundle model"
  - "permission set group strategy for multiple personas"
inputs:
  - "current profile, permission-set, and permission-set-group inventory"
  - "target personas, feature bundles, and license constraints"
  - "assignment process such as manual admin work, Flow, or identity provisioning"
outputs:
  - "access architecture recommendation"
  - "review findings for profile-heavy or inconsistent access models"
  - "migration plan from profile-centric access to governed bundles"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-03-13
---

Use this skill when the problem is no longer "which permission do I grant" and has become "how should the org structure access so future changes stay safe?" The goal is to produce a layered access model that supports least privilege, lowers operational risk, and makes persona-based changes predictable.

## Before Starting

- Which user licenses are in scope, and do those licenses restrict which permissions can even be granted?
- How many custom profiles, permission sets, and permission set groups already exist, and which of them are genuinely assigned?
- Is the pain coming from feature access composition, one-off exceptions, or a sharing model problem that permission architecture cannot solve?

## Core Concepts

### Profiles Are The Base Layer, Not The Whole Architecture

Profiles still matter for baseline settings such as login hours, page layout assignment, and a minimal set of app access, but they should not carry every feature permission for every job role. When profiles become job-title snapshots, every change request turns into profile cloning, regression risk, and audit noise.

### Permission Sets Should Model Capabilities

Permission sets work best when they describe a coherent capability such as "Case Console Core", "Refund Approval", or "Quote Generation". They become difficult to govern when they are named after people, projects, or emergency exceptions. Capability-based design is what makes bundle reuse possible.

### Permission Set Groups Are The Assignment Unit

A user should rarely receive a large pile of unrelated permission sets one by one. Permission Set Groups let the architecture describe a persona or bundle as a unit. That makes onboarding, change review, and attestation easier because the assignment object has meaning.

### Muting And Exceptions Need Governance

Muting is useful when a shared bundle is almost right but slightly too broad. It is not a substitute for coherent bundle design. A good architecture limits subtractive exceptions and documents who owns them, because muted access can drift away from the intent of the base bundle if nobody reviews it.

## Common Patterns

### Baseline Plus Feature Bundles

**When to use:** Multiple business personas share a common baseline but need different feature combinations.

**How it works:** Keep profiles thin, create focused permission sets per capability, then compose job-specific bundles through permission set groups. Use naming that exposes scope and ownership.

**Why not the alternative:** One profile per persona mixes baseline setup and feature entitlements into one brittle object. Every new feature becomes a profile-change project.

### Shared Bundle With Controlled Muting

**When to use:** Several personas need the same large bundle except for a few permissions that one persona must not receive.

**How it works:** Build one reusable PSG, apply muting only for the delta, and track the business reason for the muted variant.

**Why not the alternative:** Cloning nearly identical groups or permission sets multiplies maintenance and makes audits harder.

### Migration Off Profile-Centric Access

**When to use:** The org already has many custom profiles and access changes are slow or unsafe.

**How it works:** Identify common permissions in profiles, move feature access to permission sets, introduce PSGs for recurring personas, and leave profiles as thinner baselines over time.

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| One capability must be granted to many personas | Permission Set | Capability-level reuse is cleaner than editing many profiles |
| A recurring job role needs several capability bundles together | Permission Set Group | PSGs are the right assignment and review unit |
| One persona needs slightly less than the shared bundle | Muting Permission Set in a PSG | Subtractive exception is clearer than cloning the whole bundle |
| Users see the right permissions but the wrong records | Use sharing-model skills instead | Permission architecture does not solve record visibility |
| A request is truly one-off and temporary | Time-boxed permission set assignment | Avoid distorting the core architecture for an exception |


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

- [ ] Profiles are being minimized instead of expanded for every new feature.
- [ ] Permission sets have clear capability-based names and ownership.
- [ ] Recurring access bundles are represented as PSGs rather than manual piles of assignments.
- [ ] Muting is rare, intentional, and documented.
- [ ] License boundaries and package dependencies are checked before designing bundles.
- [ ] The architecture distinguishes feature entitlements from record-sharing decisions.

## Salesforce-Specific Gotchas

1. **Permission Set Group recalculation is not instantaneous** — a changed PSG can stay in recalculation before the effective access matches the metadata update, so rollout plans must allow for propagation and validation.
2. **License fit matters before architecture elegance** — some permissions only exist for certain user licenses, so a clean bundle model still fails if it ignores license boundaries.
3. **Muting only subtracts from grouped permissions** — it never grants access and it cannot fix a poor base design that should have been split into smaller capabilities.
4. **Apex class, tab, app, and object access often drift separately** — teams sometimes move object permissions into permission sets but forget Apex class access and UI entry points, creating half-migrated bundles.

## Output Artifacts

| Artifact | Description |
|---|---|
| Access architecture review | Findings on profile sprawl, bundle reuse, muting overuse, and governance gaps |
| Persona-to-bundle matrix | Recommended baseline profile, permission sets, and PSGs per persona |
| Migration backlog | Sequenced changes for moving from profile-heavy access to governed bundles |

## Related Skills

- `security/permission-set-groups-and-muting` — use when the detailed PSG composition and muting strategy is the main question.
- `admin/permission-sets-vs-profiles` — use when the user needs the admin-level distinction and assignment basics rather than full architecture.
- `admin/sharing-and-visibility` — use when the real issue is record access, OWD, roles, or sharing rules.
