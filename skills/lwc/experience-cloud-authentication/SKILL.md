---
name: experience-cloud-authentication
description: "Use when building custom login pages, social SSO flows, self-registration flows, or passwordless OTP login for Experience Cloud (community) sites. Trigger keywords: custom login page Experience Cloud, social SSO community portal, passwordless login Experience Cloud, self-registration custom flow, headless authentication community, auth provider OIDC SAML site. NOT for internal SSO configuration (use identity/sso skills). NOT for standard username/password authentication with no customization."
category: lwc
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
triggers:
  - "How do I add Google or social login to my Experience Cloud site?"
  - "How do I implement passwordless login with OTP in a community?"
  - "How do I build a custom self-registration flow for an Experience Cloud portal?"
  - "Headless authentication for mobile app using Experience Cloud identity"
  - "Custom login page not working for LWR site — still showing default login"
tags:
  - experience-cloud
  - authentication
  - sso
  - social-login
  - passwordless
  - self-registration
  - headless-identity
  - auth-provider
  - lwc
  - aura
inputs:
  - Experience Cloud site type (Aura/LWR) and site URL
  - Identity provider details if using social login (OIDC/SAML metadata or client credentials)
  - Whether login is standard, headless, or passwordless
  - Whether self-registration is required and if a custom RegistrationHandler is needed
outputs:
  - Configured auth provider and registration handler Apex class
  - Custom login page component (VF for Aura, LWC for LWR)
  - Headless passwordless flow implementation using HeadlessPasswordlessLogin API
  - Federation ID or matching-rule configuration for user matching
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Experience Cloud Authentication

Use this skill when designing or building custom authentication flows for Experience Cloud sites: social SSO via OIDC or SAML auth providers, self-registration with custom Apex handlers, passwordless OTP login (standard or headless), and custom login pages for Aura or LWR sites.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Site type (Aura vs LWR):** This controls whether a custom login page must be a Visualforce page (Aura) or an LWC (LWR). Mixing them is a silent failure — LWR ignores VF login pages.
- **Authentication mode (standard, headless, or passwordless):** Headless and passwordless flows require distinct Apex handler interfaces (`HeadlessUserDiscoveryHandler`, `HeadlessSelfRegistrationHandler`) that are separate from the standard `Auth.RegistrationHandler` used for non-headless flows.
- **Who the user population is:** External guest users, community members, or partner users each have different license and profile constraints that affect what auth flows are permissible.
- **Sandbox-first constraint:** Auth providers require an external identity provider that must be pre-configured in sandbox before production. Skipping sandbox causes mismatched callback URLs and production incidents.

---

## Core Concepts

### Auth Providers (OIDC/SAML) for Social Login

An auth provider is a Salesforce-managed connector to an external identity provider. When a site visitor clicks "Sign in with Google," Salesforce redirects them to the IdP, receives an OAuth token or SAML assertion, and then maps the returned identity to a Salesforce user via a Registration Handler Apex class.

- **OIDC providers** (Google, Okta, custom) are configured under Setup > Auth. Providers with provider type "OpenID Connect". You supply the consumer key, secret, and authorize/token/userinfo endpoints.
- **SAML providers** configured as auth providers (distinct from SAML SSO settings) require the issuer, entity ID, and certificate. The Start SSO URL must include the `?community=<site-url>` query parameter to route the assertion back to the correct site rather than the internal org login.
- **Federation ID** is the primary matching key. The value returned in the IdP's subject or a custom attribute must match `User.FederationIdentifier`. OIDC can also match on email, but Federation ID is more reliable for long-lived accounts.

### Registration Handlers: Standard vs Headless

Two distinct Apex interfaces govern how Salesforce creates or matches users after an external identity is verified:

| Interface | Used When | Key Methods |
|---|---|---|
| `Auth.RegistrationHandler` | Standard (non-headless) social login via auth provider | `createUser()`, `updateUser()` |
| `Auth.ConfigurableSelfRegHandler` | Standard self-registration with fine-grained control | `getUserAttributes()`, `createUser()`, `postRegister()` |
| `HeadlessUserDiscoveryHandler` | Headless passwordless — discover existing user by identifier | `discover()` |
| `HeadlessSelfRegistrationHandler` | Headless passwordless — register new user via headless flow | `createUser()`, `autoConfirm()` |

The `HeadlessUserDiscoveryHandler` and `HeadlessSelfRegistrationHandler` interfaces live in the headless identity API surface and are **not** the same as `Auth.RegistrationHandler`. Using the wrong interface compiles successfully but the headless flow will fail at runtime because Salesforce cannot locate the handler.

### Passwordless Login and the HeadlessPasswordlessLogin API

Passwordless login sends a one-time passcode (OTP) to the user's email or phone without a password. Two modes:

- **Standard passwordless** — Salesforce manages the OTP prompt within the site's login page. Enable under Digital Experience > Administration > Login & Registration > Allow passwordless login.
- **Headless passwordless** — Your custom front end (mobile app, React, custom LWC) calls the `HeadlessPasswordlessLogin` REST resource directly. The API issues an OTP; your UI collects it and exchanges it for a session. Requires headless identity to be enabled in the org and the site must be configured for headless flows.

Headless flows require `HeadlessUserDiscoveryHandler` to locate an existing user and `HeadlessSelfRegistrationHandler` to create new users. Both classes are assigned in the Headless Identity settings for the site.

### Custom Login Pages: VF for Aura, LWC for LWR

- **Aura sites** use a Visualforce page as the custom login page. Assign it under Administration > Login & Registration > Login Page Type = Visualforce Page.
- **LWR sites** use an LWC-based login page. Build the component extending `lwc/loginForm` or composing the `c/selfRegisterLwc` pattern, then assign it under the same Administration panel. Setting a VF page on an LWR site has no effect — the default login page renders silently.
- Login page LWCs must be deployed before they appear in the Administration drop-down. Deploy them as metadata-type `LightningComponentBundle` with `isExposed: true` and `targets` including `lightningCommunity__Page`.

---

## Common Patterns

### Pattern 1: Social Login with OIDC Auth Provider

**When to use:** Site users should be able to authenticate with Google, Okta, LinkedIn, or any OIDC-compatible IdP instead of creating a Salesforce community account with a password.

**How it works:**

1. Create an Auth Provider in Setup under the provider type (e.g., "Google", "OpenID Connect"). Supply client ID, client secret, authorize endpoint, token endpoint, and userinfo endpoint.
2. Set the Callback URL in your IdP application to `https://<myDomain>.my.site.com/services/authcallback/<ProviderName>`.
3. Write an `Auth.RegistrationHandler` Apex class. In `createUser()`, look up an existing `User` by `FederationIdentifier` or email. If found, return the existing user. If not, create a new external user with the appropriate profile and community.
4. Assign the Registration Handler on the Auth Provider setup page.
5. On the Experience Cloud site, go to Administration > Login & Registration > Login Page Branding, enable the auth provider as a social sign-on option.
6. For Aura sites, the login button is rendered automatically. For LWR sites with a custom login LWC, call the standard `authprovider` navigation target or use `window.location` redirect to the Start SSO URL.

**Why not redirect directly to the IdP:** Bypassing the auth provider Start SSO URL loses the `community` parameter routing and the registration handler. Users authenticate but land on the internal org login, not the community.

### Pattern 2: Headless Passwordless OTP for Mobile App

**When to use:** A mobile or SPA front end needs to authenticate community users without showing a Salesforce-hosted login page — typically a branded mobile app using Experience Cloud as the identity layer.

**How it works:**

1. Enable Headless Identity in Setup > Digital Experiences > Settings.
2. Create a `HeadlessUserDiscoveryHandler` Apex class implementing `Auth.HeadlessUserDiscoveryHandler`. The `discover()` method receives the identifier (email or phone) and returns a `Auth.UserDiscoveryResult` indicating whether to challenge the existing user or route to registration.
3. Create a `HeadlessSelfRegistrationHandler` Apex class implementing `Auth.HeadlessSelfRegistrationHandler`. The `createUser()` method provisions a new external user; `autoConfirm()` controls whether email verification is skipped.
4. Assign both handlers in the Headless Identity settings for the Experience Cloud site.
5. From the mobile app, POST to `<siteUrl>/services/auth/headless/init/passwordless/login` with the user's email or phone. Salesforce returns an OTP via email/SMS.
6. User enters the OTP; the app POSTs to the verification endpoint. On success, Salesforce returns an access token.

**Why not use standard passwordless:** Standard passwordless requires a Salesforce-hosted page. Headless gives full front-end control and works in native mobile contexts where a webview cannot be used.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Social SSO with external IdP (Google, Okta) | Auth Provider + `Auth.RegistrationHandler` | Standard pattern; Salesforce manages OAuth handshake |
| Self-registration with custom validation | `Auth.ConfigurableSelfRegHandler` | More lifecycle hooks than standard RegistrationHandler |
| Passwordless login on Salesforce-hosted page | Enable passwordless in Administration > Login & Registration | Simplest; no custom code needed |
| Passwordless login from mobile/SPA (no hosted page) | Headless Passwordless API + `HeadlessUserDiscoveryHandler` + `HeadlessSelfRegistrationHandler` | Headless flow is required when you control the UI |
| Custom login page on Aura site | Visualforce page assigned in site Administration | Aura requires VF for custom login |
| Custom login page on LWR site | LWC with `lightningCommunity__Page` target | LWR ignores VF login pages; LWC is required |
| Matching returning social login users | Federation ID (`User.FederationIdentifier`) | More stable than email matching across IdP re-registrations |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Identify site type and auth mode** — Confirm whether the target site is Aura or LWR. Confirm whether the flow is standard social SSO, self-registration, standard passwordless, or headless passwordless. This determines which interfaces and page types are required.
2. **Configure the auth provider or headless settings** — For social SSO, create the Auth Provider in Setup and register the Callback URL with the IdP. For headless flows, enable Headless Identity in Digital Experiences settings before writing any Apex.
3. **Implement the correct Apex handler** — For social SSO, implement `Auth.RegistrationHandler`. For headless passwordless, implement both `HeadlessUserDiscoveryHandler` and `HeadlessSelfRegistrationHandler`. Never substitute one interface for the other.
4. **Build the login page component** — For Aura, create a VF page and assign it in Administration > Login & Registration. For LWR, build an LWC with `lightningCommunity__Page` in its target metadata and deploy it before assigning.
5. **Verify user matching and license** — Confirm Federation ID is populated correctly for social login users. Confirm the profile and license assigned in `createUser()` are valid for the site's member configuration.
6. **Test in sandbox end-to-end** — Auth providers use callback URLs that must match exactly. Test the full login round-trip in a sandbox with the real IdP before promoting to production.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Auth provider callback URL registered with IdP matches `services/authcallback/<ProviderName>` on the correct domain
- [ ] Registration handler implements the correct interface for the flow type (standard vs headless)
- [ ] Custom login page type matches site engine (VF for Aura, LWC for LWR)
- [ ] LWC login page has `lightningCommunity__Page` in targets metadata and is deployed
- [ ] Federation ID populated and matches across both IdP and Salesforce user records
- [ ] Headless Identity enabled in org settings if using any headless or headless passwordless flow
- [ ] Sandbox end-to-end login test completed before production deployment

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Start SSO URL missing `community` parameter** — When constructing the social login redirect URL, the `community` parameter (`?community=<encoded-site-url>`) tells Salesforce which site to return the user to after the IdP handshake. Omitting it causes the user to be redirected to the internal org login page instead of the community, with no error message.
2. **VF login page silently ignored on LWR sites** — Assigning a Visualforce page as the custom login page on an LWR site produces no error in Setup, but the site continues to render the default login page. The fix is to create an LWC with the `lightningCommunity__Page` target and assign it instead.
3. **`HeadlessSelfRegistrationHandler` is a different interface than `Auth.RegistrationHandler`** — The two interfaces share a `createUser()` method name but are entirely different Apex types. A class that implements `Auth.RegistrationHandler` cannot be assigned in the Headless Identity settings; doing so causes a runtime error. Implement `Auth.HeadlessSelfRegistrationHandler` for headless flows.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Auth Provider configuration | Setup record connecting Salesforce to external IdP |
| Registration Handler Apex class | Apex class implementing the correct handler interface for user creation/matching |
| Custom login page component | VF page (Aura) or LWC bundle (LWR) handling the login UI |
| Headless Identity handler classes | `HeadlessUserDiscoveryHandler` and `HeadlessSelfRegistrationHandler` implementations for headless flows |
| Federation ID mapping | Documentation of how IdP subject maps to `User.FederationIdentifier` |

---

## Related Skills

- security/ip-range-and-login-flow-strategy — Post-authentication login flows that run after Experience Cloud SSO completes; use when you need MFA enforcement or custom verification steps on top of social login
