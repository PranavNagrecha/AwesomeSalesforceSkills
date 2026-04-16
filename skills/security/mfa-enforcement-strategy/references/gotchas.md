# Gotchas — MFA Enforcement Strategy

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: SSO MFA Does Not Automatically Cover a Parallel Password Path

**What happens:** Users complete strong MFA at the corporate IdP when they use SSO, but they can still log in to Salesforce with a username and password that never completed Salesforce-side verification.

**When it occurs:** Orgs that introduced SSO years ago but never disabled or rotated off legacy Salesforce credentials for all populations.

**How to avoid:** Inventory both channels; for SSO-only populations, align technical controls and communications so the password path is not a realistic alternative. Validate with a small pilot that reports **login type** or equivalent operational telemetry.

---

## Gotcha 2: Integration and “API-Only” Identities Are Easy to Confuse With Humans

**What happens:** MFA enforcement is applied to accounts that represent automation. Jobs fail, queues stall, and on-call engineers burn time reverting broad policy changes.

**When it occurs:** Shared developer accounts, service accounts running scheduled Apex or middleware, or vendors using personal licenses for integration.

**How to avoid:** Classify principals as **human** versus **automation** up front. For automation, use documented integration patterns (OAuth client credentials, JWT bearer flows where appropriate, dedicated integration users) rather than stretching interactive MFA flows onto unattended processes.

---

## Gotcha 3: Exemptions Become Permanent Because Nobody Owns the Review Date

**What happens:** A temporary exemption for a legacy app survives for years. Auditors find dozens of “temporary” exceptions with no business owner.

**When it occurs:** Exemption workflows lack ticketing, expiry, and executive sign-off; teams rotate and context is lost.

**How to avoid:** Store exemptions in your ITSM tool with **expiry**, **business owner**, and **compensating controls**. Review quarterly; tie renewals to architecture board approval.
