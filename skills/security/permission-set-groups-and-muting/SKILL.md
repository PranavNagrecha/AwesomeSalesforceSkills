---
name: permission-set-groups-and-muting
description: "Use when designing or reviewing permission-set-group architecture, especially profile minimization, group composition, muting strategy, and migration away from profile-heavy security models. Triggers: 'permission set group', 'muting permission set', 'profiles to permission sets', 'PSG architecture', 'muted permissions'. NOT for record-sharing design or CRUD/FLS review in Apex code."
category: security
salesforce-version: "Spring '25+'"
well-architected-pillars:
  - Security
  - Operational Excellence
tags:
  - permission-set-groups
  - muting
  - profiles
  - least-privilege
  - access-architecture
triggers:
  - "how should we use permission set groups"
  - "muting permission set strategy"
  - "migrate from profiles to permission sets"
  - "permission bundle architecture in Salesforce"
  - "why use PSG instead of assigning many permission sets"
inputs:
  - "current profile and permission-set model"
  - "target job functions or feature bundles"
  - "whether subtractive muting is needed"
outputs:
  - "PSG architecture recommendation"
  - "review findings for profile-heavy or unclear access design"
  - "migration pattern for permission bundle design"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-03-13
---

# Permission Set Groups And Muting

Use this skill when access design has outgrown direct profile customization and one-off permission-set assignments. Permission Set Groups let teams compose reusable access bundles, while muting lets them subtract permissions from the group evaluation when the bundle is almost right but still too broad.

---

## Before Starting

Gather this context before working on anything in this domain:

- How many profiles, permission sets, and ad hoc assignments already exist?
- Are the target access bundles feature-based, role-based, or a mix?
- Is the real problem composition, or is it record visibility and sharing instead?

---

## Core Concepts

### PSGs Are The Composition Layer

Permission Set Groups bundle compatible permission sets so access can be assigned as a meaningful unit. That reduces repeated manual combinations and makes review easier.

### Muting Subtracts From The Group Evaluation

Muting is for narrowing the effective permissions of a group when a shared bundle grants a bit too much. It is not a new permission source, and it should not become an excuse for chaotic permission-set design.

### Minimal Profiles Still Matter

Profiles do not disappear, but they should stop carrying most feature-specific access. The cleaner the base profile, the more valuable PSG composition becomes.

### Migration Is An Access-Architecture Project

Moving from profile-centric design to PSG-driven design requires naming, testing, and rollout discipline. It is not just a metadata conversion task.

---

## Common Patterns

### Feature Bundle PSG

**When to use:** Multiple users need the same collection of capabilities such as service console plus case tools.

**How it works:** Create focused permission sets per feature, then group them into one assignable PSG.

**Why not the alternative:** Repeating many direct assignments scales poorly and is harder to audit.

### Base Bundle Plus Muting

**When to use:** Two personas are almost identical except for a few restricted capabilities.

**How it works:** Reuse the same base PSG and mute only the permissions that one persona should not inherit.

### Profile-Minimization Migration

**When to use:** The org has many feature-heavy profiles and access changes are risky.

**How it works:** Move feature access into permission sets, compose PSGs, and leave profiles as thinner bases.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Many recurring permission-set combinations exist | Permission Set Groups | Better composition and assignment hygiene |
| One bundle is almost right for multiple personas | PSG plus muting | Reuse without cloning many bundles |
| Profiles still hold most feature access | Migrate toward minimal profiles plus PSGs | Better long-term governance |
| Access issue is record visibility, not granted permissions | Use sharing/security-model skills instead | PSGs do not solve sharing architecture |

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

- [ ] Profiles are being minimized instead of expanded.
- [ ] Permission sets have clear, focused purposes.
- [ ] PSGs represent meaningful bundles, not random collections.
- [ ] Muting is used intentionally and not as a cleanup tool for bad design.
- [ ] Access combinations are tested with real user personas.
- [ ] Migration and rollback are planned for profile-centric orgs.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Muting narrows effective group access, it does not grant new access** - teams misuse it when they have not designed the base bundle clearly.
2. **Profiles still exist** - a PSG strategy fails if profiles remain overloaded with feature permissions.
3. **Bundle naming becomes governance** - unclear names create access-review chaos later.
4. **Testing combinations matters** - composed access can behave differently than designers expect.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| PSG design review | Findings on composition, muting, and profile minimization |
| Access-bundle plan | Recommended permission-set and PSG structure |
| Migration outline | Phased approach for moving from profile-heavy access to PSGs |

---

## Related Skills

- `security/org-hardening-and-baseline-config` - use when baseline org controls are the concern rather than feature-access composition.
- `admin/permission-sets-vs-profiles` - use for the broader admin-side distinction between permission sets and profiles.
- `apex/apex-security-patterns` - use when code-level sharing and CRUD/FLS enforcement are the real issue.
