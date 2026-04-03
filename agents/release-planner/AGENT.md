# Release Planner Agent

## What This Agent Does

Generates structured release notes and risk assessments from a git diff, component list, or sprint summary. Flags breaking changes, sharing model impacts, and governor limit risks.

## Triggers

- "release notes"
- "sprint summary"
- "what changed this sprint"
- "generate release notes"
- "risk assessment for this release"
- User shares a git diff, component list, or PR summary

## Orchestration Plan

```
1. DETERMINE input type
   → git diff (raw or summary)
   → Component list (Apex classes, LWC, Flows, objects changed)
   → PR list (titles + descriptions)
   → Free-text sprint summary

2. READ salesforce-context.md (if present)
   → Deployment pipeline (Dev → SIT → UAT → Prod)
   → Managed package context (affects what can ship and when)
   → Known freeze windows

3. CLASSIFY each change
   → Type: New Feature / Enhancement / Bug Fix / Refactor / Config Change / Data Migration
   → Risk: Critical / High / Medium / Low
   → Audience: Internal Users / Community Users / System / Integration

4. FLAG high-risk patterns automatically
   → Use python3 scripts/search_knowledge.py to load relevant risk guidance for the changed component types
   → Use registry-backed skill discovery and skill-local validators where the changed assets match a known checker
   → Sharing model changes → Always Critical
   → Permission set / profile changes → High
   → New SOQL queries on large objects → Medium (check for indexes)
   → Trigger modifications → High (check for re-entrancy)
   → Flow deactivation/deletion → High (check for active processes using it)
   → Named credential changes → High (integration impact)
   → Custom metadata / custom settings changes → Medium
   → Batch Apex schedule changes → High

5. GENERATE release notes
   → Title + date + version
   → Executive summary (non-technical, 2-3 sentences)
   → Changes by type with risk flags
   → Deployment checklist
   → Rollback plan (if high-risk changes present)

6. PRODUCE deployment checklist
   → Pre-deployment steps
   → Deployment order (if dependencies exist)
   → Post-deployment verification steps
   → Smoke test scenarios
```

## Validation Inputs

- `python3 scripts/search_knowledge.py` for relevant release, security, and deployment guidance
- `registry/skills.json` for skill tags, outputs, and validator paths
- discovered skill-local validators for changed assets when the release includes a matching skill domain

## Risk Classification Rules

| Change Type | Default Risk | Escalation Condition |
|-------------|-------------|---------------------|
| New Apex class | Low | If queries large objects or uses async → Medium |
| Modified trigger | High | If sharing model objects involved → Critical |
| New Flow | Medium | If sends emails or modifies records in bulk → High |
| Sharing rule change | Critical | Always |
| Permission set change | High | If adds object/field access → Critical |
| New integration callout | High | If no error handling → Critical |
| Data migration | High | If > 10k records or schema change → Critical |
| Custom metadata update | Medium | If drives process logic → High |

## Output Format

```
## Release Notes — [Sprint/Version] — [Date]

**Environment:** [UAT → Prod]
**Release Type:** Standard / Emergency / Hotfix
**Overall Risk:** 🔴 Critical / 🟠 High / 🟡 Medium / 🟢 Low

---

## Executive Summary
[2-3 sentences. Non-technical. What changed and why it matters.]

---

## Changes

### 🆕 New Features
- **[Feature Name]** `[Component]` — [Description] — Risk: 🟡 Medium
  - [Why this risk level]

### 🔧 Bug Fixes
- **[Fix Name]** `[Component]` — [Description] — Risk: 🟢 Low

### ⚠️ Breaking Changes
- **[Change]** — [What breaks, what to do]

---

## Risk Flags
🔴 **[Sharing model impact]** — [Specific objects affected, specific user groups affected]
🟠 **[Governor limit risk]** — [Scenario where limit could be hit]

---

## Deployment Checklist

### Pre-Deployment
- [ ] Backup current sharing rules configuration
- [ ] Verify no scheduled jobs running during deployment window
- [ ] [Specific to this release]

### Deployment Order
1. Custom Metadata changes
2. Apex classes
3. Triggers
4. Flows (deactivate old → deploy new → activate)

### Post-Deployment Verification
- [ ] Run smoke test: [specific scenario]
- [ ] Verify [specific integration endpoint] returns 200
- [ ] Check [specific report] for data integrity

---

## Rollback Plan
[If rollback needed: specific steps, estimated time, data risk]
```

## Related Agents

- **code-reviewer**: Run before release planning to catch issues before they ship.
- **org-assessor**: Run after a major release to verify org health impact.
