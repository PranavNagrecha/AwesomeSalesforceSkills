---
name: lwc-offline-and-mobile
description: "Use when designing or reviewing Lightning Web Components for the Salesforce mobile app, mobile device capabilities, or offline-aware behavior. Triggers: 'lightning/mobileCapabilities', 'mobile lwc', 'offline lwc', 'supported mobile app only', 'barcode scanner availability'. NOT for Mobile SDK or fully native app architecture unless the decision is whether LWC in the Salesforce mobile app is sufficient."
category: lwc
salesforce-version: "Spring '25+'"
well-architected-pillars:
  - User Experience
  - Reliability
  - Performance
triggers:
  - "how do i use lwc in the salesforce mobile app"
  - "lightning mobilecapabilities isavailable"
  - "offline behavior for lwc"
  - "barcode scanner or device api in lwc"
  - "should this be mobile sdk instead of lwc"
tags:
  - mobile-lwc
  - offline
  - mobilecapabilities
  - salesforce-mobile-app
  - device-apis
inputs:
  - "target container such as salesforce mobile app, desktop, or experience cloud"
  - "which device capabilities or offline behaviors are required"
  - "whether the component depends on apex, ui api, or local-first interaction"
outputs:
  - "mobile/offline implementation recommendation"
  - "review findings for capability checks and stale-state handling"
  - "decision on lwc in mobile app vs a different mobile architecture"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-03-13
---

Use this skill when a component is expected to behave well on phones or tablets and the team needs to be explicit about what the Salesforce mobile app can and cannot provide. Mobile capability APIs, offline expectations, and container-specific behavior all need to be designed intentionally instead of assumed from desktop LWC behavior.

## Before Starting

- Will the component run in the Salesforce mobile app, a mobile browser, Experience Cloud, or multiple containers?
- Does it need device hardware access such as camera, barcode scanning, or location, or is the main concern responsive rendering and limited connectivity?
- What must happen when the device is offline, regains connectivity, or resumes after the app was backgrounded?

## Core Concepts

### Mobile Capabilities Exist Only In Supported Mobile App Contexts

Salesforce mobile capability APIs are available only when the LWC runs in a supported mobile app on a mobile device. A component that imports a mobile capability module must still detect availability and degrade gracefully for unsupported containers.

### Offline Is A Product Design Question, Not A Checkbox

An LWC is not automatically offline-capable just because it renders in the mobile app. The team has to choose a data strategy that tolerates network loss, stale state, and reconnect behavior. Any Apex or server-dependent action should be treated skeptically until its offline story is explicit.

### Touch And Form Factor Shape The Interaction Model

Small screens, intermittent connectivity, and foreground/background transitions make a mobile component behave differently from desktop even when the code is identical. Dense tables, hover assumptions, and desktop-only interaction patterns are usually the first things to break.

### Container Choice Matters

Some requirements fit well inside the Salesforce mobile app with LWC. Others require deeper mobile platform control or a different channel strategy. Choosing between LWC in the mobile app and a more specialized mobile architecture should happen before the implementation grows around the wrong container.

## Common Patterns

### Capability-Gated Device Access

**When to use:** The component needs camera, location, barcode, or another mobile capability.

**How it works:** Detect capability availability first, then show the mobile path only in supported environments and offer a safe fallback elsewhere.

**Why not the alternative:** Assuming every device or container supports the API causes broken buttons and dead-end UX.

### Offline-Tolerant Read And Resume Pattern

**When to use:** Users may lose connectivity while viewing or collecting information.

**How it works:** Keep the UI resilient to stale data, preserve in-progress state intentionally, and refresh or reconcile when connectivity returns.

**Why not the alternative:** Desktop-style refresh assumptions produce confusing behavior after reconnect or app resume.

### Mobile-First Simplification

**When to use:** The same business task must work on desktop and mobile, but the mobile surface has less space and less tolerance for heavy UI.

**How it works:** Reduce fields, favor clear primary actions, and avoid patterns that require hover, precise pointer control, or dense grid interaction.

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need supported device APIs inside Salesforce mobile | LWC plus mobile capability modules | Best fit when the supported app container is enough |
| Must work in desktop and mobile | Capability-gated LWC with graceful fallback | Keep one component contract while respecting container differences |
| Requires reliable work with intermittent connectivity | Design an explicit offline-tolerant state model | Offline behavior will not emerge automatically |
| Needs deeper native platform control than the mobile app provides | Reconsider architecture, possibly Mobile SDK or another mobile approach | LWC in Salesforce mobile has deliberate boundaries |


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

- [ ] Mobile capability APIs are checked for availability before use.
- [ ] Unsupported containers have an intentional fallback or disabled state.
- [ ] Offline, reconnect, and app-resume behavior were designed explicitly.
- [ ] The UI fits touch interaction and smaller form factors.
- [ ] Server-dependent actions are reviewed for what happens without connectivity.
- [ ] The team verified that LWC in the Salesforce mobile app is the right container choice.

## Salesforce-Specific Gotchas

1. **Mobile capability APIs are not generally available on desktop or unsupported browsers** — the component must gate them at runtime.
2. **Offline expectations fail first at the server boundary** — Apex or other server-only actions need an explicit degraded experience.
3. **App resume can leave UI state stale** — mobile users re-enter the app after navigation and backgrounding, so refresh logic matters.
4. **A layout that is acceptable on desktop can be unusable on touch devices** — form factor and interaction design are part of the implementation, not follow-up polish.

## Output Artifacts

| Artifact | Description |
|---|---|
| Mobile/offline fit assessment | Decision on whether the LWC and container fit the mobile requirement |
| Capability review | Findings on device API checks, unsupported environments, and fallback behavior |
| Offline behavior plan | Guidance on stale-state handling, reconnect, and mobile-first interaction design |

## Related Skills

- `lwc/wire-service-patterns` — use when the core issue is data provisioning and refresh rather than mobile behavior itself.
- `lwc/lifecycle-hooks` — use when app resume, cleanup, or render timing issues dominate the bug.
- `experience/experience-cloud-headless-and-lwr` — use when the requirement may fit a different channel rather than the Salesforce mobile app.
