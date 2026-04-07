---
name: experience-cloud-performance
description: "Use when diagnosing slow Experience Cloud site load times, planning CDN and caching strategy, optimizing page weight, or advising on component loading patterns for Aura and LWR-based sites. Trigger phrases: 'Experience Cloud site loads slowly', 'CDN cache not updating after publish', 'LWR site stale after deployment', 'too many Apex calls on Experience Cloud page', 'browser caching Experience Builder', 'CDN configuration Experience Cloud', 'how to reduce page load time community site', 'Experience Cloud performance audit'. NOT for LWC component-level JavaScript performance (use lwc/lwc-performance). NOT for initial site setup (use admin/experience-cloud-site-setup). NOT for multi-site topology decisions (use architect/multi-site-architecture)."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Reliability
tags:
  - experience-cloud
  - cdn
  - caching
  - lwr
  - page-performance
  - browser-caching
  - site-speed
  - page-weight
  - apex-wire
  - performance-optimization
inputs:
  - "Experience Cloud template type: LWR (Build Your Own) or Aura"
  - "Whether a custom domain and Salesforce CDN are enabled for the site"
  - "Current site publish frequency and expected visitor traffic volume"
  - "Number and type of Apex-wired components on the highest-traffic pages"
  - "Whether browser caching is enabled in Experience Builder Performance settings"
  - "Page weight baseline (JS, CSS, image asset sizes) if available"
outputs:
  - "CDN and caching configuration guidance per template type (LWR vs Aura)"
  - "Page composition recommendations: component count, Apex wire consolidation, lazy loading"
  - "Browser caching enablement steps with experience builder location"
  - "Publish timing guidance to minimize CDN stale HTML exposure windows"
  - "Performance audit checklist for Experience Cloud sites"
triggers:
  - "Experience Cloud site loads slowly — pages take 4+ seconds to become interactive"
  - "CDN cache not updating after publish — visitors still see old content minutes after deploy"
  - "LWR site stale after deployment — how long does the CDN cache last after publish"
  - "too many Apex calls on Experience Cloud page — dashboard is slow on mobile"
  - "how to enable browser caching for Experience Cloud in Experience Builder"
  - "CDN configuration for Experience Cloud — do I need to set anything up"
  - "Experience Cloud performance audit — what should I check to improve load time"
  - "permission changes not showing on Experience Cloud site after assignment"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-07
---

Use this skill when diagnosing or improving the performance of an Experience Cloud site — including CDN configuration, HTTP caching behavior, component loading strategy, and page weight optimization. It covers both LWR and Aura-based templates, with particular depth on LWR caching semantics which differ materially from Aura. It does not cover LWC component-level JavaScript profiling or rendering loop optimization (use `lwc/lwc-performance` for that).

---

## Before Starting

Gather this context before working on anything in this domain:

- **Template type:** Confirm whether the site uses the Build Your Own (LWR) template or the classic Aura-based template. The caching model, CDN behavior, and optimization levers are meaningfully different between the two. Check `Setup > Digital Experiences > All Sites`, click the site name, and look at the template designation.
- **CDN status:** CDN is enabled by default for Experience Builder sites on custom domains starting Winter '19. Confirm whether the site uses a custom domain. If it uses the default `my.site.com` URL pattern, CDN behavior may differ. Navigate to `Setup > CDN` or check `Experience Builder > Settings > General` for CDN status.
- **Browser caching setting:** Browser caching in Experience Builder is a separately toggled performance setting. It is not enabled by default on all sites. Check `Experience Builder > Settings > Performance` for the browser caching toggle.
- **Most common wrong assumption:** Teams frequently assume that publishing a new version of a site immediately invalidates the CDN cache and all visitors see the updated content. On LWR sites, the initial HTML document is cached by the CDN for 60 seconds. For JS/CSS (permissions modules), the TTL is 5 minutes. Visitors can see a stale version for the duration of those windows after a publish.

---

## Core Concepts

### LWR Caching Architecture

LWR (Lightning Web Runtime) sites make heavy use of HTTP caching to achieve fast load times. The caching model divides site resources into distinct layers with different TTL values:

**Generated framework scripts, views, and components:**
These are generated at publish time and given immutable URLs (the URL includes a version key that changes on every publish). The browser and CDN can cache these resources for up to 150 days. Because the URL changes when the content changes, there is no cache invalidation problem here — old URLs simply become unreachable.

**HTML document (the initial page response):**
The HTML document is the entry point that references all other resources. Salesforce's first-party CDN caches the HTML document for 60 seconds. During a publish event, HTML caching is temporarily disabled to allow the new document to propagate. After the publish window closes and the 60-second TTL expires, CDN edge nodes serve the updated HTML. This means there is a window of up to 60 seconds after a publish where some visitors may receive the pre-publish HTML document.

**Permissions modules (`@salesforce/userPermission/`, `@salesforce/customPermission/`):**
These are not bundled into the HTML document. They are fetched as separate per-user resources with a 5-minute TTL. After a permission set assignment changes, a user may continue to see their old permission state for up to 5 minutes.

**Org assets and content assets (`@salesforce/staticResource/`, `@salesforce/contentAsset/`):**
These have a 1-day max-age cache header. If you update a static resource, users may see the old version for up to 24 hours unless the resource URL includes a version token.

The practical implication: LWR sites serve static content extremely efficiently through CDN, but dynamic user-specific content (permissions, user data) is short-lived or uncached. Publish-time decisions determine the structure of the static layer.

### CDN Configuration

Experience Builder sites automatically receive Salesforce CDN support starting in Winter '19. Key facts:

- CDN applies to Lightning-based Experience Builder sites on custom domains.
- CDN caches publicly cacheable resources at edge nodes close to the user's geographic location.
- No manual CDN configuration is required to enable the basic CDN layer — it activates with the custom domain.
- CDN coverage includes the HTML document (with 60s TTL as noted above), generated JS/CSS bundles (150-day TTL with URL versioning), and static resources.
- For LWR sites, the static layer (all publish-time-generated assets) is served entirely from CDN. The dynamic layer — Salesforce data API responses, Apex wire calls, record data — is served from Salesforce servers and is not CDN-cached.

To enable the CDN explicitly in Experience Builder: navigate to `Settings > General` and ensure CDN is toggled on. For orgs where the CDN toggle is not visible, CDN may be configured at the org level under `Setup > CDN`.

### Browser Caching in Experience Builder

Experience Builder includes a separate browser caching performance toggle in `Settings > Performance`. When enabled, this instructs the browser to cache site resources for longer using appropriate `Cache-Control` headers. This must be explicitly enabled — it is not on by default across all org configurations.

Browser caching reduces round trips on page revisits and navigations within the same session. Without it, the browser may re-request resources it could safely reuse. For high-traffic sites with returning users, enabling this setting provides measurable load time improvement.

### Aura vs LWR Performance Model

Aura-based Experience Cloud sites use a different runtime and have a different caching profile:

- Aura sites do not benefit from the LWR publish-time static generation model. JavaScript is evaluated at request time rather than generated into immutable bundles at publish time.
- CDN still applies to Aura-based sites for static assets but the HTML document caching behavior differs.
- Aura pages load more JS framework code per page than equivalent LWR pages. LWR delivers lighter, standard-compliant bundles.
- For performance-critical public-facing sites with high traffic volume, migrating from Aura to LWR is the most impactful architectural decision. This is a site-recreation step (templates cannot be changed on an existing site).

---

## Common Patterns

### Pattern 1: Consolidate Apex-Wired Components to Reduce Server Round-Trips

**When to use:** A high-traffic Experience Cloud page has 4+ components each making independent `@wire(apex.MyController.getX)` calls, and the page is experiencing slow time-to-interactive on low-latency connections.

**How it works:**
1. Audit the Experience Builder page for all components that make wire or imperative Apex calls. Document each Apex method called and the data it returns.
2. Identify components fetching related or overlapping data (for example, three components each fetching the current user's account data plus one fetching the user's cases).
3. Create a single Apex controller method that returns a combined result — a wrapper class or a `Map<String, Object>` — covering the consolidated data needs.
4. Refactor the page to use one "data provider" LWC that calls the consolidated controller and passes data down via `@api` properties to the child components.
5. Republish the site and validate with the browser Network panel that the number of Apex callouts on page load has dropped.

**Why not the alternative:** Multiple independent `@wire` calls each initiate separate server requests. On a mobile connection with 150ms+ latency, four independent Apex calls at page load add 600ms or more of unavoidable sequential or parallel round-trip overhead. Consolidation eliminates the per-call overhead and reduces the server-side query count.

### Pattern 2: Defer Component Loading for Below-the-Fold Content

**When to use:** A page has substantial content below the initial viewport — lists of records, dashboards, recommendation panels — that users may or may not scroll to, and these components initiate Apex calls on mount regardless of whether the user ever sees them.

**How it works:**
1. Identify below-the-fold sections of the page using Experience Builder's page structure view.
2. Wrap components in an LWC container that uses an Intersection Observer (or a simpler conditional rendering toggle in LWR) to delay initialization until the component enters the viewport.
3. For simple cases, use a boolean `isVisible` property that flips to `true` on first scroll past the fold, conditionally rendering the data-fetching component with `{#if isVisible}` (LWR template syntax) or `lwc:if` (standard LWC).
4. Validate that the initial page load completes without triggering below-the-fold Apex calls.

**Why not the alternative:** Loading all components eagerly at page load, including those the user will never reach, wastes both browser rendering budget and server-side governor limit capacity. On Experience Cloud sites serving thousands of sessions per hour, eager loading of below-the-fold Apex components amplifies server-side load unnecessarily.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| LWR site visitors see stale content after publish | Confirm CDN HTML TTL of 60s is expected; advise scheduling publishes during off-peak hours | CDN caches HTML document for up to 60s post-publish; this is normal platform behavior |
| Aura site with poor load performance — no LWR migration budgeted | Enable browser caching in Experience Builder Performance settings; consolidate Apex calls | CDN still applies but LWR static optimization is unavailable; browser caching and Apex consolidation are the available levers |
| Permission changes not reflected for users after assignment | Advise that permissions modules have a 5-minute TTL; users will see updated state within 5 minutes | Permissions modules are separately cached per-user with 5-min TTL on LWR sites |
| Static resource image updated but users see old version | Version the static resource URL or use a content asset with a new version key | Org assets have a 1-day max-age cache header; URL versioning is the only guaranteed invalidation path |
| High page component count driving slow first load | Consolidate data access into a single Apex controller; defer below-the-fold components | Each independent Apex wire call adds network round-trip latency; consolidation is the correct pattern |
| Considering LWR migration from Aura for performance | Recommend LWR for new sites; plan recreation (not in-place migration) for existing Aura sites | LWR provides superior CDN-cacheable static layer, lighter JS bundles, and 150-day asset TTL — Aura cannot match this with configuration alone |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. **Establish baseline context.** Identify the template type (LWR vs Aura), confirm custom domain and CDN status in `Settings > General`, and check whether browser caching is enabled in `Settings > Performance`. Without these three data points the right levers cannot be identified.
2. **Audit page composition.** In Experience Builder, review the high-traffic pages for component count and component types. Count distinct Apex wire calls. Identify which components load eagerly versus which could defer initialization. Document the audit results before making any changes.
3. **Configure CDN and browser caching.** If CDN is not showing as active, verify the custom domain is configured and the CDN toggle is on. Enable browser caching in Performance settings if not already enabled. These are configuration changes with no code risk.
4. **Consolidate Apex data access.** For pages with 3+ Apex-wired components, evaluate whether data can be consolidated into a single server call. Refactor using a data provider component pattern. Prioritize the pages with the highest traffic volume and the most distinct wire calls.
5. **Implement deferred loading for below-the-fold content.** Wrap heavy below-the-fold sections in conditional rendering tied to scroll position or user interaction. Validate using the browser Network tab that initial page load does not trigger their Apex calls.
6. **Validate static resource versioning.** For any static resources or content assets that are updated without URL versioning, establish a versioning convention or use Salesforce-managed content assets that receive a new URL on update.
7. **Review publish timing.** For sites with SLA-sensitive updates, advise publishing during off-peak hours to minimize the window where users may receive the 60-second-stale HTML document from the CDN. Document this constraint for the site operations runbook.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Template type confirmed (LWR or Aura) — caching behavior guidance differs between them.
- [ ] Custom domain configured and Salesforce CDN active for the site.
- [ ] Browser caching enabled in Experience Builder `Settings > Performance`.
- [ ] High-traffic pages audited for Apex wire call count; consolidation plan in place for pages with 3+ independent calls.
- [ ] Below-the-fold components deferred where possible to avoid eager Apex loading.
- [ ] Static resources and content assets on version-keyed URLs to allow cache invalidation on update.
- [ ] Publish schedule documented and aligned with off-peak windows to limit stale HTML exposure.
- [ ] For LWR sites: team understands the 60s HTML TTL and 5-minute permissions module TTL and has set expectations accordingly.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **CDN caches the LWR HTML document for 60 seconds after a publish.** Teams that publish a critical fix and immediately ask "why haven't visitors seen the update?" are hitting this window. The CDN will serve the pre-publish HTML to some users for up to 60 seconds after the publish completes. Plan publish communications accordingly.

2. **JS/CSS frameworks and component bundles on LWR are cached for up to 150 days — but URLs change on every publish.** This is intentional cache-busting design. The long TTL is safe because a new publish generates new URLs. However, if users have a very old tab open with links pointing to old versioned URLs, those requests will 404 after the old files are removed from CDN. Ensure the site handles navigation gracefully on stale tab refreshes.

3. **Browser caching is not automatically enabled on all sites.** The Experience Builder Performance settings tab contains a browser caching toggle. It is not enabled by default in all org configurations. Teams that assume browser caching is active without verifying this setting will see more re-requests than necessary and attribute the problem to CDN misconfiguration instead.

4. **Permissions modules have a 5-minute per-user TTL.** After updating a permission set assignment that should change what a user can see or do on the site, the change may not be visible for up to 5 minutes. This is expected behavior, not a bug. Instruct support and test teams to wait 5 minutes and hard-refresh before investigating permission-related issues.

5. **The LWR dynamic layer is NOT served from CDN.** Apex wire calls, `getRecord`, and other User Interface API calls hit Salesforce servers directly regardless of CDN configuration. Teams expecting CDN to cache Apex call responses and reduce server load are incorrect. CDN acceleration applies to the static layer only (HTML, JS, CSS, static resources). Dynamic data must be optimized through Apex design and Salesforce caching APIs separately.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Performance audit summary | Per-page inventory of component count, Apex call count, CDN and browser caching status, and identified optimization opportunities |
| CDN and caching configuration record | Documented state of custom domain, CDN toggle, browser caching setting, and any site-specific cache TTLs |
| Apex consolidation design | Data provider component design showing consolidated Apex controller interface, wire call reduction, and impacted components |
| Publish schedule recommendation | Off-peak publish window recommendation with rationale tied to CDN HTML TTL and site traffic patterns |

---

## Related Skills

- `lwc/lwc-performance` — use for component-level JavaScript profiling, rendering loop optimization, and LWC-specific performance tooling; this skill covers site-level architecture, not component internals
- `admin/experience-cloud-site-setup` — use for initial site creation and settings; this skill assumes a working site in need of performance improvement
- `architect/multi-site-architecture` — use when designing topology for multiple Experience Cloud sites; CDN and domain strategy overlap
- `lwc/lwr-site-development` — use for LWR-specific component development patterns and LWR template constraints
