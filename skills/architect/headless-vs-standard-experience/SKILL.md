---
name: headless-vs-standard-experience
description: "Use when choosing between Headless, LWR (Lightning Web Runtime), or Aura as the Experience Cloud frontend architecture: performance tradeoffs, developer cost, migration readiness, and flexibility. Trigger keywords: headless vs LWR, LWR vs Aura, Experience Cloud architecture decision, site performance architecture, community site technology choice. NOT for implementing a chosen architecture, NOT for Experience Builder component development, NOT for CMS headless content delivery via Connect REST API."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Operational Excellence
  - Security
triggers:
  - "should we use headless or LWR for our Experience Cloud portal?"
  - "what is the difference between Aura and LWR for community sites?"
  - "our site is slow — should we migrate from Aura to LWR?"
  - "we need full UI control, should we go headless instead of Experience Builder?"
  - "how do LWR performance benefits compare to the migration cost?"
  - "which Experience Cloud architecture fits our team's React skills?"
tags:
  - experience-cloud
  - lwr
  - aura
  - headless
  - architecture-decision
  - performance
  - digital-experience
inputs:
  - Current site engine (Aura, LWR, or none yet)
  - Team's frontend skills (LWC, React/Vue/Angular, or Salesforce admin)
  - Performance requirements and target audience (authenticated vs public)
  - Degree of UI customization required
  - Existing Aura component library size if migrating
  - Timeline and budget constraints
outputs:
  - Architecture decision recommendation (Aura / LWR / Headless) with rationale
  - Decision matrix comparing all three options against project requirements
  - Migration readiness assessment if moving from Aura to LWR
  - Risk summary for the chosen approach
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-07
---

# Headless vs Standard Experience Architecture Decision

Use this skill when choosing the frontend architecture tier for an Experience Cloud digital experience — specifically deciding between Aura (legacy standard template), LWR (Lightning Web Runtime — the modern standard template), or a fully Headless frontend (custom app consuming Salesforce APIs). This skill produces a recommendation and decision matrix. It does not cover how to implement the chosen architecture.

---

## Before Starting

Gather this context before advising on architecture:

- **Current engine** — Is there an existing site (Aura or LWR) to migrate, or is this greenfield? Migration from Aura to LWR requires auditing every custom Aura component because LWR cannot render Aura components at all.
- **Team composition** — LWR requires LWC knowledge. Headless requires full-stack web development expertise (React, Vue, or equivalent) plus Salesforce API experience. Aura can be maintained by Salesforce-experienced admins and developers.
- **Performance baseline** — LWR sites load approximately 50% faster than Aura sites because of its two-layer architecture (static CDN-cached shell + dynamic data calls). If performance is not a primary driver, the migration cost may not be justified.
- **Component inventory** — Any Aura components used on an existing site must be rewritten as LWC before migrating to LWR. There is no compatibility shim.
- **Republish model** — LWR sites require an explicit site publish action before any component or theme change is visible to end users. This is a significant operational difference from Aura, which reflects some changes without republish.

---

## Core Concepts

### Aura Template

Aura is the original Experience Cloud site engine, built on the Aura component framework. It is fully supported but no longer receiving performance or feature investment. Sites run under Lightning Locker Service, which provides component isolation via JavaScript sandboxing. Aura supports both Aura components and LWC components on the same page. It is the appropriate choice only when: (a) an existing Aura site is not yet ready to migrate, or (b) a specific Aura-only feature (such as Visualforce-based custom login pages) is required.

Aura sites deliver the full application bundle on first load. They have more browser-level overhead than LWR because the Aura framework itself is larger, and Locker Service adds runtime cost.

### LWR Template (Lightning Web Runtime)

LWR is the modern Experience Builder template engine introduced in Winter '22. Its architecture splits the site into two layers:

1. **Static layer** — HTML shell, CSS, and JavaScript chunks served from Salesforce's CDN (Akamai). These assets are cached at the edge and served with low latency globally.
2. **Dynamic layer** — Data calls made from the browser to Salesforce APIs (Connect REST, Apex, Wire adapters) after the shell loads.

This split produces approximately 50% faster Time to First Contentful Paint compared to Aura, because the browser gets a cached static shell immediately and only then fetches live data.

LWR uses **Lightning Web Security (LWS)** instead of Locker Service. LWS enforces namespace isolation at the module level rather than wrapping every API call at runtime, which reduces overhead. However, LWS behaves differently from Locker Service in some edge cases — third-party libraries that worked under Locker may fail under LWS.

**Key constraint**: LWR supports **only LWC components**. Existing Aura components will not render on an LWR site and must be rewritten. This is the primary migration cost driver.

**Key operational difference**: Every content, component, or theme change to an LWR site requires an explicit **Publish** action in Experience Builder before it is visible to site visitors. Changes saved but not published are invisible to end users.

### Headless (Fully Custom Frontend)

Headless Experience Cloud means building a completely custom frontend application — typically in React, Vue, or a mobile framework — that communicates with Salesforce exclusively via APIs:

- **Connect REST API** for CMS content, community data, and catalog
- **Experience Cloud API** (part of Connect REST) for site-specific operations
- **Apex REST / GraphQL** for custom data
- **OAuth 2.0 Connected App** for authentication

Headless gives complete UI freedom: any design system, any rendering framework, any hosting provider (Vercel, Netlify, AWS). There is no dependency on Experience Builder, LWR, or Aura at all.

The cost is substantial: the team must build and maintain the entire frontend, handle authentication flows, manage CSP/CORS, and keep the custom app in sync with org changes. There is no drag-and-drop Experience Builder support and no access to standard Experience Builder components.

Headless is appropriate when the UX requirements genuinely cannot be met within Experience Builder constraints (LWR or Aura), or when the team is a full-stack product team with no Salesforce-specific skills.

---

## Common Patterns

### Aura-to-LWR Migration

**When to use:** An existing Aura site has performance issues or the business needs capabilities only available on LWR templates (e.g., new LWR-only standard components).

**How it works:**
1. Audit all custom Aura components on the current site — these must all be rewritten as LWC.
2. Audit third-party libraries for LWS compatibility (Locker-era workarounds may break).
3. Build a parallel LWR site and migrate pages incrementally.
4. Test Publish → verify → repeat. Do not go live without verifying the publish workflow.
5. Decommission the Aura site only after full validation.

**Why not stay on Aura:** Aura is in maintenance mode. New Experience Cloud features (enhanced CMS, LWR-only templates, improved search) are LWR-only. Performance deficit compounds over time as expectations rise.

### LWR Greenfield

**When to use:** Net-new Experience Cloud site where the team has LWC skills and standard Experience Builder capabilities are sufficient.

**How it works:** Select an LWR template (Enhanced LWR or a vertical template). Build pages and components as LWC. Establish a CI/CD-aware publish workflow — every deployment must include a site publish step, or changes will not reach users.

**Why not headless:** LWR covers the vast majority of B2B and B2C portal use cases with far less development overhead than a fully custom frontend.

### Headless with Connected App

**When to use:** The product team needs complete design freedom (custom animation, non-standard navigation, mobile-first PWA) that cannot be achieved within Experience Builder constraints.

**How it works:** Provision a Connected App with the required OAuth scopes. Expose data via Apex REST or GraphQL. Build the frontend as a standalone app. Host outside Salesforce (external CDN or cloud). Use the Connect REST API for community data.

**Why not LWR:** LWR's Experience Builder layout system has constraints on page structure, navigation patterns, and component composition that cannot be overridden. If the design system or UX pattern is fundamentally incompatible, headless is the only option.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Existing Aura site, no major custom components, performance matters | Migrate to LWR | Low migration cost; ~50% performance gain from CDN-cached static layer |
| Existing Aura site, large custom Aura component library | Evaluate LWR migration cost vs. staying on Aura | Each Aura component requires a full LWC rewrite before migration |
| Greenfield site, LWC-skilled team, standard portal UX | LWR | Fastest path to performant site with full Experience Builder tooling |
| Greenfield site, admin-led, minimal custom code | Aura or LWR | Either works; LWR preferred for performance. Aura acceptable if team has no LWC skills |
| Unique UX requirements incompatible with Experience Builder | Headless | Complete UI freedom; highest dev cost; requires full-stack web expertise |
| Mobile app needing Salesforce community data | Headless | Native mobile apps cannot use Experience Builder; use Connect REST API |
| Team is React/Vue-only with no LWC skills | Headless (if justified) | LWR requires LWC; headless lets the team stay in their stack — only if UX demands justify cost |
| Need to use existing Aura components on new LWR site | Not possible | Aura components do not render on LWR; must rewrite as LWC first |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this architecture decision:

1. **Establish current state** — Confirm whether there is an existing site and what engine it uses. If migrating, catalog all custom Aura components (count and complexity). This single factor most heavily determines migration cost to LWR.
2. **Assess team skills** — Map the team's capabilities to each option: Aura/LWC skills enable LWR; full-stack web skills enable headless; admin skills favor staying on Aura or a simple LWR migration.
3. **Evaluate UX requirements** — Determine whether the required UX can be delivered within Experience Builder's layout and component model. If standard portals, catalogs, or community sites are the goal, LWR is almost always sufficient. If the design demands complete layout freedom or is a native mobile app, headless is warranted.
4. **Score against the decision matrix** — Apply the decision table from the Decision Guidance section. Flag any hard blockers (e.g., existing Aura components = LWR migration requires rewrite; no LWC skills = LWR is higher cost).
5. **Quantify migration cost** — For Aura-to-LWR migrations, count Aura components that need rewriting. Estimate effort per component. Compare against the performance and feature benefits of LWR.
6. **Produce the recommendation** — State the recommended architecture tier (Aura / LWR / Headless), the primary rationale, the top risks, and what must be true for the recommendation to hold. Use the template in `templates/headless-vs-standard-experience-template.md`.
7. **Document the publish workflow requirement** — If recommending LWR, explicitly note that a site publish is required for every component or content change to reach users. This must be incorporated into the team's deployment process.

---

## Review Checklist

Run through these before marking the architecture decision complete:

- [ ] Existing Aura component inventory completed (if migration scenario)
- [ ] Team LWC and frontend skills assessed and documented
- [ ] UX requirements explicitly evaluated against Experience Builder constraints
- [ ] LWR publish-on-change workflow acknowledged and planned for
- [ ] LWS vs Locker Service compatibility verified for any third-party libraries
- [ ] Decision matrix filled in with project-specific scores
- [ ] Recommendation includes rationale, risks, and conditions that would change it

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **LWR requires explicit Publish before changes reach users** — Unlike Aura, saving a page or component change in Experience Builder on an LWR site does not update what end users see. The Publish action must be explicitly triggered. This catches teams who expect Aura-like behavior. A CI/CD pipeline that deploys metadata but skips the publish step will leave the live site stale.
2. **Aura components do not render on LWR sites** — There is no compatibility layer or wrapper that allows Aura components to run on an LWR template. Every Aura component used on a site must be rewritten as an LWC before an Aura-to-LWR migration is feasible. Underestimating this is the most common cause of failed or abandoned LWR migrations.
3. **LWS behaves differently from Locker Service for third-party libraries** — Libraries that worked under Aura's Locker Service (which wrapped DOM APIs at runtime) may fail under LWR's Lightning Web Security (which enforces isolation at module import time). Libraries using `eval()`, `Function()`, or direct prototype manipulation are most at risk. Test all third-party dependencies before committing to LWR.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Architecture decision recommendation | Written recommendation stating chosen tier, rationale, risks, and conditions |
| Decision matrix | Table comparing Aura / LWR / Headless against project requirements |
| Migration readiness assessment | For Aura-to-LWR: component inventory, rewrite effort estimate, LWS compatibility check |

---

## Related Skills

- `admin/experience-cloud-site-setup` — Use after this decision skill to configure the chosen site engine
- `lwc/headless-experience-cloud` — Use for headless CMS content delivery via Connect REST API (a distinct headless pattern)
- `lwc/experience-cloud-authentication` — Authentication flows differ between Aura, LWR, and headless; consult after architecture is chosen
