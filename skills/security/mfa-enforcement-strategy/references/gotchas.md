# Gotchas: MFA Enforcement Strategy

Non-obvious Salesforce platform behaviors that cause real production problems in this domain. Each gotcha names the official source it rests on.

## Gotcha 1: SSO MFA Does Not Cover a Parallel Password Path

**What happens:** Users complete strong MFA at the corporate IdP when they use SSO, but they can still log in to Salesforce with a username and password that never had a Salesforce verification method.

**When it occurs:** Orgs that introduced SSO years ago but never disabled Salesforce credentials for SSO-only populations.

**How to avoid:** Inventory both channels per population. For populations that must be SSO-only, use `isLoginWithSalesforceCredentialsDisabled` so users are redirected to the identity provider, and keep a documented break-glass admin path. Pilot first and watch login history by login type.

**Source:** Salesforce Security Guide, Multi-Factor Authentication ("This contractual requirement applies equally to direct logins with a Salesforce username and password and to logins via single sign-on (SSO)"). Metadata API Developer Guide, SingleSignOnSettings `isLoginWithSalesforceCredentialsDisabled` ("users are redirected to third-party identity providers for authentication").

---

## Gotcha 2: The Org-Wide Setting Targets UI Logins, So Automation Needs Its Own Plan

**What happens:** MFA rollout is applied to accounts that are really automation. Jobs that log in through the UI flow with a shared password fail, and engineers revert broad policy changes under pressure.

**When it occurs:** Shared developer accounts, service accounts that run middleware through username and password, or vendors using personal licenses for integration.

**How to avoid:** Classify principals as human or automation first. Move automation to OAuth-based integration patterns with dedicated integration users, rather than stretching interactive MFA onto unattended processes.

**Source:** Metadata API Developer Guide, SessionSettings `enableMFADirectUILoginOptIn` ("Requires all users in your Salesforce org to provide an additional verification method when logging in directly to the UI with their username and password").

---

## Gotcha 3: The Waiver Permission's Behavior Depends on Which Source You Read

**What happens:** A runbook relies on "Waive Multi-Factor Authentication for Exempt Users" for a handful of accounts. After enforcement, those users are prompted to register a verifier anyway.

**When it occurs:** Orgs that planned exemptions from the Metadata API description, which says the permission overrides the org-wide opt-in, after Salesforce Help announced the 2026 change.

**How to avoid:** Treat every waiver as temporary. Give each one an owner, an expiry, and a migration path to a real verification method or an OAuth integration pattern before the sandbox enforcement date.

**Source:** Metadata API Developer Guide, Summer '26, SessionSettings `enableMFADirectUILoginOptIn` ("The Waive Multi-Factor Authentication for Exempt Users user permission overrides this setting"). UNVERIFIED (2026-10-03): the removal of the waiver behavior is stated only in Salesforce Help ("Prepare for MFA Enforcement for All Employee Users"), which does not fetch.

---

## Gotcha 4: Transaction Security "MFA" Becomes a Block in Most Clients

**What happens:** A team adds a Transaction Security policy with a multi-factor authentication action to protect report exports, expecting a step-up prompt. In Lightning Experience, the mobile app, and API access, users are blocked instead.

**When it occurs:** Policies that rely on the MFA action outside Salesforce Classic.

**How to avoid:** Use org-wide MFA and session security levels for authentication strength. Use Transaction Security policies for targeted blocks and notifications, and test the action in the clients your users actually use.

**Source:** Salesforce Security Guide, Transaction Security: "The multi-factor authentication action isn't available in the Salesforce mobile app, Lightning Experience, or via API for any events. Instead, the block action is used."

---

## Gotcha 5: Registration Reporting Needs a Specific Permission and Its Own Transaction

**What happens:** A readiness script queries `TwoFactorMethodsInfo` and fails with an access error, or an Apex job that updates users and then queries the object in the same call fails with an UncommittedWork error.

**When it occurs:** Building the "who has not registered yet" report for the rollout.

**How to avoid:** Run the query as a user with "Manage MFA in API." Keep DML and the query in separate asynchronous calls. Use the SOQL in [metadata-examples.md](metadata-examples.md).

**Source:** Object Reference, TwoFactorMethodsInfo (Special Access Rules and the UncommittedWork note).

---

## Gotcha 6: The Registration Screen Defaults to Salesforce Authenticator

**What happens:** Users who can't install a phone app see only the Salesforce Authenticator option when prompted to register, call the help desk, and stall the rollout.

**When it occurs:** `skipSFAWhenMFADirectUILogin` is false, so users must navigate to another page to see other methods.

**How to avoid:** Set `skipSFAWhenMFADirectUILogin` to true when the approved list includes TOTP apps, security keys, or built-in authenticators, and enable those methods (`enableU2F`, `enableBuiltInAuthenticator`).

**Source:** Metadata API Developer Guide, SessionSettings `skipSFAWhenMFADirectUILogin` ("If true, users see a list of all supported verification methods. If false, users see only the Salesforce Authenticator option").

---

## Gotcha 7: Trusted IP Ranges Are Not an MFA Substitute

**What happens:** A team assumes office users are exempt from MFA because their network is in Trusted IP Ranges.

**When it occurs:** Rollout plans that reuse network-trust settings as an authentication control.

**How to avoid:** Treat trusted ranges as a device-activation convenience only. Plan MFA for every human UI login regardless of network.

**Source:** Metadata API Developer Guide, SecuritySettings > NetworkAccess ("The trusted IP address ranges from which users can always log in without requiring computer activation"). Salesforce Security Guide, Device Activation.

---

## Gotcha 8: Exemptions Become Permanent Because Nobody Owns the Review Date

**What happens:** A temporary exemption for a legacy app survives for years. Auditors find dozens of "temporary" exceptions with no business owner.

**When it occurs:** Exemption workflows lack ticketing, expiry, and executive sign-off; teams rotate and context is lost.

**How to avoid:** Store exemptions in your ITSM tool with expiry, business owner, and compensating controls. Review quarterly; tie renewals to architecture board approval. Pair this with `PermissionSetAssignment.ExpirationDate` when the exemption is granted through a permission set.

**Source:** Object Reference, PermissionSetAssignment `ExpirationDate` (API 52.0+). The governance practice itself is design guidance, not a platform rule.
