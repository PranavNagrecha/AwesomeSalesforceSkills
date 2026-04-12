# Examples — Fundraising Integration Patterns

## Example 1: Reconciling Stripe Payment Outcomes with GiftTransaction via Elevate Connect REST API

**Context:** A mid-size nonprofit running Nonprofit Cloud with Salesforce.org Elevate uses a hosted online giving form. When a donor completes a gift, the Stripe payment processor sends authorization and capture events back through Elevate infrastructure. The org's integration team needs to update `GiftTransaction` records with the Stripe payment intent ID and processor status without creating a custom payment adapter.

**Problem:** The team initially attempts to write a custom Apex trigger that calls Stripe's API directly and upserts fields on `GiftTransaction`. This bypasses Elevate entirely, breaks the PCI tokenization boundary, and duplicates work that the Elevate connector already performs. A second attempt tries implementing the `blng.PaymentGateway` interface — this fails to compile because Salesforce Billing is not installed in the NPC org.

**Solution:**

The correct approach is to let Elevate handle the processor callback and call the Connect REST API endpoint to surface results on the `GiftTransaction` record. For cases where the org's internal systems need to initiate a metadata update (for example, a reconciliation job after a nightly batch):

```http
POST /services/data/v59.0/connect/fundraising/transactions/payment-updates
Authorization: Bearer {session_token}
Content-Type: application/json

{
  "transactionId": "a0Q8G000001EXAMPLE",
  "gatewayRefId": "pi_3NXXXXXXXXXXXX",
  "processorResponseCode": "CAPTURED",
  "gatewayName": "Stripe",
  "lastModifiedDate": "2026-04-12T10:30:00Z"
}
```

This call updates only the specified gateway metadata fields. It does not create a new `GiftTransaction` record or alter giving totals. If the call fails (network timeout, expired session), the org must log the failure and retry — partial updates are possible in batch scenarios.

**Why it works:** The Connect REST API endpoint is the documented integration contract for Elevate payment callbacks at API v59.0+. It operates within the Elevate PCI boundary and maintains the audit trail that Elevate manages. The org never handles raw card data or processor credentials.

---

## Example 2: Bulk Wealth Screening with iWave for Major Gift Cultivation

**Context:** A healthcare nonprofit wants to score 15,000 contacts in Salesforce against iWave's wealth database to identify prospects for a capital campaign. Gift officers want the screening scores visible on Contact records alongside giving history.

**Problem:** A developer proposes building a custom integration using iWave's REST API, storing scores in a custom object, and writing a trigger to copy scores to Contact fields. This approach requires reimplementing the iWave field schema, handling API rate limits (iWave enforces per-minute and daily limits), managing credential rotation, and manually updating mappings when iWave changes their API version.

**Solution:**

Install **iWave for Salesforce** from AppExchange and configure it using the vendor-issued API key via a Named Credential:

1. Install the iWave managed package from AppExchange (package ID published in the iWave AppExchange listing).
2. In Setup > Named Credentials, create a credential named `iWave_API` with the endpoint `https://api.iwave.com` and store the API key as a password field.
3. In the iWave package settings, point the integration to the Named Credential.
4. Use the iWave bulk screening interface to submit Contact IDs. The package's internal batch job polls iWave's queue and writes results to fields including `iwv__RatingScore__c` and `iwv__P2GScore__c` on the Contact record.
5. Build a Contact list view filtered on `iwv__RatingScore__c >= 7` for major gift officer assignment.

The package handles API versioning, rate limit backoff, error logging, and field schema updates. Gift officers see scores directly on the Contact detail page via the iWave Lightning component included in the package.

**Why it works:** The managed package approach delegates authentication, schema management, and versioning to the vendor. The scores land on `Contact` — the correct object for donor capacity data — where they can be included in Marketing Cloud or Pardot segmentation without additional sync configuration.

---

## Anti-Pattern: Using blng.PaymentGateway for NPSP Payment Processing

**What practitioners do:** When asked to integrate a custom payment processor with NPSP, a practitioner (or AI assistant) searches for "Salesforce payment gateway Apex" and finds the Salesforce Billing documentation describing the `blng.PaymentGateway` interface. They scaffold an Apex class implementing this interface expecting it to intercept NPSP donation payments.

**What goes wrong:** The `blng.PaymentGateway` interface is part of the `blng` (Salesforce Billing) managed package namespace. In an org where Salesforce Billing is not installed, the class fails to compile with an error: `No such type blng.PaymentGateway`. Even if Billing is installed alongside NPSP, the `blng.PaymentGateway` implementation is invoked by Billing invoice payment processing — it has no hook into NPSP's `npe01__OppPayment__c` lifecycle or Nonprofit Cloud's `GiftTransaction` flow.

**Correct approach:** For payment gateway integration in NPSP/NPC orgs, use Salesforce.org Elevate (Payment Services) as the integration layer. Elevate exposes payment results via the Connect REST API `POST /connect/fundraising/transactions/payment-updates` endpoint at API v59.0+. If Elevate is not available, evaluate AppExchange connectors from established nonprofit payment processors (iATS, Stripe for Nonprofits, Classy) — none of which use the `blng.PaymentGateway` interface.
