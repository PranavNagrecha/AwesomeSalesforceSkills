---
name: experience-cloud-lwc-components
description: "Use when building custom LWC components for Experience Cloud (Experience Builder sites, LWR portals, Aura-based communities). Covers community context imports, guest user Apex access patterns, navigation API differences between LWR and Aura, and JS-meta.xml target configuration for Experience Builder exposure. NOT for internal LWC components deployed to Lightning App Builder or standard record pages (see lwc/lwc-development). NOT for Aura community components. Trigger keywords: build LWC for Experience Cloud, custom component community portal LWC, guest user LWC component, community context import salesforce, lightningCommunity target, @salesforce/community, guest Apex."
category: lwc
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
triggers:
  - "build LWC for Experience Cloud"
  - "custom component community portal LWC"
  - "guest user LWC component"
  - "community context import salesforce"
  - "lightningCommunity target component not showing in Experience Builder"
  - "how do I expose LWC to Experience Builder"
tags:
  - experience-cloud
  - lwc
  - guest-user
  - community-context
  - lwr
  - lightning-navigation
inputs:
  - "Site type: LWR or Aura-based Experience Builder site"
  - Whether the component must be accessible to guest (unauthenticated) users
  - Apex classes the component calls, if any
  - Navigation targets the component must support
outputs:
  - LWC component files (JS, HTML, JS-meta.xml) configured for Experience Builder
  - Apex class annotated for guest and authenticated access
  - Navigation implementation matched to site runtime (LWR vs Aura)
  - Review checklist confirming security and exposure configuration
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Experience Cloud LWC Components

This skill activates when a practitioner needs to build or review custom LWC components for Experience Cloud sites (LWR or Aura-based). It covers the platform-specific APIs, Apex access requirements, navigation differences, and JS-meta.xml configuration that are unique to the Experience Builder context and do not apply to internal Lightning pages.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Site runtime:** Is this an LWR (Lightning Web Runtime) site or an Aura-based community? The navigation API, some base component availability, and theming APIs differ between runtimes.
- **Guest access requirement:** Does the component need to render for unauthenticated (guest) users? Guest Apex access requires explicit sharing model configuration and profile/permission-set grants — it is not automatic.
- **Apex involvement:** Which Apex classes does the component call? Each `@AuraEnabled` method needs explicit profile or permission-set access grants for both guest and authenticated portal users.
- **Platform constraint:** `@salesforce/community/Id`, `@salesforce/community/basePath`, and `@salesforce/user/isGuest` are scoped modules that only resolve inside Experience Builder. Deploying the component to a non-Experience-Builder target causes a runtime error on these imports.

---

## Core Concepts

### Community Context Modules

LWC components deployed to Experience Builder can import two community-scoped modules:

```js
import communityId from '@salesforce/community/Id';
import basePath from '@salesforce/community/basePath';
```

`communityId` returns the 18-character Site ID of the current community. `basePath` returns the URL path prefix (e.g., `/portal`) for the site — required when constructing client-side URLs to avoid hardcoding the site prefix.

**Critical constraint:** These modules are only available when the component target is `lightningCommunity__Default` or `lightningCommunity__Page`. Attempting to use them in a component deployed to `lightning__AppPage` or `lightning__RecordPage` throws a module resolution error at runtime. If a component must run in both internal and Experience Cloud contexts, guard the import with a lazy dynamic pattern or split the component into context-specific variants.

### Guest User Detection and Apex Security

```js
import isGuest from '@salesforce/user/isGuest';
```

`isGuest` is `true` when the viewing user is unauthenticated (the site Guest User profile). Use this to conditionally render UI elements that should only appear for logged-in users.

Apex classes called by a guest-accessible component must:

1. Use `with sharing` — without it the class executes in a system context and bypasses object- and record-level security for the Guest User profile.
2. Be explicitly granted to the Guest User profile via Profile settings or a Permission Set assigned to the guest user. Simply annotating with `@AuraEnabled` does not grant access.
3. Never expose sensitive records or fields that the Guest User profile's OWD and sharing rules would not permit.

For authenticated portal users, the same explicit profile/permission-set grant applies. Portal user licenses (Customer Community, Partner Community, etc.) do not automatically inherit internal permission sets.

### LWR vs Aura Navigation APIs

LWR sites use `lightning/navigation`:

```js
import { NavigationMixin } from 'lightning/navigation';
```

Aura-based communities use a community-specific `pageReference` type (`comm__namedPage`, `comm__loginPage`) through the same `NavigationMixin`. The page reference type names differ between runtimes:

| Scenario | LWR pageReference type | Aura community pageReference type |
|---|---|---|
| Named community page | `comm__namedPage` | `comm__namedPage` |
| Standard object list | `standard__objectPage` | `standard__objectPage` |
| Login page | `comm__loginPage` | `comm__loginPage` |

Despite some overlap, `lightning/navigation` import itself is the correct module in both runtimes as of Spring '25. Do **not** use the legacy `c/communityNavigation` utility or Aura `force:navigateToURL` events in LWC — those are Aura-specific and do not work in LWR.

### JS-meta.xml Target Configuration

A component only appears in the Experience Builder component palette when its `lwc/[name]/[name].js-meta.xml` declares the correct target:

```xml
<LightningComponentBundle>
  <apiVersion>61.0</apiVersion>
  <isExposed>true</isExposed>
  <targets>
    <target>lightningCommunity__Default</target>
  </targets>
  <targetConfigs>
    <targetConfig targets="lightningCommunity__Default">
      <!-- design attributes for audience targeting / admin config -->
    </targetConfig>
  </targetConfigs>
</LightningComponentBundle>
```

`lightningCommunity__Default` makes the component available in Experience Builder drag-and-drop. `lightningCommunity__Page` makes it available as a full-page component. Without `isExposed: true` the component does not appear in the palette even if the target is declared.

Design attributes declared inside `targetConfig` appear as configuration properties in Experience Builder, enabling admins to tailor component behavior per-audience without code changes.

---

## Common Patterns

### Pattern 1: Guest-Accessible Product Catalog Component

**When to use:** The component displays public-facing data (e.g., product listings, knowledge articles) visible without login.

**How it works:**
- Import `isGuest` to conditionally show a "Log in to purchase" CTA instead of the cart button.
- All SOQL runs in an Apex method declared `with sharing` and explicitly granted to the Guest User profile.
- basePath is used to build any internal links so the URL is portable across sandbox and production sites.

**Why not the alternative:** Omitting `with sharing` on the Apex class means the guest user executes queries as the system user, potentially returning records that OWD would block — a security violation flagged in penetration tests and Security Review.

### Pattern 2: Authenticated User Profile Component Using Community Context

**When to use:** The component personalizes content based on the current portal user's data or needs to link to other pages within the same site.

**How it works:**
- Import `communityId` to pass the site context to an Apex call that scopes queries to the correct site's data.
- Import `basePath` to prefix any programmatic navigation URLs.
- Use `NavigationMixin` with `standard__namedPage` or a `comm__namedPage` type as appropriate for the LWR or Aura runtime.
- Guard any admin-configurable properties with `@api` and declare them as `targetConfig` design attributes for Experience Builder admins.

**Why not the alternative:** Hard-coding the site prefix breaks when the component is reused across sandbox and production, or when the site path is renamed.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Component must be visible to guest users | Apex class uses `with sharing`; guest profile granted access via Profile settings | Without explicit grant, `@AuraEnabled` call throws a `System.NoAccessException` for unauthenticated users |
| Component navigates within site on LWR | `NavigationMixin` from `lightning/navigation` | LWR does not support Aura event-based navigation |
| Component navigates within site on Aura community | `NavigationMixin` from `lightning/navigation` with `comm__namedPage` page reference | Same module, runtime resolves page type correctly |
| Component should appear in Experience Builder palette | `isExposed: true` + `lightningCommunity__Default` target in JS-meta.xml | Missing either flag hides the component from the palette |
| Component needs different behavior per audience | Declare `@api` design attributes in `targetConfig` | Allows no-code configuration per audience segment in Experience Builder |
| Component reads community ID or base path | Import `@salesforce/community/Id` and `@salesforce/community/basePath` | These modules only resolve in Experience Builder targets — do not add them to components with internal targets |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner building an Experience Cloud LWC component:

1. **Confirm site runtime and access model.** Determine whether the site is LWR or Aura-based. Confirm which users (guest, authenticated portal, internal) will view the component. This drives Apex sharing model and navigation API choice.
2. **Configure JS-meta.xml targets.** Add `lightningCommunity__Default` (and/or `lightningCommunity__Page`) to the component's `<targets>`. Set `isExposed: true`. Add `<targetConfig>` entries for any admin-configurable properties. Do not add internal Lightning targets if community context modules are imported.
3. **Implement community context imports.** Import `@salesforce/community/Id` and `@salesforce/community/basePath` where needed. Import `@salesforce/user/isGuest` to gate UI sections. Confirm these imports are only used in components with Experience Builder targets.
4. **Implement Apex with correct sharing and access.** Declare all called Apex methods `@AuraEnabled`. Apply `with sharing` to the Apex class. After deployment, grant the class to the Guest User profile (if needed) and to the portal user profile or permission set.
5. **Implement navigation using the correct API.** Use `NavigationMixin` from `lightning/navigation`. Use `comm__namedPage` or `standard__namedPage` page reference types as appropriate for the runtime. Avoid hard-coded URL strings; use `basePath` as a prefix when constructing links.
6. **Validate and test.** Run the skill's `check_experience_cloud_lwc_components.py` against the component metadata to verify target and sharing flags. Test the component as a guest user in a sandbox preview. Test as an authenticated portal user. Confirm navigation works end-to-end in the target runtime.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] `JS-meta.xml` declares `lightningCommunity__Default` or `lightningCommunity__Page` target; `isExposed: true` is set
- [ ] Community context modules (`@salesforce/community/*`, `@salesforce/user/isGuest`) are only used in components with Experience Builder targets
- [ ] All called Apex classes use `with sharing`
- [ ] Guest User profile has explicit access to all `@AuraEnabled` methods the component calls (if guest access is required)
- [ ] Portal user profile or permission set has explicit access to all `@AuraEnabled` methods
- [ ] Navigation uses `NavigationMixin` from `lightning/navigation` — no legacy Aura event navigation
- [ ] `basePath` is used to construct any internal site URLs; no hard-coded site path prefixes
- [ ] Component tested as guest user in sandbox Experience Cloud preview
- [ ] Component tested as authenticated portal user

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **`@salesforce/community/*` modules throw at runtime outside Experience Builder** — These scoped modules resolve only when the component is rendered inside an Experience Builder page. If the same component is reused on a Lightning App Page or Record Page, the module import fails at runtime with an unresolved module error. Keep community-context-dependent components under `lightningCommunity__*` targets only, or split into a base component plus an Experience-Cloud-specific wrapper.
2. **Guest Apex without `with sharing` bypasses record-level security** — A common audit finding: the Apex class compiles and runs without error, but returns records that the Guest User profile's sharing configuration would block. The class silently elevates to system context. Always declare `with sharing` on classes invoked from guest-accessible components. Add a SOQL `WHERE` clause scoped to the site's data if needed.
3. **LWR and Aura navigation page-reference types are not fully interchangeable** — While both runtimes use `lightning/navigation`, certain page reference types (especially older community-specific ones like `comm__loginPage`) behave differently or resolve differently per runtime. Test navigation in the actual runtime — a reference that works in an Aura community sandbox may silently no-op or error in an LWR site.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| LWC component bundle | JS, HTML, CSS, and JS-meta.xml files with correct Experience Builder targets and community context imports |
| Apex class | `@AuraEnabled` methods with `with sharing`, ready for profile/permission-set grants |
| Profile/Permission Set grant checklist | List of `@AuraEnabled` methods requiring explicit access grants for guest and portal users |
| Experience Builder configuration | `targetConfig` design attributes for admin-configurable component properties |

---

## Related Skills

- `lwc/lwc-development` — use for internal LWC components deployed to Lightning App Builder or record pages; not Experience Builder
- `security/experience-cloud-security` — use when the core concern is site-wide sharing, guest user OWD, or portal user record visibility beyond individual component Apex access
- `flow/flow-for-experience-cloud` — use when the Experience Cloud requirement involves embedding Screen Flows rather than custom LWC components
