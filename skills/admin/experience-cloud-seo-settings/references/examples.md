# Examples — Experience Cloud SEO Settings

## Example 1: Configuring Dynamic SEO Properties for a Knowledge Article Detail Page

**Context:** A B2C self-service portal built on an Aura Experience Cloud template serves hundreds of Knowledge articles. The team wants each article's Google search result to show the article title and a summary snippet rather than a generic site description.

**Problem:** Without per-page SEO configuration, all Knowledge article detail pages share the same default site title and no meta description. Search engines show the site name and a crawled text excerpt, producing low click-through rates.

**Solution:**

1. In Experience Builder, navigate to the Knowledge Article Detail page.
2. Open Page Settings (gear icon) > SEO.
3. Set Title to:
   ```
   {!Record.Title} | Acme Support
   ```
4. Set Meta Description to:
   ```
   {!Record.Summary}
   ```
5. Leave No Index unchecked.
6. Verify the guest user profile has Read on the Knowledge object.
7. Open each target Knowledge article in Salesforce and confirm it has at least one Topic assigned.
8. In production, browse to a Knowledge article URL and use browser DevTools to confirm the `<title>` and `<meta name="description">` tags contain article-specific values.

**Why it works:** Experience Builder resolves merge fields in SEO properties server-side when rendering the page for a guest user (or a crawler). Each article URL gets a unique, descriptive title and meta description without any custom LWC or Apex. The Topic assignment ensures the article is included in sitemap.xml.

---

## Example 2: Custom robots.txt Blocking Login, Search, and Profile Pages

**Context:** A partner community on an LWR template sits at `https://partners.example.com`. The team wants to block crawlers from the login, search results, and user profile pages, while allowing the product catalog and knowledge base to be indexed. They also want the sitemap URL included in the robots.txt for Google Search Console.

**Problem:** Without a custom robots.txt, crawlers can and will index login and search pages, wasting crawl budget and potentially surfacing authentication pages in search results.

**Solution:**

Create a Visualforce page named exactly `robots` in the org:

```xml
<apex:page contentType="text/plain" showHeader="false" sidebar="false" standardStylesheets="false">
User-agent: *
Disallow: /login
Disallow: /secur/login.jsp
Disallow: /search
Disallow: /profile
Disallow: /register
Allow: /products
Allow: /articles
Allow: /

Sitemap: https://partners.example.com/sitemap.xml
</apex:page>
```

Note: Because this site uses the LWR template, paths do not have the `/s/` prefix. For an Aura site the same rules would read `/s/login`, `/s/search`, etc.

Associate the VF page with the site in Site.com Studio or the Sites configuration. Verify the output by browsing to `https://partners.example.com/robots.txt` in a browser.

**Why it works:** Naming the VF page `robots` and using `contentType="text/plain"` causes the platform to serve the rendered output at the `/robots.txt` path. The `Sitemap:` directive tells Google and other crawlers where to find the XML sitemap, accelerating index discovery.

---

## Anti-Pattern: Using noindex to Block Crawl-Sensitive Pages

**What practitioners do:** A practitioner sets No Index on the login and search pages via Page Settings > SEO, then concludes those pages are "protected from search engines."

**What goes wrong:** noindex only prevents indexing — crawlers still visit the page, consuming crawl budget and potentially triggering rate limits or security scanners. The login page may still appear in crawl reports, and sensitive parameter patterns (e.g., `?next=`) may be discovered by crawlers even though they are not indexed.

**Correct approach:** Use `Disallow` directives in the custom robots.txt VF page to prevent crawlers from fetching these URLs. noindex can be used additionally as a belt-and-suspenders measure, but robots.txt Disallow is the primary tool for blocking crawl access entirely.
