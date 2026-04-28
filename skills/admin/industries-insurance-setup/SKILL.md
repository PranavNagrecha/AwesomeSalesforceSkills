---
name: industries-insurance-setup
description: "Use this skill to configure Salesforce Industries Insurance (Financial Services Cloud Insurance) including permission set licenses, irreversible org settings, core insurance objects, coverage types, claim configuration, and OmniScript-based quoting using the Insurance Product Administration API. Trigger keywords: insurance setup, FSC Insurance, InsurancePolicy object, InsurancePolicyCoverage, policy quoting OmniScript, claim type configuration, InsProductService, Digital Insurance Platform, many-to-many policy, multiple producers. NOT for generic OmniStudio setup, standard CPQ/Pricebook quoting, Health Cloud enrollment, or general FSC configuration unrelated to insurance line-of-business."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
triggers:
  - "how do I enable insurance for Financial Services Cloud and set up InsurancePolicy records"
  - "configuring OmniScript quoting with InsProductService getRatedProducts for insurance products"
  - "setting up claim types and coverage configuration in FSC Insurance org"
  - "how to issue a policy using the Connect API insurance policy administration endpoint"
  - "enabling many-to-many policy relationships or multiple producers per policy in insurance settings"
tags:
  - insurance
  - fsc
  - industries
  - omnistudio
  - policy-administration
  - claims
  - quoting
  - connect-api
  - digital-insurance-platform
inputs:
  - "Org edition and license type (FSC Insurance permission set license required, distinct from standard FSC)"
  - "Line of business: personal lines (auto, home), commercial, life/annuity"
  - "Whether managed-package or native-core Digital Insurance Platform path is in use"
  - "OmniStudio license availability (required for quoting OmniScripts)"
  - "List of coverage types, claim types, and product definitions needed"
  - "Whether many-to-many policy relationships or multiple producers per policy are required"
outputs:
  - "Enabled insurance org settings with correct irreversible flags documented"
  - "InsurancePolicy, InsurancePolicyCoverage, Claim, and CoverageType object configuration"
  - "OmniScript quoting flow using InsProductService:getRatedProducts Remote Action"
  - "Issue Policy flow using Connect API POST /connect/insurance/policy-administration/policies"
  - "Insurance permission set license assignment and profile configuration"
  - "Claim type setup with associated coverage and participant records"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# Industries Insurance Setup

This skill activates when configuring the Salesforce Industries Insurance (FSC Insurance) product — covering the FSC Insurance permission set license, org-level insurance settings, core insurance objects, OmniScript-based quoting via the Insurance Product Administration API, and policy issuance via the Insurance Connect API. Use this skill before any hands-on configuration work on an insurance-enabled org.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the org has the **FSC Insurance permission set license** assigned — this is a separate license from the base FSC license and must be provisioned by Salesforce before any insurance objects or settings appear.
- Identify whether the org uses the **managed-package Digital Insurance Platform** or the **native-core path** (Salesforce is migrating managed package to core, targeting October 2025). Configuration steps differ between paths.
- Determine whether **many-to-many policy relationships** or **multiple producers per policy** are required — these are irreversible org settings in Insurance Settings and cannot be undone once enabled.
- Confirm OmniStudio is licensed if OmniScript-based quoting is in scope — the quoting journey requires OmniStudio runtime.
- Understand the lines of business being configured: personal lines (auto/homeowners), commercial, life/annuity, or specialty — each has different coverage type structures.

---

## Core Concepts

### FSC Insurance Permission Set License and Org Settings

Insurance for Financial Services Cloud requires an explicit **FSC Insurance permission set license** (also called the Industries Insurance Add-On), separate from the core FSC license. After license provisioning, an admin must navigate to **Setup > Insurance Settings** to enable the feature. Several settings in this panel are **permanently irreversible** once saved:

- **Enable many-to-many policy relationships** — allows a policy to be associated with multiple named insureds or accounts via InsurancePolicyParticipant junction records. Once enabled, the underlying data model changes cannot be reversed.
- **Enable multiple producers per policy** — allows multiple InsurancePolicyParticipant records of type Producer on a single policy. Irreversible.

Enabling these settings without understanding the downstream data model implications is a common and costly mistake. Plan the participant model before touching Insurance Settings.

### Core Insurance Objects

The insurance data model centers on these standard objects:

| Object | Role |
|---|---|
| InsurancePolicy | The master policy record. Linked to Account via NameInsuredId. Supports policy number, effective/expiration dates, status, and line-of-business picklist. |
| InsurancePolicyCoverage | Child of InsurancePolicy. Represents a single coverage line (e.g., collision, liability). Linked to CoverageType. |
| CoverageType | Lookup object defining the type of coverage, used across policies and claims. |
| Claim | Represents an insurance claim. Linked to InsurancePolicy. Has ClaimType picklist and supports ClaimParticipant child records. |
| InsurancePolicyParticipant | Junction between InsurancePolicy and Account/Contact. Role picklist controls named insured, producer, driver, beneficiary, and others. |
| InsurancePolicyProductClause | Stores product clause details attached to a policy, used in clause-driven commercial policies. |

These are platform-native standard objects introduced with FSC Insurance. They are not custom objects and cannot be replaced with generic custom schema.

### Insurance Quoting via OmniScript and Connect API

The quoting journey uses OmniStudio OmniScripts with **Remote Action elements** calling the `InsProductService` Apex service class. The key method is `InsProductService.getRatedProducts()`, which returns rated product options for a given quoting context (coverage inputs, account, effective date). The prebuilt LWC component `insOsGridProductSelection` renders the product selection UI inside an OmniScript step.

After the customer selects a product and the quote is finalized, policy issuance uses the **Insurance Policy Administration Connect API**:

```
POST /services/data/vXX.0/connect/insurance/policy-administration/policies
```

This endpoint creates the InsurancePolicy record and associated coverage records atomically. It is a dedicated insurance endpoint — standard Salesforce DML or generic REST object creation is not a substitute.

The Digital Insurance Platform (DIP) is in mid-transition from a managed package to native Salesforce core (target October 2025). On managed-package orgs, OmniScript components and the InsProductService namespace may differ from native-core orgs. Always confirm which path the org is on before configuring quoting flows.

---

## Common Patterns

### Pattern: Quoting OmniScript with Remote Action Rating

**When to use:** When an org needs a guided quoting experience for agents or customers, using rated insurance products from the backend rating engine.

**How it works:**
1. Create an OmniScript with data-gathering steps (coverage inputs, vehicle/property details, applicant info).
2. Add a Remote Action element pointing to `InsProductService.getRatedProducts`. Pass coverage inputs as the action input map.
3. Add an OmniScript step using the `insOsGridProductSelection` LWC component to display returned rated products.
4. On product selection, store the selected product context in OmniScript state.
5. Add a final Integration Procedure or Remote Action step to POST to the Insurance Policy Administration Connect API to issue the policy.

**Why not generic OmniStudio flows:** Standard OmniScript HTTP Actions to generic REST endpoints do not carry the insurance context required by the rating engine. The `InsProductService` Remote Action handles authentication, context assembly, and rating engine routing internally.

### Pattern: Claim Setup with Coverage Linking

**When to use:** When setting up initial claim intake for a new line of business.

**How it works:**
1. Define CoverageType records for each coverage line the org supports (e.g., Bodily Injury, Property Damage, Comprehensive).
2. Create ClaimType picklist values in the Claim object matching the lines of business.
3. Configure InsurancePolicyCoverage records on policy templates or via automation to link CoverageType to each policy.
4. Build Claim intake OmniScripts or Screen Flows that query InsurancePolicyCoverage records to drive which coverages are claimable.
5. Use InsurancePolicyParticipant records to associate claimants (role = Claimant) with the policy during claim creation.

**Why not generic Case:** The Claim object carries insurance-specific fields (ClaimType, InsurancePolicy lookup, coverage association) and is the target of downstream insurance analytics and regulatory reporting. Routing claim intake through Case loses this context.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Org needs multiple named insureds on one policy | Enable many-to-many policy relationships in Insurance Settings before creating any policies | Irreversible setting; must be decided before go-live |
| Quoting for personal lines with standard products | Use InsProductService.getRatedProducts via OmniScript Remote Action + insOsGridProductSelection LWC | Industry-standard quoting path; other approaches bypass rating engine |
| Org is on managed-package Digital Insurance Platform | Follow managed-package setup guides; namespace prefixes on OmniScript components differ from native core | Mid-transition; native core path is not yet fully GA for all features |
| Need to issue a policy after quote acceptance | Use POST /connect/insurance/policy-administration/policies Connect API | Atomic creation of policy + coverages; DML-only approach misses coverage linking |
| Claim intake required for multiple coverage types | Configure CoverageType records and link via InsurancePolicyCoverage; drive claim form from these records | Preserves regulatory-grade claim-to-coverage traceability |
| Multiple producers or agents on one policy | Enable multiple producers per policy in Insurance Settings (irreversible) | Required for producer commission splits and multi-agent book of business |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Verify licensing and org readiness** — Confirm the FSC Insurance permission set license is provisioned. Assign the license to relevant users. Verify OmniStudio is licensed if quoting OmniScripts are in scope. Navigate to Setup > Insurance Settings to confirm the Insurance Settings panel is visible.

2. **Plan and enable irreversible org settings** — Decide before any configuration whether many-to-many policy relationships and/or multiple producers per policy are needed. Document the decision. Enable required settings in Insurance Settings. Record which settings were enabled and when — these cannot be reversed.

3. **Configure CoverageType and Claim object** — Create CoverageType records for each coverage line. Add or verify ClaimType picklist values on the Claim object. Define any custom fields needed for the line of business. Ensure field-level security is set on the FSC Insurance permission set.

4. **Set up InsurancePolicy and participant model** — Create any policy templates or seed data needed for the line of business. Configure the InsurancePolicyParticipant role picklist to include Named Insured, Producer, Driver, Claimant, or Beneficiary as needed. Verify page layouts on InsurancePolicy, InsurancePolicyCoverage, and Claim show relevant fields.

5. **Build OmniScript quoting flow** — Scaffold the quoting OmniScript. Add Remote Action elements for InsProductService.getRatedProducts. Embed the insOsGridProductSelection LWC for product selection. Wire OmniScript state to the Connect API issue policy call. Test with representative coverage inputs.

6. **Test policy issuance via Connect API** — Use Workbench or a test OmniScript step to POST to /connect/insurance/policy-administration/policies with a valid payload. Verify InsurancePolicy and InsurancePolicyCoverage records are created correctly. Confirm InsurancePolicyParticipant records reflect the expected roles.

7. **Review checklist and document configuration decisions** — Run the review checklist below. Document which irreversible settings were enabled, which platform path (managed package vs native core) is in use, and any custom coverage types created.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] FSC Insurance permission set license confirmed provisioned and assigned to all relevant users
- [ ] Insurance Settings panel visible in Setup; irreversible settings decision documented
- [ ] CoverageType records created for all lines of business; ClaimType picklist values configured
- [ ] InsurancePolicy, InsurancePolicyCoverage, and Claim page layouts configured with relevant fields visible
- [ ] InsurancePolicyParticipant role picklist matches the org's participant model (named insured, producer, claimant, etc.)
- [ ] OmniScript quoting flow tested end-to-end with InsProductService.getRatedProducts returning rated products
- [ ] Policy issuance via Connect API POST /connect/insurance/policy-administration/policies tested and verified
- [ ] Managed-package vs native-core platform path documented for the org

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Irreversible Insurance Settings cannot be undone** — Enabling many-to-many policy relationships or multiple producers per policy in Insurance Settings permanently alters the org's data model. There is no "undo" button and Salesforce Support cannot reverse these settings. Orgs that enable these without understanding the participant model often face data migration issues at go-live.

2. **FSC Insurance license is separate from FSC base license** — Users with a standard FSC license do not automatically get access to Insurance objects. The FSC Insurance permission set license must be explicitly provisioned by Salesforce (requires an order) and then assigned in Setup. Forgetting this causes confusing "object not found" errors that look like a configuration problem but are actually a licensing gap.

3. **InsProductService is not callable from standard Apex without the correct namespace** — On managed-package orgs, the InsProductService class lives in a namespace. Calling it without the correct namespace prefix causes a compile error. On native-core orgs, the namespace differs. Always confirm which path the org is on and reference the correct class name in Remote Action elements.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Insurance Settings decision record | Documentation of which irreversible org settings were enabled and when |
| CoverageType configuration | List of CoverageType records created per line of business |
| OmniScript quoting flow | OmniStudio OmniScript with InsProductService Remote Action and insOsGridProductSelection LWC |
| Policy issuance Connect API payload | Example POST payload for /connect/insurance/policy-administration/policies |
| Permission set license assignment checklist | Record of FSC Insurance license assignments per user/profile |

---

## Related Skills

- omnistudio-admin-configuration — for general OmniStudio setup, FlexCards, and DataRaptor configuration outside the insurance quoting context
- client-onboarding-design — for FSC-based onboarding flows that may feed into insurance policy creation
- household-model-configuration — for FSC account model setup required before insurance participant records can be correctly linked
