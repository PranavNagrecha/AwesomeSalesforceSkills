---
name: experience-cloud-api-access
description: "Use this skill when configuring or troubleshooting API access for Experience Cloud external users and guest users: guest user Apex data access, Customer Community Plus or Partner Community REST/SOAP API access, external user OAuth scopes, and sharing enforcement on API responses. Trigger keywords: Experience Cloud API access external user, community user REST API, guest user API limits, Customer Community API permissions, external user OAuth. NOT for internal Salesforce API authentication, non-community OAuth flows, or internal user API security."
category: lwc
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
triggers:
  - "Experience Cloud API access external user — how do I let a community user call an Apex endpoint"
  - "community user REST API — can a Customer Community user call the Salesforce REST API directly"
  - "guest user API limits — what data can an unauthenticated guest user access via Apex"
  - "Customer Community API permissions — why does my Customer Community user get an error calling the REST API"
  - "external user OAuth — what OAuth scopes apply to Partner Community or Customer Community Plus users"
tags:
  - experience-cloud
  - api-access
  - guest-user
  - external-user
  - oauth
  - community
  - sharing
  - fls
inputs:
  - "Experience Cloud license type in use (Customer Community, Customer Community Plus, or Partner Community)"
  - "Whether guest (unauthenticated) access is enabled on the site"
  - "List of Apex classes or REST resources the external user needs to call"
  - "Current guest profile object permissions and FLS settings"
  - "External OWD settings for objects the API response will touch"
outputs:
  - "Assessment of whether the required API access is achievable for the given license type"
  - "Recommended Apex with-sharing pattern and FLS configuration for guest or external users"
  - "Permission set and profile configuration steps for Customer Community Plus or Partner Community API access"
  - "Checklist of sharing enforcement and data leakage risks"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Experience Cloud API Access

This skill activates when a practitioner needs to configure or troubleshoot API access for Experience Cloud external users (guest, Customer Community, Customer Community Plus, or Partner Community). It covers the hard license-tier boundaries on REST/SOAP API access, Apex sharing enforcement for guest users, and the OAuth scope model for authenticated external users. It does NOT cover internal user API authentication or non-community OAuth flows.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Identify the license tier:** Customer Community, Customer Community Plus, or Partner Community. The license determines whether direct REST/SOAP API access is possible at all — this is a hard platform constraint, not a permission issue.
- **Determine user type:** Guest (unauthenticated) vs. authenticated external user. Guest users have no named session and cannot authenticate with OAuth. The most common wrong assumption is treating guest user API constraints as a permission gap fixable with permission sets.
- **Check FLS on the guest profile:** Field-level security on the guest profile is the hard enforcement boundary for Apex running on behalf of guest users. Permission sets grant class access but they do not override guest profile FLS.
- **Review external OWDs:** External object-wide defaults (OWDs) control what records API responses can return to external users. These are distinct from internal OWDs and must be set explicitly.
- **Confirm whether the Apex class runs with or without sharing:** For guest users, `with sharing` is required. Running `without sharing` on guest-accessible Apex is a critical security violation.

---

## Core Concepts

### Guest Users Have No OAuth Context and No Named Session

Guest users access Experience Cloud sites without authenticating. They have no Salesforce user session in the OAuth sense and cannot use OAuth 2.0 flows to obtain access tokens. All Apex that runs on behalf of a guest user runs in the context of the **guest user profile** — a special system profile automatically created for each site. Because there is no named session, guest users cannot call the Salesforce REST or SOAP API directly. Any data access must go through Apex classes explicitly enabled on the guest profile.

The guest user profile has its own object permissions and FLS settings that are completely separate from permission sets. Permission sets can grant guest users access to Apex classes, but they cannot override FLS defined on the guest profile itself. FLS on the guest profile is the final enforcement boundary.

### Customer Community License Cannot Access REST/SOAP API Directly

Customer Community is a high-volume, low-cost license intended for self-service portal users. It does **not** include the ability to call the Salesforce REST or SOAP API directly from an external application. This is a license-level restriction, not a permission configuration problem. Adding permission sets, enabling API access in profiles, or opening sharing rules will not change this. The user simply does not have the platform entitlement.

If a Customer Community user needs programmatic data access, it must go through Apex classes surfaced via Experience Cloud pages, or through a mid-tier server-side integration using a separate integration user credential (not the community user credential).

### Customer Community Plus and Partner Community Support REST/SOAP API Access

Customer Community Plus and Partner Community licenses include API access entitlement. Authenticated users on these licenses can call Salesforce REST and SOAP API endpoints using OAuth-obtained access tokens, subject to:

- **Sharing rules and external OWDs:** The API response is filtered by the sharing model. Records the user cannot see in the UI are also invisible via API. External OWDs must explicitly grant access — external users default to private on most objects unless configured.
- **Profile and permission set API access setting:** The user's profile must have the "API Enabled" permission. For external profiles this is often disabled by default.
- **Per-request and daily API limits:** External users consume the org's shared API request limits. Customer Community Plus and Partner Community licenses each carry a per-user-per-day API call allocation that counts against org limits.

### Apex Sharing Enforcement for External User API Calls

When an LWC component on an Experience Cloud page calls an Apex `@AuraEnabled` or `@RemoteAction` method, the method runs in the context of the logged-in external user. For authenticated external users (Customer Community Plus, Partner Community), Apex declared `with sharing` enforces the user's sharing access, profile object permissions, and FLS. For guest users, the same applies but against the guest profile's permissions.

Running Apex `without sharing` for guest-accessible endpoints exposes all records in the org regardless of the guest profile configuration. This is the most common data exposure pattern in Experience Cloud implementations.

---

## Common Patterns

### Pattern 1: Apex Gateway for Guest User Data Access

**When to use:** An unauthenticated page on an Experience Cloud site needs to display or submit data — for example, a product catalog or a case submission form.

**How it works:**
1. Create an Apex class declared `with sharing`.
2. Add the Apex class to the guest user profile via Setup > Experience Cloud > Guest User Profile > Apex Class Access.
3. Configure object-level permissions and FLS on the guest profile for only the minimum fields needed.
4. Set external OWDs for the objects to the minimum necessary (typically "Public Read Only" for catalog-style data, or "Private" with a sharing rule for record-specific access).
5. Expose the Apex class via `@AuraEnabled` and call it from the LWC component.

**Why not the alternative:** Calling a public REST resource endpoint directly from the browser would require CORS configuration, no authentication enforcement, and would bypass the guest profile FLS — exposing broader data. An Apex gateway lets the platform enforce the guest profile as the security boundary.

```apex
public with sharing class GuestProductController {
    @AuraEnabled(cacheable=true)
    public static List<Product2> getProducts() {
        // with sharing enforces guest profile FLS and object permissions
        return [SELECT Id, Name, Description FROM Product2 WHERE IsActive = true];
    }
}
```

### Pattern 2: OAuth-Based REST API Access for Partner Community Users

**When to use:** A Partner Community user needs to call Salesforce REST API from a server-side integration or mobile application, not from within the Experience Cloud site itself.

**How it works:**
1. Confirm the user holds a Partner Community or Customer Community Plus license (required for API access).
2. Enable "API Enabled" on the external user's profile (Setup > Profiles > [External Profile] > System Permissions).
3. Create a Connected App with the required OAuth scopes. For external users with limited data access, `api` scope is sufficient. Do not grant `full` scope.
4. Use the OAuth 2.0 Username-Password or JWT Bearer flow for server-side integrations (user-context flows for interactive apps).
5. Verify external OWDs ensure the user can see the records the API response returns — use Sharing Debugger or test with a real user record.
6. Monitor API usage via Setup > API Usage to ensure allocations are not exhausted.

**Why not the alternative:** Using an integration user with a full System Administrator profile (a common shortcut) bypasses all the sharing enforcement and exposes the entire org's data. Always use the actual community user credential so the platform's sharing model acts as the data filter.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Guest user needs read-only catalog data | Apex `with sharing` class, enabled on guest profile, with Public Read Only external OWD on the object | Only viable path — guest users have no API access. FLS on guest profile is the hard boundary. |
| Guest user needs to submit a form (create record) | Apex `with sharing` class with explicit insert, minimum object/field permissions on guest profile | Same Apex gateway pattern; use `Schema.sObjectType.Case.fields.Subject.isCreateable()` to guard field writes |
| Customer Community user needs programmatic data access | Use a server-side mid-tier integration user, not the community user credential | Customer Community license does not include API entitlement — no configuration can change this |
| Customer Community Plus user needs REST API access | Enable "API Enabled" on profile, configure Connected App with `api` scope, confirm external OWDs | License supports it; sharing enforcement is still fully in effect |
| Partner Community user needs REST API access | Same as Customer Community Plus; also validate Sharing Sets and Share Groups if data access is unexpectedly narrow | Partner Community has the broadest external user API entitlement |
| Any external user's API response omits expected records | Check external OWDs, Sharing Sets, and Share Groups — not just profile permissions | External OWDs are separate from internal OWDs and default to more restrictive values |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Establish license tier and user type** — confirm whether the user is guest (unauthenticated), Customer Community, Customer Community Plus, or Partner Community. If the user is Customer Community, stop: direct REST/SOAP API access is not available for this license. Redirect to the Apex gateway pattern for on-page data access, or a mid-tier integration for server-side access.
2. **Audit the guest profile or external profile** — for guest users, check object permissions and FLS on the guest site profile directly (not via permission sets). For authenticated external users, check the profile's "API Enabled" system permission. Identify the minimum permissions needed and remove everything else.
3. **Review external OWDs and sharing configuration** — check external OWDs for every object the API call will touch. Confirm Sharing Sets or Share Groups are configured if the user needs access to records they own or that are related to their account. Use the Sharing Debugger to verify actual access.
4. **Implement or review the Apex class** — for guest user access, confirm every Apex class is declared `with sharing`. Add explicit CRUD/FLS checks using `Schema.sObjectType` guards before any DML. For authenticated external users calling the API directly, confirm the Connected App scope is the minimum required (`api`, not `full`).
5. **Test with a real external user credential** — do not test with a System Administrator or internal user. Use a test user holding the actual external license and profile. Verify both the positive case (expected data returned) and the negative case (records outside sharing are not returned). Check API usage limits post-test.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] License tier confirmed — Customer Community users are not being asked to call REST/SOAP API directly
- [ ] Guest profile FLS is the minimum necessary — no extra object or field permissions left open
- [ ] Every guest-accessible Apex class is declared `with sharing` — no `without sharing` on public-facing endpoints
- [ ] External OWDs are reviewed for all objects touched by the API call — they do not default from internal OWDs
- [ ] "API Enabled" system permission is set on the external user profile for Customer Community Plus or Partner Community users
- [ ] Connected App OAuth scopes are `api` (not `full`) for external user integrations
- [ ] Sharing Debugger or test user verification confirms records outside sharing are not visible via API
- [ ] API usage allocation reviewed — external user API calls consume org-level limits

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Customer Community license API access is a hard platform limit, not a permission gap** — Adding "API Enabled" to a Customer Community profile or granting the permission via permission set has no effect. The license itself does not include API entitlement. Support cases, partner escalations, and workaround attempts will all fail. The only path is to upgrade the license or use a mid-tier integration.
2. **Guest profile FLS is independent of permission sets** — Permission sets can grant a guest user Apex class access. They cannot grant field-level permissions. FLS for guest users is configured exclusively on the guest user profile (Setup > Users > [site guest user] > Edit > Field Permissions). This surprises practitioners who use permission sets for all other FLS management.
3. **External OWDs are not inherited from internal OWDs** — An object with Public Read/Write as its internal OWD can still have a "Private" external OWD. Changing the internal OWD does not change the external OWD. Practitioners often diagnose sharing issues without checking the external OWD row in Setup > Sharing Settings.
4. **`without sharing` Apex on a guest-accessible endpoint bypasses all guest profile restrictions** — If an Apex class called by a guest user is declared `without sharing` or inherits `without sharing` from a calling class, it runs in system context and can return any record in the org. The guest profile and external OWDs provide no protection in this scenario.
5. **OAuth flows cannot be used by guest users — there is no token to obtain** — Guest users browse anonymously. There is no login, no session, and no mechanism to exchange credentials for an access token. Patterns like the OAuth 2.0 Client Credentials flow for guest user API access are inapplicable to Experience Cloud guest sessions.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| License tier assessment | Determination of whether the requested API access is achievable given the user's Experience Cloud license |
| Guest profile configuration checklist | Object permissions and FLS settings needed on the guest profile for Apex gateway patterns |
| Apex class review | Confirmation that all guest-accessible and external-user-accessible Apex classes use `with sharing` and explicit CRUD/FLS guards |
| External OWD review | Summary of external OWD settings for all objects touched by the API call, with recommended changes |
| Connected App OAuth scope recommendation | Minimum OAuth scope set for Customer Community Plus or Partner Community API access |

---

## Related Skills

- security/experience-cloud-security — authenticated external user sharing model, Sharing Sets, Share Groups, external OWDs, and guest user record hardening
- security/guest-user-security — deep-dive on guest user profile hardening, object permission minimization, and site security posture
- lwc/lwc-apex-patterns — Apex `@AuraEnabled` design patterns for LWC components, including CRUD/FLS enforcement
