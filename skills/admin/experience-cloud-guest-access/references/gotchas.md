# Gotchas — Experience Cloud Guest Access

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Each Site Has Exactly One Guest Profile — Shared Across All Public Pages

**What happens:** An admin adds Read access to a new object on the guest user profile to support a newly launched public page. Unknown to the admin, other public pages on the same site have components that query the same object. Those components now return data they were never intended to show publicly, because the guest profile permission applies site-wide.

**When it occurs:** Any time the guest profile is modified to support one new page without auditing all other public pages on the same site for unintended side effects.

**How to avoid:** Before adding any object or field to the guest user profile, list all public pages on the site and check whether any existing component queries that object. Use the guest profile edit page alongside Experience Builder's page inventory. Treat the guest profile as a site-wide setting, not a per-page setting.

---

## Gotcha 2: FLS on the Guest Profile Applies to All Guest Apex Calls, Not Just the Page You Changed

**What happens:** A developer removes field-level Read access from the guest profile for a field deemed too sensitive for public display. The targeted public page no longer shows the field — which is correct. However, an Apex controller on a different public page queries the same field. That Apex call now either returns null for the field or throws a FLS exception in system mode, breaking the second page unexpectedly.

**When it occurs:** When multiple public pages share Apex controllers that query overlapping fields, and FLS changes on the guest profile are made with only one page in mind.

**How to avoid:** Before removing field-level access from the guest profile, search for all @AuraEnabled and @InvocableMethod Apex classes reachable from guest context and check whether they reference the affected field. Coordinate FLS changes with a full review of guest-accessible Apex, not just the immediate page trigger. See `security/guest-user-security` for Apex review guidance.

---

## Gotcha 3: External OWD Controls Guest Record Visibility — Internal OWD Does Not

**What happens:** An admin sets the internal OWD for a custom object to Public Read Only so internal users can see all records. They expect this also makes records visible to guest users on a public page. The public page still shows empty results because the external OWD for that object is Private.

**When it occurs:** Whenever internal OWD and external OWD are confused. Experience Cloud introduced a split OWD model where guest users and external authenticated users follow external OWD, not internal OWD.

**How to avoid:** Always check external OWD separately from internal OWD (Setup > Sharing Settings — external OWD is the second column in the OWD table). For any object that must be visible on a public page, the external OWD must be set to Public Read Only, OR a Guest User Sharing Rule for the site must grant Read access to the specific records.

---

## Gotcha 4: Guest User Sharing Rules Are Site-Specific and Do Not Transfer Between Sites

**What happens:** An admin copies or clones a site and expects the Guest User Sharing Rules from the original site to carry over to the new site. The new site's public pages show empty results because sharing rules are associated with the original site's guest user (a distinct system user) and do not apply to the new site's guest user.

**When it occurs:** During site cloning, template changes, or when a second site is created to serve a different audience with similar public content.

**How to avoid:** After any site clone or creation, navigate to Setup > Sharing Settings > Guest User Sharing Rules and confirm rules are present and correctly configured for the new site's guest user. Do not assume sharing rules from the original site are inherited.

---

## Gotcha 5: Page Access = Public Does Not Override Missing Guest Profile Permissions

**What happens:** An admin sets a page to Public in Experience Builder and publishes the site. The page is accessible without login but displays blank components. They assume the content is published incorrectly. The actual issue is that the guest user profile has no Read access on the object the page components are querying.

**When it occurs:** When admins configure page access and profile permissions as separate steps and one step is missed — common during initial site setup or when adding a new page type to an existing site.

**How to avoid:** After setting any page to Public, immediately verify the guest user profile has the required object Read access, relevant field permissions, and appropriate sharing visibility. Use a checklist (see the template in templates/) to ensure all three gates are checked together rather than in isolation.
