# Examples — Industries Integration Architecture

## Example 1: Insurance — OmniScript Calls Policy Admin System via Integration Procedure

**Context:** An Insurance Cloud implementation has a "Policy Change" OmniScript that allows agents to modify coverage on an existing policy. The policy administration system (external PAS) is the authoritative owner of all policy state. The Salesforce org holds the engagement history.

**Problem:** The team initially designed the OmniScript to read policy data from `InsurancePolicy` records in Salesforce, allow the agent to edit coverage fields, and write the changes back to both `InsurancePolicyCoverage` in Salesforce and the PAS simultaneously (dual-write). Within weeks of go-live, the PAS and Salesforce held different coverage values for the same policy because the PAS sync batch and the agent-initiated dual-write conflicted on timing.

**Solution:**

Integration Procedure action chain (conceptual — no Apex required):

```
IntegrationProcedure: Insurance_PolicyChange_Read
  Step 1: HTTP Action
    Named Credential: PAS_System
    Method: GET
    URL: /api/v1/policies/{policyId}
    Response Mapping:
      $.coverageType   → output:coverageType
      $.effectiveDate  → output:effectiveDate
      $.premium        → output:premium

  Step 2: Set Values (error handling)
    If HTTP Action statusCode != 200:
      output:error = "Policy system unavailable. Please try again later."

IntegrationProcedure: Insurance_PolicyChange_Write
  Step 1: HTTP Action
    Named Credential: PAS_System
    Method: PUT
    URL: /api/v1/policies/{policyId}/coverage
    Body: { "coverageType": "{input:newCoverageType}", ... }

  Step 2: Data Raptor Transform (engagement record)
    Create/Update: Interaction__c (engagement artifact only)
    Fields: PolicyId__c, ChangeType__c, ChangeTimestamp__c, AgentId__c
    // InsurancePolicy record is NOT updated by Salesforce
```

OmniScript calls `Insurance_PolicyChange_Read` to display current PAS values to the agent (read-only), then on submit calls `Insurance_PolicyChange_Write` to POST the change to PAS. Salesforce creates an `Interaction__c` engagement artifact recording what the agent did — it does not write back to `InsurancePolicy` or `InsurancePolicyCoverage` as an authoritative update.

**Why it works:** The PAS remains the single source of truth for policy state. The next scheduled sync from PAS into Salesforce `InsurancePolicy` objects will reflect the change without conflict. The engagement artifact in Salesforce provides the audit trail without creating a duplicate state management problem.

---

## Example 2: Communications Cloud — Migrating from MuleSoft Gateway to Direct TM Forum API Access

**Context:** A telecom carrier has Communications Cloud integrated with their BSS/OSS stack (Amdocs OMS) via a MuleSoft API Gateway that mediates all TM Forum API calls. The architecture was built in 2024 before the Winter '27 deprecation announcement.

**Problem:** The existing MuleSoft gateway routes all Communications Cloud product catalog (TMF620) and order management (TMF622) traffic through a MuleSoft-hosted API proxy layer. With the MuleSoft gateway pattern deprecated for Winter '27, the gateway will no longer receive Communications Cloud compatibility updates, creating a compliance and support risk.

**Solution:**

Direct TM Forum API Access migration steps:

```
1. In Communications Cloud Setup, navigate to:
   TM Forum API Settings → Access Mode → Switch from "MuleSoft Gateway" to "Direct Access"

2. Configure a Named Credential for each BSS/OSS endpoint:
   - PAS_TMF620_ProductCatalog: https://bss.carrier.example.com/tmf-api/productCatalogManagement/v4
   - PAS_TMF622_OrderManagement: https://bss.carrier.example.com/tmf-api/productOrderingManagement/v4

3. Create External Credential with OAuth 2.0 client_credentials grant type
   pointing to BSS/OSS auth server. Associate with Named Credentials above.

4. Validate with Salesforce TM Forum API test tool (Setup > TM Forum API Diagnostics)
   to confirm TMF620 GET /productOffering returns HTTP 200.

5. Update any Apex or Integration Procedure HTTP Actions that had hardcoded
   MuleSoft Gateway URLs to reference the new Named Credentials.

6. Deprecate MuleSoft gateway route — do not leave dual-routing active.
```

**Why it works:** Direct Access removes the MuleSoft intermediary layer entirely, puts the org on the only forward-supported path for Winter '27+, and reduces per-request latency by one network hop. OAuth 2.0 client_credentials via Named Credential provides secure, rotation-safe auth without embedding credentials in metadata.

---

## Example 3: Energy & Utilities — CIS Rate Plan One-Way Sync Pattern

**Context:** A utility company uses Salesforce E&U Cloud for customer service interactions. Their CIS (SAP IS-U) owns all rate plan definitions, tariff codes, and billing configurations. Agents need to see available rate plans when enrolling customers in a new service, but the service enrollment OmniScript was making a live callout to SAP IS-U on every step render, causing 3–8 second delays and occasional failures when SAP was in a batch window.

**Problem:** Live callout from OmniScript to CIS on every rate plan display step created user experience degradation and enrollment failures during SAP maintenance windows.

**Solution:**

```
Architecture:
  CIS (SAP IS-U) ──[nightly batch + change event]──► Salesforce E&U Cloud
  Direction: one-way inbound only

Sync job (runs nightly + on SAP rate change event):
  For each active RatePlan in SAP IS-U:
    Upsert EnergyRatePlan__c (or standard E&U rate object) in Salesforce
    Fields: ExternalId__c (SAP rate code), RateName__c, TariffCode__c,
            EffectiveDate__c, ExpirationDate__c, IsActive__c

FLS configuration (immediate post-sync):
  All CIS-sourced fields on EnergyRatePlan__c → Read-Only for all profiles
  Prevents Salesforce users from overwriting CIS data between syncs

OmniScript enrollment step:
  Data Raptor → SOQL EnergyRatePlan__c WHERE IsActive__c = true
  (local Salesforce query — zero dependency on SAP availability at runtime)

On enrollment submission:
  OmniScript Integration Procedure:
    HTTP Action → ServiceOrder creation in SAP IS-U
    Salesforce: create ServiceOrder__c with ExternalSAPOrderId__c
    Salesforce does NOT update EnergyRatePlan__c — SAP activates the rate
```

**Why it works:** The OmniScript reads rate plan data from a local Salesforce copy, so CIS maintenance windows or slow responses do not affect the enrollment UI. FLS locks prevent accidental Salesforce edits from corrupting the CIS projection. The one-way sync ensures SAP IS-U remains the exclusive rate authority.

---

## Anti-Pattern: Treating InsurancePolicy as a Dual-Write System

**What practitioners do:** When an external policy administration system is integrated, some teams configure a scheduled batch to sync PAS → Salesforce InsurancePolicy, AND allow OmniScript-triggered writes to update InsurancePolicy simultaneously. They believe this keeps Salesforce "up to date" and "as the authoritative system."

**What goes wrong:** The outbound sync (PAS → Salesforce) and the inbound agent edits compete. When the PAS sync batch runs after an agent edits a field in Salesforce, the PAS values overwrite the agent's change without notification. When the agent edit happens after PAS sync, Salesforce holds stale PAS data for up to one sync cycle. In high-volume environments, these conflicts produce data quality incidents that require manual reconciliation. The `InsurancePolicy` object was not designed to be a conflict-resolution merge point — it has no built-in versioning or merge strategy.

**Correct approach:** Designate one system as authoritative per field/domain. If PAS owns policy state: PAS → Salesforce is read-only projection, FLS-locked. Salesforce writes only engagement artifacts. If Salesforce must own a specific field (e.g., a custom service flag), exclude that field from PAS sync scope so the PAS batch never touches it.
