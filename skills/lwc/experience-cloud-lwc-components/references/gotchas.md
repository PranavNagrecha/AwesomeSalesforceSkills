# Gotchas — Experience Cloud LWC Components

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: `@salesforce/community/*` Modules Throw at Runtime Outside Experience Builder

**What happens:** A component that imports `@salesforce/community/Id`, `@salesforce/community/basePath`, or `@salesforce/user/isGuest` renders fine in Experience Builder preview but throws a module resolution error — breaking the entire page — when the same component is placed on a Lightning App Page, Record Page, or Home Page.

**When it occurs:** Whenever a component with community context imports is added to a non-Experience-Builder target. This typically surfaces during a refactor when a developer adds `lightning__AppPage` to JS-meta.xml thinking it makes the component more reusable, or when an admin drags the component onto an internal page without realizing the import constraint.

**How to avoid:** Never add internal Lightning targets (`lightning__AppPage`, `lightning__RecordPage`, etc.) to components that import `@salesforce/community/*` or `@salesforce/user/isGuest`. If the component logic must be shared, extract the community-independent logic into a base component with no community imports, and create a thin Experience Builder wrapper that imports community modules and passes values as `@api` properties.

---

## Gotcha 2: Guest Apex Without `with sharing` Silently Bypasses Record-Level Security

**What happens:** An Apex class called by a guest-accessible component compiles and runs without error, but returns records that the Guest User profile's OWD, sharing rules, and criteria-based sharing would normally block. There is no runtime exception — the query succeeds and returns data.

**When it occurs:** Any time an Apex class is declared `without sharing` (or inherits system context because sharing is not specified) and is invoked from a component accessible to unauthenticated site visitors. The Guest User runs as a special system-elevated context when the class omits `with sharing`.

**How to avoid:** Declare `with sharing` on every Apex class called from a guest-accessible component. Add `WITH USER_MODE` to SOQL/SOSL queries inside those classes to enforce CRUD and FLS on top of sharing. If the class must run mixed sharing contexts (e.g., a utility called from both internal and external code), use explicit sharing keywords per method or split into separate classes with documented sharing intent. Flag any `without sharing` class that is `@AuraEnabled` in code review.

---

## Gotcha 3: LWR and Aura Navigation APIs Are Not Interchangeable

**What happens:** A component that navigates using an Aura community-specific `pageReference` type (e.g., an event-based `force:navigateToURL` or a `comm__loginPage` reference built for the Aura runtime) fails silently or produces a no-op in an LWR site. Conversely, some LWR-specific navigation syntax is not recognized in Aura communities.

**When it occurs:** When a component originally built for an Aura community is migrated to or reused in an LWR site without updating the navigation logic. The component may not surface any error — navigation simply does nothing or redirects to an unexpected page.

**How to avoid:** Always confirm the site runtime before implementing navigation. For LWR sites, use `NavigationMixin` from `lightning/navigation` with standard page reference types (`standard__namedPage`, `standard__objectPage`, `comm__namedPage`). Never use Aura-specific navigation events (`force:navigateToURL`, `force:navigateToComponent`) in LWC. Test navigation end-to-end in the actual target runtime — sandbox previews in Experience Builder reflect the runtime accurately.

---

## Gotcha 4: Missing `isExposed: true` Hides Component from Experience Builder Palette

**What happens:** A component with the `lightningCommunity__Default` target declared in JS-meta.xml does not appear in the Experience Builder component panel. Builders cannot add it to any page.

**When it occurs:** When `<isExposed>false</isExposed>` is explicitly set or when the `<isExposed>` element is omitted (it defaults to `false`). This frequently happens when a component is first scaffolded for internal use and later repurposed for Experience Cloud without updating the metadata.

**How to avoid:** Set `<isExposed>true</isExposed>` in JS-meta.xml any time the component is intended for Experience Builder drag-and-drop placement. The `check_experience_cloud_lwc_components.py` script in this skill flags missing or `false` `isExposed` values automatically.

---

## Gotcha 5: `@AuraEnabled` Grant Required Separately for Guest and Portal Users

**What happens:** An Apex method decorated with `@AuraEnabled` works for internal users and even for some authenticated portal users, but throws `System.NoAccessException` for guest users — or for portal users on a different profile that was not explicitly granted access.

**When it occurs:** After deployment, when the Apex class has not been granted to the Guest User profile (for guest access) or to the portal user profile or permission set (for authenticated portal access). `@AuraEnabled` makes the method callable via Lightning data channels, but it does not grant profile-level access to the class. Each profile or permission set must have the class explicitly listed under Apex Class Access.

**How to avoid:** After deploying any Apex class called from an Experience Cloud component, grant it explicitly: Setup > Experience Cloud Sites > [Site] > Workspaces > Administration > Guest User Profile > Apex Class Access (for guest). For authenticated portal users: Setup > Profiles > [Portal Profile] > Apex Class Access, or via a Permission Set. Include these grants in the deployment package or post-deploy script so they are not forgotten in future deployments.
