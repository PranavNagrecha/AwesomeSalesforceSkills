# Examples — Industries Energy Utilities Setup

## Example 1: New Residential Customer ServicePoint Provisioning in a Regulated Market

**Context:** A regulated electricity utility is migrating residential customer service locations from a legacy CIS into E&U Cloud. The admin needs to create a ServicePoint, Meter, and ServiceContract for a new residential customer whose account already exists in Salesforce.

**Problem:** Without a defined setup sequence, admins create the ServiceContract before the RatePlan records are synced from the CIS. The ServiceContract is created successfully (no error fires), but the RatePlan lookup is null. Billing cycles then produce zero-charge Consumption records, which are discovered during the first billing run — not at setup time.

**Solution:**

The correct sequence is to validate CIS sync first, then create objects top-down:

```
Step 1 — Verify RatePlan sync from CIS:
  SOQL: SELECT Id, Name, RatePlanCode__c, ServiceType__c, MarketSegment__c
        FROM RatePlan
        WHERE ServiceType__c = 'Electricity' AND MarketSegment__c = 'Residential'
  → Confirm at least one record exists matching the tariff class in the CIS.
  → If zero records return, halt and investigate the CIS integration before proceeding.

Step 2 — Create ServicePoint:
  Object: ServicePoint
  Fields:
    AccountId      = <Customer Account Id>
    ServiceType    = 'Electricity'
    MarketSegment  = 'Residential'
    Status         = 'Active'
    Street, City, State, PostalCode = <Service location address>
  → Do NOT use Account Billing Address fields as a substitute.

Step 3 — Create Meter linked to ServicePoint:
  Object: Meter
  Fields:
    ServicePointId = <ServicePoint Id from Step 2>
    MeterType      = 'AMI'      -- Advanced Metering Infrastructure
    Status         = 'Active'
    InstallDate    = <Installation date>

Step 4 — Create ServiceContract:
  Object: ServiceContract
  Fields:
    AccountId      = <Customer Account Id>
    ServicePointId = <ServicePoint Id from Step 2>
    RatePlanId     = <RatePlan Id from Step 1 matching tariff class>
    StartDate      = <Contract effective date>
    Status         = 'Active'
  → Verify Status = 'Active' after save. If Status remains 'Draft',
    inspect the RatePlanId lookup — a null or mismatched lookup blocks activation.
```

**Why it works:** The CIS sync validation in Step 1 is the critical gate. E&U Cloud does not validate the RatePlan lookup at ServiceContract insert time — a null RatePlanId is accepted without error. The failure only appears when Consumption records are processed against the contract during a billing run. Validating RatePlan presence before creating the ServiceContract prevents silent billing failures.

---

## Example 2: Rate Plan Change Service Order for a Competitive Market Customer

**Context:** A competitive energy retailer using E&U Cloud needs to process a customer request to switch from a fixed-rate plan to a time-of-use (TOU) plan. The customer's ServicePoint, Meter, and active ServiceContract already exist. The new RatePlan has been synchronized from the CIS.

**Problem:** An admin directly edits the RatePlan lookup field on the ServiceContract record to point to the new plan. The edit saves successfully. However, the change bypasses the service order workflow, creates no audit trail, does not notify the CIS of the rate change, and in a regulated-market configuration would violate the audit trail required for regulatory reporting.

**Solution:**

Use the service order workflow rather than a direct field edit:

```
Step 1 — Confirm the target RatePlan record exists:
  SOQL: SELECT Id, Name, RatePlanCode__c
        FROM RatePlan
        WHERE RatePlanCode__c = 'TOU-STANDARD-001'
  → If the record is absent, the CIS integration must sync it before proceeding.
  → Never create a RatePlan record manually; CIS is the authoritative source.

Step 2 — Create a Rate Change service order:
  Object: WorkOrder (or CustomerOrder depending on E&U edition)
  Fields:
    ServicePointId     = <Existing ServicePoint Id>
    AccountId          = <Customer Account Id>
    ServiceOrderType   = 'RateChange'
    TargetRatePlanId   = <RatePlan Id from Step 1>
    RequestedStartDate = <Customer-requested effective date>

Step 3 — Execute the service order:
  → Service order execution triggers the configured integration process to notify
    the CIS of the rate change. Wait for the CIS acknowledgement callback before
    updating the ServiceContract.

Step 4 — Update ServiceContract after CIS acknowledgement:
  → On receipt of the CIS acknowledgement event (Platform Event or webhook
    depending on integration design), update ServiceContract.RatePlanId to the
    new plan and set the effective date.

Step 5 — Verify Consumption calculation basis:
  → Query recent Consumption records to confirm the billing rate basis has
    updated to the new plan code.
```

**Why it works:** The service order workflow preserves the audit trail, ensures the CIS is notified before Salesforce is updated (maintaining CIS as authoritative), and applies the correct effective date. Direct field edits on ServiceContract skip all of this and produce orphaned CIS state — the CIS continues billing the old plan while Salesforce reflects the new plan.

---

## Anti-Pattern: Using Account and Asset to Track Service Locations

**What practitioners do:** Admins familiar with standard Salesforce store utility service location data as Account address fields (for the location) and Asset records (for the meter equipment). They add custom fields on Account for tariff class and meter serial number, then build reports from Account.

**What goes wrong:** All native E&U Cloud OmniStudio integrations, service order workflows, and CIS sync processes expect ServicePoint as the anchor object. Reports and dashboards built on Account-based location data do not connect to Consumption, MeterReading, or ServiceContract records. When the org later enables E&U Cloud native workflows, the Account-based data must be migrated into ServicePoint and Meter records — a costly, error-prone data migration that could have been avoided.

**Correct approach:** Use ServicePoint as the physical metering location object from the start. Use Meter for metering device tracking. Use Account only as the customer relationship anchor (linked to ServicePoint via the AccountId lookup on ServicePoint). Do not replicate ServicePoint data onto Account or Asset.
