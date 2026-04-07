# LLM Anti-Patterns — Experience Cloud SEO Settings

Common mistakes AI coding assistants make when generating or advising on Experience Cloud SEO configuration. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Advising SEO Validation or Debugging in Sandbox

**What the LLM generates:** "To test your SEO configuration, open your sandbox org, navigate to your site URL, and verify that sitemap.xml returns the expected pages."

**Why it happens:** LLMs treat sandbox and production as functionally equivalent environments. Training data rarely emphasizes platform features that are selectively inactive by environment.

**Correct pattern:**

```
SEO features — sitemap.xml generation, robots.txt serving, and search-engine
meta tag rendering — are only active on production Experience Cloud sites.
All SEO validation must be performed on the production org after deployment.
In sandbox, verify individual page HTML source for <title> and <meta
name="description"> tags, but do not expect sitemap.xml or robots.txt to
work correctly.
```

**Detection hint:** Any response recommending SEO validation steps that include the word "sandbox", "scratch org", or a sandbox URL (`.sandbox.my.salesforce-sites.com`, `.sandbox.my.site.com`) is suspect.

---

## Anti-Pattern 2: Omitting Topic Assignment as a Sitemap Prerequisite for Knowledge

**What the LLM generates:** "To include Knowledge articles in your sitemap, grant the guest user Read access to the Knowledge object and Knowledge Article object. Once access is granted, articles will appear in sitemap.xml."

**Why it happens:** LLMs correctly identify guest user access as a requirement but miss the additional platform constraint that Knowledge articles must also have a Topic or Data Category assignment to be included in the sitemap.

**Correct pattern:**

```
Two conditions must both be met for a Knowledge article to appear in
sitemap.xml:
1. The site's guest user profile must have Read access to the Knowledge object.
2. The article must be assigned to at least one Topic or Data Category.
Access alone is not sufficient. Articles that pass the access check but
lack a topic assignment are silently omitted from the sitemap.
```

**Detection hint:** Any response about Knowledge sitemap inclusion that does not mention Topic or Data Category assignment is likely incomplete.

---

## Anti-Pattern 3: Using Aura /s Path Prefixes for LWR Sites in robots.txt

**What the LLM generates:**

```
User-agent: *
Disallow: /s/login
Disallow: /s/search
Disallow: /s/profile
```

(Presented as a universal robots.txt template for Experience Cloud sites.)

**Why it happens:** The `/s/` prefix pattern is well-represented in Salesforce documentation and community resources for Aura-based sites. LWMs conflate Aura and LWR URL structures.

**Correct pattern:**

```
LWR sites use clean URLs without the /s prefix:
  Aura:  Disallow: /s/login
  LWR:   Disallow: /login

Always confirm the site template type (Aura vs. LWR) before writing
path-based robots.txt rules. Incorrect prefixes cause Disallow directives
to silently have no effect.
```

**Detection hint:** A robots.txt snippet that uses `/s/` paths should prompt a check: is the target site definitely Aura-based, not LWR?

---

## Anti-Pattern 4: Treating noindex as Full Crawler Exclusion

**What the LLM generates:** "To prevent search engines from accessing your login page, enable No Index in the page's SEO settings in Experience Builder."

**Why it happens:** LLMs often conflate "not indexed" with "not accessible to search engines." The distinction between crawling and indexing is subtle and often glossed over in general SEO content.

**Correct pattern:**

```
noindex suppresses indexing — it does not prevent crawling. A crawler will
still visit a noindex page, consuming crawl budget and potentially
discovering linked pages or URL patterns.

For pages that must not be crawled (login, admin tools, draft content):
- Add Disallow directives in the custom robots.txt VF page.
- noindex can be used as a belt-and-suspenders measure but must not be
  the sole protection.
```

**Detection hint:** Any recommendation to use noindex as the primary or sole method to "protect" or "hide" a page from search engines is incomplete.

---

## Anti-Pattern 5: Claiming Independent robots.txt Is Possible for Subpath-Shared Domains

**What the LLM generates:** "You can configure a separate robots.txt for each of your Experience Cloud sites by creating a `robots` Visualforce page in each site's configuration."

**Why it happens:** LLMs treat each Experience Cloud site as independently configurable without accounting for the shared-domain constraint. The platform's behavior for subpath-sharing is an edge case not prominently documented in training-representative sources.

**Correct pattern:**

```
Sites that share a custom domain via subpaths (e.g., example.com/service
and example.com/partners) resolve to a single robots.txt file. Creating
separate `robots` VF pages per site does not produce separate robots.txt
files in this topology.

To achieve independent robots.txt files, each site must have its own
subdomain (service.example.com, partners.example.com).
```

**Detection hint:** Any advice to configure per-site robots.txt for sites on the same domain base URL (where sites are distinguished by path segment, not subdomain) is incorrect.

---

## Anti-Pattern 6: Missing Sitemap Refresh After Publishing New Pages or Objects

**What the LLM generates:** "Once your site is live, the sitemap.xml is always up to date."

**Why it happens:** LLMs model sitemap.xml as a live, always-current artifact. In Experience Cloud, the sitemap regenerates on a platform-managed schedule, not instantly.

**Correct pattern:**

```
sitemap.xml in Experience Cloud regenerates on a platform-managed schedule,
typically within 24 hours of changes. There is no on-demand regeneration
button in the UI. After publishing new pages, enabling guest access to new
objects, or adding topic assignments to Knowledge articles, expect up to
24 hours before those changes are reflected in sitemap.xml.

To accelerate discovery, submit the sitemap URL directly in Google Search
Console after making significant changes.
```

**Detection hint:** Any response claiming sitemap.xml updates immediately or in real time after publishing changes is incorrect.
