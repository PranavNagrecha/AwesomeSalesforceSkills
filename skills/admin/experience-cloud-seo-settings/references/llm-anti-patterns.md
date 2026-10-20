# LLM Anti-Patterns — Experience Cloud SEO Settings

Common mistakes AI coding assistants make when generating or advising on Experience Cloud SEO configuration. These patterns help the consuming agent self-check its own output. Cites are to the Winter '27 (264) `api_meta` guide and the Summer '26 (262) Security Implementation Guide (`secguide`).

UNVERIFIED (2026-10-20): Anti-Patterns 1, 2, 4, 5 and 6 restate Help-only behaviour (environment limits, Knowledge sitemap rules, noindex, shared robots.txt, sitemap refresh timing); each is marked again inside.

## Anti-Pattern 1: Advising SEO Validation or Debugging in Sandbox

**What the LLM generates:** "To test your SEO configuration, open your sandbox org, navigate to your site URL, and verify that sitemap.xml returns the expected pages."

**Why it happens:** LLMs treat sandbox and production as functionally equivalent environments. Training data rarely emphasizes platform features that are selectively inactive by environment.

**Correct pattern:**

```
UNVERIFIED (2026-10-20): that sitemap.xml generation, robots.txt serving and meta tag rendering are
only active on production sites is Help-only.
Validate on production after deployment, and record what a sandbox actually returns instead of
assuming it. In either environment, inspect the page HTML for <title> and <meta name="description">
(set through the SEO assistant component, api_meta 264 L63443-63448).
```

**Detection hint:** Any response that asserts how sitemap.xml behaves in a sandbox, in either direction, without having observed it is suspect.

---

## Anti-Pattern 2: Treating Profile Read Access as Guest Record Access

**What the LLM generates:** "To make Knowledge articles visible to search engines, grant the guest user Read access to the Knowledge object and Knowledge Article object. Once access is granted, articles will appear in sitemap.xml."

**Why it happens:** LLMs treat a profile object permission as enough for guest record access and skip the guest sharing rule.

**Correct pattern:**

```
Guest record access comes first: guest users' org-wide defaults are Private and cannot be
changed, and a guest user sharing rule (Read Only) is the only way to grant record access to
unauthenticated guests (secguide 262 L2868-2869, L2986-2987, L3223-3225).

UNVERIFIED (2026-10-20): that a Knowledge article also needs a Topic or Data Category to appear
in sitemap.xml, and that articles without one are silently omitted, is Help-only; the corpus has no
line about sitemap generation.
```

**Detection hint:** Any response about guest visibility that mentions only the profile object permission and no guest user sharing rule is incomplete.

---

## Anti-Pattern 3: Assuming the /s Prefix From the Template Name

**What the LLM generates:**

```
User-agent: *
Disallow: /s/login
Disallow: /s/search
Disallow: /s/profile
```

(Presented as a universal robots.txt template for Experience Cloud sites.)

**Why it happens:** The `/s/` prefix pattern is well-represented in Salesforce documentation and community resources for Aura-based sites, and models conflate Aura and LWR URL structures.

**Correct pattern:**

```
The prefix comes from ExperienceBundle.urlPathPrefix: it ends in /s for authenticated LWR sites
created before Winter '23 and for Aura sites, and does not contain /s for unauthenticated LWR sites
and authenticated LWR sites created after Winter '23 (api_meta 264 L62430-62435).

Read urlPathPrefix from the retrieved bundle before writing path-based robots.txt rules.
UNVERIFIED (2026-10-20): that a wrong prefix makes Disallow lines silently have no effect is Help-only.
```

**Detection hint:** A robots.txt snippet that uses `/s/` paths should prompt a check of the site's `urlPathPrefix`.

---

## Anti-Pattern 4: Treating noindex as Full Crawler Exclusion

**What the LLM generates:** "To prevent search engines from accessing your login page, enable No Index in the page's SEO settings in Experience Builder." (UNVERIFIED 2026-10-20: the No Index setting is Help-only.)

**Why it happens:** LLMs often conflate "not indexed" with "not accessible to search engines." The distinction between crawling and indexing is subtle and often glossed over in general SEO content.

**Correct pattern:**

```
An indexing flag is not a crawl control and not an access control (general web behaviour; UNVERIFIED
2026-10-20 as a corpus statement). For pages that must not be fetched by crawlers:
- Add Disallow directives in the Visualforce page named by CustomSite.robotsTxtPage
  (api_meta 264 L49406-49407).
- Treat an indexing flag as a secondary measure, and protect sensitive data with sharing and permissions.
```

**Detection hint:** Any recommendation to use noindex as the primary or sole method to "protect" or "hide" a page from search engines is incomplete.

---

## Anti-Pattern 5: Claiming Independent robots.txt Is Possible for Subpath-Shared Domains

**What the LLM generates:** "You can configure a separate robots.txt for each of your Experience Cloud sites by creating a `robots` Visualforce page in each site's configuration." (The page name is not fixed: `CustomSite.robotsTxtPage` names it, api_meta 264 L49406-49407.)

**Why it happens:** LLMs treat each Experience Cloud site as independently configurable without accounting for the shared-domain case. UNVERIFIED (2026-10-20): the platform's behaviour for subpath-sharing is Help-only and not in the corpus.

**Correct pattern:**

```
UNVERIFIED (2026-10-20): that sites sharing a custom domain via subpaths (e.g., example.com/service
and example.com/partners) resolve to a single robots.txt file, and that independent files then need
a subdomain per site (service.example.com, partners.example.com), is Help-only.
Test what each site's path serves before promising independence either way.
```

**Detection hint:** Any advice about per-site robots.txt for sites distinguished by path segment that does not say it was tested is unverified.

---

## Anti-Pattern 6: Missing Sitemap Refresh After Publishing New Pages or Objects

**What the LLM generates:** "Once your site is live, the sitemap.xml is always up to date."

**Why it happens:** LLMs model sitemap.xml as a live, always-current artifact. UNVERIFIED (2026-10-20): that Experience Cloud regenerates the sitemap on a platform-managed schedule is Help-only.

**Correct pattern:**

```
UNVERIFIED (2026-10-20): that sitemap.xml regenerates on a platform-managed schedule, typically within
24 hours of changes, with no on-demand regeneration button, is Help-only; the corpus has no sitemap line.
After publishing new pages or enabling guest access to new objects, re-fetch the sitemap and record
how long the change took to appear. Submitting the sitemap URL in Google Search Console is general
SEO practice.
```

**Detection hint:** Any response that states a sitemap refresh time without having measured it is unverified.
