# LLM Anti-Patterns — Manufacturing Cloud Setup

Common mistakes AI coding assistants make when generating or advising on Manufacturing Cloud Setup.
These patterns help the consuming agent self-check its own output.

## Pattern 1: Modeling Multi-Period Demand as Opportunity + Custom Term Field

**What the LLM generates:** An Opportunity with a custom `Term__c` field and child OpportunityLineItems for each period of the commitment.

**Why it happens:** Sales-Cloud-trained LLMs default to Opportunity for any sale-related concept. `SalesAgreement` is under-represented in pretrained material.

**Correct pattern:** When the org has Manufacturing Cloud licensed and the use case is multi-period planned demand, use `SalesAgreement` + `SalesAgreementProduct` + `SalesAgreementProductSchedule`.

**Detection hint:** Any answer that builds Opportunity-with-Term__c without first asking "do you have Manufacturing Cloud licensed?" is suspect. Also flag custom `Sales_Agreement__c` objects when standard `SalesAgreement` is available.

---

## Pattern 2: Building Custom Apex Rebate Calculation Without Considering Native

**What the LLM generates:** Apex batch class that scans Orders, applies tier logic, and writes custom `Rebate_Payout__c` records.

**Why it happens:** Rebate calculation is a familiar batch-processing pattern; LLMs reach for the bespoke implementation rather than asking about native engine availability.

**Correct pattern:** Use `RebateProgram` + `RebateProgramMember` + `ProgramRebatePayout` with the **Rebate Payout Calculation** DPE definition. Only build custom Apex if marginal-tier semantics or other native-unsupported behavior is genuinely required.

**Detection hint:** Any Apex batch class with name containing "Rebate" alongside Custom `Rebate_Payout__c` objects is suspect. Verify whether native Rebate Management can handle the calculation first.

---

## Pattern 3: Forgetting to Activate ABF Recalc DPE

**What the LLM generates:** A go-live checklist that covers `SalesAgreement` configuration but omits the ABF DPE activation step.

**Why it happens:** DPE activation is a Setup-UI step, not a metadata file, so it doesn't appear in code-centric LLM training material.

**Correct pattern:** Every Manufacturing Cloud go-live checklist must explicitly include "Activate Account-Based Forecasting recalc DPE definition" and "Schedule the recalc job (typical: nightly)" and "Run once manually to backfill."

**Detection hint:** Any Manufacturing Cloud rollout plan or runbook that lacks an explicit DPE activation step will produce empty `AccountProductForecast` data on day one.

---

## Pattern 4: Auto-Populating `OrderItem.SalesAgreementId` Assumption

**What the LLM generates:** Code or documentation that assumes the `SalesAgreementId` lookup on OrderItem is automatically populated when an order is placed against an account with an active agreement.

**Why it happens:** Salesforce has many auto-populated lookups (CurrencyIsoCode, OwnerId fallbacks); LLMs over-generalize this pattern.

**Correct pattern:** `OrderItem.SalesAgreementId` requires explicit population in the Order ingest path. Add the lookup-and-set logic to the Apex / Flow that creates the OrderItem.

**Detection hint:** Documentation that says "actuals automatically reconcile to the agreement" without explaining the OrderItem lookup population is suspect.

---

## Pattern 5: Recommending Channel Revenue Management for Direct-to-Customer Rebates

**What the LLM generates:** "To set up rebates, enable Channel Revenue Management and configure ChannelProgram..."

**Why it happens:** LLMs conflate Channel Revenue Management (sell-in / sell-through tracking) with Rebate Management (rebate calculation). They are separate modules.

**Correct pattern:** For direct-customer rebates, base Manufacturing Cloud Rebate Management is sufficient. CRM module is required only for true two-step distribution (OEM → distributor → consumer) with partner inventory tracking.

**Detection hint:** Any rebate-program guidance that recommends enabling CRM without first confirming the OEM has a two-step distribution model is over-prescribing complexity.
