# Gotchas — Industries Energy Utilities Setup

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Incomplete CIS Integration Silently Breaks Billing Cycles

**What happens:** When the external CIS or billing system integration is incomplete or not yet configured, RatePlan records are absent from Salesforce. ServiceContracts can still be created successfully — Salesforce does not enforce a non-null RatePlanId at insert time. The ServiceContract saves with a null or stale RatePlan reference. When billing cycle jobs run and process Consumption records against the ServiceContract, charges calculate as zero or use the wrong tariff. No error fires at setup time; the failure surfaces days or weeks later during billing reconciliation.

**When it occurs:** During initial E&U Cloud rollout when admins configure ServicePoints and ServiceContracts before the CIS integration is fully operational, or after a CIS migration where rate plan codes change and the sync is not updated to reflect new codes.

**How to avoid:** Before creating any ServiceContract, run a SOQL query on the RatePlan object to confirm that plan records matching the expected service type and market segment exist and carry current CIS codes. If zero records return, halt ServiceContract creation and resolve the CIS integration first. Add a pre-deployment validation step to the release checklist that confirms RatePlan record counts match the expected tariff class count in the CIS.

---

## Gotcha 2: ServicePoint Is a Distinct Object — Not Account and Not Asset

**What happens:** Practitioners store service location data in Account billing address fields and meter equipment data in Asset records, using custom fields for tariff class and meter serial numbers. The setup appears functional because Account and Asset records exist and display correctly. However, all E&U Cloud native OmniStudio components, service order automation, and CIS sync processes require ServicePoint as the physical location anchor. Consumption, MeterReading, and ServiceContract records link to ServicePoint, not to Account address fields. Any native E&U workflow that relies on ServicePoint returns no data, and reports built on Account-based location data cannot join to industry-specific billing records.

**When it occurs:** When admins with standard Salesforce backgrounds begin setting up E&U Cloud before reading the industry object model, defaulting to familiar objects (Account, Asset) for data they recognize (location, equipment).

**How to avoid:** Establish ServicePoint as the canonical metering location object before any configuration work begins. Review the E&U Cloud data model documentation to confirm that ServicePoint, Meter, and Consumption are the expected objects, and that Account serves only as the customer relationship anchor via the AccountId lookup on ServicePoint.

---

## Gotcha 3: Regulated vs Competitive Market Configuration Rules Are Not Interchangeable

**What happens:** An admin configuring a competitive-market utility uses the setup pattern from a regulated-market reference, omitting retailer identifiers and Distribution System Operator (DSO) fields on ServicePoint. Alternatively, an admin in a regulated market applies competitive-market setup patterns, allowing customer-driven rate plan selection when tariffs are legally mandated by regulators. Neither configuration fails with an error. Both produce ServicePoint records that appear structurally complete but cause service order and rate plan assignment failures at runtime — in some cases only during actual billing cycle execution or when a service order is submitted.

**When it occurs:** When project teams reference generic E&U Cloud documentation or tutorials without confirming whether the guide is written for regulated or competitive market contexts. Also common during multi-market rollouts where the same configuration template is reused across markets with different regulatory models.

**How to avoid:** Identify the market type (regulated or competitive) as the first configuration step, before creating any ServicePoint records. Document the market type in the project setup assumptions. Use separate ServicePoint configuration checklists for regulated and competitive markets. In competitive markets, confirm that retailer and DSO identifier fields are populated. In regulated markets, confirm that MarketSegment values map to legally defined tariff classes from the CIS.

---

## Gotcha 4: Managed Package Permission Sets Are Required — Custom Permission Sets Are Not Sufficient

**What happens:** An admin creates a custom permission set with full CRUD on the ServicePoint, Meter, RatePlan, ServiceContract, and related E&U Cloud objects, then assigns it to users. Users still receive object-not-found errors or cannot see E&U Cloud objects in App Builder or OmniStudio. The issue is that access to E&U Cloud objects requires the managed package permission sets shipped with the Energy and Utilities Cloud package, not just object-level CRUD permissions on a custom permission set.

**When it occurs:** When admins unfamiliar with Industries Cloud managed package permission sets attempt to grant access using standard Salesforce permission set patterns. Also occurs when the E&U permission set license is assigned but the specific managed package feature permission sets (e.g., Energy and Utilities Cloud Standard User) are not also assigned.

**How to avoid:** After installing the E&U Cloud managed package, locate the permission sets deployed by the package in Setup > Permission Sets. Assign both the permission set license and at least one managed package feature permission set to each user who requires E&U Cloud access. Validate access by confirming the user can navigate to a ServicePoint record before proceeding with broader configuration.

---

## Gotcha 5: ServiceContract Status Remains Draft When RatePlan Lookup Is Null

**What happens:** A ServiceContract is created and saved without a valid RatePlanId (either because the RatePlan has not been synced from the CIS, or because the lookup was set to the wrong record). The ServiceContract saves in Draft status. There is no validation error and no warning — the record appears created successfully. Subsequent automation or billing jobs that depend on an Active ServiceContract skip the record because it never transitioned from Draft. The issue is not discovered until the service location fails to appear in billing reports.

**When it occurs:** When the ServiceContract is created before RatePlan records are available in Salesforce, or when a data migration load does not correctly map RatePlan external IDs to Salesforce record IDs.

**How to avoid:** After creating each ServiceContract, explicitly query the Status field to confirm it is Active. Build a post-migration validation script that queries ServiceContracts where Status != 'Active' and RatePlanId = null, and alerts the admin team before billing cycles run. Do not assume a successful DML insert means the contract is in Active status.
