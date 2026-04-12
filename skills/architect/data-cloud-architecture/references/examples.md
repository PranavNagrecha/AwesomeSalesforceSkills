# Examples — Data Cloud Architecture

## Example 1: Retailer Unifying CRM, E-Commerce, and Loyalty Program Data

**Context:** A mid-size retailer ingests data from Salesforce CRM (Sales Cloud), a Shopify e-commerce platform, and a third-party loyalty program. Each source uses a different primary key (CRM uses Salesforce Contact ID, Shopify uses Shopify Customer ID, loyalty uses Loyalty Member Number) but all three capture email addresses. The business goal is a single unified customer profile that combines purchase history, loyalty tier, and CRM interactions.

**Problem:** Without deliberate DMO mapping and identity resolution design, each source produces isolated records in Data Cloud. Segments built on CRM attributes cannot be enriched with loyalty tier, and activation to the ad platform sends only the CRM population, missing customers who exist only in e-commerce or loyalty data.

**Solution:**

The architecture uses email as the anchor identity attribute across all three sources:

```
Source: Salesforce CRM
  DLO: CRM_Contact_DLO
  DMO mappings:
    Individual.firstName       ← Contact.FirstName
    Individual.lastName        ← Contact.LastName
    ContactPointEmail.emailAddress ← Contact.Email   [identity resolution eligible]
    ContactPointPhone.telephoneNumber ← Contact.Phone [identity resolution eligible]

Source: Shopify
  DLO: Shopify_Customer_DLO
  DMO mappings:
    ContactPointEmail.emailAddress ← customer.email  [identity resolution eligible]
    PartyIdentification.partyIdentificationNumber ← customer.id
    PartyIdentification.partyIdentificationType ← "ShopifyCustomerID"

Source: Loyalty Program
  DLO: Loyalty_Member_DLO
  DMO mappings:
    ContactPointEmail.emailAddress ← member.email    [identity resolution eligible]
    PartyIdentification.partyIdentificationNumber ← member.loyalty_id
    PartyIdentification.partyIdentificationType ← "LoyaltyMemberNumber"
    Individual.loyaltyTier ← member.tier  (custom DMO field)

Identity Resolution Ruleset:
  Match Rule 1: Exact match on ContactPointEmail.emailAddress  (primary)
  Match Rule 2: Exact match on PartyIdentification where type = ShopifyCustomerID (secondary)

  Reconciliation Rules:
    Individual.firstName     → Most Recent
    Individual.lastName      → Most Recent
    Individual.loyaltyTier   → Source Priority (Loyalty Program first)
    ContactPointEmail.emailAddress → Most Recent
```

**Why it works:** All three sources contribute to the same identity cluster because all three map `ContactPointEmail` — the exact match rule on email links records across sources. The loyalty tier uses Source Priority reconciliation to ensure the loyalty program (the authoritative source for tier) always wins, even if CRM stores a stale cached value. The Shopify PartyIdentification mapping adds a second resolution path for customers who have changed their email in CRM but not yet in Shopify.

---

## Example 2: B2B Company Diagnosing Low Unified Individual Coverage

**Context:** A B2B software company ingests CRM Account, Contact, and Opportunity data into Data Cloud. After identity resolution runs, the Unified Individual count is 8,000 records against 45,000 Contact records in CRM — a coverage rate of under 18%. The expectation was coverage above 80%.

**Problem:** The architecture team assumed all ingested DMOs automatically participate in identity resolution. In fact, only DMOs with ContactPoint or PartyIdentification mappings contribute to identity clusters. The CRM ingestion mapped Contact records to the `Individual` DMO and the `Opportunity` DMO but did not create a `ContactPointEmail` mapping.

**Solution:**

```
Diagnosis steps:
1. In Data Cloud Setup > Identity Resolution > Ruleset, check the "Source DMOs" panel
   — Only DMOs explicitly listed there participate in identity resolution.
   — Individual DMO alone does NOT qualify — it must be paired with a ContactPoint mapping.

2. Audit the CRM data stream's field mapping:
   BEFORE (incorrect):
     Individual.firstName  ← Contact.FirstName
     Individual.lastName   ← Contact.LastName
     Individual.email      ← Contact.Email     ← THIS IS WRONG
     (email mapped to Individual, not ContactPointEmail)

   AFTER (correct):
     Individual.firstName  ← Contact.FirstName
     Individual.lastName   ← Contact.LastName
     ContactPointEmail.emailAddress  ← Contact.Email   ← correct DMO target

3. After fixing the mapping, re-run the data stream ingestion and then re-run identity resolution.
   Coverage rate after fix: 82% (close to expected, with remaining gap explained
   by Contacts with no email address on record).
```

**Why it works:** The `Individual` DMO is the profile container, but identity resolution operates on `ContactPointEmail`, `ContactPointPhone`, and `PartyIdentification` DMOs — these are the link entities that carry the matchable identifiers. Mapping email to `Individual.email` (a custom field) instead of `ContactPointEmail.emailAddress` bypasses the identity resolution engine entirely with no error.

---

## Anti-Pattern: Building Segments with Calculated Insights for a Real-Time Use Case

**What practitioners do:** A marketing team wants to re-target website visitors who viewed a product page in the last 30 minutes. They build a Calculated Insight that counts page views per contact in a rolling window, then create a segment that filters `pageViewsLast30Min > 0`. The segment is published to a Meta Ads activation target with a "continuous" publish schedule.

**What goes wrong:** Calculated Insights run on a batch schedule. Even with the most aggressive CI refresh (every 15 minutes in some configurations), the segment activation reflects the last CI batch run — not the truly current 30-minute window. High-intent visitors leave the site before the segment activates to the ad platform. The campaign underperforms relative to expectations.

**Correct approach:** Replace the Calculated Insight with a Streaming Insight that processes page view events from the real-time ingestion stream. Streaming Insights update in near-real-time and can accurately represent activity within the last few minutes. The segment filter then reads from the Streaming Insight value, which is continuously updated as new events arrive. The architectural rule: if the use case requires data fresher than the CI batch schedule, use a Streaming Insight.
