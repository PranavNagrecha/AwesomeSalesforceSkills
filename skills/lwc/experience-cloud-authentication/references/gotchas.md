# Gotchas — Experience Cloud Authentication

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: `HeadlessSelfRegistrationHandler` Is a Different Interface Than `Auth.RegistrationHandler`

**What happens:** A practitioner writes a class implementing `Auth.RegistrationHandler` (the standard social login handler) and assigns it in the Headless Identity settings as the self-registration handler for passwordless flows. The class compiles without error, but at runtime the headless flow throws an error and user creation fails.

**When it occurs:** Whenever a headless passwordless or headless self-registration flow triggers user provisioning. The `HeadlessSelfRegistrationHandler` interface has a different method signature for `createUser()` — it receives a `Map<String, String>` of user attributes and a `networkId`, not the `Auth.UserData` object expected by `Auth.RegistrationHandler`.

**How to avoid:** Always implement `Auth.HeadlessSelfRegistrationHandler` in a separate class for headless flows. The two interfaces are not interchangeable. Similarly, implement `Auth.HeadlessUserDiscoveryHandler` for user discovery in headless flows — this is also separate from any standard registration handler logic.

---

## Gotcha 2: Custom VF Login Pages Are Silently Ignored on LWR Sites

**What happens:** A developer creates a Visualforce page, assigns it as the custom login page under Administration > Login & Registration, saves successfully, and then navigates to the site login URL. The default Salesforce login page still renders with no error.

**When it occurs:** LWR (Lightning Web Runtime) sites — the newer site engine introduced for modern Experience Cloud templates — do not support Visualforce login pages. Only Aura-engine sites (Customer Community, Partner Community, Customer Community Plus templates based on the older engine) support VF login pages. The Administration panel in Setup allows the assignment regardless of site type, which creates a false sense of configuration success.

**How to avoid:** Check the site engine in Setup > Digital Experiences > All Sites > Builder. LWR sites require an LWC-based login component with `lightningCommunity__Page` in its `targets` metadata. Deploy the LWC, then assign it in Administration > Login & Registration > Login Page Type.

---

## Gotcha 3: Auth Provider Start SSO URL Must Include `community` Parameter for Site Routing

**What happens:** A developer constructs a social login button that redirects users to `/services/auth/sso/<ProviderName>` (the standard Start SSO URL). After the IdP handshake completes, users are redirected to the internal Salesforce org login page instead of the Experience Cloud site — even though authentication succeeded.

**When it occurs:** The `community` query parameter tells Salesforce which Experience Cloud site to return the user to after authentication. Without it, Salesforce defaults to the internal org login endpoint. The auth provider handshake completes correctly, but the user lands in the wrong place.

**How to avoid:** Always append `?community=<URL-encoded-site-base-URL>` to the Start SSO URL. Example:

```
/services/auth/sso/GoogleProvider?community=https%3A%2F%2Fmysite.my.site.com%2Fportal
```

The site base URL must exactly match the Experience Cloud site's base URL as configured, including the path prefix.

---

## Gotcha 4: Federation ID Case Sensitivity Causes Duplicate User Records

**What happens:** Social login creates a duplicate community user on each login rather than matching the existing record. Both records are active and share the same email.

**When it occurs:** `User.FederationIdentifier` is a case-sensitive field. If the Registration Handler stores the value from the IdP in one case (e.g., uppercase subject ID) during creation but the IdP returns a slightly different casing on subsequent logins — or if the SOQL query in `createUser()` uses a case-insensitive match — the lookup fails and a new user is created.

**How to avoid:** Normalize the Federation ID to a consistent casing (e.g., `.toLowerCase()`) both when writing it in `createUser()` and when querying in the lookup. Use `FIND` or SOQL with explicit casing logic, and test with the actual IdP subject format before going to production.

---

## Gotcha 5: Headless Identity Must Be Enabled at Org Level Before Site-Level Configuration

**What happens:** A practitioner navigates to the Experience Cloud site's Administration > Login & Registration to assign `HeadlessUserDiscoveryHandler` and `HeadlessSelfRegistrationHandler` classes, but the Headless Identity section is absent from the page.

**When it occurs:** Headless Identity is a separate org-level feature that must be enabled in Setup > Digital Experiences > Settings before it becomes configurable per site. The site-level UI for headless handler assignment does not appear until the org-level switch is on.

**How to avoid:** Enable Headless Identity in Setup > Digital Experiences > Settings first. Then configure the per-site handlers. This also applies to sandbox — the org-level switch is not enabled by default in sandbox refreshes.
