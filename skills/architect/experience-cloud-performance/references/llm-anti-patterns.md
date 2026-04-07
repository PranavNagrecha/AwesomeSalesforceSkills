# LLM Anti-Patterns — Experience Cloud Performance

Common mistakes AI coding assistants make when generating or advising on Experience Cloud performance.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Claiming CDN Caches Apex or Data API Responses

**What the LLM generates:**
```
"Enable the Salesforce CDN for your Experience Cloud site. This will cache your
Apex wire call responses at CDN edge nodes, reducing server load and improving
data loading latency for your users."
```

**Why it happens:** LLMs associate CDN with general performance improvement and over-generalize what a CDN can cache. Training data contains performance guidance that bundles CDN and Apex optimization together without clearly delineating which layer each applies to. The LLM conflates "CDN improves site performance" with "CDN caches everything."

**Correct pattern:**
```
The Salesforce CDN caches the static layer of LWR Experience Cloud sites:
HTML documents (60s TTL), generated JS/CSS bundles (150-day TTL with version URLs),
and static/content assets (1-day TTL).

CDN does not cache Apex wire call responses, User Interface API data requests,
or any authenticated user-scoped data. These requests always reach Salesforce
origin servers.

To reduce Apex call latency, use Apex consolidation (fewer @wire calls per page),
cacheable=true on read-only Apex methods, deferred loading for below-the-fold
components, and Salesforce Platform Cache for frequently-read data.
```

**Detection hint:** Any claim that CDN will "cache your data", "reduce Apex latency", or "cache API responses" should be flagged. CDN and Apex optimization are separate tracks.

---

## Anti-Pattern 2: Saying Changes Are Immediately Visible After Publish on LWR Sites

**What the LLM generates:**
```
"After publishing your LWR Experience Cloud site, your changes will be
immediately visible to all visitors."
```

**Why it happens:** LLMs often smooth over operational caveats when describing publish flows. The 60-second CDN HTML TTL is a nuanced platform behavior that is underrepresented in training data relative to the general "publish to go live" narrative. LLMs trained on earlier Experience Cloud documentation (pre-LWR or Aura-era) may also apply the Aura publish model, which does not have the same CDN HTML caching behavior.

**Correct pattern:**
```
After publishing an LWR Experience Cloud site, the CDN caches the HTML document
for up to 60 seconds. During this window, users whose requests hit the CDN edge
nodes may receive the pre-publish HTML.

Post-publish procedure:
1. Publish in Experience Builder.
2. Wait 90 seconds (60s TTL + 30s margin).
3. Validate in an incognito browser window.
4. Notify stakeholders only after validation.

For time-sensitive content, schedule publishes during off-peak hours to minimize
the number of users in the stale window.
```

**Detection hint:** Any advice that says changes are "immediately visible", "live instantly", or "visible to all users right away" after an LWR site publish should trigger a review for CDN TTL acknowledgment.

---

## Anti-Pattern 3: Advising Users to Log Out and Back In to Refresh Permissions

**What the LLM generates:**
```
"I've assigned you the permission set. To see the changes on the site, please
log out of Experience Cloud and log back in."
```

**Why it happens:** "Log out and in" is a universal troubleshooting instinct for authentication and session state issues. LLMs apply it broadly to Salesforce permission changes. However, on LWR sites, permission module caching (5-minute TTL) is independent of the user's Salesforce session. Logging out and immediately logging back in does not invalidate the permissions cache.

**Correct pattern:**
```
On LWR Experience Cloud sites, user permission modules are cached with a 5-minute TTL.
After assigning a permission set, the change takes effect within 5 minutes regardless
of session state.

Correct guidance:
1. Assign the permission set.
2. Ask the user to wait 5 minutes.
3. Ask the user to hard-refresh the page (Ctrl+Shift+R / Cmd+Shift+R).
4. The updated permission state will then be fetched.

Logging out and back in immediately after assignment does not accelerate the cache expiry.
```

**Detection hint:** Any advice recommending "log out and log in" specifically to see Experience Cloud permission changes should be reviewed for accuracy.

---

## Anti-Pattern 4: Recommending Multiple Independent @wire Calls Without Noting the Performance Impact

**What the LLM generates:**
```
// Component A
@wire(getAccountDetails, { accountId: '$recordId' })
account;

// Component B (separate LWC on the same page)
@wire(getAccountContacts, { accountId: '$recordId' })
contacts;

// Component C (separate LWC on the same page)
@wire(getAccountCases, { accountId: '$recordId' })
cases;
```
(Presented as the default pattern for a dashboard page with no mention of the performance implication of N independent wire calls.)

**Why it happens:** LLMs learn the `@wire` decorator as the standard pattern for LWC data access and correctly generate independent wire calls per component. They do not apply traffic-volume context or latency analysis that would flag N separate round-trips as a page architecture concern. The pattern is syntactically correct but architecturally suboptimal for high-traffic Experience Cloud pages.

**Correct pattern:**
```
For a dashboard page with multiple data-dependent components, consolidate
Apex calls into a single controller method using a wrapper class:

@AuraEnabled(cacheable=true)
public static DashboardData getDashboardData(Id accountId) {
    DashboardData data = new DashboardData();
    data.account = [SELECT Id, Name FROM Account WHERE Id = :accountId LIMIT 1];
    data.contacts = [SELECT Id, Name FROM Contact WHERE AccountId = :accountId];
    data.cases = [SELECT Id, Subject FROM Case WHERE AccountId = :accountId];
    return data;
}

Use a single data-provider LWC with one @wire call that passes results
to child components via @api properties. This reduces N server round-trips
to 1 and reduces SOQL query count.
```

**Detection hint:** A generated page design with 4+ independent `@wire` calls across separate components on the same page should trigger a recommendation to evaluate Apex consolidation.

---

## Anti-Pattern 5: Claiming That Enabling CDN Also Enables Browser Caching

**What the LLM generates:**
```
"To improve your Experience Cloud site's performance, enable CDN in your
Experience Builder settings. This will enable browser caching and CDN
edge caching for your site's assets."
```

**Why it happens:** LLMs often conflate CDN and browser caching as a bundled feature because they serve similar performance goals (reduce repeat asset fetching) and are often discussed together in web performance documentation. On Salesforce Experience Cloud, CDN enablement and browser caching are two separate toggles in separate settings locations.

**Correct pattern:**
```
CDN and browser caching are two separate settings in Experience Builder:

1. CDN: Experience Builder > Settings > General
   - Enables Salesforce CDN edge caching for public static resources
   - Active by default for sites on custom domains since Winter '19

2. Browser caching: Experience Builder > Settings > Performance
   - Enables browser-level caching (Cache-Control headers for returning users)
   - Must be explicitly toggled on — not automatically enabled with CDN
   - Requires a site republish to take effect

Enabling CDN does NOT automatically enable browser caching. Both should
be confirmed independently as part of a performance review.
```

**Detection hint:** Any statement that CDN "also enables browser caching", "covers browser caching", or "automatically optimizes browser caching" should be flagged.

---

## Anti-Pattern 6: Assuming Static Resource Updates Are Immediately Reflected After Save

**What the LLM generates:**
```
"Update the static resource in Setup > Static Resources, upload the new file,
and save. Your changes will be live on the Experience Cloud site immediately."
```

**Why it happens:** LLMs often describe Salesforce metadata changes as taking immediate effect because many metadata types do have near-immediate visibility. Static resource caching TTL is a less-prominent platform constraint that is frequently omitted from how-to guidance.

**Correct pattern:**
```
Salesforce static resources and content assets referenced in Experience Cloud
have max-age cache headers set to 1 day (86400 seconds) in the CDN.

After updating a static resource, users and CDN edge nodes may continue
to serve the cached old version for up to 24 hours.

To force immediate refresh:
1. Rename the static resource (generates a new URL).
2. Update all component references to use the new name.
3. Republish the site.

For content that changes frequently, use CMS content or digital asset management
tools rather than static resources to leverage Salesforce-managed versioning.
```

**Detection hint:** Any advice that static resource updates are "live immediately", "visible right away", or "take effect on save" without noting the 1-day TTL should be flagged for Experience Cloud contexts.
