---
name: flow-for-experience-cloud
description: "Use when embedding or exposing Salesforce Flows in Experience Cloud, especially for guest or external users, `lightning-flow` usage, site runtime differences, and data-access safety. Triggers: 'flow in experience cloud', 'guest user flow', 'lightning-flow on community page', 'external user flow access', 'LWR flow limitations'. NOT for general Experience Cloud sharing architecture when Flow is not part of the problem."
category: flow
salesforce-version: "Spring '25+'"
well-architected-pillars:
  - User Experience
  - Security
  - Reliability
triggers:
  - "how do i show a flow on an experience cloud page"
  - "guest user flow cannot access data"
  - "lightning-flow lwr custom component limitation"
  - "screen flow for external users"
  - "experience cloud flow running user context"
tags:
  - experience-cloud
  - lightning-flow
  - guest-user
  - external-users
  - screen-flow
inputs:
  - "whether the audience is guest, authenticated external, or internal"
  - "site runtime such as Aura-based site or LWR site"
  - "whether the flow contains custom lwc or aura screen components"
outputs:
  - "experience-cloud flow design recommendation"
  - "security and runtime review findings"
  - "decision on guest-safe flow exposure and site compatibility"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-03-13
---

Use this skill when the question is not merely how to build a Flow, but how to expose that Flow safely and predictably inside Experience Cloud. The design has to account for who the user is, what the site runtime supports, and whether Flow is the right mechanism for a public or external-facing interaction at all.

## Before Starting

- Is the user anonymous, authenticated external, or an internal user visiting through the site?
- Is the site based on Aura runtime or Lightning Web Runtime, and does the flow contain custom screen components?
- Does the flow read or write Salesforce data directly, invoke Apex, or depend on assumptions about `$User`, sharing, or record visibility?

## Core Concepts

### Running User Context Changes The Safety Model

Experience Cloud flows do not run in the abstract; they run in the context of a guest or authenticated user. That means object access, field access, Apex exposure, and record visibility all need to be designed for the actual site audience rather than the admin building the Flow.

### `lightning-flow` Is A Site Integration Choice

Embedding a screen flow through `lightning-flow` is a powerful pattern for reusable guided experiences, but it comes with runtime-specific considerations. It is not just a visual embedding choice; it determines how the site launches the interview, passes variables, and handles finish behavior.

### LWR Compatibility Must Be Checked Early

Experience Builder sites using Lightning Web Runtime have different capabilities from Aura-based sites. In particular, flows that depend on custom Aura or custom LWC screen components need an explicit compatibility review before `lightning-flow` is chosen as the delivery pattern.

### Guest Flows Need Narrower Data Design

Guest users are the highest-risk audience for Flow exposure. Public flows should minimize DML, avoid unnecessary data reads, and be paired with a deliberate sharing and Apex-access review. If the business need is sensitive, forcing authentication is often the better design.

## Common Patterns

### Authenticated Member Self-Service Flow

**When to use:** Logged-in partner or customer users need guided self-service such as updating a case, submitting a request, or following a wizard.

**How it works:** Expose the flow on a page where authenticated users already have the necessary access, pass only the minimum context variables, and validate sharing-safe data access.

**Why not the alternative:** Public exposure would widen the attack surface for no business value.

### Guest-Safe Intake Flow

**When to use:** A public site needs a narrow intake experience such as a lead form or support request capture.

**How it works:** Keep the flow minimal, avoid broad record lookups, tightly review any Apex or DML, and treat the flow as a public endpoint.

**Why not the alternative:** Reusing an internal flow usually leaks assumptions about `$User`, sharing, or object access.

### LWC Wrapper Around A Screen Flow

**When to use:** The site needs custom finish behavior, input/output variable control, or a more tailored page experience.

**How it works:** Use `lightning-flow` inside an LWC wrapper and design the site page around that wrapper rather than dropping the flow directly on the page.

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Public anonymous intake with minimal data needs | Guest-safe screen flow or simpler form pattern | Keep the public surface narrow |
| Authenticated partner or customer self-service | Screen flow for authenticated external users | Sharing and profile context are clearer |
| LWR site and flow uses custom screen LWCs or Aura components | Reassess the embedding pattern early | `lightning-flow` on LWR has important component limitations |
| Sensitive process depends on wide data access or privileged Apex | Require authentication or redesign | Guest exposure is too risky |


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

- [ ] The site runtime and `lightning-flow` compatibility were confirmed before implementation.
- [ ] Guest and authenticated user paths are treated as different security models.
- [ ] Flow data access was reviewed for sharing, CRUD, FLS, and Apex exposure.
- [ ] Custom screen components were checked for Experience Cloud runtime support.
- [ ] Finish behavior, navigation, and resume expectations were tested in the actual site.
- [ ] The team challenged whether Flow is the right public-facing surface for the use case.

## Salesforce-Specific Gotchas

1. **Guest-user flows are public endpoints** — every data lookup, Apex action, and DML path must be reviewed with that threat model in mind.
2. **`lightning-flow` on LWR sites has component limitations** — screen flows that use custom LWC or Aura components need explicit compatibility checks before choosing this pattern.
3. **Internal-flow assumptions fail quickly in Experience Cloud** — `$User`, sharing, and profile-based access behave differently for external audiences.
4. **A flow that works in Flow Builder can still fail in-site** — Experience Cloud runtime, navigation, and exposed resources must be tested in the real site container.

## Output Artifacts

| Artifact | Description |
|---|---|
| Experience Cloud flow review | Findings on runtime compatibility, user context, and data-access risk |
| Exposure recommendation | Guidance on guest-safe, authenticated, or wrapper-based Flow delivery |
| Security checklist | Required access, sharing, and Apex review items before site launch |

## Related Skills

- `experience/guest-user-security` — use when the core risk is public-site access design beyond Flow itself.
- `lwc/lifecycle-hooks` — use when the wrapper component around `lightning-flow` has LWC lifecycle issues.
- `admin/flow-for-admins` — use when the main problem is Flow design rather than Experience Cloud runtime.
