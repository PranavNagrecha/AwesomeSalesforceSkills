# Gotchas — Org Setup And Configuration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Deploying My Domain Breaks Hardcoded Login URLs In Integrations

**What happens:** After My Domain is deployed to users, any external system that has the old login URL (`https://login.salesforce.com` or `https://test.salesforce.com`) hardcoded in OAuth callback URLs, SAML metadata, or Connected App endpoint configurations will fail to authenticate. Users who bookmarked the old login URL will be redirected, but machine-to-machine integrations that construct the authorization URL programmatically will break.

**When it occurs:** Immediately after deploying My Domain to users in production. Common victims: CI/CD pipeline credentials, ETL tools (MuleSoft, Informatica), managed packages that registered their OAuth callback against the legacy URL, and Salesforce mobile SDK apps using the old token endpoint.

**How to avoid:** Before deploying My Domain, audit all Connected Apps in the org (**Setup > App Manager**) and check their callback URLs. Update them to the new domain format. Similarly, update any external IdP (Okta, Azure AD) SAML configurations that reference `salesforce.com/saml`. After deployment, monitor integration logs for authentication failures on day 1 and day 2.

---

## Gotcha 2: Session Lock-To-IP Breaks Mobile And VPN Users Without Warning

**What happens:** When "Lock sessions to the IP address from which they originated" is enabled in Session Settings, any session request that arrives from a different IP than the one that created the session is immediately invalidated. The user sees a generic "Session expired" or login page with no explanation.

**When it occurs:** Users on mobile data connections (where the carrier dynamically reassigns IPs), users who switch from office WiFi to cellular (or VPN off to VPN on), or users behind load balancers that change source IPs. It also affects mobile app users more than desktop users.

**How to avoid:** Do not enable this setting in orgs with significant mobile usage or users on cellular networks. If it must be enabled for compliance, exempt mobile-device users via a separate profile or warn them about expected logouts when switching networks. The security benefit of IP-locking is largely superseded by MFA, which provides stronger session assurance without the UX disruption.

---

## Gotcha 3: Tightening Password Policy Does Not Immediately Expire Existing Passwords

**What happens:** An admin changes the org-level password policy to a shorter expiration window (e.g., from 90 days to 30 days) or adds complexity requirements. Existing users whose passwords were set under the old policy are not immediately affected. The new policy only applies to passwords set after the change date.

**When it occurs:** After any upward tightening of the password policy. The security change has no effect on the current user population until their passwords naturally expire or are manually reset.

**How to avoid:** To make the policy change effective immediately, use the **Expire All Passwords** button at the bottom of **Setup > Security > Password Policies**. This forces all users to change their password on next login. Plan this for a low-traffic period and communicate to users in advance to avoid support load.

---

## Gotcha 4: CSP Violations Are Silent To End Users

**What happens:** When a Lightning page, LWC, or Visualforce page attempts to load a resource from a domain not in CSP Trusted Sites, the browser silently blocks the resource. The component either renders blank, shows no image, or silently skips an API call. There is no Salesforce error message — only a browser console error.

**When it occurs:** During development or after deploying a new component that calls an external API or loads an external resource. Also occurs after an external vendor changes their CDN subdomain.

**How to avoid:** When a Lightning component appears blank or is missing expected content, always check **browser DevTools > Console** first. A CSP violation message will name the blocked domain and violated directive. Then navigate to **Setup > Security > CSP Trusted Sites** and add the specific domain and directive. For Apex callouts (server-side HTTP), the fix is **Setup > Security > Remote Site Settings**, not CSP Trusted Sites.

---

## Gotcha 5: MFA Enforcement Waiver Does Not Automatically Apply To New Integration Users

**What happens:** An admin enables org-wide MFA enforcement and then creates a new integration/service account user intended for API-only access. The new user's profile does not automatically inherit the MFA waiver — and if that user attempts a UI login, MFA is required.

**When it occurs:** When new API users are provisioned after org-wide MFA enforcement is turned on. Some automation scripts or ETL tools may attempt UI-session-based authentication instead of OAuth, which will fail if MFA is enforced and no waiver is set.

**How to avoid:** For API-only users, assign the **Waive Multi-Factor Authentication for Exempt Users** system permission via a permission set or profile, or use an integration user profile with the **API Only** user interface access restriction. Better still, migrate all API integrations to OAuth 2.0 JWT bearer token or client credentials flow, which never attempts a UI session and is outside the scope of MFA enforcement entirely.
