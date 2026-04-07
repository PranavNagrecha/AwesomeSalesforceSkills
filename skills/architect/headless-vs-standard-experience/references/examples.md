# Examples — Headless vs Standard Experience

## Example 1: Aura-to-LWR Migration for a B2B Partner Portal

**Scenario:** A manufacturing company runs a partner portal on an Aura Experience Cloud template. Page load times average 6–8 seconds on mobile. The business wants sub-3-second loads and access to new LWR-only catalog components.

**Problem:** The portal has 14 custom Aura components (account dashboards, order trackers, document upload). The team assumes they can flip a switch to move to LWR.

**Solution:**

1. Audit all 14 custom Aura components. Classify each as: (a) LWC equivalent already exists, (b) needs rewrite, or (c) uses Aura-only features (e.g., `aura:handler` event model) requiring redesign.
2. Rewrite the 9 components that are straightforward LWC ports. Redesign the 2 components with Aura event patterns to use LWC wire and custom events.
3. Verify all 3 third-party libraries (a drag-and-drop uploader, a chart library, a date picker) under LWS. The date picker uses `Function()` constructor — replace with a Salesforce-compatible alternative.
4. Build the LWR site in a sandbox, migrate pages, and test the full publish → cache-bust cycle.
5. Establish a deploy checklist that includes "Publish site" as a mandatory post-deploy step.

**Why it works:** LWR's two-layer architecture (CDN-cached static shell + dynamic data calls) drops Time to First Contentful Paint from ~7s to ~3s because the browser receives a pre-cached HTML shell from Akamai before any Salesforce data is fetched. The migration cost (component rewrites + library audit) is front-loaded, but the site is then on the supported, actively developed platform.

---

## Example 2: Greenfield Headless for a Consumer Mobile App

**Scenario:** A financial services firm wants to build a mobile app (iOS and Android) that lets customers view account summaries, submit service requests, and access a knowledge base — all data-sourced from Salesforce. The mobile development team has React Native skills but no Salesforce experience.

**Problem:** The team initially considers an LWR Experience Cloud site rendered in a WebView. After prototyping, they find that the WebView + Experience Builder model introduces layout constraints that conflict with the app's native navigation and gesture design requirements.

**Solution:**

Architecture chosen: Headless via Connected App and Apex REST.

Key decisions documented:

- **Auth**: OAuth 2.0 with PKCE for mobile native app. Connected App configured with `api` and `refresh_token` scopes.
- **Data access**: Apex REST endpoints expose account summary, case creation, and Knowledge article search. No direct SOQL from mobile.
- **CMS content**: Marketing banners and help content served via Connect REST API headless delivery channel (public channel, no auth required for CMS content).
- **CORS / CSP**: Not applicable — native mobile app, not browser-based.

The React Native team consumes these endpoints using standard HTTP calls. No Salesforce component library is used. UI is fully custom.

**Why it works:** Native mobile apps cannot render Experience Builder pages. Headless via Connected App + Apex REST is the only viable architecture when the client is a native mobile app. The Connect REST API headless delivery channel handles CMS content without per-request authentication for public content. The team stays entirely in React Native, avoiding a context switch to LWC.

---

## Anti-Pattern: Recommending LWR Without Addressing the Publish Requirement

**What practitioners do:** Recommend an LWR migration based on performance benchmarks without addressing the site publish model. Teams deploy metadata changes and expect users to see them immediately (Aura behavior).

**What goes wrong:** After migrating to LWR, the team deploys a component fix to production. Users continue seeing the broken component because the site was not published post-deploy. The team raises an incident, assuming a deployment failure. Hours are lost debugging a non-bug.

**Correct approach:** When recommending LWR, always include the publish workflow as a first-class architectural consideration. Add "Publish Site" as a mandatory step in the CI/CD pipeline. Document this in the architecture decision record. Confirm the team's release process can accommodate a publish step that may take 2–5 minutes for large sites.
