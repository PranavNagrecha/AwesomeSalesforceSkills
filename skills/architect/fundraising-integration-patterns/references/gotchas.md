# Gotchas — Fundraising Integration Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: blng.PaymentGateway Is a Salesforce Billing Interface — Not a Nonprofit Payment Hook

**What happens:** Apex classes that implement `blng.PaymentGateway` fail to compile in orgs without Salesforce Billing installed, with the error: `No such type blng.PaymentGateway`. Even in orgs where both Billing and NPSP are installed, the interface is invoked only by Billing invoice payment processing — it has zero connection to NPSP's `npe01__OppPayment__c` lifecycle or Nonprofit Cloud's `GiftTransaction` flow.

**When it occurs:** Any time a practitioner or AI assistant searches for "Salesforce payment gateway Apex interface" and finds Billing documentation, then attempts to apply the pattern to an NPSP or Nonprofit Cloud payment scenario.

**How to avoid:** Verify which product is in scope before recommending Apex payment interfaces. If the installed packages include `npe01` (NPSP) or `npc` (Nonprofit Cloud) and the goal is payment gateway integration, route to Salesforce.org Elevate and the Connect REST API — not to `blng.PaymentGateway`. Check installed packages in Setup > Installed Packages before writing any payment-related Apex.

---

## Gotcha 2: The Elevate Connector Has No Apex Extension Point

**What happens:** Unlike Salesforce Billing's architecture where a new payment processor is added by implementing the `blng.PaymentGateway` Apex interface, Elevate has no equivalent hook. The Elevate processing infrastructure is hosted outside the Salesforce org boundary. There is no Apex interface, trigger, or custom metadata record that redirects Elevate callbacks to a different handler. Attempts to intercept or override the Elevate flow with custom Apex have no effect.

**When it occurs:** When an org wants to switch payment processors within Elevate (e.g., from Stripe to a different gateway) or add custom pre/post-processing logic to the Elevate payment flow. Practitioners assume — by analogy to Billing — that an Apex implementation can substitute or augment the connector.

**How to avoid:** Treat Elevate as a black-box managed connector. Custom logic that must run on payment completion should be implemented as a Platform Event subscriber or Change Data Capture listener on `GiftTransaction`, which fires after Elevate has already written the payment outcome. Do not attempt to intercept the Elevate callback path. If an unsupported payment processor must be integrated, evaluate a non-Elevate AppExchange connector rather than trying to extend Elevate with Apex.

---

## Gotcha 3: Wealth Screening Scores Target Contact/Account — Not GiftTransaction

**What happens:** Wealth screening tools assess donor financial capacity, not individual gift transactions. Both iWave and DonorSearch write output scores to `Contact` (and optionally `Account`) records. There is no supported package-level field mapping that writes wealth scores to `GiftTransaction` or `GiftEntry`. If custom fields are added to `GiftTransaction` for this purpose, no vendor tooling will populate them — custom Apex or flows must be built and maintained to copy scores from Contact to the transaction, which adds fragility for no architectural benefit.

**When it occurs:** When gift officers request "show the donor's wealth score on the gift record" and a developer creates custom fields on `GiftTransaction` expecting the screening package to populate them, or when a practitioner designs the screening integration with `GiftTransaction` as the target object.

**How to avoid:** Store wealth screening scores on `Contact` where the managed packages write them. If gift officers need to see scores while reviewing a transaction, use a related list, formula field, or cross-object formula on `GiftTransaction` to surface the parent Contact's score. This keeps the data model aligned with what the vendor packages support and avoids custom synchronization code.

---

## Gotcha 4: Connect REST API Payment Updates Endpoint Requires API v59.0 Minimum

**What happens:** The `/connect/fundraising/transactions/payment-updates` endpoint was introduced at API version 59.0 (Spring '23). Orgs that have not been updated, or API clients that pin to an older version in their endpoint URL (e.g., `/services/data/v55.0/connect/...`), receive a `404 Not Found` or `UNSUPPORTED_API_VERSION` error. This is easy to miss in sandbox testing if the sandbox is on a different API version than production.

**When it occurs:** When building an integration against the Connect REST API using a hardcoded API version in the URL, or when moving from a sandbox built on an older API version to a production org. Also occurs in Named Credential external credential configurations that pin an old API version.

**How to avoid:** Always use API v59.0 or higher in the endpoint URL for Elevate Connect REST API calls. If the client dynamically discovers the API version from `/services/data/`, ensure the version selection logic enforces a minimum of 59.0 rather than selecting the org's default (which may be lower for legacy orgs).

---

## Gotcha 5: GiftTransaction Records Cannot Be Directly Created by External Systems Outside of Elevate

**What happens:** `GiftTransaction` records in Nonprofit Cloud are created through the Elevate-managed gift entry flow or through the Nonprofit Cloud gift processing batch API. External systems (event platforms, peer-to-peer fundraising tools) that attempt to insert `GiftTransaction` records directly via the Salesforce REST or Bulk API outside of this flow may succeed at the DML level but will be missing required Elevate-managed fields (payment method token, gateway reference) that downstream reconciliation and reporting rely on. The records appear in reports but cannot be associated with a real payment event, creating phantom gift records.

**When it occurs:** When integrating third-party platforms that need to post charitable contributions into Salesforce and a developer maps the external transaction directly to `GiftTransaction` via a standard REST insert rather than routing through the Elevate API or a GiftEntry promotion pattern.

**How to avoid:** External systems should land transaction data in an intermediate staging object or use the `GiftEntry` promotion workflow. For event ticket purchases that include a charitable component, create a staging record and promote it through the standard Elevate gift entry path. This ensures all Elevate-managed fields are populated correctly and the payment audit trail is intact.
