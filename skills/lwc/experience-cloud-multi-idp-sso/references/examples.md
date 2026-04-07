# Examples — Experience Cloud Multi-IdP SSO

## Example 1: Single Portal with Google OIDC, Microsoft OIDC, and Okta SAML on the Same Login Page

**Context:** A B2B portal serves three distinct user populations: employees of partner companies who authenticate via Okta (enterprise SAML), freelance contractors who use Google accounts (OIDC), and vendor admins who use Microsoft Entra ID (OIDC). All three populations access a single Experience Cloud site.

**Problem:** A single Auth Provider record cannot handle two different OIDC providers (Google and Microsoft) or mix SAML with OIDC. A naive implementation either creates three separate sites (multiplicating maintenance) or forces all users through a single IdP that many cannot use.

**Solution:**

Register three Auth Provider records in Setup > Auth. Providers:

1. **Okta SAML** — Type: SAML, Entity ID: `https://okta-tenant.okta.com`, SSO URL: Okta app SSO endpoint. Assigns Federation ID matching on `NameID = email`.
2. **Google OIDC** — Type: Open ID Connect, Consumer Key/Secret from Google Cloud Console, Authorization Endpoint: `https://accounts.google.com/o/oauth2/auth`. Assign `GoogleRegistrationHandler`.
3. **Microsoft OIDC** — Type: Open ID Connect, Consumer Key/Secret from Azure App Registration, Authorization Endpoint: `https://login.microsoftonline.com/<tenant>/oauth2/v2.0/authorize`. Assign `MicrosoftRegistrationHandler`.

Each generates a Start SSO URL. Append `?community=https://myportal.my.site.com/partners` to each.

In Experience Builder on the Login page, add three Social Login button components, one per provider, each pointing to its Start SSO URL with the community parameter.

```apex
// GoogleRegistrationHandler.cls — simplified OIDC user lookup
global class GoogleRegistrationHandler implements Auth.RegistrationHandler {

    global User createUser(Id portalId, Auth.UserData data) {
        // Attempt to match by email first
        List<User> existing = [
            SELECT Id FROM User
            WHERE Email = :data.email AND IsActive = true
            LIMIT 1
        ];
        if (!existing.isEmpty()) {
            return existing[0];
        }
        // Create a new community user
        User u = new User();
        u.Username = data.email + '.partner';
        u.Email = data.email;
        u.LastName = (data.lastName != null) ? data.lastName : 'Unknown';
        u.FirstName = data.firstName;
        u.Alias = data.email.left(8);
        u.ProfileId = [SELECT Id FROM Profile WHERE Name = 'Partner Community User' LIMIT 1].Id;
        u.TimeZoneSidKey = 'America/Los_Angeles';
        u.LocaleSidKey = 'en_US';
        u.EmailEncodingKey = 'UTF-8';
        u.LanguageLocaleKey = 'en_US';
        return u;
    }

    global void updateUser(Id userId, Id portalId, Auth.UserData data) {
        // Sync name changes on subsequent logins
        User u = new User(Id = userId, FirstName = data.firstName, LastName = data.lastName);
        update u;
    }
}
```

**Why it works:** Each Auth Provider is independently configured and independently routable. The `community` parameter on each Start SSO URL ensures the browser returns to the same portal after each provider's auth flow completes. The RegistrationHandler handles the OIDC user-matching logic that SAML handles via Federation ID.

---

## Example 2: Separate Vendor and Citizen Portals Sharing One Org with Different IdPs

**Context:** A utilities company runs two Experience Cloud sites in one org: a `VendorPortal` for corporate contractors (authenticated via the company's Azure AD using SAML) and a `CitizenPortal` for residential customers (authenticated via a social OIDC provider). The two portals must never show each other's login options.

**Problem:** Without explicit routing, a user who bookmarks the Vendor SAML Start SSO URL could potentially be redirected to the Citizen portal if the `community` parameter is missing or incorrect. Conversely, exposing both login buttons on both portals creates confusion and a potential for mis-authentication.

**Solution:**

1. Register **AzureAD-SAML** Auth Provider — SAML type, Azure federation metadata XML uploaded.
2. Register **SocialOIDC** Auth Provider — OIDC type, social IdP credentials, `CitizenRegistrationHandler` assigned.
3. Build the Vendor portal login page with only the AzureAD-SAML button:
   ```
   Start SSO URL: https://mycompany.my.salesforce.com/services/auth/sso/AzureAD-SAML?community=https://mycompany.my.site.com/vendors
   ```
4. Build the Citizen portal login page with only the SocialOIDC button:
   ```
   Start SSO URL: https://mycompany.my.salesforce.com/services/auth/sso/SocialOIDC?community=https://mycompany.my.site.com/citizens
   ```
5. Pre-populate `FederationIdentifier` on all vendor User records with the Azure AD Object ID (the value Azure sends as the SAML NameID).

**Why it works:** The `community` parameter is the routing key. The AzureAD-SAML URL carries the vendor site URL; the SocialOIDC URL carries the citizen site URL. Post-authentication, Salesforce redirects back to whichever site the URL referenced. The two portals share one org's data model but each presents only the relevant login mechanism.

---

## Anti-Pattern: One Portal Per IdP Instead of Multi-Provider on One Login Page

**What practitioners do:** Create a separate Experience Cloud site for each identity provider — one "Vendor Site" fronting the SAML IdP and one "Contractor Site" fronting the OIDC IdP — when both user types actually need to access the same data.

**What goes wrong:** Data access permissions, sharing rules, and Apex logic must be duplicated across sites. Portal license consumption doubles. Release management complexity grows. When a user belongs to both communities, their membership records conflict.

**Correct approach:** Register multiple Auth Providers in the same org. Expose multiple login buttons on a single Experience Cloud site's login page. The platform supports up to the org's Auth Provider limit per org (not per site), and a single login page can host multiple Social Login components.
