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
version: 2.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

Use this skill when the question is not merely how to build a Flow, but how to expose that Flow safely and predictably inside Experience Cloud. The design has to account for who the user is, what the site runtime supports, and whether Flow is the right mechanism for a public or external-facing interaction at all.

Experience Cloud Flows fail in specific ways internal Flows don't: guest-user Flows touching data the Guest User profile doesn't have access to, LWR-incompatible custom components breaking silently, `$User` references resolving to unexpected values, hardcoded record IDs that only existed in sandbox. This skill catches those failure modes before they hit production.

## Before Starting

Check for `salesforce-context.md` in the project root. If present, read it first.

Gather if not available:
- Is the user anonymous, authenticated external, or an internal user visiting through the site?
- Is the site based on Aura runtime or Lightning Web Runtime (LWR), and does the flow contain custom screen components?
- Does the flow read or write Salesforce data directly, invoke Apex, or depend on assumptions about `$User`, sharing, or record visibility?
- Is this site subject to privacy / compliance requirements (GDPR, HIPAA, PCI) that affect what data the Flow can touch?
- What's the Guest User profile's object/field access set to today? (If unknown, audit BEFORE building.)

## Core Concepts

### Running User Context Changes The Safety Model

Experience Cloud flows do not run in the abstract; they run in the context of a guest or authenticated user. That means object access, field access, Apex exposure, and record visibility all need to be designed for the actual site audience rather than the admin building the Flow.

| Audience | Running user | Sharing context | Typical access |
|---|---|---|---|
| Guest (anonymous) | `Site Guest User` | Public record sharing via Sharing Sets | Minimal; "need to know" only |
| Authenticated external | The login user (Customer Community, Partner Community, etc.) | External user's role + Sharing Sets + Account-Contact sharing | Broader but scoped to their own records + shared |
| Internal user via site | The internal user (treated as internal) | Standard sharing | Full internal access |

An admin who builds the flow while logged in as System Admin sees full access. The flow deploys. The Guest User profile sees 0 records. The flow fails silently. This is the #1 Experience Cloud + Flow failure mode.

### `lightning-flow` Is A Site Integration Choice

Embedding a screen flow through `lightning-flow` is a powerful pattern for reusable guided experiences, but it comes with runtime-specific considerations. It is not just a visual embedding choice; it determines how the site launches the interview, passes variables, and handles finish behavior.

Two embedding paths:
1. **Flow component on Experience Builder page** — drag the standard Flow component onto a page; configure flow name + input variables. Simple; limited customization.
2. **Custom LWC wrapping `lightning-flow`** — build an LWC that uses `lightning-flow` with full control over input mapping, finish behavior, and surrounding page context.

### LWR Compatibility Must Be Checked Early

Experience Builder sites using Lightning Web Runtime have different capabilities from Aura-based sites. In particular, flows that depend on custom Aura or custom LWC screen components need an explicit compatibility review before `lightning-flow` is chosen as the delivery pattern.

| Custom component type | Aura site | LWR site |
|---|---|---|
| Aura screen components | ✅ | ❌ (incompatible) |
| LWC screen components (no managed packages) | ✅ | ✅ if built for both; verify `isExposed` / targets |
| Managed-package LWC screen components | ✅ | ⚠️ depends on package |
| Standard Flow screen components | ✅ | ✅ |

### Guest Flows Need Narrower Data Design

Guest users are the highest-risk audience for Flow exposure. Public flows should minimize DML, avoid unnecessary data reads, and be paired with a deliberate sharing and Apex-access review. If the business need is sensitive, forcing authentication is often the better design.

**Guest-flow hardening checklist:**
- Review Guest User profile object/field permissions.
- Audit Apex classes the flow invokes — are they Guest-accessible? Do they use `with sharing`?
- Avoid `$User.Id` references in Guest flows (guest users share the Site Guest User record).
- Avoid `$Record` in Guest flows unless the record is explicitly Guest-accessible via Sharing Set.
- Rate-limit the flow's public endpoint (Site-level throttling) to mitigate abuse.

## Common Patterns

### Pattern 1: Authenticated Member Self-Service Flow

**When to use:** Logged-in partner or customer users need guided self-service such as updating a case, submitting a request, or following a wizard.

**Structure:**
1. Expose flow on Experience Builder page visible only to authenticated users.
2. Pass minimum context variables (current User ID via `{!$User.Id}`, record ID from page context).
3. Use sharing-aware `Get Records`; validate FLS on the authenticated external user's profile.
4. Commit changes in-session with a confirmation screen.
5. Audit: can the authenticated user SEE every record the flow touches? Can they EDIT every field the flow writes?

**Why not internal Flow reuse:** Internal flows often assume access via internal roles; external users fail those assumptions.

### Pattern 2: Guest-Safe Intake Flow

**When to use:** A public site needs a narrow intake experience (lead form, support request, event registration).

**Structure:**
1. Flow minimizes DML — ideally ONE Create Records element for the intake (Lead / Case / custom object).
2. No `Get Records` on Guest-restricted data.
3. No Apex invocation unless the Apex class is explicitly Guest-accessible.
4. Treat the flow as a public endpoint: recipient fields validated, spam protection (reCAPTCHA on the page), rate limit.
5. No `$User` references.

**Why not reusing internal flow:** Leaks assumptions about `$User`, sharing, or object access.

### Pattern 3: LWC Wrapper Around A Screen Flow

**When to use:** The site needs custom finish behavior, input/output variable control, or a more tailored page experience.

**Structure:**
1. Build an LWC (let's call it `experienceFlowHost`) with `<lightning-flow>` embedded.
2. `@api` accept `recordId` / `flowApiName` etc.
3. Handle `onstatuschange` event: branch on FINISHED_SCREEN / FINISHED / ERROR.
4. Deploy the LWC as an Experience Builder component, configurable per-page.

**Why not direct Flow component:** Direct component doesn't expose the granular lifecycle events; custom wrapper gives full control over post-finish navigation and finish-screen behavior.

### Pattern 4: Flow With External Identity

**When to use:** The flow needs to know the external user's identity across Salesforce and another system.

**Structure:** Use the authenticated external user's Contact record as the bridge. Flow reads `{!$User.Contact.ExternalId__c}` (or equivalent) to correlate with the external system. Does NOT store external credentials; uses Named Credentials for external API calls.

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Public anonymous intake with minimal data needs | Guest-safe screen flow or simpler HTML form (Pattern 2) | Keep the public surface narrow |
| Authenticated partner or customer self-service | Screen flow for authenticated external users (Pattern 1) | Sharing and profile context clearer |
| LWR site + flow uses custom Aura screen components | Migrate components to LWC OR use Aura site instead | Aura screen components aren't LWR-compatible |
| Sensitive process wide data access or privileged Apex | Require authentication OR redesign | Guest exposure too risky |
| Custom finish behavior or navigation | LWC wrapper pattern (Pattern 3) | Standard component too limited |
| Identity bridging to external system | Pattern 4 + Named Credentials | Don't embed credentials in Flow |

## Review Checklist

- [ ] Site runtime and `lightning-flow` compatibility confirmed before implementation.
- [ ] Guest and authenticated user paths treated as different security models.
- [ ] Flow data access reviewed for sharing, CRUD, FLS, and Apex exposure.
- [ ] Custom screen components checked for Experience Cloud runtime support.
- [ ] Finish behavior, navigation, and resume expectations tested in the actual site.
- [ ] Team challenged whether Flow is the right public-facing surface for the use case.
- [ ] For Guest flows: audit of Guest User profile object/field permissions done.
- [ ] For Guest flows: Apex classes invoked are `with sharing` AND Guest-accessible.
- [ ] Flow tested under ACTUAL external user profile (not System Admin) in sandbox.

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the site runtime, audience type, and existing Flow requirements
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Common Patterns above; harden Guest flows per checklist
4. Validate — run the skill's checker script and verify against the Review Checklist above; test under the actual external user profile
5. Document — record any deviations from standard patterns and update the template if needed

---

## Salesforce-Specific Gotchas

1. **Guest-user flows are public endpoints** — every data lookup, Apex action, and DML path must be reviewed with that threat model in mind.
2. **`lightning-flow` on LWR sites has component limitations** — screen flows that use custom LWC or Aura components need explicit compatibility checks before choosing this pattern.
3. **Internal-flow assumptions fail quickly in Experience Cloud** — `$User`, sharing, and profile-based access behave differently for external audiences.
4. **A flow that works in Flow Builder can still fail in-site** — Experience Cloud runtime, navigation, and exposed resources must be tested in the real site container.
5. **Guest User profile has NO object access by default** — granting access is a deliberate configuration; forgetting it causes "flow works in sandbox / fails on site launch."
6. **Sharing Sets differ from Sharing Rules** — Sharing Sets grant record-level access based on the Contact's Account; Sharing Rules use criteria. Audit which one applies.
7. **Aura components in an LWR site fail at runtime, not at deploy time** — the flow passes deploy validation but throws runtime errors when the LWR site tries to render the Aura.
8. **`{!$User.Id}` in a Guest flow returns the Site Guest User ID, not the visitor** — visitors are not distinguishable without explicit session correlation (IP + cookies + form tokens).
9. **External user flows may need `RunInMode` consideration** — some Apex invocables run in user mode vs system mode; ensure the chosen mode respects the external user's boundaries.
10. **Experience Cloud cache can serve stale flows** — after publishing a flow update, site users may see the old version until CDN cache expires. Plan deploys accordingly.

## Proactive Triggers

Surface these WITHOUT being asked:

- **Internal-flow reused for Guest audience without review** → Flag as Critical. Security posture not validated.
- **Flow on LWR site with custom Aura component** → Flag as Critical. Will fail at runtime.
- **Guest flow invoking Apex class without Guest-access grant** → Flag as Critical. Access denied.
- **`{!$User.Id}` used in Guest flow expecting visitor identity** → Flag as High. Wrong semantics.
- **Public flow without rate limiting** → Flag as High. Spam/abuse risk.
- **Flow tested only as System Admin, never as external user** → Flag as High. Sandbox testing gap.
- **Hardcoded record IDs in Flow for Experience Cloud use** → Flag as Medium. Environment-brittle.
- **Flow with DML fan-out on Guest path** → Flag as High. Amplifies public-surface risk.

## Output Artifacts

| Artifact | Description |
|---|---|
| Experience Cloud flow review | Findings on runtime compatibility, user context, data-access risk |
| Exposure recommendation | Guest-safe, authenticated, or wrapper-based Flow delivery |
| Security checklist | Required access, sharing, and Apex review items before site launch |
| Guest-user profile audit | Object/field permissions the Guest profile needs + any hardening gaps |

## Related Skills

- `admin/experience-cloud-guest-access` — the guest-user security skill in detail.
- `admin/experience-cloud-member-management` — authenticated external user identity + lifecycle.
- `flow/screen-flows` — companion design skill for the interaction UX.
- `flow/fault-handling` — fault-routing matters more in public-surface flows (fail-closed).
- `lwc/lwc-in-flow-screens` — for LWC wrappers around `lightning-flow`.
- `admin/flow-for-admins` — use when the main problem is Flow design rather than Experience Cloud runtime.
