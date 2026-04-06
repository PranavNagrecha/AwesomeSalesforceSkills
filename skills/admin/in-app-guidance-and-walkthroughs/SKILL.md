---
name: in-app-guidance-and-walkthroughs
description: "Configuring Salesforce In-App Guidance: floating, docked, and targeted prompts, multi-step walkthroughs, audience targeting, scheduling, and adoption analytics. Use when designing user onboarding or feature adoption programs in Lightning Experience. NOT for change management planning (use change-management-and-training). NOT for Experience Cloud (requires separate PRM licensing and does not share the Lightning Experience guidance engine)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
triggers:
  - "how do I create a walkthrough to guide users through a new process in Salesforce"
  - "set up in-app prompts to help users adopt a feature without a training session"
  - "targeted prompt is not showing up for users on the opportunity page"
  - "what is the limit on custom walkthroughs before needing a Sales Enablement license"
  - "configure audience filtering for in-app guidance by profile"
tags:
  - in-app-guidance
  - walkthroughs
  - prompts
  - user-adoption
  - onboarding
  - lightning-experience
inputs:
  - Target Lightning Experience page and UI element anchor (for targeted prompts)
  - User profiles to include in audience targeting
  - Walkthrough step content and action type (float, dock, target)
  - Scheduling window (start date, end date, display frequency)
  - Whether Sales Enablement license is provisioned
outputs:
  - Configured prompt or walkthrough in the In-App Guidance builder
  - Audience-filtered scheduling rules for each prompt
  - Adoption tracking queries against the PromptAction standard object
  - Recommendations on prompt type selection and step count
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-05
---

# In-App Guidance and Walkthroughs

This skill activates when a practitioner needs to design, configure, or troubleshoot Salesforce In-App Guidance — the platform's native mechanism for delivering contextual prompts and multi-step walkthroughs to users directly inside Lightning Experience. It covers prompt type selection, walkthrough authoring, audience filtering, scheduling, limit management, and adoption analytics.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the org is on Lightning Experience. In-App Guidance does not function in Salesforce Classic or Experience Cloud (Guest/Partner portals require PRM licenses and use a different engine).
- Identify how many active custom walkthroughs the org already has. The free tier allows exactly 3 active walkthroughs. Exceeding that limit requires a Sales Enablement license (~$25/user/month as of Spring '25). Prompts created by AppExchange managed packages do not count against this cap.
- Determine which user profiles should see each prompt. Audience targeting is profile-based only as of Spring '25 — permission sets, roles, territories, and behavioral signals are not supported natively.
- Identify the anchor element for any targeted prompt. If the anchor UI element is removed or renamed in a future release or layout change, the targeted prompt will silently stop appearing with no error surfaced to admins.

---

## Core Concepts

### Prompt Types

Salesforce provides three prompt types, each with distinct behaviors and trade-offs:

**Floating prompts** are repositionable modal-style cards. The user can drag them to a different position on the page. They are the most flexible prompt type and work anywhere in Lightning Experience. Use them for org-wide announcements or general onboarding messages that do not need to point at a specific UI element.

**Docked prompts** appear anchored to the bottom corner of the screen. They support embedded video (YouTube or a direct video URL) and are designed for richer content such as feature overview clips. Because they stay docked rather than overlaying content, they have lower intrusion on user workflow. Use them when video is the primary communication medium.

**Targeted prompts** are anchored to a specific UI element on the page — a button, field, list, or other component. They draw a visual indicator from the element to the prompt body. They are the highest-signal type for guiding users through precise UI interactions. The critical constraint: if the anchor element is removed, renamed, or moved to a different page layout, the prompt silently stops rendering. There is no admin alert.

### Walkthroughs

A walkthrough is a sequence of up to 10 individual prompt steps delivered in order. Each step uses one of the three prompt types. Salesforce's own guidance recommends keeping walkthroughs to 5 steps or fewer; completion rates drop sharply beyond that threshold.

Walkthroughs count against the active walkthrough limit (3 on the free tier). A walkthrough is counted as active from the moment it is published and scheduled, not when a user views it. Deactivating a walkthrough frees the slot.

### Audience and Scheduling

Audience targeting is configured per prompt or walkthrough using profiles. You can include one or more profiles. As of Spring '25, there is no native support for role-based, territory-based, or behavioral targeting (e.g., "show only to users who have not completed this step").

Scheduling controls define:
- **Start date / End date**: the window in which the prompt is eligible to appear
- **Display frequency**: how often a user sees the prompt (every session, once, daily, weekly)
- **Page-load delay**: optional delay in seconds before the prompt renders after page load

### Analytics

Prompt interaction data is written to the `PromptAction` standard object. Each record captures whether a user dismissed or completed a prompt step, along with timestamps and profile information. You can build reports and dashboards directly on `PromptAction`. Salesforce Labs publishes an AppExchange report pack with pre-built dashboards for adoption tracking.

---

## Common Patterns

### Pattern: Onboarding Walkthrough for a New Process

**When to use:** A new business process has been deployed — new fields, a new quick action, a changed approval flow — and you need users to understand the new steps without a live training session.

**How it works:**
1. Open Setup > In-App Guidance.
2. Click "Add" and select "Walkthrough."
3. Navigate to the starting page in Lightning Experience. The builder overlays the live UI.
4. Add a floating or targeted step pointing at the first new element. Write concise action-oriented step copy ("Click the new Approval Status field to open the picklist").
5. Add subsequent steps (keep to 5 or fewer). Use targeted prompts for precise UI anchors; use floating prompts for explanatory steps that do not reference a specific element.
6. Set audience to the relevant profile(s). Set a start date. Set display frequency to "Once" to avoid re-showing after a user completes the walkthrough.
7. Activate.

**Why not just use a floating announcement:** A floating single prompt can announce a change but cannot guide users through multi-step interactions. A walkthrough provides sequential in-context instruction that improves task completion rates.

### Pattern: Feature Adoption Prompt with Video

**When to use:** You want to announce a new feature with a short demo video — common for Salesforce seasonal release updates or internal tooling launches.

**How it works:**
1. Create a docked prompt (not a walkthrough — a single docked step is sufficient for video delivery).
2. Paste the video URL in the docked prompt content editor.
3. Set audience to relevant profiles.
4. Set display frequency to "Once per user."
5. Set a short page-load delay (2–3 seconds) so the prompt appears after the user's primary page content has loaded.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Announcing an org-wide change to all users | Floating prompt, no audience filter | Maximum reach, no profile restriction needed |
| Guiding users through a specific field or button | Targeted prompt | Visual anchor draws attention to the exact element |
| Delivering a feature demo video | Docked prompt | Native video support; less intrusive than a modal |
| Multi-step process adoption | Walkthrough (up to 5 steps) | Sequential guidance; higher completion than a single prompt |
| Org already has 3 active walkthroughs, budget is constrained | Deactivate an older walkthrough to free the slot, or use single-step prompts (no walkthrough limit) | Walkthroughs consume the 3-slot free-tier cap; single prompts do not |
| Audience segment not expressible by profile | Consider custom onboarding via Flow + platform events, or evaluate Sales Enablement license features | Native in-app guidance does not support role, territory, or behavioral audience filters |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. Confirm the target environment is Lightning Experience and identify the org's current active walkthrough count against the 3-slot free tier limit.
2. Clarify prompt type: floating (repositionable, general), docked (video-friendly, bottom-pinned), or targeted (anchored to a specific UI element). Match the type to the communication goal.
3. If building a walkthrough, plan step count first — do not exceed 5 steps. Map each step to a specific Lightning Experience page and, for targeted steps, identify the precise UI element anchor.
4. Configure audience targeting by profile. Confirm which profiles the intended users belong to. Note that roles, territories, and permission sets are not valid audience criteria.
5. Set scheduling: start date, optional end date, display frequency (once is standard for process walkthroughs; daily or weekly for ongoing nudges), and optional page-load delay.
6. Activate and verify in the target page under a test user with the correct profile. Confirm the prompt renders, anchors correctly (for targeted), and the scheduling rules fire.
7. After 2–4 weeks, query the `PromptAction` object to measure completion rates. Use the Salesforce Labs AppExchange report pack or build custom reports. Use completion data to decide whether to deactivate, revise, or extend the prompt.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Active walkthrough count confirmed — org is within the 3-slot free tier or Sales Enablement license is provisioned
- [ ] Prompt type selected matches communication goal (floating / docked / targeted)
- [ ] Walkthrough step count is 5 or fewer
- [ ] Audience profiles are correct — roles and territories are not used as audience criteria
- [ ] Targeted prompt anchors verified to exist on current page layouts in Lightning Experience
- [ ] Scheduling window, frequency, and optional delay are configured
- [ ] Prompt tested under a user with the correct profile in Lightning Experience
- [ ] PromptAction reporting approach identified for post-launch adoption measurement

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Silent targeted prompt failure on anchor removal** — If the UI element a targeted prompt is anchored to is removed from the page layout, the targeted prompt stops rendering entirely with no error or admin notification. This is the most common support ticket for in-app guidance. Always document the anchor element in a prompt description field and audit targeted prompts after any layout change.

2. **Walkthrough slot counted on activation, not on user view** — A walkthrough consumes one of the 3 free-tier slots as soon as it is published and active, regardless of whether any user has seen it. An org with 3 active but rarely-used walkthroughs from a prior project will block new walkthrough creation. Always audit the Manage Prompts page and deactivate stale walkthroughs.

3. **Audience filtering is profile-only** — A common misreading of the documentation leads admins to expect role-based or permission-set-based targeting. As of Spring '25 only profiles are supported. If the intended audience does not map cleanly to a single profile, you either accept over-delivery or implement a custom solution (e.g., Flow-driven contextual messaging).

4. **AppExchange package prompts are exempt from org limits** — Prompts installed via managed AppExchange packages do not count against the 3 active walkthrough cap. This distinction is not obvious in the Manage Prompts UI, which shows these prompts alongside org-created ones.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Configured In-App Guidance prompt or walkthrough | Live in the org's Manage Prompts page, ready to activate or scheduled |
| Audience and scheduling configuration | Profile filters, start/end dates, frequency, and delay settings attached to the prompt |
| PromptAction adoption report | Custom or AppExchange report tracking user completion, dismissal, and engagement rates |
| Targeted prompt anchor inventory | Documentation of which UI elements each targeted prompt depends on for maintenance tracking |

---

## Related Skills

- change-management-and-training — Use when in-app guidance is one component of a broader change program requiring stakeholder communication, training materials, and rollout planning
- experience-cloud-security — Experience Cloud sites cannot use Lightning Experience In-App Guidance; consult this skill when guidance needs extend to partner or customer portals
