# Examples — Industries Process Design

## Example 1: Insurance FNOL Customization for Commercial Property Claims

**Context:** A commercial lines insurer uses Salesforce Insurance Cloud (FSC + Claims Management module). Their standard auto claims FNOL process runs on the prebuilt Claims Management OmniScript. They need to add a Commercial Property branch: when a claim is of type "Commercial Property", the FNOL intake must capture building details (address, square footage, construction type), multiple loss locations, and a preliminary loss estimate. Auto claims must be unaffected.

**Problem:** The team's first instinct was to build a new Screen Flow to replace the FNOL OmniScript for commercial property claims, reasoning that Screen Flow is simpler to configure. The Screen Flow version passed UAT but created Claim records without the correct ClaimType relationship needed by the Claims Management API for financial processing. The Adjuster's Workbench could not load the claims because it expected data structures populated by the OmniScript-framework Remote Actions, not by Screen Flow DML.

**Solution:**

The correct approach is to add a Commercial Property conditional branch within the prebuilt FNOL OmniScript rather than replace it:

```
1. In OmniStudio Designer, open the FNOL OmniScript (Claims namespace or org namespace depending on DIP path).
2. Locate the Step covering "Incident Details".
3. Add a Block element named "CommercialPropertyDetails" within that Step.
4. Set the Block's Conditional View property:
   Condition: %ClaimType:value% == 'CommercialProperty'
5. Inside the Block, add Text, Number, and Lookup elements for:
   - BuildingAddress (Text)
   - SquareFootage (Number)
   - ConstructionType (Picklist — values: Frame, Masonry, Fire Resistive)
   - LossLocations (multi-entry repeatable section using OmniScript's Repeat element)
   - PreliminaryLossEstimate (Currency)
6. Add a Post-Step DataRaptor Transform action that writes the commercial property
   field values to the Claim record's custom fields alongside the standard ClaimType
   and InsurancePolicy relationships.
7. Confirm the ClaimType picklist on the Claim object includes 'CommercialProperty'
   as an active value.
```

**Why it works:** The OmniScript framework preserves the Claims Management API integration — the Remote Action calls that link the Claim to the InsurancePolicy and populate the ClaimParticipant records still execute as part of the original OmniScript lifecycle. The commercial property fields are additive, not replacements for the standard claims data model. The Adjuster's Workbench loads correctly because the Claim record carries all required field values from the framework's standard data writes plus the new commercial property fields.

---

## Example 2: Telecom Bundle Decomposition Rule for a New 5G Home Bundle

**Context:** A Communications Cloud org has a functioning EPC catalog for broadband and voice services individually. The product team has launched a new "5G Home Bundle" combining broadband, home phone, and TV streaming. EPC configuration for the bundle (Product Specification, Product Offering, and ProductChildItem records for all three components) was completed by the catalog team. The implementation team now needs to configure order decomposition so that commercial orders for this bundle generate correct technical order records.

**Problem:** The development team wrote an Apex after-insert trigger on the OrderItem object. When a commercial order was placed for the 5G Home Bundle, the trigger detected the bundle OrderItem and created three technical order records manually in the vlocity_cmt__TechnicalOrderItem__c object. The records appeared in the database. However, they did not participate in the Industries Order Management lifecycle — status callbacks from provisioning systems had nowhere to update, dependency sequencing was not respected, and the technical orders never transitioned to a "Completed" status even after provisioning finished. Order fulfilment was stuck.

**Solution:**

Decomposition is configured declaratively in Industries Order Management, not via Apex:

```
1. Navigate to the Industries Order Management app (Communications Cloud App Launcher).
2. Open the Decomposition Rules configuration for the Commercial product category
   that contains the 5G Home Bundle.
3. Create a Decomposition Rule Set entry for the 5G Home Bundle Product Offering:
   - Source: 5G Home Bundle Product Offering (reference EPC Product Offering ID)
   - Decomposition type: Bundle
4. Add three Decomposition Rule child entries — one per component:
   a. Broadband Circuit Provisioning
      - Target action: ProvisionBroadbandCircuit
      - Dependency: none (first in sequence)
      - EPC Child Item reference: Broadband 100Mbps ProductChildItem
   b. CPE Equipment Activation
      - Target action: ActivateCPEDevice
      - Dependency: Broadband Circuit Provisioning (must complete first)
      - EPC Child Item reference: Home Gateway CPE ProductChildItem
   c. TV Streaming Account Creation
      - Target action: CreateStreamingAccount
      - Dependency: none (parallel to CPE, after circuit)
      - EPC Child Item reference: TV Streaming Service ProductChildItem
5. Submit a test commercial order in sandbox for the 5G Home Bundle.
6. Verify that three vlocity_cmt technical order records are generated, that
   CPE Activation shows Broadband Circuit as a prerequisite, and that
   status transitions propagate correctly when provisioning callbacks fire.
```

**Why it works:** The Industries Order Management decomposition engine owns the technical order record lifecycle, dependency graph, and status callback processing. Declarative decomposition rules are the platform's designed extension point for this pattern. Apex triggers cannot participate in this lifecycle — they can only create records, not enroll them in the managed order orchestration.

---

## Example 3: E&U Temporary Disconnect Service Order Process Design

**Context:** An energy retailer needs to add a "Temporary Disconnect for Non-Payment" service order type to their E&U Cloud implementation. The standard service order types (Connect, Disconnect, Rate Change) are already operational with the CIS integration active. The new order type must capture the disconnect reason, the reconnect conditions, and send the request to the CIS for field crew dispatch.

**Problem:** The project team designed the new service order type and built the OmniScript-based order capture UI before confirming how the CIS handles the new request code. In sandbox, the service order appeared to execute successfully because the sandbox CIS mock accepted all request types. In production, the CIS rejected the new order code with a 400 error. The service order stalled with no user-visible error message and no automatic retry — the Salesforce record showed status "In Progress" indefinitely.

**Solution:**

The correct sequence gates process design on CIS API confirmation:

```
1. Before any Salesforce configuration, confirm with the CIS team:
   - What request code the CIS uses for temporary disconnects
   - What payload fields are required (disconnect reason code, reconnect conditions date)
   - What status values the CIS returns on success vs failure
2. Map the Salesforce service order record fields to the CIS payload fields:
   - DisconnectReasonCode → CIS field: DISC_RSN_CD
   - ReconnectConditions → CIS field: RECN_COND_TXT
   - EffectiveDate → CIS field: EFF_DT
3. Configure the service order type in E&U Cloud:
   - Name: Temporary_Disconnect_NonPayment
   - Status flow: Draft → Submitted → In Progress → Completed / Failed
   - CIS endpoint mapping: POST /cis/api/serviceorders with correct request code
4. Build the OmniScript order capture UI with fields for disconnect reason
   (picklist) and reconnect conditions (text area).
5. Configure the exception path:
   - On CIS 400/500 response: set service order status to 'Failed'
   - Trigger a Task for the collections team to follow up manually
   - Log the CIS error response in a custom ExternalCalloutLog field
6. Test with the live CIS in a test environment (not just sandbox mock)
   before deploying to production.
```

**Why it works:** The CIS integration dependency is treated as a hard gate, not an assumption. The exception path is designed before the happy path is deployed. The service order status model includes a terminal failure state that gives operations staff a clear signal rather than a stuck "In Progress" record.

---

## Anti-Pattern: Rebuilding the Insurance Claims Process as a Screen Flow

**What practitioners do:** A team unfamiliar with the Claims Management OmniScript framework builds a multi-step Screen Flow to capture FNOL information. The Screen Flow creates the Claim record via standard DML and links it to the InsurancePolicy. UAT passes because data appears in the Claim record.

**What goes wrong:** The Claims Management Adjuster's Workbench, the financial calculation actions (reserve setting, deductible calculation, payment authorization), and the Claims Management Connect API endpoints expect specific data structures and field relationships that are only populated by the OmniScript-framework Remote Actions. A Screen Flow that creates the Claim record via standard DML does not populate these relationships correctly. Claims created via Screen Flow cannot be processed through the standard adjuster workflow and appear as orphaned records in the Claims Management system.

**Correct approach:** Use the prebuilt Claims Management OmniScript framework. Customize stages by adding Steps, Blocks, and DataRaptor actions within the OmniScript designer. For net-new capabilities not covered by the prebuilt framework, build new OmniScript flows using the Claims Management Remote Actions, not Screen Flow DML.
