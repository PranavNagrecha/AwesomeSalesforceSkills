# LLM Anti-Patterns — Industries Process Design

Common mistakes AI coding assistants make when generating or advising on Industries Process Design.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Screen Flow to Implement Insurance Claims FNOL

**What the LLM generates:** A multi-step Screen Flow with record-create elements that creates a `Claim` record linked to `InsurancePolicy` via standard DML, using standard Screen Flow screens for incident data capture.

**Why it happens:** Screen Flow is the most widely documented Salesforce process automation tool and is the default recommendation for guided data entry in training data. The Claims Management OmniScript framework is less represented in general LLM training data. LLMs default to the familiar tool without accounting for the Claims Management API integration requirements.

**Correct pattern:**

```
1. Use the prebuilt Claims Management OmniScript (FNOL stage) as the starting point.
2. Customize within the OmniScript designer by adding Steps, Blocks,
   and DataRaptor actions.
3. Do not build a Screen Flow as a replacement. Screen Flow cannot:
   - Call Claims Management Connect API endpoints
   - Integrate with the Adjuster's Workbench component
   - Populate ClaimParticipant and financial record relationships
     expected by the Claims Management lifecycle
```

**Detection hint:** Any response that suggests building a Screen Flow for FNOL intake without first confirming whether the org has Claims Management module is applying the wrong tool. Look for the phrase "Record-Create element" or "standard Screen Flow" in the context of insurance claims capture.

---

## Anti-Pattern 2: Suggesting Apex Triggers to Generate Technical Order Records for Communications Cloud

**What the LLM generates:** An Apex `after insert` trigger on `OrderItem` that detects bundle products and programmatically creates `vlocity_cmt__TechnicalOrderItem__c` records to represent the technical fulfillment actions.

**Why it happens:** Apex trigger-based automation is a well-established pattern for order processing in standard Salesforce. The LLM applies this pattern to Communications Cloud without knowing that Industries Order Management has its own decomposition engine that is the platform-native mechanism for this behavior.

**Correct pattern:**

```
1. Configure decomposition rules in Industries Order Management.
   These are declarative configuration records — not Apex.
2. Decomposition rules reference EPC ProductChildItem relationships
   to determine which technical order items to generate.
3. Apex-generated technical order records do not participate in
   the IOM order lifecycle (status callbacks, dependency tracking,
   retry logic) even if they appear in the correct objects.
```

**Detection hint:** Any Apex snippet that writes to `vlocity_cmt__TechnicalOrderItem__c` or `vlocity_cmt__FulfilmentRequest__c` from a trigger on Order or OrderItem without mentioning decomposition rules is applying the wrong mechanism. Check for trigger-based creation of IOM objects.

---

## Anti-Pattern 3: Conflating Industries Order Management (Communications Cloud) with Salesforce Order Management (Commerce)

**What the LLM generates:** Advice to use `OrderSummary`, `FulfillmentOrder`, `OrderDeliveryGroup`, or Commerce Cloud REST endpoints for order processing in a Communications Cloud implementation. Alternatively: advice to use Industries Order Management for a B2C/B2B Commerce implementation.

**Why it happens:** Both products have "Order Management" in their names. General Salesforce documentation for Order Management primarily covers the Commerce platform (which is more heavily documented). LLMs conflate the two products because they share vocabulary but not object models, APIs, or fulfillment engines.

**Correct pattern:**

```
Communications Cloud → Industries Order Management
  Objects: vlocity_cmt namespace (TechnicalOrderItem, FulfilmentRequest, etc.)
  APIs: vlocity_cmt namespace APIs and EPC-integrated order flows
  Decomposition: declarative decomposition rules in IOM app

B2C/B2B Commerce → Salesforce Order Management
  Objects: OrderSummary, FulfillmentOrder, OrderDeliveryGroup
  APIs: Commerce REST APIs
  Fulfillment: Commerce fulfillment workflows
```

**Detection hint:** Any response mixing `OrderSummary` or `FulfillmentOrder` with EPC, vlocity_cmt, or Communications Cloud context is applying the wrong platform. Similarly, any response using IOM decomposition rule concepts in a pure Commerce Cloud context is incorrect.

---

## Anti-Pattern 4: Designing E&U Service Order Process Without Gating on CIS Integration Readiness

**What the LLM generates:** A complete E&U service order process design — OmniScript UI, service order type configuration, status transitions — without any mention of confirming that the CIS integration is operational or designing an exception path for CIS callout failures.

**Why it happens:** The LLM treats service order design as a Salesforce-internal configuration task and does not know that E&U service order execution is gated on an external CIS API callout. The LLM lacks context about the CIS dependency because it is an infrastructure concern outside the Salesforce platform.

**Correct pattern:**

```
Before any service order process design:
1. Confirm CIS integration is active — test an existing service order type
   end-to-end and verify the CIS callout fires and returns a success response.
2. Obtain the CIS API spec for the new order type: request code, payload
   fields, and response status values.
3. Design the exception path:
   - Service order status on CIS failure: 'Failed' (not 'In Progress')
   - Alert mechanism: Task creation, platform event, or named queue
   - Manual resolution procedure
Only then design the order capture UI and status transition logic.
```

**Detection hint:** A service order process design response that does not mention CIS integration, does not define an exception path for callout failure, or does not flag the need to validate against a production-equivalent CIS endpoint is incomplete for E&U Cloud. Look for absence of "CIS callout", "exception path", or "callout failure" handling.

---

## Anti-Pattern 5: Treating All Three Industry Verticals as Having the Same Process Runtime

**What the LLM generates:** A generic "industry process design" recommendation that suggests the same toolset and approach for Insurance, Communications, and E&U — typically defaulting to OmniScript for all three, or suggesting Screen Flow for all three, without distinguishing the vertical-specific runtimes.

**Why it happens:** The LLM groups all "Salesforce Industries" process design into a single category and applies a single tool recommendation, not knowing that the process runtime differs materially per vertical: Insurance uses OmniScript on Claims Management framework; Communications Cloud uses declarative IOM decomposition rules (not OmniScript as the primary process engine); E&U uses service order records with CIS callouts.

**Correct pattern:**

```
Insurance Cloud: Process runtime = Claims Management OmniScript framework (FSC)
  Tool: OmniStudio OmniScript designer
  Primary mechanism: OmniScript step customization + Claims Management Remote Actions

Communications Cloud: Process runtime = Industries Order Management decomposition engine
  Tool: IOM decomposition rule configuration (declarative, not OmniScript)
  Primary mechanism: Decomposition rules reading EPC child item relationships

Energy & Utilities Cloud: Process runtime = Service order records + CIS callout automation
  Tool: E&U service order configuration + OmniScript for capture UI (if licensed)
  Primary mechanism: Service order type configuration + CIS API callout mapping
```

**Detection hint:** Any response that recommends OmniScript as the primary mechanism for Communications Cloud order decomposition (rather than IOM decomposition rules) is applying the Insurance/E&U pattern to the wrong vertical. Also flag responses that apply IOM decomposition rules to Insurance claims processes.

---

## Anti-Pattern 6: Assuming Prebuilt Industry OmniScripts Must Be Rebuilt for Customization

**What the LLM generates:** Instructions to create a brand-new OmniScript from scratch for FNOL intake, with all steps, data sources, and actions defined by the implementer, because the requirement includes custom fields or branching not visible in the prebuilt OmniScript.

**Why it happens:** LLMs default to create-from-scratch recommendations when customization details are given. They do not know that the Insurance Cloud prebuilt FNOL OmniScript is a supported asset with Claims Management integrations pre-wired, and that those integrations are lost if the OmniScript is rebuilt rather than extended.

**Correct pattern:**

```
1. Locate the prebuilt FNOL OmniScript in OmniStudio.
2. For managed-package DIP orgs: work within the extension points
   (add Steps or element groups to the existing OmniScript, do not clone).
3. For native-core DIP orgs: the OmniScript is in the org namespace
   and can be modified directly.
4. Custom fields → add Block elements within the correct Step.
5. Branching → add Conditional View on Block containers.
6. Custom data writes → add or modify DataRaptor Transform Post-Step actions.
7. Rebuild from scratch only when the prebuilt OmniScript is genuinely
   incompatible with the business process and the architect has signed off
   on losing upgrade compatibility.
```

**Detection hint:** A response that says "create a new OmniScript with the following steps" for an Insurance claims intake scenario without first asking whether a prebuilt Claims Management OmniScript exists in the org is applying the wrong approach. Look for absence of "prebuilt", "existing OmniScript", or "Claims Management framework" in the response.
