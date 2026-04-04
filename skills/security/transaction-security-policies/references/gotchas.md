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

**How to avoid:** Always use ISO 3166-1 alpha-2 country codes in the condition value. Reference the ISO standard or the Salesforce LoginEvent Object Reference to confirm the exact two-letter code for each country. When in doubt, query `LoginEventStream` via SOQL (`SELECT Country, UserId FROM LoginEventStream LIMIT 20`) in a sandbox to inspect actual field values from real login events before building the condition.

---

## Gotcha 4: Deactivated Execution Users or Notification Recipients Break Policies Silently

**What happens:** Each Transaction Security Policy has a designated execution user. For Enhanced (Condition Builder) policies, the execution user provides the running context for evaluation. For legacy Apex policies, the execution user must also have "Author Apex" permission. If the execution user is deactivated — for example, a former employee whose account was disabled — the policy stops evaluating entirely. No error is logged, no alert is raised. Similarly, deactivated notification recipients simply stop receiving alerts with no fallback.

**When it occurs:** After org user offboarding. If the policy execution user or a notification recipient's Salesforce user record is deactivated (or deleted), the policy or notification breaks silently. This can go undetected for months until an incident reveals that the expected policy never fired.

**How to avoid:** Assign execution users and notification recipients to service accounts or role-based accounts that are not tied to individual employee tenure. Run a periodic audit SOQL query to detect broken references:

```soql
SELECT Id, MasterLabel, ExecutionUser.IsActive, ExecutionUser.Name
FROM TransactionSecurityPolicy
WHERE ExecutionUser.IsActive = false
```

Add this check to offboarding checklists. The `check_transaction_security.py` script in `scripts/` also flags inactive execution users when run against metadata.

---

## Gotcha 5: Legacy Apex Policies Fail When the PolicyCondition Class Has Compile Errors

**What happens:** Legacy Transaction Security Policies reference an Apex class that implements `TxnSecurity.PolicyCondition`. If the referenced Apex class fails to compile — due to a deploy error, a related class deletion, or an API version mismatch — the policy silently stops evaluating. There is no runtime error surfaced to the end user. The block or MFA that should fire simply does not.

**When it occurs:** During deployments that modify or delete Apex classes. A change to a shared utility class used by the `PolicyCondition` implementation can introduce an indirect compile failure. Sandbox refreshes that pull partial metadata can also leave the policy class in a broken state.

**How to avoid:** After any Apex deployment that touches classes related to Transaction Security, verify that all `PolicyCondition` classes compile cleanly. Run `sfdx force:source:retrieve -m ApexClass` and check for compile errors. Prefer Enhanced Condition Builder policies over Apex-based policies for any use case the Condition Builder can express — Enhanced policies have no Apex compile dependency and are significantly more resilient to deployment side effects.
