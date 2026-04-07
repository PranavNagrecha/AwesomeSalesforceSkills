# Gotchas — Experience Cloud Multi-IdP SSO

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Start SSO URL Missing the `community` Parameter Routes Users to the Internal Org

**What happens:** After a successful authentication with the external IdP, Salesforce redirects the user to the internal Salesforce org login page (or the My Domain root) rather than the Experience Cloud site. No error is thrown; the browser simply lands in the wrong place.

**When it occurs:** Any time a Start SSO URL is used without appending `?community=<site-base-url>`. This is the default state of the URL as shown in Setup — the community parameter is not auto-included. It also occurs when the community parameter is URL-encoded incorrectly or when the site base URL contains a trailing slash that does not match the registered URL.

**How to avoid:** Always append `?community=https://<your-site>.my.site.com/<path>` to every Start SSO URL before placing it on a login page or in configuration. Verify the site base URL exactly matches the URL listed in the Experience Cloud site settings (no trailing slash, correct subdomain). Test end-to-end in a sandbox before activating.

---

## Gotcha 2: Federation ID Must Be Populated Before SAML SSO Is Activated — It Is Never Auto-Derived

**What happens:** When a SAML assertion arrives and the `FederationIdentifier` field on the User record is blank or does not match the NameID value in the assertion, Salesforce silently fails to match the user and returns a generic "We can't log you in" error. The user receives no actionable message and the server-side log entry is minimal.

**When it occurs:** Any SAML SSO activation where User records were created before the IdP integration was planned — which is most brownfield implementations. The field is also not populated by SCIM provisioning unless the SCIM connector is explicitly configured to write to `FederationIdentifier`.

**How to avoid:** Before activating SAML SSO on any profile or permission set, run a SOQL query to count users with a blank Federation ID, then bulk-update via Data Loader using the IdP's user export as the source of truth. The IdP-side value should match the NameID format configured in the SAML Auth Provider (email address format vs. persistent vs. transient). Test with one pilot user in sandbox using Setup > SAML Assertion Validator before rolling out.

---

## Gotcha 3: SF Acting as Both SP and IdP Can Produce Redirect Loops

**What happens:** When Salesforce is configured as an SP (it receives SAML assertions from an external IdP for user login) and simultaneously as an IdP (it issues SAML assertions to a connected app), a browser session that needs to authenticate for the connected app initiates a login flow, Salesforce redirects to the external IdP, the external IdP redirects back to Salesforce, and Salesforce then redirects back to the connected app login initiation — which triggers the same loop again.

**When it occurs:** When the Connected App's **Start URL** is set to the app's login initiation endpoint rather than a resource URL, or when the connected app's SAML configuration uses Salesforce's own SSO endpoint as the assertion consumer. It also occurs when testing SP-initiated flow from a session that has no cached Salesforce session cookie.

**How to avoid:** Set the Connected App's Start URL to an actual resource or landing page, not the initiation endpoint. Ensure the assertion consumer service URL in the Connected App points to the external system's ACS endpoint, not back to Salesforce. Test both flows (SP-initiated login via the portal, and IdP-initiated access to the connected app) independently before combining them in an end-to-end test.

---

## Gotcha 4: RegistrationHandler `createUser` Must Return a Non-Null User for OIDC to Complete

**What happens:** If the `createUser` method in a RegistrationHandler returns `null` — for example, because a lookup finds no match and a creation branch is skipped — the OIDC authentication silently fails with a generic error. Salesforce does not distinguish a null return from an exception in the user-facing message.

**When it occurs:** Common in RegistrationHandler implementations that attempt to match an existing user and throw or return null when no match is found, intending to block unauthorized users. The intent is correct but the mechanism (returning null) is indistinguishable from an implementation bug.

**How to avoid:** If the business intent is to block unrecognized OIDC users, throw an `Auth.RegistrationHandlerException` with a descriptive message rather than returning null. If the intent is to create a new user for every new OIDC subject, ensure the creation branch is always reached when the lookup finds nothing.

---

## Gotcha 5: Auth Provider Callback URL Must Be Registered in the External IdP Application

**What happens:** The OIDC or SAML flow fails at the IdP side with a "redirect_uri mismatch" or "invalid ACS URL" error after the user authenticates. Salesforce never receives the assertion or token.

**When it occurs:** When a new Auth Provider record is created in Salesforce but its Callback URL (shown in the Auth Provider detail page under "Salesforce Configuration") has not been added to the allowed redirect URIs in the external IdP's application configuration (e.g., in Azure App Registration, Google Cloud Console, or Okta application settings).

**How to avoid:** After creating the Auth Provider record in Setup, copy the Callback URL shown on the record's detail page and register it in the IdP application before attempting any SSO test. The callback URL format is `https://<my-domain>.my.salesforce.com/services/authcallback/<provider-name>`. For Experience Cloud sites, also verify that the community-specific callback URL (if used) is registered.
