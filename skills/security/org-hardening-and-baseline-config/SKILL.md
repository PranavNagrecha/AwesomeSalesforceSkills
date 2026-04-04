---
name: org-hardening-and-baseline-config
description: "Use when defining or reviewing baseline org hardening settings, especially Security Health Check gaps, clickjack and browser protections, CSP and CORS governance, password/session policies, network restrictions, and release-update hygiene. Triggers: 'org hardening', 'baseline security config', 'Health Check', 'CSP trusted sites', 'clickjack protection'. NOT for feature-level app permissions or record-sharing design."
category: security
salesforce-version: "Spring '25+'"
well-architected-pillars:
  - Security
  - Operational Excellence
tags:
  - org-hardening
  - security-health-check
  - csp
  - cors
  - clickjack
triggers:
  - "baseline security checklist for a Salesforce org"
  - "Health Check is green but what else should we review"
  - "clickjack CSP CORS settings in Salesforce"
  - "password session IP restriction review"
  - "critical updates and release hardening cadence"
inputs:
  - "org type and risk profile"
  - "existing hardening settings and exception history"
  - "browser, integration, and network-control requirements"
outputs:
  - "baseline hardening checklist"
  - "review findings for missing or risky org controls"
  - "operational cadence for release and security settings review"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-03-13
---

# Org Hardening And Baseline Config

Use this skill when the question is "what should every serious org have locked down before feature work keeps expanding the blast radius?" Hardening is not one setting. It is the baseline combination of browser protections, session and password controls, network policy, release-update discipline, and exception management.

---

## Before Starting

Gather this context before working on anything in this domain:

- Is this a new org baseline, an inherited production org, or a regulated environment with stricter controls?
- Which browser, mobile, integration, and network behaviors are actually required?
- Does the org already track exceptions for CSP, CORS, IP allowlists, or other trust decisions?

---

## Core Concepts

### Health Check Is A Starting Point

Security Health Check is useful, but a good score does not replace deliberate review of browser protections, session behavior, trusted sites, and release updates. Baseline hardening is broader than one score.

### Browser And Trust Controls Need Governance

CSP Trusted Sites, CORS allowlists, clickjack protections, and similar browser-facing controls should be treated as risk decisions. Every exception should have a reason and an owner.

### Session And Authentication Settings Are Baseline Security

Password policy, session timeout, login hours, IP policies, and login restrictions often matter more than teams realize because they define how much damage routine credential compromise can do.

### Release Updates Are Part Of Hardening

Critical updates and security-related release settings are operational work, not optional cleanup. Teams that never revisit them accumulate preventable risk and surprise.

---

## Common Patterns

### New-Org Baseline Checklist

**When to use:** A new org or business unit needs a repeatable security baseline.

**How it works:** Define minimum settings for browser protections, session policy, network restrictions, and security review cadence before apps proliferate.

**Why not the alternative:** Retrofitting hardening after many integrations and exceptions exist is slower and politically harder.

### Exception Register For Trusted Sites

**When to use:** The org uses CSP Trusted Sites, CORS allowlists, or similar trust exceptions.

**How it works:** Record owner, purpose, and review date for each exception instead of letting them accumulate silently.

### Quarterly Release-Hardening Review

**When to use:** The org runs continuously and wants a practical hardening cadence.

**How it works:** Review Health Check changes, critical updates, browser trust settings, and stale exceptions on a fixed operational schedule.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| New org or major environment setup | Establish baseline hardening checklist early | Easier than retrofitting later |
| Many trusted-site and allowlist exceptions exist | Create explicit exception governance | Trust sprawl is still risk |
| Team relies only on Health Check score | Expand review to browser, network, and release settings | Score alone is not the full baseline |
| Release updates are handled ad hoc | Create a recurring hardening cadence | Security posture drifts without it |

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

- [ ] Security Health Check is reviewed, but not treated as the whole baseline.
- [ ] CSP, CORS, and trusted-site exceptions are documented and owned.
- [ ] Session, password, and network restrictions reflect real policy.
- [ ] Clickjack and browser protections are reviewed deliberately.
- [ ] Critical updates and release security settings have an operating cadence.
- [ ] The org can explain why each trust exception still exists.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **A good Health Check score can hide real gaps** - browser and exception governance still matter.
2. **Trusted sites linger forever unless someone owns them** - convenience exceptions become permanent risk.
3. **Release updates are security work** - delaying them casually creates future outages and blind spots.
4. **Hardening decisions are cross-functional** - security, admins, and integration teams all affect the baseline.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Hardening checklist | Baseline control list for the org or environment |
| Security config review | Findings on browser, session, network, and release controls |
| Exception register guidance | Operational model for trusted-site and allowlist governance |

---

## Related Skills

- `security/permission-set-groups-and-muting` - use when access-bundle design is the real issue instead of baseline org controls.
- `admin/connected-apps-and-auth` - use when connected apps and integration auth are the main hardening focus.
- `security/security-health-check` - use when the question is specifically about interpreting or using Health Check itself.
