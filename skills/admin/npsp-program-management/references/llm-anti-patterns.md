# LLM Anti-Patterns — NPSP Program Management Module (PMM)

Common mistakes AI coding assistants make when generating or advising on NPSP PMM configuration. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Conflating PMM with NPSP Case Management

**What the LLM generates:** Instructions to create Case records, Case Teams, or CaseComment records to track client service delivery. The LLM may also suggest enabling Salesforce Service Cloud features (Omni-Channel routing, entitlements) for "program case management."

**Why it happens:** LLMs associate "nonprofit program management" with social services case management, which is a Service Cloud pattern. NPSP does not ship a case management module, and PMM is not a case management tool — it is a program delivery and attendance tracking tool. Training data conflates these domains.

**Correct pattern:**
```
Use PMM's dedicated objects:
- ProgramEngagement__c for client enrollment (not Case)
- ServiceDelivery__c for recording services delivered (not CaseComment)
- ServiceSchedule__c / ServiceParticipant__c for scheduled sessions (not Case Team)
```

**Detection hint:** Look for any mention of "Case" objects, "Entitlement," "Milestone," or "Omni-Channel" in a PMM context. These are Service Cloud constructs and do not belong in a PMM implementation.

---

## Anti-Pattern 2: Assuming ServiceDelivery__c Data Rolls Up into NPSP Giving Reports

**What the LLM generates:** SOQL queries joining ServiceDelivery__c to Opportunity, or instructions to add ServiceDelivery__c as a related list on the NPSP Opportunity page layout for "program impact reporting." May also suggest formula fields on npe01__OppPayment__c that reference pmdm__ServiceDelivery__c.

**Why it happens:** LLMs pattern-match "nonprofit program data + Salesforce" to NPSP Opportunity as the central object, and assume all program-related records roll up through it. PMM is a separate managed package with its own object graph that has no Opportunity relationship.

**Correct pattern:**
```
PMM reporting uses ServiceDelivery__c as the primary fact object.
Build reports from:
  - Report type: Service Deliveries with Program Engagements
  - Group by: pmdm__Program__c, pmdm__Service__c, pmdm__ProgramCohort__c
Do NOT attempt to join ServiceDelivery__c to Opportunity in SOQL or reports.
Cross-package joins are unsupported and will break on package upgrades.
```

**Detection hint:** Any SOQL with both `pmdm__ServiceDelivery__c` and `Opportunity` in the same query, or any formula referencing NPSP rollup fields (npo02__TotalOppAmount__c) from a PMM object.

---

## Anti-Pattern 3: Treating Field-Set Required Flag as Validation Enforcement

**What the LLM generates:** Instructions telling admins to "check the Required box" in the Bulk_Service_Deliveries_Fields field set to make a field mandatory. The LLM may also suggest this as a substitute for writing validation rules.

**Why it happens:** In standard Salesforce page layouts, marking a field Required on the layout does enforce the save validation. LLMs generalize this behavior to field sets, which have a similar UI but a fundamentally different execution model — field sets are metadata structures consumed by Lightning components, not by the platform's validation pipeline.

**Correct pattern:**
```
For required-field enforcement in Bulk Service Delivery:
1. Add the field to the field set (for UI visibility)
2. Check Required in the field set (for the visual asterisk only)
3. Create a Validation Rule on ServiceDelivery__c:
   Name: PMM_Require_<FieldName>
   Condition: ISBLANK(pmdm__<FieldAPIName>__c)
   Error: "<FieldName> is required for service delivery records."
```

**Detection hint:** Any advice that stops at "mark the field required in the field set" without mentioning a validation rule. Search the response for "validation rule" — if it is absent when discussing PMM required fields, the guidance is incomplete.

---

## Anti-Pattern 4: Referencing PMM Objects Without the pmdm__ Namespace

**What the LLM generates:** SOQL, Apex, or Flow configuration referencing PMM objects without the namespace prefix, e.g., `SELECT Id FROM ServiceDelivery__c` or `ServiceDelivery__c.Quantity__c` in a formula.

**Why it happens:** LLMs are trained on Salesforce documentation and community content that sometimes omits namespace prefixes for readability. In sandbox or developer edition orgs used for training examples, the namespace may not be installed. The LLM reproduces namespace-free references that fail in a real PMM org.

**Correct pattern:**
```sql
-- Correct SOQL for PMM:
SELECT Id, pmdm__Quantity__c, pmdm__DeliveryDate__c,
       pmdm__ProgramEngagement__c, pmdm__Service__c
FROM pmdm__ServiceDelivery__c
WHERE pmdm__ProgramEngagement__r.pmdm__Program__c = :programId

-- Correct object API name: pmdm__ServiceDelivery__c
-- Correct field API names: pmdm__Quantity__c, pmdm__DeliveryDate__c
-- NOT: ServiceDelivery__c, Quantity__c
```

**Detection hint:** Any SOQL or Apex using `ServiceDelivery__c`, `ProgramEngagement__c`, `ServiceSchedule__c`, or `Program__c` without the `pmdm__` prefix in a PMM context.

---

## Anti-Pattern 5: Suggesting NPSP Triggers or Rollup Helper as the Solution for PMM Aggregation

**What the LLM generates:** Instructions to use NPSP's Rollup Helper feature, configure NPSP Customizable Rollups, or write Apex triggers leveraging the NPSP trigger framework to aggregate ServiceDelivery__c quantities onto parent Contact or Account records.

**Why it happens:** LLMs know that NPSP has an extensible rollup and trigger infrastructure (Customizable Rollups, the TDTM trigger framework) and assume it covers all custom objects in the NPSP ecosystem. PMM objects are in a separate namespace and are not registered in the NPSP TDTM trigger catalog or Customizable Rollups configuration.

**Correct pattern:**
```
For aggregating PMM data onto parent records:
Option A: Use Salesforce standard Roll-Up Summary fields — only if ServiceDelivery__c
          has a master-detail to the target object (it does not by default).
Option B: Use a custom Apex trigger on pmdm__ServiceDelivery__c — write this as a
          standalone trigger, NOT using NPSP's TDTM framework.
Option C: Use a scheduled Flow or scheduled Apex that queries ServiceDelivery__c
          and updates a custom field on Program__c or Contact.
Do NOT reference npsp__ trigger handlers or NPSP Customizable Rollups for PMM objects.
```

**Detection hint:** Any mention of "TDTM," "NPSP Customizable Rollups," "Rollup Helper," or "npsp__" namespace trigger classes in the context of PMM ServiceDelivery__c aggregation.
