---
name: flow-governance
description: "Use when establishing operational standards for a Salesforce Flow portfolio, including naming conventions, ownership, version discipline, retirement of stale flows, and release readiness checks. Triggers: 'flow naming convention', 'too many old flows', 'who owns this flow', 'flow version governance'. NOT for element-by-element flow logic design or dedicated fault-handling review."
category: flow
salesforce-version: "Spring '25+'"
well-architected-pillars:
  - Operational Excellence
tags:
  - flow-governance
  - naming-conventions
  - version-management
  - ownership
  - flow-standards
triggers:
  - "how should we govern flows in the org"
  - "flow naming convention and ownership"
  - "too many stale flow versions"
  - "who owns this automation"
  - "flow release readiness checklist"
inputs:
  - "how many flows exist, which teams own them, and where operational confusion appears today"
  - "current naming, documentation, and activation practices"
  - "how releases, testing, and retirement decisions are currently made"
outputs:
  - "governance standard for naming, ownership, and lifecycle management"
  - "review findings for stale, weakly named, or undocumented flows"
  - "release checklist for safe activation and retirement decisions"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-03-15
---

Use this skill when the problem is no longer one flow, but the portfolio of flows in the org. Governance matters once teams start asking which flow is active, who owns it, why two versions exist, or whether a copied automation can be retired safely. Good governance turns Flow from a sprawl risk into an operable platform capability.

---

## Before Starting

Gather this context before working on anything in this domain:

- How are flows named today, and do labels, API names, descriptions, and interview labels help or confuse operators?
- Who owns activation, deactivation, and release approval for production flows?
- Which pain is most acute right now: duplicate automations, stale versions, weak documentation, or unclear support ownership?

---

## Core Concepts

Flow governance is about operational clarity. A well-built flow that nobody can identify, safely activate, or retire is still a platform liability. Naming, ownership, description quality, and version discipline are not paperwork. They are what allow admins, support teams, and delivery teams to understand the automation surface they are changing.

### Names Need To Describe Purpose, Not History

Labels like `New Flow`, `Copy of Case Process`, or `Test Version 7` tell the next maintainer almost nothing. Strong naming conventions encode domain, business purpose, and trigger type well enough that an operator can tell what the flow is for before opening it.

### Ownership Must Be Visible

Every production flow should have an accountable owner or owning team, even if several contributors edit it over time. When a failure, deployment question, or retirement opportunity appears, support should not need archaeology to find the right decision-maker.

### Version Discipline Prevents Automation Drift

Flow versions accumulate easily. Without activation standards and retirement reviews, old inactive versions and copied replacements obscure the true production path. Governance is what turns versioning from a safety feature into a manageable lifecycle.

### Documentation Should Support Operations

Descriptions, interview labels, release notes, and test intent should make logs and deployment review more understandable. Operational documentation is not a separate project from the flow. It is part of the flow's maintainability.

---

## Common Patterns

### Domain-Purpose Naming Standard

**When to use:** The org has enough flows that labels and API names are becoming ambiguous.

**How it works:** Define naming rules that include domain or object context, business purpose, and trigger style, then apply them consistently to new and revised flows.

**Why not the alternative:** Free-form naming works only until troubleshooting or retirement depends on it.

### Activation Gate With Named Owner

**When to use:** Teams frequently activate flows without clear support responsibility or regression review.

**How it works:** Require a named owner, summary of change, test evidence, and rollback approach before activation.

**Why not the alternative:** Activation becomes a low-visibility change with high operational consequences.

### Periodic Retirement Review

**When to use:** The org has many inactive copies, superseded automations, or uncertainty about what is still in use.

**How it works:** Review inventory regularly, classify flows as active, deprecated, or retireable, and remove ambiguity before the next release cycle.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| New production flow is being introduced | Apply naming, owner, description, and activation standards immediately | Governance is easiest at creation time |
| Existing portfolio has many ambiguous labels | Run a focused inventory and rename plan | Operators need a readable automation map |
| Multiple inactive copies exist and nobody knows the current path | Do a retirement review before more changes land | Flow sprawl compounds quickly |
| Teams activate flows ad hoc | Add a release gate with ownership and test evidence | Reduces support surprises |
| A flow is technically correct but poorly documented | Treat documentation as part of the fix | Operational clarity is a functional requirement |

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

- [ ] The flow label and API name describe purpose clearly.
- [ ] A support or product owner is identified.
- [ ] The flow description explains business purpose and notable dependencies.
- [ ] Activation and rollback expectations are documented.
- [ ] Superseded or duplicate flows were reviewed for retirement.
- [ ] Logs and interview labels are readable enough for support use.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Copied flows keep confusing names longer than teams expect** - naming debt compounds every time a flow is cloned instead of redesigned cleanly.
2. **Inactive versions still create cognitive load** - even when they are not live, they make support and release review harder.
3. **Interview labels matter operationally** - weak labels make logs and diagnostics harder to interpret.
4. **No visible owner means production changes stall or become risky** - governance gaps surface most clearly during incidents.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Governance standard | Naming, ownership, version, and activation rules for flows |
| Portfolio findings | Concrete risks such as generic names, missing owners, or stale copies |
| Release checklist | Minimum metadata and review expectations before activation |

---

## Related Skills

- `flow/flow-migration-from-legacy` - use when governance work is tied to retirement of old Process Builder or Workflow replacements.
- `flow/fault-handling` - use when the operational pain is primarily failure behavior rather than portfolio discipline.
- `admin/change-management-and-deployment` - use when the release process itself is the harder systems problem.
