# LLM Anti-Patterns — Fundraising Integration Patterns

Common mistakes AI coding assistants make when generating or advising on Fundraising Integration Patterns.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending blng.PaymentGateway for NPSP or Nonprofit Cloud Payment Processing

**What the LLM generates:** When asked to integrate a payment processor with NPSP, the LLM produces an Apex class implementing `blng.PaymentGateway` with methods like `authorize()`, `capture()`, and `refund()`, citing Salesforce Billing documentation.

**Why it happens:** The Salesforce Billing developer guide is prominent in training data for "Salesforce payment gateway Apex interface." The `blng.PaymentGateway` pattern is well-documented and syntactically plausible, so LLMs surface it confidently for any Salesforce payment gateway request regardless of whether the org is running Billing, NPSP, or Nonprofit Cloud.

**Correct pattern:**

```
For NPSP/NPC payment gateway integration:
- Use Salesforce.org Elevate (Payment Services) as the payment processor connector
- Payment outcomes surface on GiftTransaction via the Connect REST API:
  POST /services/data/v59.0/connect/fundraising/transactions/payment-updates
- There is no Apex interface to implement for nonprofit payment processing
- blng.PaymentGateway is Salesforce Billing only and will not compile without the blng package
```

**Detection hint:** Any Apex snippet containing `implements blng.PaymentGateway` in a nonprofit/NPSP context is wrong. Flag all occurrences of `blng.PaymentGateway` when the skill context is NPSP or Nonprofit Cloud.

---

## Anti-Pattern 2: Treating Wealth Screening as a Native Salesforce API

**What the LLM generates:** Apex callout code that calls an undocumented or imagined Salesforce endpoint like `/services/data/vXX.0/wealth/screen` or a generic HTTP callout to `api.salesforce.com/wealth-data`, as if Salesforce provides a native wealth data service.

**Why it happens:** LLMs learn that Salesforce provides many native APIs and may hallucinate a wealth screening endpoint or conflate Salesforce's partnership with wealth data vendors with a native platform capability. The `Einstein Scoring` or `Data Cloud enrichment` patterns in training data may also bleed over.

**Correct pattern:**

```
Wealth screening in Salesforce:
- No native Salesforce API for wealth data exists
- Use a managed package from AppExchange:
  - iWave for Salesforce (iWave AppExchange listing)
  - DonorSearch for Salesforce (DonorSearch AppExchange listing)
- The package handles vendor API calls and writes scores to Contact fields
- Scores land on Contact (e.g., iwv__RatingScore__c) — not on GiftTransaction
- Custom direct API integration to iWave/DonorSearch requires the vendor's proprietary REST API
  and Named Credentials — not a Salesforce platform endpoint
```

**Detection hint:** Any reference to a Salesforce-native wealth, capacity, or screening endpoint is hallucinated. Flag `salesforce.com/wealth`, `einstein/screening`, or any non-AppExchange path for prospect data.

---

## Anti-Pattern 3: Directly Inserting GiftTransaction Records from External Systems

**What the LLM generates:** Integration code that uses the Salesforce REST API to POST new `GiftTransaction` records from an external event platform or peer-to-peer fundraising tool, treating `GiftTransaction` like any standard or custom object that accepts direct DML inserts from external callers.

**Why it happens:** LLMs know that the Salesforce REST API supports DML on standard and custom objects and generalize this to all objects. The fact that `GiftTransaction` is part of a managed processing flow with required gateway metadata fields is not obvious from the object's API name.

**Correct pattern:**

```
To create gift records from external systems in Nonprofit Cloud:
- Land the external transaction in a staging object first
- Promote to GiftEntry through the Elevate gift processing flow
- Do NOT insert GiftTransaction directly via REST API — records created this way
  will be missing Elevate-managed gateway metadata fields and will create
  reconciliation problems in gift reporting
- For event platform connectors with charitable components, use purpose-built
  AppExchange connectors (Classy, Bonterra) that handle GiftEntry promotion
```

**Detection hint:** Any code that performs a `POST /services/data/vXX.0/sobjects/GiftTransaction__c` from an external system without going through the Elevate gift entry path is likely wrong.

---

## Anti-Pattern 4: Using Marketing Cloud for Direct GiftTransaction Sync

**What the LLM generates:** A Marketing Cloud Connect configuration that syncs the `GiftTransaction` object as a Marketing Cloud data extension, or Apex code that pushes `GiftTransaction` records to Marketing Cloud via the SOAP/REST API for segmentation.

**Why it happens:** LLMs know that Marketing Cloud Connect can sync Salesforce objects and may suggest syncing `GiftTransaction` directly for fundraising campaign targeting, not knowing that `GiftTransaction` is not a natively supported synchronized object in Marketing Cloud Connect.

**Correct pattern:**

```
For email marketing segmentation in fundraising:
- GiftTransaction is NOT a natively supported Marketing Cloud Connect sync object
- Promote giving totals to Contact or Account via roll-up summary fields or
  calculated custom fields (e.g., Contact.Total_Lifetime_Giving__c)
- Sync Contact to Marketing Cloud with the giving total fields included
- Use Contact (and optionally Campaign Member) as the segmentation data source
- Wealth screening scores on Contact are also available for segmentation
  after the iWave/DonorSearch package writes them
```

**Detection hint:** Any Marketing Cloud Connect configuration that lists `GiftTransaction` as a sync object should be flagged. Check for `GiftTransaction` in data extension source configurations.

---

## Anti-Pattern 5: Hardcoding Payment Processor or Wealth Screening Credentials in Apex

**What the LLM generates:** Apex code with string literals like `String apiKey = 'sk_live_XXXX';` or custom metadata queries that retrieve API keys stored in plaintext custom metadata fields, used to authenticate callouts to payment processors or wealth screening APIs.

**Why it happens:** LLMs optimize for working code and commonly demonstrate credential usage with inline string assignments in tutorial-style examples. The Named Credentials pattern requires additional setup steps that LLMs may omit when focused on making the callout logic compile.

**Correct pattern:**

```apex
// WRONG — never store credentials in Apex or custom metadata plaintext
HttpRequest req = new HttpRequest();
req.setHeader('Authorization', 'Bearer sk_live_XXXX');

// CORRECT — use Named Credentials
HttpRequest req = new HttpRequest();
req.setEndpoint('callout:iWave_API/v1/screen');
req.setHeader('Content-Type', 'application/json');
// Authentication is handled by the Named Credential — no key in code
```

**Detection hint:** Any Apex string literal that looks like an API key, bearer token, or password in a callout context is a credential exposure risk. Flag patterns matching: `'Bearer [A-Za-z0-9_\-]{20,}'`, `apiKey = '`, or `password = '` in HTTP callout Apex.

---

## Anti-Pattern 6: Assuming Elevate Is Included in All Nonprofit Cloud Licenses

**What the LLM generates:** Integration architecture guidance that assumes Elevate (Payment Services) is automatically available in any Nonprofit Cloud or NPSP org, or designs that require Elevate as a hard dependency without noting the separate licensing requirement.

**Why it happens:** Salesforce.org Elevate is tightly associated with Nonprofit Cloud in marketing materials and documentation, leading LLMs to assume it is bundled. The separate licensing and provisioning step is not prominent in most training data.

**Correct pattern:**

```
Before designing any payment gateway integration in NPSP/NPC:
1. Confirm Elevate is installed: Setup > Installed Packages > search "Elevate" or "Payment Services"
2. If absent, surface the licensing requirement to the project team before proceeding
3. If Elevate cannot be procured, evaluate AppExchange payment connectors as alternatives
4. Document the Elevate dependency in integration architecture diagrams — it is not automatic
```

**Detection hint:** Any integration design that specifies the `/connect/fundraising/transactions/payment-updates` endpoint without first verifying Elevate provisioning should include an explicit prerequisite check for the Elevate managed package.
