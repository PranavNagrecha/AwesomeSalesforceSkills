# LLM Anti-Patterns — Media Cloud Setup

Common mistakes AI coding assistants make when configuring Media Cloud.

## Anti-Pattern 1: Confusing Media Cloud with Marketing Cloud

**What the LLM generates:** Suggests Journey Builder, Email Studio, or Automation Studio when the user asks about "Media Cloud campaigns."

**Why it happens:** Naming collision — both have "Cloud" and "campaign." Media Cloud is ad-sales; Marketing Cloud is outbound marketing.

**Correct pattern:**

```
Media Cloud: advertising sales, deal/contract/placement model, revenue
recognition for impressions/spots/issues.
Marketing Cloud: outbound messaging (email, SMS, push) for marketers.
```

**Detection hint:** Any answer referencing Journey Builder / Automation Studio in response to a Media Cloud question.

---

## Anti-Pattern 2: Storing raw impression logs in Salesforce

**What the LLM generates:** A custom object `Impression_Event__c` loaded with billions of raw ad server rows.

**Why it happens:** The model treats Salesforce as the primary data store; ad server log volumes exceed Salesforce sustainable ingestion.

**Correct pattern:**

```
Aggregate upstream (in ad server or a data warehouse). Load only daily
rollups into Salesforce for billing and reporting. Keep the raw logs
in the ad server or a data lake.
```

**Detection hint:** A Media Cloud org with an `Impression_Event__c` or similar high-volume custom object.

---

## Anti-Pattern 3: Hand-rolling revenue recognition in Apex

**What the LLM generates:** An Apex scheduled job that iterates Placements and creates Revenue_Schedule__c rows based on hard-coded rules.

**Why it happens:** Revenue recognition per media type is complex; the model defaults to code when BRE/Revenue Cloud shipped rules are unfamiliar.

**Correct pattern:**

```
Use Media Cloud Revenue Management. Configure recognition rules per
product family. The shipped engine is audited and GAAP/ASC 606 aligned.
Rolling your own risks SOX audit findings.
```

**Detection hint:** Apex classes named like `RevRec`, `RecognizeRevenue`, or `MonthlyRevenueCalc` in a Media Cloud org.

---

## Anti-Pattern 4: Static audience counts on Placements

**What the LLM generates:** Copies audience size from the DMP once, stores on `Placement.Audience_Size__c`, and uses that for pricing.

**Why it happens:** The model does not model audience volatility.

**Correct pattern:**

```
Refresh audience size on every Placement save and before pricing. Audience
segments change daily as profiles move; stale sizes cause under/over
pricing and inventory over-commitment.
```

**Detection hint:** A Placement page layout showing a static `Audience_Size__c` field with no refresh button or on-save automation.

---

## Anti-Pattern 5: One Placement per media type with rigid schema

**What the LLM generates:** Separate `Digital_Placement__c`, `Linear_Placement__c`, `Print_Placement__c` custom objects.

**Why it happens:** The model prefers specialized objects over record types.

**Correct pattern:**

```
Use one Placement object with record types per media type. Shared fields
(flight dates, audience, contract link) stay common; product-specific
fields live in record-type-specific page layouts.
```

**Detection hint:** Multiple `*_Placement__c` custom objects in the same org.
