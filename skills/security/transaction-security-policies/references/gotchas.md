# Gotchas — Transaction Security Policies

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Monitor Mode Never Enforces — Silently

**What happens:** A policy set to Monitor mode logs every condition match but takes absolutely no enforcement action. No blocks are applied, no MFA prompts are triggered, no sessions are ended. The user experience is completely unaffected. The only output is a log entry visible in the policy's match history.

**When it occurs:** This affects every newly created policy. It also affects any policy intentionally left in Monitor mode that the org later forgets to promote to Active. Practitioners who test a policy by triggering the matching condition and then check whether a block appears will see nothing and conclude the policy is broken — when in fact it is working in Monitor mode exactly as designed.

**How to avoid:** After creating a policy and confirming it matches expected events in the Monitor log, explicitly switch the policy's Active flag to true. Treat the Monitor period as a mandatory step with a defined end date. For policies configured via Metadata API, set `<active>true</active>` in the XML before deployment to production, and separately have Monitor mode versions in a pre-prod org to validate.

---

## Gotcha 2: Unsupported Event Types Silently Never Fire

**What happens:** Certain RTEM event types do not support Transaction Security Policy enforcement. Policies created against these event types are accepted by the UI without error, appear in the policy list as configured, and even allow you to set conditions and actions — but they will never evaluate, match, or enforce. There is no warning, no error log, and no indication in the UI that the event type is unsupported.

Confirmed unsupported event types (as of Spring '25):
- `MobileEmailEvent`
- `MobileScreenshotEvent`
- `MobileEnforcedPolicyEvent`
- `MobileTelephonyEvent`
- `IdentityProviderEvent`
- `IdentityVerificationEvent`

**When it occurs:** When a practitioner selects one of these event types in the Transaction Security Policies UI and builds a policy, expecting it to enforce. Most commonly seen with mobile event types for practitioners trying to detect screenshot-taking behavior on mobile sessions.

**How to avoid:** Before designing a policy on any event type, verify the "Can Be Used in a Transaction Security Policy?" column in the Salesforce Platform Events Developer Guide or the Object Reference entry for that event type. If the column is "No", the policy will never fire regardless of how it is configured. Use the policy-supported event set in `scripts/check_transaction_security.py` as a quick local reference.

---

## Gotcha 3: Country Field Requires ISO Codes, Not Full Country Names

**What happens:** The `Country` field on `LoginEvent` is populated with ISO 3166-1 alpha-2 two-letter country codes (e.g., `US`, `GB`, `DE`, `IN`), not full country names (e.g., `United States`, `United Kingdom`, `Germany`). A condition that filters `Country` Equals `United States` never matches because the stored value is `US`. The policy silently never fires — no error, no log entry.

**When it occurs:** When a practitioner builds a country-based login restriction and types the full country name in the condition value field. The Condition Builder UI accepts the string without validation, so the error is invisible until the policy is tested.

**How to avoid:** Always use ISO 3166-1 alpha-2 country codes in the condition value. Reference the ISO standard or the Salesforce LoginEvent Object Reference to confirm the exact two-letter code for each country. When in doubt, query the `LoginEvent` big object in a sandbox to inspect actual field values from real login events before building the condition: `SELECT Country, UserId, EventDate FROM LoginEvent ORDER BY EventDate DESC LIMIT 20`. `LoginEventStream` is a platform event and cannot be queried — SOQL against it always fails.

---

## Gotcha 4: Deactivated Notification Recipients Stop Receiving Alerts Silently

**What happens:** A policy's notifications go to named recipients. If a recipient's Salesforce user record is deactivated (for example a former employee), the alert is not delivered. UNVERIFIED (2026-11-19): the guides do not document what the platform logs or raises in that case, so treat the failure as silent until tested in a sandbox. Do not look for an execution user as the cause: `executionUser` / `ExecutionUserId` is Legacy Transaction Security only (retired Summer '20; api_meta.txt L138943, object_reference.txt L294806-294813).

**When it occurs:** After org user offboarding, when a recipient's account is deactivated or deleted. This can go undetected until an incident reveals that the expected alert never arrived.

**How to avoid:** Point notifications at role-based or shared mailboxes and service accounts that are not tied to individual employee tenure, and add the recipients of every policy to the offboarding checklist. The `check_transaction_security.py` script does not check recipient status, so review the `notifications` blocks in source by hand.

---

## Gotcha 5: Legacy Apex Policies Fail When the PolicyCondition Class Has Compile Errors

**What happens:** Legacy Transaction Security Policies reference an Apex class that implements `TxnSecurity.PolicyCondition`. If the referenced Apex class fails to compile — due to a deploy error, a related class deletion, or an API version mismatch — the policy silently stops evaluating. There is no runtime error surfaced to the end user. The block or MFA that should fire simply does not.

**When it occurs:** During deployments that modify or delete Apex classes. A change to a shared utility class used by the `PolicyCondition` implementation can introduce an indirect compile failure. Sandbox refreshes that pull partial metadata can also leave the policy class in a broken state.

**How to avoid:** After any Apex deployment that touches classes related to Transaction Security, verify that all `PolicyCondition` classes compile cleanly. Run `sfdx force:source:retrieve -m ApexClass` and check for compile errors. Prefer Enhanced Condition Builder policies over Apex-based policies for any use case the Condition Builder can express — Enhanced policies have no Apex compile dependency and are significantly more resilient to deployment side effects.

---

## Gotcha 6: A Default ReportEvent Policy Exists That Nobody in the Org Authored (2026)

**What happens:** Salesforce deploys a default `ReportEvent` Transaction Security Policy to eligible Event Monitoring customers — both Shield and standalone EM licenses. "This policy is triggered when an export exceeds 10,000 records. Such report export activities will also require step-up authentication." It arrives as "a new, disabled, separate policy" that does not modify any policy already in the org, and Salesforce "will not automatically enable the default policy if another ReportEvent policy already exists in the org." If a condition-builder `ReportEvent` policy is already present, the default is not deployed at all. Scope is narrow: UI report exports only. It does not affect report exports performed via API, including Data Loader CLI.

The same change gates policy administration behind a new permission — "both the **Modify Transaction Security Policy** and **Customize Application** permissions are required" to create, update, delete, enable, or disable a policy. "Read-only access will be granted to all other users having only the Customize Application permission."

Dates: available in sandboxes June 1, 2026 and production June 15, 2026; enforced in sandboxes June 22, 2026 and production July 13, 2026.

**When it occurs:** During a policy audit of an EM or Shield org after mid-2026, when a `ReportEvent` policy appears that no one on the team created. Also when a long-tenured admin who has always managed policies with Customize Application suddenly finds the Setup page read-only, and reads it as a licensing or org-permission bug rather than a missing user permission.

**How to avoid:** Inventory `ReportEvent` policies and establish whether the default was ever deployed and whether anyone enabled it. The suppression rule applied at deployment time, so an org that already ran a condition-builder ReportEvent policy in mid-2026 simply never received the default. The source says nothing about a policy authored *after* deployment removing an already-deployed default, so do not assume you can suppress it retroactively — check Setup instead of reasoning about it. And because the default arrives disabled and Salesforce does not enable it for you, treat it as a candidate control to review and switch on deliberately, not as coverage the org already has. It is not coverage for API or Data Loader CLI extraction either. Add **Modify Transaction Security Policy** to the permission set used by whoever administers policies, and confirm they also have step-up authentication configured — Salesforce's stated pre-enforcement action is to "assign them the new Modify Transaction Security Policy permission and ensure that they have step-up authentication configured."
