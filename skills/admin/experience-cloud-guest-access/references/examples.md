# Examples — Experience Cloud Guest Access

## Example 1: Configuring a Public Knowledge Base Page

**Context:** A support team is launching an Experience Cloud help center built on the LWR template. They want Knowledge articles to be readable without login so customers can self-serve before contacting support. The site is new and the guest user profile has no permissions yet.

**Problem:** The knowledge article detail page loads but shows a blank body. The article list page shows zero results. The page is set to Public in Experience Builder but the guest user cannot read Knowledge records.

**Solution:**

1. Navigate to Setup > Digital Experiences > All Sites > [Help Center] > Workspaces > Administration > Guest User Profile.
2. Under Object Settings > Knowledge, grant Read access to the Knowledge object.
3. Under Field Permissions for Knowledge, grant Read on: Title, Summary, Article Body, URL Name, Article Number, Last Published Date. Remove Read from: Owner, Internal Notes, any custom internal-only fields.
4. Navigate to Setup > Sharing Settings. Under Guest User Sharing Rules for [Help Center], create a criteria-based sharing rule: Share Knowledge records where Publication Status = Online with the guest user (Read Only).
5. Confirm external OWD for Knowledge is set appropriately. For a public help center, Public Read Only is acceptable for Knowledge if no sensitive drafts exist. If the org has sensitive draft articles, keep external OWD Private and rely entirely on the sharing rule.
6. Test in an incognito browser. Navigate to the article list page — confirm only Published/Online articles appear. Open a detail page — confirm the article body renders.

**Why it works:** The page access setting allows the page to render for guests. The guest profile Read access on Knowledge allows the components to query the object. The sharing rule (or Public OWD) makes specific records visible. All three gates must be open for a public Knowledge page to work correctly.

---

## Example 2: Setting Up a Product Catalog Accessible Without Login

**Context:** A B2B commerce company is building an Experience Cloud site where anonymous visitors can browse products before registering. Product2 records and their list prices should be visible on public catalog pages. Account-specific pricing should remain authenticated-only.

**Problem:** Product catalog pages show components with no data. The Experience Builder page is set to Public but the site was previously members-only and the guest profile was never configured for product data.

**Solution:**

1. In Experience Builder, open each catalog page (product list, product detail, category pages) and set Page Access = Public.
2. Open the guest user profile. Under Object Settings, grant Read access to: Product2, Pricebook2, PricebookEntry.
3. For Product2 field permissions, grant Read on: Name, Description, ProductCode, IsActive, Family, and any display-facing custom fields. Do not grant Read on internal cost fields or supplier fields.
4. For PricebookEntry, grant Read on: UnitPrice, IsActive, CurrencyIsoCode. Do not expose custom discount or contract fields.
5. Confirm Product2 external OWD is Public Read Only (appropriate for a catalog — Product2 has no owner-sensitive data). Confirm PricebookEntry external OWD matches.
6. Keep all pages related to cart, checkout, account-specific pricing, and order history set to Requires Login. These pages must not be reachable by guests.
7. Test in an incognito browser. Navigate the catalog — confirm product names and list prices are visible. Confirm that navigating to cart or checkout redirects to login.

**Why it works:** Public OWD on Product2 and PricebookEntry means no Guest User Sharing Rules are needed — all records are readable once the guest profile has object and field Read access. Keeping checkout pages as Requires Login ensures unauthenticated visitors cannot access account-specific data even if they guess the URL.

---

## Anti-Pattern: Granting Broad Object Permissions to Avoid Empty Pages

**What practitioners do:** When a public page shows empty results, admins grant View All or broaden OWD to Public Read/Write on the object to "fix" the visibility issue quickly.

**What goes wrong:** View All on the guest profile exposes every record of that object to unauthenticated visitors regardless of any other access controls. Public Read/Write OWD allows guests to potentially write records depending on profile permissions. Both approaches violate least-privilege and can expose sensitive business data on a public-facing site.

**Correct approach:** Diagnose the empty page by checking all three gates in order: (1) Is Page Access set to Public? (2) Does the guest profile have Read on the object and relevant fields? (3) Does the external OWD and/or Guest User Sharing Rule make the specific records visible? Fix the narrowest gate that is actually blocked rather than broadening permissions to bypass the investigation.
