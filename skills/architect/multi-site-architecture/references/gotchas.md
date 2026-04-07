# Gotchas — Multi-Site Architecture

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Preview sites count against the 100-site limit — and they accumulate silently

**What happens:** Every time a team publishes a site to preview, it occupies one slot in the org's 100-site quota. Teams create preview sites for feature reviews, demos, and stakeholder sign-off without a plan to delete them. Over time, an org accumulates 20–40 preview and inactive sites that nobody owns, consuming quota until site creation is blocked.

**When it occurs:** Any time a new site is published to preview — which is the standard workflow before making a site active. The problem surfaces suddenly when the org hits 100 sites and cannot create any more, including for production launches.

**How to avoid:** Establish and enforce an org-wide site lifecycle policy. Require that preview sites created for non-production purposes are deleted when the associated project closes. Include a site count check in the project completion checklist.

---

## Gotcha 2: Deactivating a site does not free the 100-site quota

**What happens:** Admins deactivate (make inactive) an unused Experience Cloud site expecting to reclaim the quota slot. The count does not decrease. The inactive site continues to occupy one of the 100 available slots indefinitely.

**When it occurs:** Any time a site is deactivated rather than deleted. The error is often discovered only when the org approaches 100 total sites and the team cannot understand why there are so few "active" sites but the limit is still being approached.

**How to avoid:** Permanently delete sites that are no longer needed. If the site configuration must be preserved for documentation, export the page layout screenshots and Experience Builder settings before deletion. Do not use deactivation as a long-term archival strategy.

---

## Gotcha 3: Custom domain configuration cannot be done in sandbox — it is production-only

**What happens:** The `Setup > Custom URLs` configuration required to bind a custom domain (e.g., `portal.company.com`) to an Experience Cloud site is only functional in production orgs. In sandbox orgs, the option is absent or non-functional. Sandbox Experience Cloud sites always use the `.sandbox.my.site.com` URL pattern.

**When it occurs:** When teams attempt to configure or test custom domains in sandbox as part of pre-production validation. SSO callback URLs, CSP trusted site entries, and CORS configurations that reference the custom domain will not match the sandbox URL, producing authentication and security errors in sandbox that do not exist in production.

**How to avoid:** Use Named Credential or Custom Metadata records to externalize the site base URL per environment. Test SSO flows in sandbox using the default `.sandbox.my.site.com` URL and update the IdP Service Provider configuration to match. Document that custom domain configuration is a production-only step in the deployment runbook.

---

## Gotcha 4: Cross-site navigation drops unauthenticated users to a login page — there is no native session hand-off

**What happens:** A user authenticated in Experience Cloud Site A follows a hyperlink to Site B. The user's session cookie from Site A is not recognized by Site B. The user is redirected to Site B's login page rather than arriving authenticated.

**When it occurs:** Any time a user journey crosses site URL boundaries without SSO configured. Business stakeholders frequently assume "same org, same login" — the underlying org is the same, but the session management is per-site.

**How to avoid:** Configure SSO via an external IdP (Okta, Azure AD, Ping Identity). Register each site as a separate Service Provider with the same IdP. The IdP maintains an active session; when the user navigates to Site B, the IdP issues a new SAML assertion silently. Do not attempt to replicate this behavior by passing session context in URL parameters — this is a security vulnerability and is not supported.

---

## Gotcha 5: Guest user profiles are per-site and are not inherited across sites

**What happens:** A permission granted on one site's guest user profile (e.g., Read access on the Knowledge object) does not apply to any other site's guest user profile. A shared LWC component that works correctly on Site A fails silently on Site B because Site B's guest profile is missing the same permission.

**When it occurs:** When deploying shared LWC components that serve guest (unauthenticated) users across multiple sites without independently verifying each site's guest profile. Also occurs after Salesforce releases that change guest user sharing behavior — teams audit and fix one site but miss others.

**How to avoid:** Treat guest user profile configuration as a per-site deployment artifact. Include a guest profile permission verification step in the deployment checklist for every site that shares a component. When a shared component's data access requirements change, update and verify the guest profile on every site where the component is deployed.

---

## Gotcha 6: License type enforcement blocks cross-audience access even within the same org

**What happens:** A user provisioned with a Customer Community license attempts to log in to a Partner Community site in the same org. The login fails with an authorization error — the license type does not permit access to that site template. This is enforced at the platform level and cannot be overridden with permission sets or profiles.

**When it occurs:** When designing a multi-audience site topology where some users need access to both a customer site and a partner site. Also when a shared login portal attempts to route users dynamically to different sites — the routing logic may succeed but the user's license prevents access.

**How to avoid:** Map each user type to the license it requires for every site it needs to access. Users who need access to both a Customer Community site and a Partner Community site require a Partner Community license (or a combined license). Confirm the license allocation and cost implications with the Salesforce Account team before finalizing the site topology.
