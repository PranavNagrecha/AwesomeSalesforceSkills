# Examples — Industries Cloud Selection

## Example 1: Insurance Carrier Selecting the Wrong Cloud

**Context:** A property and casualty insurance carrier wants to modernize its policy administration system on Salesforce. The SI proposes Financial Services Cloud (FSC) because the customer is in "financial services." The proposal budget includes only FSC licenses.

**Problem:** The carrier's core data model requires `InsurancePolicy`, `InsurancePolicyCoverage`, and `InsurancePolicyParticipant` — objects that exist only in Insurance Cloud. FSC provides financial account, household, and relationship group objects but does not include insurance policy lifecycle objects. The SI discovers this mid-build when SOQL against `InsurancePolicy` fails with an "object not found" error in the FSC-licensed sandbox. Recovering requires re-licensing (Insurance Cloud + FSC base), re-scoping the data model, and rebuilding components already developed against FSC-only objects.

**Solution:**

```
Step 1 — Object-first selection:
  Required objects: InsurancePolicy, InsurancePolicyCoverage, InsurancePolicyParticipant
  Map to vertical cloud: Insurance Cloud (requires FSC base)

Step 2 — License dependency check:
  Insurance Cloud requires FSC as base layer
  Budget must include: FSC license + Insurance Cloud license (both required)

Step 3 — Validate in sandbox:
  Provision sandbox with correct license set before any development begins
  Confirm SOQL: SELECT Id, PolicyName FROM InsurancePolicy LIMIT 1
  Expected result: empty result set (not an error) confirms objects exist
```

**Why it works:** Identifying required standard objects before evaluating vertical cloud names prevents the FSC-only trap. The object landscape drives the license decision — not the customer's industry category. Confirming object availability in a licensed sandbox before any development starts eliminates the mid-build discovery failure mode.

---

## Example 2: Telecom Operator Evaluating Communications Cloud vs Custom Solution

**Context:** A regional telecommunications operator processes tens of thousands of multi-product orders per month — each order may contain mobile voice, broadband, and equipment items that must be decomposed into separate fulfillment work orders and sent to distinct downstream systems. An architect must recommend whether Communications Cloud or a custom Apex-based order management solution is more appropriate.

**Problem:** Without Communications Cloud, the customer would need to build custom objects to represent the product catalog hierarchy (`EnterpriseProduct`, `ProductCatalog`, `ProductSellingModel`) and custom Apex to handle TM Forum-aligned order decomposition. This is a large, complex build. The architect needs to assess whether the Communications Cloud license investment is justified.

**Solution:**

```
Decision framework applied:

Requirement: TM Forum-aligned order decomposition
  → Provided by: Communications Cloud (BillingAccount, EnterpriseProduct, OrderItem decomposition)
  → Custom alternative: 6-12 months of custom Apex; ongoing maintenance burden

Requirement: Multi-level billing account hierarchy (corporate → site → service)
  → Provided by: BillingAccount hierarchy in Communications Cloud
  → Custom alternative: Custom object hierarchy; no native platform behaviors

Requirement: Enterprise Product Catalog with pricing rules
  → Provided by: Enterprise Product Catalog (EPC) in Communications Cloud
  → Custom alternative: Custom product catalog; no native OmniStudio integration

Verdict: Communications Cloud license cost is justified. The pre-built TM Forum 
data model and EPC eliminate 12-18 months of custom development and reduce 
ongoing maintenance burden significantly.
```

**Why it works:** Expressing each business requirement as a data model and platform capability need — rather than a feature checklist comparison — makes the license value case concrete. When Communications Cloud standard objects cover the majority of the required data model, the build-vs-buy analysis favors the license.

---

## Example 3: Energy Utility Greenfield Selection

**Context:** An energy utility is building a new customer information system (CIS) replacement on Salesforce to manage residential and commercial service points, meter reads, and rate plans. They are evaluating whether Energy & Utilities Cloud is required or whether standard Salesforce with custom objects would suffice.

**Problem:** The utility's CIS currently manages `ServicePoint` records (the physical meter location), `UtilityAccount` (the customer billing account), and `RatePlan` (the pricing tier assigned to each service point, sourced from the CIS billing system). Without E&U Cloud, all three entities would need to be implemented as custom objects with no native integration patterns for CIS system sync.

**Solution:**

```
Required objects identified:
  ServicePoint      → E&U Cloud standard object (license required)
  UtilityAccount    → E&U Cloud standard object (license required)
  RatePlan          → E&U Cloud standard object with CIS-authoritative sync pattern

OmniStudio deployment model:
  New org on Spring '26+ = platform-native OmniStudio
  No managed package required
  Components deployable via Metadata API

Customization scope:
  Pre-built: ServicePoint 360 view (FlexCard), service order OmniScript templates
  Custom: Integration Procedures to sync RatePlan from legacy CIS billing system
  Note: RatePlan data is CIS-authoritative; E&U Cloud provides the object 
  and integration hooks but the billing system remains the source of truth

License: Energy & Utilities Cloud (no base license dependency — standalone)
```

**Why it works:** E&U Cloud's `ServicePoint` and `RatePlan` standard objects come with pre-built OmniStudio components and integration patterns for CIS sync. Implementing these as custom objects would reproduce the platform behavior without any of the standard integration hooks — the equivalent of building a worse version at higher cost.

---

## Anti-Pattern: Selecting a Vertical Cloud by Industry Name Alone

**What practitioners do:** A team at a bank recommends Financial Services Cloud because the customer is "a bank." They build an FSC implementation. Midway through, the customer clarifies their primary use case is managing motor vehicle insurance policies written through a bank-owned insurance subsidiary. The required objects — `InsurancePolicy`, `InsurancePolicyCoverage` — do not exist in their FSC-licensed org.

**What goes wrong:** FSC provides financial account, household, and relationship group objects. It does not include insurance policy lifecycle objects. The bank's insurance subsidiary needs Insurance Cloud (built on top of FSC). The team discovers this when attempting to access insurance-specific objects and receives SOQL errors. Re-licensing, re-scoping, and renegotiating the implementation contract are required — a costly and avoidable outcome.

**Correct approach:** Start with the required standard objects, not the industry label. If the solution requires `InsurancePolicy`, the answer is Insurance Cloud (+ FSC). If the solution requires `FinancialAccount` and `FinancialHolding` without policy management, FSC alone is sufficient. The object-first approach eliminates the industry-name trap entirely.
