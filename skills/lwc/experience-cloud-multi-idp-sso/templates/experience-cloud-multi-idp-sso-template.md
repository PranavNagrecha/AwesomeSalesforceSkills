# Experience Cloud Multi-IdP SSO — Design Template

Use this template when designing or implementing multi-IdP SSO for an Experience Cloud deployment.

---

## Scope

**Skill:** `experience-cloud-multi-idp-sso`

**Request summary:** (fill in what the stakeholder asked for)

**Site(s) in scope:**

| Site Name | Site Base URL | Audience |
|---|---|---|
| (e.g., VendorPortal) | (e.g., https://myorg.my.site.com/vendors) | (e.g., Corporate contractors) |
| | | |

---

## Identity Provider Inventory

Complete one row per IdP before beginning configuration:

| IdP Name | Protocol | Metadata / Discovery URL | User Matching Key | Expected User Count |
|---|---|---|---|---|
| (e.g., Okta) | SAML | (federation metadata XML URL) | FederationIdentifier = employeeId | (e.g., 2,000) |
| (e.g., Google) | OIDC | https://accounts.google.com/.well-known/openid-configuration | Email claim | (e.g., 500) |
| | | | | |

---

## Auth Provider Configuration

Complete one block per IdP:

### IdP 1: [Name]

- **Protocol:** SAML / OIDC
- **Auth Provider Name in Salesforce:** _____________
- **Callback URL (from Salesforce Setup):** `https://<my-domain>.my.salesforce.com/services/authcallback/<ProviderName>`
- **Callback URL registered in IdP application:** [ ] Yes / [ ] No
- **Start SSO URL (with community parameter):**
  ```
  https://<my-domain>.my.salesforce.com/services/auth/sso/<ProviderName>?community=<site-base-url>
  ```
- **RegistrationHandler class (OIDC only):** _____________
- **Federation ID source field (SAML only):** _____________

### IdP 2: [Name]

- **Protocol:** SAML / OIDC
- **Auth Provider Name in Salesforce:** _____________
- **Callback URL (from Salesforce Setup):** _____________
- **Callback URL registered in IdP application:** [ ] Yes / [ ] No
- **Start SSO URL (with community parameter):** _____________
- **RegistrationHandler class (OIDC only):** _____________
- **Federation ID source field (SAML only):** _____________

---

## Login Page Configuration

| Site | Login Buttons to Show | Start SSO URLs |
|---|---|---|
| (e.g., VendorPortal) | Okta SAML | `https://…/sso/Okta?community=https://…/vendors` |
| (e.g., CitizenPortal) | Google OIDC, Microsoft OIDC | `https://…/sso/Google?community=…` and `https://…/sso/Microsoft?community=…` |

---

## Federation ID Population (SAML only)

- **Source of FederationIdentifier values:** (e.g., IdP user export, HR system)
- **Update method:** Data Loader bulk update / Flow / Apex batch
- **Count of User records needing update:** _____________
- **Validation step:** Setup > SAML Assertion Validator with test user assertion
- **Target completion date before SSO activation:** _____________

---

## RegistrationHandler Design (OIDC only)

For each OIDC auth provider, document the matching and provisioning logic:

| Auth Provider | Match Strategy | Create Strategy | Block Strategy |
|---|---|---|---|
| (e.g., Google) | Match by Email | Create new Partner Community User | Throw RegistrationHandlerException if domain not in allowlist |
| | | | |

---

## SP+IdP Topology (if applicable)

- **Salesforce acts as SP for:** (list sites/portals)
- **Salesforce acts as IdP for:** (list connected apps)
- **Redirect loop risk assessed:** [ ] Yes / [ ] No
- **Break-glass authentication method if SSO fails:** _____________

---

## Pre-Activation Checklist

- [ ] All Auth Provider records created and saved in Setup
- [ ] All callback URLs registered in external IdP applications
- [ ] Start SSO URLs constructed with correct `community` parameter for each site
- [ ] FederationIdentifier populated on all SAML-bound User records
- [ ] RegistrationHandler deployed and assigned to each OIDC Auth Provider
- [ ] Login pages configured to show correct providers per site
- [ ] End-to-end SSO tested in sandbox with at least one user per IdP
- [ ] SAML Assertion Validator run for each SAML provider
- [ ] Login history reviewed for errors after sandbox test
- [ ] SP+IdP redirect loop tested (if applicable)

---

## Notes and Deviations

(Record any deviations from the standard pattern and the business reason for them.)
