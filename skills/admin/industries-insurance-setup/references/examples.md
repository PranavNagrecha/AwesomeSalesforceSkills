# Examples — Industries Insurance Setup

## Example 1: Enabling Insurance Settings and Configuring the Participant Model for a Personal Lines Carrier

**Context:** A regional auto and homeowners insurance carrier is implementing FSC Insurance for the first time. The carrier has multiple agents (producers) who can co-own policies and needs named insureds to be linked at the individual level, not just the household account. The implementation team has FSC provisioned but has not yet enabled Insurance Settings.

**Problem:** Without planning the participant model before touching Insurance Settings, the team risks enabling irreversible settings in the wrong combination — or failing to enable them when they are needed, requiring a full org reset. A common mistake is enabling the org without many-to-many policy relationships and then discovering mid-project that the data model cannot support co-named insureds.

**Solution:**

Before opening Insurance Settings, document the participant model decision:

```
Participant model decision (document before enabling):
- Named insureds: multiple per policy (husband + wife on an auto policy) → requires many-to-many
- Producers: single producer per policy (dedicated agent) → multiple producers NOT needed
- Decision: enable many-to-many policy relationships; do NOT enable multiple producers per policy

Steps:
1. Setup > Insurance Settings
2. Enable "Many-to-Many Policy Relationships" → Save (irreversible)
3. Do NOT enable "Multiple Producers Per Policy" (not needed; avoid unnecessary irreversible changes)
4. Assign FSC Insurance PSL to implementation users
5. Create InsurancePolicyParticipant records with Role = Named Insured for each policy member
```

With many-to-many enabled, the `InsurancePolicyParticipant` object becomes the authoritative junction between `InsurancePolicy` and `Account`/`Contact`. Each named insured gets a separate participant record with `Role = Named Insured`.

**Why it works:** The decision is documented before any configuration is touched. Irreversible settings are treated as architectural decisions, not admin toggles. The participant model drives field-level security, page layout, and downstream quoting context — getting it right at the start avoids data migration later.

---

## Example 2: Building an OmniScript Quoting Flow with InsProductService and Policy Issuance

**Context:** A commercial lines insurer needs a guided quoting experience for agents: the agent enters building details and coverage requirements into a multi-step form, the system rates available products, the agent selects a product, and the system issues the policy automatically. OmniStudio is licensed and the org is on the native-core Digital Insurance Platform path.

**Problem:** Without using the industry-specific quoting APIs, teams attempt to build quoting using standard CPQ Pricebooks, custom Apex + REST calls, or generic OmniScript HTTP Actions to external endpoints. These approaches bypass the Insurance Product Administration rating engine, cannot return properly rated products, and produce policies without correct InsurancePolicyCoverage child records.

**Solution:**

OmniScript quoting flow structure (native-core path):

```
OmniScript: CommercialLinesQuote
├── Step 1: AccountSearch — DataRaptor to resolve insured Account
├── Step 2: BuildingDetails — text inputs for address, construction type, year built, square footage
├── Step 3: CoverageInputs — inputs for desired coverage limits
├── Step 4: RateProducts (Remote Action element)
│     Class: InsProductService
│     Method: getRatedProducts
│     Input map: { accountId, effectiveDate, coverageInputs }
│     Output stored in: ratedProductsResult
├── Step 5: ProductSelection (LWC element)
│     Component: insOsGridProductSelection
│     Bound to: ratedProductsResult
│     Output: selectedProduct
└── Step 6: IssuePolicy (Integration Procedure or HTTP Action)
      Endpoint: POST /services/data/v62.0/connect/insurance/policy-administration/policies
      Payload: { accountId, productId, effectiveDate, coverageInputs, selectedProduct }
```

After the POST succeeds, the response contains the new `InsurancePolicy` record ID. The OmniScript can redirect to the policy record or trigger a follow-up confirmation step.

**Why it works:** `InsProductService.getRatedProducts` is the platform-native rating bridge — it handles the insurance product catalog, pricing rules, and rating context that no external call can replicate. The Connect API issue-policy endpoint atomically creates `InsurancePolicy` + `InsurancePolicyCoverage` records, ensuring referential integrity that manual DML cannot guarantee.

---

## Anti-Pattern: Using Standard CPQ Quote Object for Insurance Quoting

**What practitioners do:** Teams familiar with Salesforce CPQ configure standard `Quote`, `QuoteLineItem`, and `Pricebook2` objects for insurance product selection and pricing, then attempt to convert the resulting Quote to an InsurancePolicy via a custom Apex trigger.

**What goes wrong:** The standard CPQ data model has no awareness of insurance coverage types, policy participants, or rating engine context. The `InsProductService.getRatedProducts` method cannot be driven from CPQ line items. The resulting "policy" created via Apex DML lacks the `InsurancePolicyCoverage` records, `InsurancePolicyParticipant` records, and policy clause records that the rest of the Insurance platform expects. Downstream features — renewals, endorsements, Connect API billing integration — all break because they depend on the native insurance object graph, not a converted CPQ quote.

**Correct approach:** Use OmniScript with InsProductService Remote Action for quoting, and use the Insurance Policy Administration Connect API for issuance. If CPQ is already in the org for non-insurance products, maintain a clean separation: CPQ for non-insurance lines, Insurance Platform APIs for insurance lines.
