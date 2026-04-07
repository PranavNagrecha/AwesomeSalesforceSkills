---
name: experience-cloud-multi-idp-sso
description: "Use this skill when configuring multiple identity providers (OIDC and/or SAML) on a single Experience Cloud site or across tenant-specific portals in the same org — covering auth provider registration, Start SSO URL routing, Federation ID mapping, RegistrationHandler implementation, and simultaneous SP+IdP topology. Trigger keywords: multiple identity providers Experience Cloud, multi-tenant SSO community portal, vendor and citizen portal same site, OIDC SAML both on login page, tenant-specific login routing community. NOT for internal Salesforce employee SSO configuration. NOT for single auth provider setups — see experience-cloud-authentication for basic SSO."
category: lwc
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
triggers:
  - "multiple identity providers Experience Cloud login page"
  - "multi-tenant SSO community portal vendor citizen"
  - "OIDC SAML both auth providers same Experience Cloud site"
  - "tenant-specific login routing community parameter Start SSO URL"
  - "vendor portal corporate IdP citizen portal social IdP same org"
tags:
  - experience-cloud
  - sso
  - multi-idp
  - oidc
  - saml
  - auth-provider
  - federation-id
  - registration-handler
inputs:
  - "Names and protocols (OIDC or SAML) of each identity provider to surface"
  - "Experience Cloud site URL(s) and whether portals share an org or are separate sites"
  - "User matching strategy: Federation ID (SAML) or custom RegistrationHandler (OIDC)"
  - "Login page customization requirements (which providers to show per site)"
outputs:
  - "Auth Provider configuration steps per IdP"
  - "Start SSO URL per provider with correct community parameter"
  - "Federation ID population guidance for SAML user matching"
  - "Apex RegistrationHandler skeleton for OIDC user lookup/creation"
  - "Login page customization guidance to surface correct providers per site"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Experience Cloud Multi-IdP SSO

This skill activates when an org needs to present more than one identity provider on an Experience Cloud site's login page, or when separate portals in the same org must route users to different IdPs. It covers auth provider registration, Start SSO URL construction, Federation ID mapping, RegistrationHandler implementation, and the SP+IdP simultaneous topology.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm each IdP's protocol (SAML 2.0 or OIDC) and whether metadata XML (SAML) or discovery URL / client credentials (OIDC) are available from the IdP team.
- Identify whether this is a single site with multiple login buttons or multiple distinct sites (e.g., a vendor portal and a citizen portal) sharing the same Salesforce org.
- Check whether Federation ID is already populated on User records for SAML-bound users; missing Federation ID is the single most common activation failure.
- Determine whether Salesforce itself must act as an IdP (e.g., for a connected third-party app) while also acting as SP — this SP+IdP topology requires extra care to avoid redirect loops.

---

## Core Concepts

### Auth Providers and the Start SSO URL

Each identity provider is registered in Salesforce as an **Auth. Provider** record (Setup > Auth. Providers). Each Auth Provider registration generates a unique **Start SSO URL** in the format:

```
https://<my-domain>.my.salesforce.com/services/auth/sso/<provider-name>?community=<site-base-url>
```

The `community` query parameter is what routes the browser back to the correct Experience Cloud site after authentication. Without it, the user lands on the internal org login page, not the portal. Multiple Auth Providers can be registered in the same org; each gets its own Start SSO URL.

### Federation ID as the SAML Matching Key

When Salesforce receives a SAML assertion, it maps the incoming `Subject` NameID value to a User record using the **Federation ID** field (`FederationIdentifier` on the User object). The Federation ID must be populated on every User record that will authenticate via SAML before SSO is activated. It is not auto-populated from any standard field. If the field is blank, the SAML assertion silently fails to match and the user receives a generic login error.

### RegistrationHandler for OIDC User Matching and Provisioning

For OIDC auth providers, Salesforce delegates user lookup and creation to a developer-supplied **RegistrationHandler** Apex class. The class implements the `Auth.RegistrationHandler` interface and must implement two methods: `createUser` and `updateUser`. The `createUser` method is called for first-time logins; `updateUser` is called for subsequent logins. User matching is the implementer's responsibility — typically matching on email or a custom external ID claim from the OIDC token. Without a RegistrationHandler, OIDC SSO cannot proceed.

### SF as Simultaneous SP and IdP

Salesforce can act as a **Service Provider** (receiving SAML assertions from an external IdP) and as an **Identity Provider** (issuing SAML assertions to connected apps) at the same time within the same org. This is required when, for example, an Experience Cloud site federates with a corporate IdP for authentication but Salesforce also needs to issue assertions to a third-party SaaS. The topology is valid but requires that the Connected App used for the outbound IdP role does not inadvertently redirect through the same login flow, which creates a redirect loop.

---

## Common Patterns

### Pattern 1: Multi-Provider Login Page on a Single Site

**When to use:** A single Experience Cloud site must offer two or more login options — for example, "Log in with Okta (corporate)" and "Log in with Google (social)" — on the same login page.

**How it works:**

1. Register each IdP as a separate Auth Provider record in Setup.
2. For each Auth Provider, note its generated Start SSO URL and append `?community=https://<site-base-url>`.
3. In Experience Builder, open the Login page and add a **Social Login** component (or a custom LWC) for each provider.
4. Configure each component's URL to the corresponding Start SSO URL with the community parameter.
5. Optionally, suppress the standard username/password form if all users are federated.

**Why not one provider with multiple mappings:** SAML and OIDC are distinct protocols with different assertion structures; a single Auth Provider record is tied to exactly one protocol and one IdP endpoint. Trying to handle two IdPs in one record is not supported.

### Pattern 2: Tenant-Specific Portal Routing (Vendor + Citizen Portals)

**When to use:** An org hosts two Experience Cloud sites — one for corporate vendors (SAML, corporate IdP) and one for citizens/consumers (OIDC, social IdP). Both sites share the same Salesforce org but must show different login providers.

**How it works:**

1. Register the corporate SAML IdP as Auth Provider A and the social OIDC IdP as Auth Provider B.
2. For the vendor portal login page, expose only the Start SSO URL for Auth Provider A with `?community=<vendor-site-url>`.
3. For the citizen portal login page, expose only the Start SSO URL for Auth Provider B with `?community=<citizen-site-url>`.
4. The `community` parameter in each URL ensures post-authentication redirect lands on the correct portal.
5. User records for vendor users carry a populated Federation ID; citizen users are created or matched by the OIDC RegistrationHandler.

**Why not separate orgs:** Separate orgs multiply licensing cost, data integration complexity, and release management overhead. One org with two sites and two auth providers is the standard multi-tenant pattern.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Two IdPs on one portal login page | Register each as a separate Auth Provider; link both Start SSO URLs on the login page | Each provider is independent; one login page can host multiple SSO buttons |
| Separate portals in same org need different IdPs | One Auth Provider per IdP; use `community` parameter to route each to its portal | `community` parameter is the canonical routing key — do not use separate orgs |
| SAML IdP, existing users | Populate Federation ID on User records before activating SSO | Missing Federation ID is the most common SAML activation failure |
| OIDC IdP, new or external users | Implement RegistrationHandler; match on email or a stable external claim | OIDC cannot proceed without a RegistrationHandler |
| SF must also act as IdP for a connected app | Configure Connected App for outbound IdP role separately; test for redirect loops | SP+IdP topology is valid but redirect loops are a real operational risk |
| Users hit internal org login instead of portal | Add `?community=<site-base-url>` to every Start SSO URL | Missing community parameter is the most common routing failure |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Inventory providers and protocols** — List every IdP, its protocol (SAML or OIDC), and which Experience Cloud site(s) it should serve. Confirm metadata XML or OIDC discovery URL is in hand before touching Setup.
2. **Register Auth Providers** — In Setup > Auth. Providers, create one Auth Provider record per IdP. For SAML, upload the IdP metadata XML or enter the entity ID and SSO URL manually. For OIDC, enter the consumer key, consumer secret, and authorization/token/userinfo endpoints. Note the generated Start SSO URL for each.
3. **Implement and assign RegistrationHandler (OIDC only)** — Write a class implementing `Auth.RegistrationHandler`. In `createUser`, look up the User by email or a stable claim; create if not found. In `updateUser`, sync any changed claims. Assign the class to the OIDC Auth Provider record.
4. **Populate Federation ID (SAML only)** — Before activating SAML SSO, bulk-update the `FederationIdentifier` field on all affected User records to match the NameID value the IdP will send. Validate with a test SAML assertion in a sandbox first.
5. **Configure login pages** — In Experience Builder for each site, add login buttons or Social Login components pointing to the correct Start SSO URL with the `?community=<site-base-url>` parameter. Verify each button opens the correct IdP and returns to the correct portal.
6. **Test end-to-end and validate SP+IdP if applicable** — Test each provider independently in a sandbox. If Salesforce also acts as an IdP for a connected app, trace the redirect chain to confirm no loops exist. Review login history and error logs for silent failures.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Each IdP registered as its own Auth Provider record with correct protocol and endpoint configuration
- [ ] Every Start SSO URL includes the `?community=<site-base-url>` parameter pointing to the correct portal
- [ ] Federation ID populated on all User records that will authenticate via SAML before SSO activation
- [ ] RegistrationHandler implemented and assigned to each OIDC Auth Provider; `createUser` and `updateUser` both handled
- [ ] Login pages show only the appropriate providers for each site (vendor portal shows corporate IdP only, citizen portal shows social IdP only)
- [ ] SP+IdP topology tested for redirect loops if Salesforce issues assertions to connected apps
- [ ] Login history and debug logs reviewed for silent match failures after first live test

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Missing `community` parameter silently routes to internal org** — The Start SSO URL generated by Setup does not include the `community` parameter by default. When this parameter is absent, the post-authentication redirect sends users to the internal Salesforce org login page rather than the Experience Cloud site. There is no error message; users simply land in the wrong place.
2. **Federation ID must be pre-populated; it is not derived from Username or Email** — Salesforce does not auto-populate `FederationIdentifier` from any other field. Activating SAML SSO with blank Federation IDs causes every affected user to receive a generic "We can't log you in" error with no actionable server-side message. Pre-populate via a Data Loader bulk update and verify one test user in sandbox before activating production SSO.
3. **SP+IdP simultaneous use can produce redirect loops** — When Salesforce acts as both SP (receiving assertions from an external IdP) and IdP (issuing assertions to a connected app), a misconfigured Connected App login URL or a browser that follows redirects without session state can enter an infinite SP→IdP→SP loop. Break the loop by ensuring the Connected App's Start URL is a resource URL, not the login initiation endpoint.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Auth Provider configuration checklist | Per-IdP setup steps covering protocol, endpoints, and RegistrationHandler assignment |
| Start SSO URL inventory | Table of each provider's Start SSO URL with community parameter for each target site |
| RegistrationHandler skeleton | Apex class implementing `Auth.RegistrationHandler` with user lookup and creation logic |
| Federation ID population runbook | Steps to bulk-load `FederationIdentifier` values before activating SAML SSO |
| Login page configuration notes | Experience Builder steps to surface correct providers per site |

---

## Related Skills

- experience-cloud-authentication — basic single auth provider SSO and guest user access configuration
- architect/multi-org-strategy — when the question is whether to consolidate tenants into one org vs separate orgs
