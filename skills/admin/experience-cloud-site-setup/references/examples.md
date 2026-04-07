# Examples — Experience Cloud Site Setup

## Example 1: Customer Self-Service Portal Using Build Your Own (LWR)

**Context:** A B2C company wants a branded customer portal where authenticated users can view their orders, submit support cases, and access a knowledge base. All custom components are built in LWC. Performance at scale (50,000+ monthly sessions) is a stated requirement.

**Problem:** Without clear template guidance, a practitioner might default to the legacy Aura Build Your Own template out of familiarity, losing HTTP caching benefits and ending up with Aura-specific URL patterns (`/s` prefix) that complicate SEO and deep linking.

**Solution:**

```
Site creation:
  Template:    Build Your Own (LWR)
  Site name:   Customer Portal
  URL path:    /support
  Full URL:    MyDomainName.my.site.com/support

Branding set tokens (Experience Builder > Branding):
  --dxp-color-brand:         #0070D2
  --dxp-color-background:    #F4F6F9
  --dxp-font-family-primary: 'Salesforce Sans', sans-serif

Navigation menu (primary):
  Home         → /support          (public)
  My Cases     → /support/cases    (authenticated only)
  Knowledge    → /support/articles (public)
  My Account   → /support/account  (authenticated only)

Pages:
  Home page    → lwc:heroSection, lwc:caseDeflectionSearch
  Cases page   → lwc:caseList, lwc:newCaseForm
  Article page → lwc:articleDetail
```

**Why it works:** LWR's publish-time freeze means the home page and knowledge articles are served from CDN cache on every request, avoiding org compute on every page load. Clean URL paths (`/support/cases`) work without the Aura `/s` prefix, making SEO-friendly URLs straightforward to configure.

---

## Example 2: Partner Community Using Partner Central Template

**Context:** A software vendor needs a partner portal for deal registration, lead sharing, and access to partner resources. The partner team needs to be live within two weeks using standard Salesforce partner workflows. Custom branding is required but heavy UI customization is not.

**Problem:** Starting from Build Your Own LWR for a partner portal requires building deal registration pages, partner dashboards, and lead management views from scratch — weeks of LWC development. Partner Central ships these pre-built.

**Solution:**

```
Site creation:
  Template:    Partner Central
  Site name:   Partner Hub
  URL path:    /partners
  Full URL:    MyDomainName.my.site.com/partners

Post-creation steps:
  1. Enable Partner Community licenses on the relevant Profiles or Permission Sets.
  2. In Sharing Settings, grant partners read/write on Opportunities (Controlled by Parent)
     and Leads (Public Read/Write) as appropriate for the deal reg model.
  3. In Experience Builder > Branding, upload the brand logo and set primary/secondary colors
     via the theme panel (Aura template — uses theme panel, not --dxp- tokens).
  4. Configure the Partner Central navigation to show/hide standard items
     (Deals, Leads, Reports) based on partner tier profiles.
  5. Publish.

Validation:
  - Log in as a partner user. Confirm deal registration form is accessible.
  - Confirm leads assigned to the partner are visible.
  - Confirm the guest (unauthenticated) URL redirects to the login page.
```

**Why it works:** Partner Central's pre-built pages handle the Opportunity and Lead sharing model without custom LWC development. The site can be customized through Experience Builder's theme panel and page editor without touching code, meeting the two-week timeline.

---

## Anti-Pattern: Using Aura Components in an LWR Site

**What practitioners do:** After creating a Build Your Own (LWR) site, a practitioner attempts to drag an existing Aura component (e.g., `c:legacyAccountSummary`) into a page region in Experience Builder, expecting it to appear alongside LWC components.

**What goes wrong:** The component does not appear in the Experience Builder component picker. No error is shown. The practitioner may spend time troubleshooting visibility settings or component configuration before realizing the root cause. In some cases, if a component is added via a workaround, it may cause the site to error at runtime because Aura's rendering engine is not loaded in LWR pages.

**Correct approach:** For an LWR site, all page components must be LWC. Migrate the Aura component to LWC before placing it in the site, or choose the Aura-based Build Your Own template if migration is not feasible within the project timeline. Document the template choice and the rationale (Aura component dependency) so future contributors understand why LWR was not selected.
