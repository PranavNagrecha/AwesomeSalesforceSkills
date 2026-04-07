# Gotchas — Experience Cloud Site Setup

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Template Selection is Permanent

**What happens:** After a site is created with a specific template (e.g., Build Your Own Aura), there is no option to change the template. The site is permanently tied to the template family chosen at creation. Attempting to "upgrade" to LWR from Aura means deleting the site and starting over, losing all page configurations, navigation menus, branding settings, and any declarative customizations made in Experience Builder.

**When it occurs:** Any time a practitioner creates a site without fully evaluating the LWR vs Aura decision first — typically when a site is created quickly for a proof of concept and then gets treated as the production site.

**How to avoid:** Before creating the site, audit all components planned for the site. If any existing components are Aura-based and cannot be migrated to LWC within the project timeline, use the Aura Build Your Own template and document the constraint. If all components are LWC or will be built as LWC, choose LWR. Record the decision and its rationale before clicking Create.

---

## Gotcha 2: LWR Sites Require Explicit Republish — Changes Do Not Go Live Automatically

**What happens:** On an LWR site, all edits in Experience Builder (page layout, component configuration, branding token changes, navigation updates) are saved in draft state. The site continues to serve the previously published version from HTTP cache. Until the site is explicitly republished, visitors see no changes. This behavior is a direct consequence of the publish-time freeze that enables LWR's CDN caching model.

**When it occurs:** Every time a practitioner makes changes and assumes they are live because Experience Builder shows no error and the save confirms. This is especially common for practitioners migrating from Aura sites, where many changes are visible immediately without a full publish cycle.

**How to avoid:** Build an explicit "Publish" step into every deployment or change checklist. After any site modification, click the Publish button in Experience Builder. Confirm the published version timestamp updates in Site Settings. Do not mark a task as complete until the publish is confirmed.

---

## Gotcha 3: LWR and Aura Component Libraries Are Not Interchangeable

**What happens:** The Build Your Own (LWR) template's component picker in Experience Builder only surfaces LWC-compatible components. Aura components are not listed and cannot be added to LWR page regions. There is no error message explaining this — the component simply does not appear. Conversely, LWR-specific components that depend on the LWR runtime will not behave correctly if dragged into an Aura-based site.

**When it occurs:** When a team builds components in both Aura and LWC formats (common in orgs that predate the LWR templates) and assumes both types can be used in any site. Also occurs when a component built for internal Lightning App Builder pages is expected to work in an LWR Experience Cloud site without modification.

**How to avoid:** Before committing to the LWR template, run a component inventory. Check each planned component's `targetConfig` in its `*.js-meta.xml` to confirm it supports Experience Cloud (`lightning__AppPage`, `lightning__RecordPage`, or the Experience-specific target). Components without the correct targets will not be available in Experience Builder regardless of template type.

---

## Gotcha 4: Aura Sites Require the /s Path Prefix on All Page URLs

**What happens:** All page URLs in Aura-based Experience Cloud sites automatically include the `/s` prefix (e.g., `MyDomainName.my.site.com/portal/s/home`). This prefix is not configurable and cannot be removed from Aura sites. LWR sites do not have this prefix — pages are served at clean paths (e.g., `MyDomainName.my.site.com/portal/home`). When deep links, SEO configurations, or integrations are built assuming no `/s` prefix, they break on Aura sites.

**When it occurs:** When a project spec includes clean, SEO-friendly URL paths and the team creates an Aura site assuming URL configuration will be available later. Also occurs when an integration or email template embeds hard-coded links without the `/s` segment.

**How to avoid:** If clean URLs are a requirement, choose an LWR template. If an Aura template is required, document the `/s` path constraint in the URL design spec and ensure all deep links, email templates, and integration callbacks include the `/s` prefix from the start.

---

## Gotcha 5: Guest User Profile Permissions Must Be Explicitly Configured

**What happens:** By default, the guest user profile associated with a new Experience Cloud site has very restricted permissions. Public-facing pages may appear blank or show permission errors because the guest user cannot access required objects, fields, or records. This is intentional security behavior, but it surprises practitioners who expect a published site to "just work" for unauthenticated visitors.

**When it occurs:** When a site is published and tested only with an authenticated admin or partner user. The guest user experience is only broken when an unauthenticated test is performed.

**How to avoid:** After publishing, test the site explicitly as a guest user (open in an incognito/private browser window without logging in). Review the guest user profile permissions in Setup > Sites > [Site Name] > Guest User Profile. Grant object-level read access only to records the public should see. Enable field-level security for only the fields the guest user needs. Never grant guest users write access unless the use case explicitly requires it (e.g., a public case submission form) — and in that case, use a well-scoped Apex class with `without sharing` rather than direct guest user write permission.
