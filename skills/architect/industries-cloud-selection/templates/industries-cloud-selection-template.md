# Industries Cloud Selection — Decision Framework Template

Use this template to document and justify a Salesforce Industries vertical cloud selection decision. Complete all sections before finalizing a recommendation.

---

## Engagement Context

**Customer name / project:** (fill in)

**Industry:** (fill in — e.g., Telecommunications, Insurance, Energy/Utilities, Healthcare, Financial Services, Public Sector)

**Request summary:** (describe what the customer needs to accomplish — one paragraph)

**Org type:** [ ] New Salesforce org   [ ] Existing org adding Industries license   [ ] Existing Industries org expanding scope

**OmniStudio deployment model:** [ ] Platform-native (new org, Spring '26+)   [ ] Managed package (existing org)   [ ] Unknown — must confirm before development begins

---

## Step 1: Required Business Entities

List every business entity the solution must model. For each, identify the nearest Salesforce standard object and the Industries license required.

| Business Entity | Nearest Standard Object | Vertical Cloud License Required | Available Without License? |
|---|---|---|---|
| (e.g., Insurance Policy) | InsurancePolicy | Insurance Cloud + FSC | No |
| (fill in) | (fill in) | (fill in) | No |
| (fill in) | (fill in) | (fill in) | No |
| (fill in — custom extension) | Custom Object (suffix `__c`) | N/A — no license required | Yes |

**Objects requiring custom extension (no standard object available):**
- (list any entities not covered by any vertical cloud standard object)

---

## Step 2: License Dependency Map

List all licenses required, including base license dependencies.

| License | Required For | Base Dependency | Confirmed in Scope? |
|---|---|---|---|
| (e.g., Insurance Cloud) | InsurancePolicy, InsurancePolicyCoverage | FSC (required) | [ ] Yes [ ] No [ ] TBC |
| (e.g., Financial Services Cloud) | FSC base layer for Insurance Cloud | None | [ ] Yes [ ] No [ ] TBC |
| (fill in) | (fill in) | (fill in) | [ ] Yes [ ] No [ ] TBC |

**Total licenses required:** (number)

**All licenses confirmed on order form:** [ ] Yes   [ ] No — outstanding: (list which)

---

## Step 3: OmniStudio Assessment

**Org OmniStudio model confirmed:** [ ] Platform-native   [ ] Managed package   [ ] Not yet confirmed

If managed package:
- [ ] Existing managed-package components identified and documented before any migration begins
- [ ] One-way migration risk communicated to stakeholders: opening a component in the Standard Designer is irreversible — it cannot be returned to the managed-package designer
- [ ] Migration plan approved before any component is opened in the Standard Designer
- [ ] No managed-package components opened in production as a "test"

---

## Step 4: Customization vs Configuration Analysis

For each key business process, assess whether pre-built vertical cloud components cover the requirement or custom development is needed.

| Business Process | Pre-Built Coverage | Custom Development Required | Notes |
|---|---|---|---|
| (e.g., Policy enrollment) | OmniScript template in Insurance Cloud | Minor field additions | Extend standard OmniScript |
| (e.g., Billing system sync) | Integration Procedure pattern in E&U | Custom Integration Procedure | Source of truth: CIS billing system |
| (fill in) | (fill in) | (fill in) | (fill in) |

**Estimated custom development percentage:** (fill in — what % of the solution is custom vs pre-built configuration)

---

## Step 5: Greenfield vs Retrofit Risk (for existing orgs only)

Skip this section for new orgs.

| Risk Area | Finding | Mitigation |
|---|---|---|
| Custom objects that duplicate standard vertical objects | (e.g., Policy__c conflicts with InsurancePolicy) | Data migration plan required |
| Existing OmniStudio components in managed-package model | (e.g., 12 OmniScripts, 8 FlexCards) | Migration plan before any Standard Designer opens |
| Other custom code referencing objects being replaced | (fill in) | (fill in) |

---

## Step 6: Recommendation

**Recommended vertical cloud(s):**
- Primary: (fill in — e.g., Insurance Cloud)
- Required base: (fill in — e.g., Financial Services Cloud)
- Additional: (fill in if multi-vertical)

**Recommendation rationale:**
(2–4 sentences explaining why this selection is correct based on the required standard objects, license dependencies, and customization scope. Reference the object mapping table in Step 1.)

**What this selection does NOT cover:**
(List capabilities the selected vertical cloud does not provide — be explicit about gaps so the customer understands what they are accepting.)

---

## Step 7: Open Questions

Items that must be resolved before the recommendation is finalized:

| # | Question | Owner | Target Date |
|---|---|---|---|
| 1 | (e.g., Is Insurance Cloud + FSC budget approved?) | (fill in) | (fill in) |
| 2 | (e.g., Which sandbox environments will hold Industries licenses?) | (fill in) | (fill in) |
| 3 | (e.g., Is Hyperforce provisioning required?) | (fill in) | (fill in) |
| (add rows as needed) | | | |

---

## Checklist — Before Finalizing Recommendation

- [ ] All required standard objects mapped to their vertical cloud license
- [ ] License dependencies confirmed (e.g., Insurance Cloud requires FSC)
- [ ] All required licenses confirmed as line items on the order form
- [ ] OmniStudio deployment model confirmed (platform-native or managed package)
- [ ] One-way Standard Designer migration risk documented if managed-package components exist
- [ ] Customization vs configuration scope assessed for key processes
- [ ] Existing org custom object conflicts identified (retrofit scenarios)
- [ ] Capability gaps for the selected configuration documented
- [ ] Open questions log is complete with owners and dates
- [ ] Multi-vertical licensing confirmed as separate line items if applicable

---

## Notes and Deviations

(Record any deviations from the standard selection process, unusual constraints, or customer-specific considerations that influenced the recommendation.)
