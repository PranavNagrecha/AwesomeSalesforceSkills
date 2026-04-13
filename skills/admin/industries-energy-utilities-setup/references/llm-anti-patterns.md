# LLM Anti-Patterns — Industries Energy Utilities Setup

Common mistakes AI coding assistants make when generating or advising on Energy and Utilities Cloud setup.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Applying Standard Salesforce Setup Patterns Directly to E&U Cloud

**What the LLM generates:** Setup instructions that tell users to create custom permission sets with object CRUD, configure standard Account fields for service location data, and use Asset records for meter tracking — because these are the standard Salesforce patterns for equipment and customer location management.

**Why it happens:** LLMs trained on broad Salesforce documentation default to standard Sales/Service Cloud patterns. E&U Cloud adds a distinct object layer (ServicePoint, Meter, ServiceContract, RatePlan) that replaces the role of Account address fields and Asset records for utility-specific data. Training data for E&U Cloud-specific setup is sparse compared to standard Salesforce admin content.

**Correct pattern:**

```
- Use ServicePoint (not Account address fields) for physical metering locations
- Use Meter (not Asset) for metering device tracking
- Assign E&U Cloud managed package permission sets (not custom permission sets with CRUD)
- Follow the E&U Cloud setup sequence: license → permission sets → CIS integration → objects
```

**Detection hint:** Output contains "Asset" as the meter equipment object, or instructs users to add custom fields on Account for tariff class or meter serial number, or suggests creating custom permission sets for E&U Cloud object access.

---

## Anti-Pattern 2: Using Account or Asset for ServicePoint and Meter Data

**What the LLM generates:** Data model recommendations that store service location address data in Account billing/shipping address fields and meter device information in Asset records with custom fields for meter type, serial number, and reading schedule.

**Why it happens:** Account address fields and Asset records are the standard Salesforce way to model physical locations and equipment. LLMs generalize this pattern to E&U Cloud without recognizing that E&U Cloud provides dedicated objects (ServicePoint, Meter) that carry the correct relationship structure, OWD settings, and integration hooks.

**Correct pattern:**

```
ServicePoint:
  - Use for physical metering location (address, service type, market segment)
  - Linked to Account via AccountId lookup on ServicePoint
  - Do NOT replicate ServicePoint data onto Account address fields

Meter:
  - Use for metering device (type, serial number, status, install date)
  - Linked to ServicePoint via ServicePointId lookup on Meter
  - Do NOT use Asset for metering device tracking in E&U Cloud implementations
```

**Detection hint:** Output shows `Account.BillingStreet` or `Account.ShippingStreet` being used for service location addresses, or `Asset` with custom fields for MeterType or ReadingSchedule.

---

## Anti-Pattern 3: Creating Rate Plans Directly in Salesforce Without CIS Sync

**What the LLM generates:** Instructions to create RatePlan records directly in Salesforce using the UI or a data load, treating RatePlan as a Salesforce-managed configuration object, and then assigning those manually created records to ServiceContracts.

**Why it happens:** LLMs recognize RatePlan as a standard E&U Cloud object and assume it can be configured like other Salesforce objects (e.g., creating pricebooks or product records). They do not recognize that in nearly all E&U Cloud implementations the CIS or billing system is the authoritative source for rate plan definitions and that Salesforce is downstream.

**Correct pattern:**

```
- Treat the external CIS/billing system as the authoritative source for RatePlan records
- Configure the CIS-to-Salesforce integration to sync RatePlan records
- Before creating ServiceContracts, validate that RatePlan records exist in Salesforce
  via SOQL: SELECT Id, Name, RatePlanCode__c FROM RatePlan WHERE ServiceType__c = '<type>'
- Only create RatePlan records manually if the implementation explicitly designs Salesforce
  as the rate plan master — document this decision in the architecture
```

**Detection hint:** Output instructs users to "create a new Rate Plan record" in Salesforce Setup or via Data Loader without any mention of CIS synchronization or confirming that the CIS is not the authoritative source.

---

## Anti-Pattern 4: Not Distinguishing Regulated vs Competitive Market Configuration

**What the LLM generates:** A single generic E&U Cloud setup guide that applies the same ServicePoint field configuration, rate plan assignment logic, and service order workflow to all implementations, without accounting for regulated vs competitive market differences.

**Why it happens:** Generic E&U Cloud documentation and tutorials often present a single setup flow without explicitly labeling it as regulated-market or competitive-market specific. LLMs synthesize these sources into a unified setup guide without recognizing that market type is a structural branch point, not a minor configuration detail.

**Correct pattern:**

```
Regulated market:
  - MarketSegment on ServicePoint must match legally mandated tariff class from CIS
  - RatePlan assignment is automatic based on ServicePoint attributes — not customer-chosen
  - Rate plan changes require a service order and may require regulatory approval
  - DSO and retailer fields may not be applicable

Competitive market:
  - ServicePoint requires retailer identifier and DSO identifier
  - Customers can choose from multiple RatePlans — assignment is not automatic
  - Rate plan changes are initiated by customer request via a retailer change service order
  - Market type affects service order routing and CIS notification logic
```

**Detection hint:** Output does not mention market type at all, or presents rate plan assignment as always automatic (regulated-market assumption applied universally), or omits DSO and retailer fields entirely for a competitive-market context.

---

## Anti-Pattern 5: Conflating This Operational Setup Skill with the architect/industries-data-model Reference Skill

**What the LLM generates:** Setup instructions that focus primarily on SOQL queries, object relationship diagrams, and data model schema descriptions rather than the operational sequence of activating licenses, assigning permission sets, configuring objects, and validating CIS integration.

**Why it happens:** The `architect/industries-data-model` skill covers the E&U Cloud data model schema and SOQL patterns. LLMs that retrieve both skills simultaneously blend the schema reference content with the operational setup content, producing output that describes the object model correctly but does not guide the practitioner through the actual setup steps.

**Correct pattern:**

```
This skill (industries-energy-utilities-setup) covers:
  - License activation and permission set assignment
  - ServicePoint, Meter, and ServiceContract configuration sequence
  - CIS integration validation
  - Rate plan assignment dependencies
  - Service order workflow setup

Use architect/industries-data-model for:
  - Object relationship schema reference
  - SOQL query patterns for E&U Cloud objects
  - Data model comparison across Industries clouds (Insurance, Comms, Health, E&U)
```

**Detection hint:** Output is primarily SOQL queries and object relationship descriptions with no mention of license activation, permission sets, or CIS integration steps. Or output instructs the user to "refer to the data model" without providing operational setup guidance.
