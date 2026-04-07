# Gotchas — Experience Cloud Member Management

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Profile-License Binding Is Permanent

**What happens:** If you create a profile tied to the Customer Community license and later discover you need Partner Community features (such as Opportunity access or full role hierarchy), you cannot change the license on the existing profile. Attempting to edit the User License field on a profile throws an error. All users on the old profile must be migrated to a new profile created with the correct license.

**When it occurs:** Typically surfaces mid-project when business requirements expand after initial setup, or when an admin clones the wrong base profile (e.g., clones "Authenticated Website" instead of "Partner Community User").

**How to avoid:** Confirm the correct license type before creating any external profile. Run a quick requirements check: Does the portal need Opportunity, Lead, or Order access? If yes, Partner Community. Does it need robust custom object sharing via roles? Customer Community Plus. Simple case/knowledge access? Customer Community. Identity-only? External Identity. Do this before creating users — migrating users later requires deactivating old users, creating new ones, and re-sharing records.

---

## Gotcha 2: ConfigurableSelfRegHandler vs Legacy RegistrationHandler Interface Mismatch

**What happens:** Salesforce has two Apex interfaces for customising self-registration. The legacy interface is `Auth.RegistrationHandler` (requires implementing `createUser` and `updateUser` methods). The current interface is `Auth.ConfigurableSelfRegHandler` (requires implementing a single `registerUser(Auth.SelfRegistrationContext context)` method). If you implement the wrong interface and reference the class in the Registration settings, the platform either ignores the class silently or throws a runtime error during registration. The two interfaces are not interchangeable.

**When it occurs:** When an Apex developer writes a handler based on older documentation, Trailhead content, or LLM-generated code that references the legacy signature. The Registration settings panel in Setup will accept either class name, so the mismatch is not caught at configuration time — it only surfaces when a user attempts to register.

**How to avoid:** When building a new self-registration handler, always implement `Auth.ConfigurableSelfRegHandler`. Check the Apex Reference Guide to confirm the current method signatures. If maintaining a legacy org that already uses `Auth.RegistrationHandler`, leave it in place — both interfaces are still supported — but do not mix the two on the same site.

---

## Gotcha 3: Deactivated External Users Continue to Consume License Seats

**What happens:** Deactivating an external user (setting `IsActive = false` on the User record) does not release the Experience Cloud license seat. The license count in Setup > Company Information > Licenses remains unchanged. If all available seats are consumed, attempts to create new external users fail, often with a confusing error message about licenses rather than a user-limit error.

**When it occurs:** In orgs where external users churn frequently (e.g., seasonal partner portals, B2C portals with high abandonment). Over time, the deactivated user population grows while the available seat count shrinks toward zero.

**How to avoid:** Implement a periodic audit process (monthly or quarterly) using a SOQL query against the User object filtered by `IsActive = false` and the relevant Profile IDs. For bulk license recovery, use the "Freeze User" and then formal deactivation pipeline. Note that Salesforce does not automatically release seats from deactivated users — this is a manual or scripted administrative task. Add a check to your org-health runbook.

---

## Gotcha 4: Self-Registration Silently Fails Without a Default New User Account

**What happens:** When Self-Registration is enabled in the site's Administration > Registration panel but no Default New User Account is specified, self-registration POST requests complete without error on the form but then display a generic error page. The user is not created, no error appears in Setup > Login History, and the debug log may show a `System.NullPointerException` deep in the registration stack.

**When it occurs:** When an admin enables the Self-Registration toggle but forgets to scroll down and configure the Default New User Account and Default Profile fields. Also occurs when the designated catch-all account is deleted or deactivated after the fact.

**How to avoid:** After enabling self-registration, immediately confirm both the Default New User Account and Default Profile are set. Test with a guest browser session before considering the feature live. Protect the catch-all account with a validation rule or org-level policy preventing deletion. Person Accounts cannot be used as the catch-all — it must be a business (standard) Account.

---

## Gotcha 5: Login Page Structural Changes Require a Site Publish

**What happens:** Admins editing the login page in Experience Builder assume changes take effect immediately (as some property changes do for authenticated pages). However, adding or removing components on the login/registration page, or changing the page structure, requires an explicit Publish action in Experience Builder. Until the site is published, external users see the previous version of the login page. This causes confusion in UAT when the tester's browser is caching the old page.

**When it occurs:** During iterative login-page branding work, especially when multiple changes are made across a session and the admin forgets to publish after the final change. Also occurs after a sandbox refresh where the site is in Draft state.

**How to avoid:** Establish a discipline of always clicking Publish after any login page structural change. Communicate to QA that login page changes require a publish before testing. In sandboxes, confirm the site status is Active (not Preview) before testing external login flows.
