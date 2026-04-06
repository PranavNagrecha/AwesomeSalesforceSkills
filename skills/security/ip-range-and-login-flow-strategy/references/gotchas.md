# Gotchas — IP Range and Login Flow Strategy

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Login Flow User Has Severely Limited Permissions

**What happens:** Apex actions invoked from a Login Flow fail with `INSUFFICIENT_ACCESS_OR_READONLY` or `System.SecurityException` because the flow runs as the Login Flow User, not as the authenticating user. Standard DML on User, Contact, or custom objects may be denied.

**When it occurs:** Any time a Login Flow attempts to update records, query objects with restrictive sharing, or call Apex methods that rely on `UserInfo.getUserId()` returning a real user. The Login Flow User is a system principal with a narrow set of permissions.

**How to avoid:** Write Apex Invocable classes that run `without sharing` for Login Flow contexts. Explicitly pass the user's ID via `$Flow.LoginFlow_UserId` rather than relying on `UserInfo.getUserId()`. Test every Apex action from within the actual login flow, not from Flow Builder's debug mode (which runs as the admin).

---

## Gotcha 2: Site-Level Login Flow Silently Overrides Profile-Level Flow

**What happens:** A community user's profile has a Login Flow assigned, and the Experience Cloud site also has a Login Flow. Only the site-level flow runs. The profile-level flow is completely skipped -- it is not chained or executed afterward.

**When it occurs:** When both profile and site assignments exist for the same user population. This is common in orgs that configure profile-level flows for internal users and then add a site-level flow for an Experience Cloud site, not realizing that community users on that site lose their profile-level flow.

**How to avoid:** Use site-level Login Flow assignment for all Experience Cloud users. If you need logic that was previously in a profile-level flow, consolidate it into the site-level flow. Audit Setup > Login Flows to identify dual-assignment conflicts.

---

## Gotcha 3: Unhandled Flow Faults Strand Users at Login

**What happens:** If a Login Flow encounters an unhandled Apex exception, null pointer, or any fault without a Fault connector, the user sees a generic error page and cannot proceed into the org. There is no automatic bypass, and the user cannot retry without the flow executing again.

**When it occurs:** Commonly during the first deployment when Apex actions have not been tested in the login context (see Gotcha 1), or when a Custom Metadata record is missing and the flow's Get Records returns null but the next element does not handle the null case.

**How to avoid:** Add Fault connectors to every Apex Action and Get Records element. Route faults to a screen that displays a user-friendly message and provides a "Continue" button that leads to the flow's End element (allowing the user to enter the org despite the error). Log the fault details via Platform Events or a custom Apex logger so admins are notified.

---

## Gotcha 4: Login Flow Debug Mode Does Not Replicate the Login Context

**What happens:** A Login Flow works perfectly in Flow Builder's Debug mode but fails in the actual login process. Components render differently, Apex actions that succeed in debug fail in production, and `$Flow.LoginFlow_UserId` is null during debug.

**When it occurs:** Every time a developer tests exclusively through Flow Builder debug without testing the actual login experience. Debug mode runs as the current admin user with full permissions, which masks permission errors and context-dependent failures.

**How to avoid:** Always test Login Flows by actually logging in as a test user assigned to the target profile. Use a separate browser or incognito window. Debug mode is useful for flow logic development but is not a substitute for end-to-end login testing.

---

## Gotcha 5: Login Flows Add Latency to Every Login

**What happens:** Every screen in a Login Flow adds visible latency to the login experience. Users perceive the login as slow, especially if the flow calls Apex actions that query Custom Metadata, perform callouts, or run complex logic before the first screen renders.

**When it occurs:** When the Login Flow has multiple screens on the happy path (trusted IP, data already collected), or when Apex actions are not optimized. This is most noticeable on mobile devices or high-latency networks.

**How to avoid:** Design the flow so that the happy path (most common case) has zero or one screen. Use Decision elements early to skip unnecessary screens. Cache Apex results where possible. Measure login time before and after deploying the flow to quantify the impact.

---

## Gotcha 6: ConnectedAppPlugin Runs in a Different Context Than Login Flows

**What happens:** A developer builds IP-based logic in a `ConnectedAppPlugin.authorize()` override, expecting it to run during standard UI login. It only runs when the login occurs through the associated Connected App (OAuth flow), not during standard username/password or SSO login.

**When it occurs:** When the requirement is to customize the login experience for mobile app users (who authenticate via a Connected App) but the developer conflates ConnectedAppPlugin with Login Flows. They serve different authentication pathways.

**How to avoid:** Use Login Flows for standard UI login customization (profile/site assignment). Use ConnectedAppPlugin for Connected App OAuth customization. If both pathways need the same logic, implement the logic in a shared Apex utility class called from both the Login Flow's Invocable and the ConnectedAppPlugin's `authorize()` method.
