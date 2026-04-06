---
name: ip-range-and-login-flow-strategy
description: "Design and implement Salesforce Login Flows (Screen Flows assigned to profiles or Experience Cloud sites) that run post-authentication to enforce conditional MFA, IP-based branching, terms-of-service acceptance, or user data collection. Covers Login Flow creation in Flow Builder, profile/site assignment, IP-aware decision logic, and ConnectedAppPlugin extension points. NOT for static IP allowlisting or profile Login IP Ranges (see network-security-and-trusted-ips), org-wide session policies, or SSO/SAML IdP configuration."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
triggers:
  - "I need to add a custom step after login that checks the user's IP and prompts for extra verification"
  - "how do I build a login flow in Salesforce that forces users to accept terms of service before entering the org"
  - "we want to conditionally require MFA only when users log in from outside our corporate network"
  - "how do I assign a screen flow to run during the Salesforce login process for a specific profile"
  - "our Experience Cloud site needs a custom login page that collects additional information from community users"
  - "I need to route users through a different login experience based on their IP address or device"
tags:
  - login-flow
  - conditional-mfa
  - ip-based-branching
  - post-authentication
  - experience-cloud-login
  - screen-flow
  - connected-app-plugin
inputs:
  - "Profile(s) or Experience Cloud site(s) that need a custom login flow"
  - "Business rules for post-authentication logic (IP ranges, MFA conditions, data collection requirements)"
  - "Current MFA enforcement status and Identity Verification requirements"
  - "Whether the target users are internal or Experience Cloud external users"
outputs:
  - "Screen Flow configured as a Login Flow in Flow Builder"
  - "Login Flow assignment to profile(s) or Experience Cloud site(s)"
  - "IP-based decision logic within the flow for conditional routing"
  - "Testing plan covering happy-path login, blocked-IP login, and edge cases"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-05
---

# IP Range and Login Flow Strategy

This skill activates when a practitioner needs to build, assign, or troubleshoot Salesforce Login Flows -- Screen Flows that execute after credential verification but before the user enters the org. Login Flows enable post-authentication logic such as conditional MFA challenges, IP-based routing, terms-of-service acceptance, user data collection, and Experience Cloud custom login pages. The skill covers the full lifecycle from flow design through profile assignment and testing.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Login Flows run after authentication, not instead of it** -- Salesforce authenticates the user's credentials first (username/password, SSO token, etc.), then invokes the Login Flow. The flow cannot replace or bypass standard authentication. It adds steps between credential verification and org entry.
- **Login Flows must be Screen Flows** -- Only flows of type "Screen Flow" can be assigned as Login Flows. Record-Triggered Flows, Autolaunched Flows, and Scheduled Flows cannot be used. The flow runs in a special login context with limited access to standard Lightning components.
- **Login Flows are assigned per profile or per Experience Cloud site, not per user or permission set** -- There is no user-level or permission-set-level assignment. If different users on the same profile need different login experiences, you must either split them into separate profiles or use decision logic inside a single flow.
- **The login context is restricted** -- Screen elements in a Login Flow cannot use all Lightning components. Custom LWC screens, certain flow actions, and Apex Invocable Actions that require full session context may fail. Subflows are supported but must also be Screen Flows.
- **`$Flow.LoginFlow_LoginType` and `$Flow.LoginFlow_UserId`** -- These system variables are available inside Login Flows to identify how the user authenticated and who they are, enabling conditional logic without custom Apex.

---

## Core Concepts

### Login Flows in Flow Builder

A Login Flow is a standard Screen Flow that has been designated as a Login Flow through assignment in Setup. You build it in Flow Builder like any other Screen Flow, but it executes in a special runtime context during the login process.

Key mechanics:
- The flow runs under the **Login Flow User** context, which has limited permissions. The flow can read the authenticating user's record and certain session attributes but cannot perform arbitrary DML on most objects.
- The flow can use **Decision** elements to branch based on `$Flow.LoginFlow_LoginType` (values: `Application`, `SAML Idp Initiated`, etc.), `$Flow.LoginFlow_UserId`, and custom formulas that inspect the user's IP via `{!$Api.Session_ID}` or Apex invocable methods.
- If the flow ends normally (reaches the end element), the user proceeds into the org. If the flow navigates to a **Fault** path or the user closes the browser, the login session is abandoned.
- Login Flows support **subflows** (Screen Flow type only) for modular design.

### Profile and Site Assignment

Login Flows are connected to profiles or Experience Cloud sites through Setup:

- **Profile assignment:** Setup > Login Flows > New > select the Screen Flow and the target profile. One Login Flow per profile. If a profile already has a Login Flow assigned, the new one replaces it.
- **Experience Cloud site assignment:** Setup > Digital Experiences > [Site] > Administration > Login & Registration > Login Flow. This applies to all users authenticating through that site regardless of profile.
- **Priority:** If both a profile-level and a site-level Login Flow exist, the site-level flow takes precedence for users logging in through that site.

### IP-Based Branching Inside Login Flows

Login Flows can implement conditional logic based on the user's source IP address. This is distinct from profile Login IP Ranges (which are a hard allow/deny at the network layer) -- Login Flow IP branching lets you add friction (extra screens, MFA prompts) for users from untrusted IPs while still allowing login.

Approaches to get the user's IP inside a flow:
1. **Apex Invocable Action** -- Create an `@InvocableMethod` that returns `Auth.SessionManagement.getCurrentSession().get('SourceIp')` or uses `ApexPages.currentPage().getHeaders().get('True-Client-IP')`. This is the most reliable method.
2. **ConnectedAppPlugin** -- For Connected App login contexts, extend `Auth.ConnectedAppPlugin` and override `authorize()` to inspect `Auth.InvocationContext` attributes. This is relevant when login occurs through a Connected App (mobile apps, third-party OAuth).
3. **Formula variable** -- In some contexts, `{!$Api.Session_ID}` combined with a `SessionPermSetActivation` or custom metadata lookup can approximate IP-based decisions, but this is less reliable than Apex.

Once you have the IP, use a **Decision** element to compare it against known corporate CIDR ranges (stored in Custom Metadata or a Custom Setting) and route to different screens accordingly.

### Conditional MFA via Login Flow

A Login Flow can prompt for additional verification factors beyond what Salesforce's built-in MFA requires. Common patterns:

- **Step-up MFA for untrusted IPs:** If the user's IP is outside the corporate range, display a screen that triggers an SMS or email verification code via an Apex action. If inside the range, skip the screen.
- **Terms acceptance gate:** Display a terms-of-service screen. If the user declines, route to a screen that logs the refusal and ends the flow with a message (user cannot proceed).
- **Data collection:** For first-time logins or periodic re-verification, display screens that collect phone numbers, department info, or consent flags, then update the User record via an Apex action.

Important: Login Flows do not replace Salesforce's native MFA enforcement. If the org has "MFA for Direct Logins" enabled, users complete Salesforce MFA first, then encounter the Login Flow. The Login Flow adds custom verification on top of, not instead of, native MFA.

---

## Common Patterns

### Pattern 1: IP-Aware Conditional Verification Flow

**When to use:** The organization wants users from corporate IPs to proceed directly after standard authentication, but users from external IPs must complete an additional verification step (SMS code, security question, or manager approval screen).

**How it works:**

1. Create an `@InvocableMethod` Apex class that returns the user's source IP.
2. Store corporate IP ranges in Custom Metadata (`Corporate_IP_Range__mdt`) with start/end fields.
3. Build a Screen Flow with:
   - An Action element calling the Invocable to get the IP
   - A Decision element comparing the IP against the Custom Metadata ranges
   - Trusted path: proceed to end (user enters org)
   - Untrusted path: display a verification screen, then proceed to end on success
4. Assign the flow as a Login Flow to the target profile(s).

**Why not use Login IP Ranges for this:** Login IP Ranges on the profile are a hard deny -- users outside the range cannot log in at all. This pattern allows login from any IP but adds friction for untrusted locations. This is the right choice when remote work and travel are common but extra verification is desired.

### Pattern 2: Experience Cloud Custom Login Page with Data Collection

**When to use:** An Experience Cloud site needs to collect additional user information (phone number, company name, consent flags) during login, or display a terms-of-service acceptance screen before granting access.

**How it works:**

1. Build a Screen Flow with:
   - A Get Records element to check whether the user has already completed the required data (e.g., `User.Phone != null` or a custom checkbox `Terms_Accepted__c = true`)
   - A Decision element: if data is complete, skip to end; otherwise, display the collection screen
   - A Screen element with input fields for the required data
   - An Apex action or Record Update to save the collected data to the User record
2. Assign the flow to the Experience Cloud site under Administration > Login & Registration > Login Flow.
3. Test with a community user account, verifying both the first-login (data collection) and subsequent-login (skip) paths.

**Why not the alternative:** Using a custom Visualforce login page requires more development effort, does not integrate with Flow Builder's declarative tools, and is harder for admins to maintain. Screen Flow Login Flows achieve the same result with less code.

### Pattern 3: Periodic Re-Verification on Schedule

**When to use:** Compliance requirements mandate that users re-verify their identity or re-accept terms on a periodic basis (e.g., every 90 days).

**How it works:**

1. Add a custom date field to the User object: `Last_Login_Verification__c`.
2. In the Login Flow, use a Get Records element to read the current user's `Last_Login_Verification__c`.
3. Decision element: if `Last_Login_Verification__c` is null or older than 90 days, route to the verification/acceptance screen. Otherwise, skip to end.
4. After the user completes the verification screen, use an Apex action to update `Last_Login_Verification__c` to `System.today()`.
5. Assign to the profile or site.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Block login entirely from non-corporate IPs | Profile Login IP Ranges (network-security-and-trusted-ips skill) | Hard deny requires network-layer enforcement, not a Login Flow |
| Add extra verification for non-corporate IPs but still allow login | Login Flow with IP-based Decision element | Login Flows add friction without blocking; Login IP Ranges are all-or-nothing |
| Collect data from Experience Cloud users at first login | Login Flow assigned to the Experience Cloud site | Site-level assignment covers all community users regardless of profile |
| Enforce terms-of-service acceptance for internal users | Login Flow assigned to target profile(s) | Profile assignment scopes the flow to the right user population |
| Replace the entire login page UI for a community | Experience Cloud Login Page (Aura/LWC) + Login Flow | Login Flows customize post-auth steps; the login page itself is a separate component |
| Conditional MFA based on login type (SSO vs direct) | Login Flow with `$Flow.LoginFlow_LoginType` Decision | This system variable distinguishes authentication methods inside the flow |
| Mobile app post-auth customization via Connected App | ConnectedAppPlugin with authorize() override | ConnectedAppPlugin runs in the OAuth context; Login Flows run in the UI login context |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Identify the requirement** -- Determine whether the need is conditional verification, data collection, terms acceptance, or custom routing. Confirm whether users are internal (profile assignment) or external (site assignment).
2. **Check existing Login Flow assignments** -- Navigate to Setup > Login Flows to see if a flow is already assigned to the target profile. Only one Login Flow can be assigned per profile.
3. **Design the flow logic** -- Map out the decision tree: what conditions trigger which screens. Identify whether an Apex Invocable is needed (IP detection, SMS sending) or if built-in flow variables suffice.
4. **Build the Screen Flow** -- Create the flow in Flow Builder. Use `$Flow.LoginFlow_UserId` and `$Flow.LoginFlow_LoginType` for user and authentication context. Add Decision elements for conditional paths. Keep the flow short -- every screen adds login latency.
5. **Assign the Login Flow** -- For profiles: Setup > Login Flows > New, select the flow and profile. For Experience Cloud: site Administration > Login & Registration > Login Flow.
6. **Test thoroughly** -- Test the happy path (trusted IP, data already collected), the verification path (untrusted IP, missing data), and the edge cases (user closes browser mid-flow, flow faults). Use a non-admin test user to avoid masking permission issues.
7. **Document the assignment and logic** -- Record which profiles/sites have Login Flows, what conditions trigger each path, and what Apex actions are used. This is critical for future maintainability.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Login Flow is a Screen Flow (not Autolaunched or Record-Triggered)
- [ ] Flow uses `$Flow.LoginFlow_UserId` or `$Flow.LoginFlow_LoginType` where applicable, not hardcoded User IDs
- [ ] IP detection uses a reliable method (Apex Invocable with `Auth.SessionManagement` or header inspection), not formula-only approximation
- [ ] Corporate IP ranges are stored in Custom Metadata or Custom Settings, not hardcoded in flow formulas
- [ ] Flow has been tested from both a trusted and an untrusted IP address
- [ ] Flow assignment confirmed: one flow per profile; site-level assignment overrides profile-level for Experience Cloud
- [ ] Flow handles the "user closes browser" case gracefully (no partial state left)
- [ ] Flow does not attempt DML that requires full session context (Login Flow User has limited permissions)
- [ ] Login latency impact assessed -- flow has minimal screens on the happy path
- [ ] Existing MFA enforcement is not weakened or bypassed by the Login Flow logic

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Login Flows run as Login Flow User, not as the authenticating user** -- The flow executes in a restricted context. Apex actions invoked from the flow may fail if they require standard user permissions. Any DML on the User object must be done through an Apex class running `without sharing` or with explicit system-level access. Test Apex actions in the login context specifically, not just from a regular flow debug.

2. **Only one Login Flow per profile -- assigning a new one silently replaces the old one** -- There is no warning in Setup when you assign a Login Flow to a profile that already has one. The previous assignment is overwritten. Audit Setup > Login Flows before making changes to avoid accidentally removing an existing flow.

3. **Login Flows on Experience Cloud sites override profile-level flows for that site's users** -- If a community user's profile has a Login Flow and the Experience Cloud site also has a Login Flow, only the site-level flow runs. The profile-level flow is skipped entirely, not chained. This is counterintuitive and can cause requirements to be silently dropped.

4. **Login Flows cannot use all Screen Flow components** -- Certain Lightning components, file upload elements, and rich-text display options that work in standard Screen Flows may fail or render incorrectly in the login context. The login page container is not a full Lightning Experience context. Test every screen element in the actual login flow, not just in Flow Builder's debug mode.

5. **Flow faults during login leave the user stranded** -- If the Login Flow hits an unhandled fault (Apex exception, null pointer in a formula), the user sees a generic error and cannot proceed into the org. There is no automatic bypass. Always add Fault connectors to critical elements and route faults to a screen that explains the error, rather than letting them propagate.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Screen Flow (Login Flow) | The Flow Builder flow configured with post-authentication logic |
| Login Flow Assignment | Setup record linking the flow to a profile or Experience Cloud site |
| Apex Invocable (IP detection) | `@InvocableMethod` class that returns the user's source IP for flow consumption |
| Custom Metadata (IP ranges) | `Corporate_IP_Range__mdt` records storing trusted CIDR ranges for flow decision logic |
| Test plan | Documented test cases covering trusted IP, untrusted IP, flow fault, and edge scenarios |

---

## Related Skills

- `network-security-and-trusted-ips` -- Use for static IP allowlisting (Login IP Ranges on profiles, org-wide Trusted IP Ranges) rather than conditional post-authentication logic
- `session-management-and-timeout` -- Use for org-wide session policies, timeout settings, and session security levels
- `login-forensics` -- Use to investigate login failures, audit LoginHistory, and reconstruct login timelines
- `experience-cloud-security` -- Use for broader Experience Cloud security configuration beyond login flows
- `transaction-security-policies` -- Use for real-time event-driven enforcement (e.g., block login from a specific country dynamically)
