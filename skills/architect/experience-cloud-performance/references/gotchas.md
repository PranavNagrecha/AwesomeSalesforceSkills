# Gotchas — Experience Cloud Performance

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: LWR HTML Document Is Cached by CDN for 60 Seconds After Publish

**What happens:** After publishing an LWR Experience Cloud site, users requesting the site in the 60-second window following the publish may receive the pre-publish HTML document from a CDN edge node. The CDN's cached copy has not yet expired. To prevent downstream cascade failures during publish, Salesforce sets the HTML response headers to `private, must-revalidate, max-age=0` — so browsers do not cache the HTML — but the CDN itself caches the document for 60 seconds at the edge.

**When it occurs:** Every time a site is published. The window is most problematic when the publish contains time-sensitive content (pricing, legal disclosures, emergency notices) or when the site has high concurrent traffic (more users will hit the stale CDN edge during the TTL window).

**How to avoid:** Build a post-publish validation procedure: wait 90 seconds after publish, then validate the live site in an incognito browser window before notifying stakeholders. For high-stakes content, schedule publishes during low-traffic periods. Document the 60-second CDN TTL in the site operations runbook so support teams have accurate expectations.

---

## Gotcha 2: JS/CSS Permission Modules Have a 5-Minute Per-User TTL — Not Immediate After Permission Change

**What happens:** On LWR sites, `@salesforce/userPermission/` and `@salesforce/customPermission/` modules are fetched as separate per-user resources with a 5-minute CDN/browser cache TTL. If an administrator assigns a permission set to a user that should unlock additional content or functionality on the site, that user may continue to see the pre-assignment state for up to 5 minutes. This is distinct from the generated framework bundles, which are immutably versioned. Permissions are short-lived cached but not instantly refreshed.

**When it occurs:** Any time a permission set is assigned or removed and the user is expected to see the change reflected immediately on the Experience Cloud site. Common in support workflows ("I've just granted you access — can you try again?") and test scenarios where a tester assigns themselves a permission and immediately checks the site.

**How to avoid:** Train support and QA teams that permission changes on LWR sites take effect within 5 minutes, not instantly. Advise users to wait 5 minutes and perform a hard refresh (Ctrl+Shift+R / Cmd+Shift+R) before re-testing. Do not ask users to log out and log in — the TTL is independent of the Salesforce session.

---

## Gotcha 3: Browser Caching in Experience Builder Is Not Enabled by Default on All Sites

**What happens:** The Experience Builder `Settings > Performance` tab contains a browser caching toggle that improves performance for returning users by allowing their browser to cache site resources for longer. This setting is not universally enabled by default on all org configurations. Teams that audit their site using browser dev tools and observe excessive re-requests for static resources often overlook this toggle as the cause, assuming CDN handles everything.

**When it occurs:** On any Experience Cloud site where the browser caching performance toggle has not been explicitly reviewed and enabled. Common on sites migrated from Community Cloud era or sites provisioned before this feature was introduced.

**How to avoid:** As part of any performance review, explicitly check `Experience Builder > Settings > Performance` and confirm the browser caching toggle is on. Enabling it requires a re-publish to take effect. Include this in the performance audit checklist for every new site provisioning.

---

## Gotcha 4: The LWR Dynamic Layer (Apex, UIA API) Is Never Served from CDN

**What happens:** Teams enable CDN on their LWR site and measure with the browser Network tab, expecting to see Apex wire call round-trips decrease in count or improve in latency. CDN has no effect on Apex wire calls or User Interface API data requests. These are authenticated, user-scoped, dynamic requests that must reach Salesforce origin servers. The CDN only accelerates the static layer: HTML documents, generated JS/CSS bundles, and static resources.

**When it occurs:** When performance optimization discussions conflate static asset delivery (CDN's domain) with data fetching latency (Apex's domain). A common scenario is after enabling CDN, the team reports "our JS loads faster but the page still feels slow" — the remaining slowness is the unfixed Apex call count.

**How to avoid:** Separate the performance problem into two distinct concerns: (1) static asset delivery — addressed by CDN; (2) data loading latency — addressed by Apex consolidation, `cacheable=true` annotations, deferred loading, and Salesforce Platform Cache. Treat these as separate optimization tracks. Never represent CDN enablement as a solution for Apex response time.

---

## Gotcha 5: Static Resources Have a 1-Day Max-Age Header — Updating a Static Resource Without Versioning Leaves Users with the Old Version

**What happens:** Salesforce static resources (`@salesforce/staticResource/`) and content assets (`@salesforce/contentAsset/`) have `max-age` cache headers set to 1 day. If a static resource is updated in Salesforce (e.g., a component library ZIP, a CSS override file, an image asset) and the resource is referenced by a stable URL without a version token, users and CDN edge nodes will continue to serve the cached old version for up to 24 hours.

**When it occurs:** When a team updates a static resource in Setup and assumes the change is immediately live. Particularly common with image assets and CSS override files that are updated to fix visual bugs or swap branding.

**How to avoid:** Reference static resources and content assets using Salesforce's version-keyed URLs where available. When updating a static resource that must take effect immediately (e.g., fixing a broken image), rename the resource (which generates a new stable URL), update all references, and republish. For content managed through Salesforce-native mechanisms, use content assets that Salesforce versions automatically. Document this behavior in the deployment runbook.
