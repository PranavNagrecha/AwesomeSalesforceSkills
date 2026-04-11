# LLM Anti-Patterns — Industries Insurance Setup

Common mistakes AI coding assistants make when generating or advising on Industries Insurance Setup.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Standard CPQ Pricebook/Quote Objects for Insurance Quoting

**What the LLM generates:** Configuration steps or Apex code that creates `Quote`, `QuoteLineItem`, and `Pricebook2` records for insurance product selection, with a custom Apex trigger to convert a finalized Quote into an `InsurancePolicy` record.

**Why it happens:** LLMs are trained on large volumes of Salesforce CPQ documentation and community posts. "Quoting" strongly activates CPQ patterns in training data. The insurance-specific quoting API (`InsProductService`, Connect API issue-policy endpoint) appears in a much smaller training corpus slice and is easily overlooked.

**Correct pattern:**

```
Insurance quoting requires:
1. OmniScript with Remote Action element → InsProductService.getRatedProducts()
2. insOsGridProductSelection LWC for product selection display
3. POST /connect/insurance/policy-administration/policies for issuance

NOT:
- Pricebook2 / QuoteLineItem
- SBQQ__Quote__c
- Custom Apex DML to create InsurancePolicy from a Quote
```

**Detection hint:** If the generated output references `Pricebook2`, `QuoteLineItem`, `SBQQ__Quote__c`, or a custom trigger converting Quote to InsurancePolicy, this anti-pattern is present.

---

## Anti-Pattern 2: Assuming the FSC Insurance License Is Included in the Base FSC License

**What the LLM generates:** Setup instructions that say "navigate to Setup > Insurance Settings" without mentioning that the FSC Insurance permission set license must be separately provisioned and assigned. The generated steps imply Insurance Settings will simply be visible after enabling FSC.

**Why it happens:** LLMs conflate FSC as a single product, missing the add-on license model. Insurance-specific licensing details are not well-represented in general Salesforce documentation training data.

**Correct pattern:**

```
Step 0 (before any Insurance Settings config):
1. Setup > Company Information > Permission Set Licenses
2. Verify "FSC Insurance" PSL row exists and has available licenses
3. If absent: contact Salesforce AE — separate order required
4. Assign PSL to each user: Setup > Users > [User] > Permission Set License Assignments

ONLY THEN proceed to Insurance Settings configuration.
```

**Detection hint:** If generated setup steps begin with "Go to Setup > Insurance Settings" without any mention of permission set license verification or assignment, this anti-pattern is present.

---

## Anti-Pattern 3: Treating Insurance Settings Toggles as Reversible

**What the LLM generates:** Instructions like "enable many-to-many policy relationships if you need it; you can always turn it off later" or steps that enable both irreversible toggles "to be safe" without documenting the decision.

**Why it happens:** Most Salesforce Setup toggles are reversible. LLMs generalize from the common case and do not flag the handful of permanently irreversible settings. The irreversibility of Insurance Settings toggles is documented in Salesforce Help but is not prominently emphasized.

**Correct pattern:**

```
Insurance Settings irreversible decisions (document BEFORE enabling):
- Many-to-Many Policy Relationships: enables InsurancePolicyParticipant junction model
  → Cannot be disabled after saving
  → Required if: multiple named insureds per policy
  → Decision owner: Solution Architect + Client sign-off

- Multiple Producers Per Policy: enables >1 Producer role participant per policy
  → Cannot be disabled after saving
  → Required if: commission splits, multi-agent policies
  → Decision owner: Solution Architect + Client sign-off

Only enable what is confirmed needed. Enabling "to be safe" is an architectural error.
```

**Detection hint:** Any generated instructions that suggest enabling both toggles as a default, or that describe these settings as toggleable/reversible, indicate this anti-pattern.

---

## Anti-Pattern 4: Using the Wrong Namespace for InsProductService Based on Platform Path

**What the LLM generates:** OmniScript Remote Action configuration referencing `InsProductService.getRatedProducts` without confirming whether the org is on the managed-package or native-core Digital Insurance Platform path. On managed-package orgs, the class name includes a namespace prefix; on native-core orgs, it does not (or uses a different reference). The generated config works on one path and silently fails on the other.

**Why it happens:** LLMs conflate documentation from both platform paths. The Digital Insurance Platform transition (managed package → native core, target Oct 2025) means documentation from different time periods references different namespaces, and LLMs cannot reliably distinguish which applies to the current org.

**Correct pattern:**

```
Step 1: Determine platform path
  Setup > Installed Packages
  If "Digital Insurance Platform" package present → managed-package path
  If absent → native-core path

Managed-package path:
  Remote Action class: [namespace].InsProductService
  (confirm exact namespace from Installed Packages detail page)

Native-core path:
  Remote Action class: InsProductService
  (no namespace prefix)

NEVER mix namespace references. Document the platform path in the org configuration register.
```

**Detection hint:** If generated OmniScript configuration references `InsProductService` without first confirming the platform path and namespace, this anti-pattern may be present. Also look for hardcoded namespace prefixes that may not match the target org.

---

## Anti-Pattern 5: Treating a 200 Response from the Issue-Policy Connect API as Proof of Complete Issuance

**What the LLM generates:** OmniScript or Integration Procedure steps that POST to `/connect/insurance/policy-administration/policies`, check for HTTP 200/201, and then immediately display a "Policy issued successfully" confirmation — without verifying that `InsurancePolicyCoverage` child records were created.

**Why it happens:** LLMs apply standard REST API success-checking patterns (HTTP 200 = success) without knowing that the insurance issue-policy endpoint can return 200 with a valid policy ID while silently omitting coverage records if the coverage payload is incomplete or malformed.

**Correct pattern:**

```
After POST /connect/insurance/policy-administration/policies:

1. Extract policyId from response
2. Query: SELECT Id, CoverageType.Name FROM InsurancePolicyCoverage
          WHERE InsurancePolicyId = :policyId
3. Assert count matches expected coverage lines
4. If count < expected: log error, surface to user, do NOT show success confirmation
5. Only show success confirmation after coverage record validation passes

In OmniScript: add a DataRaptor Extract step after the issue-policy call to fetch
InsurancePolicyCoverage records and drive a branching condition on the count.
```

**Detection hint:** If generated OmniScript or Apex steps show a success message immediately after a 200 response from the issue-policy endpoint without a subsequent coverage record query and assertion, this anti-pattern is present.

---

## Anti-Pattern 6: Configuring InsurancePolicyParticipant Roles Without Finalizing the Picklist First

**What the LLM generates:** Steps to create InsurancePolicyParticipant records using placeholder role values like "Agent" or "Customer," with a note that roles can be renamed or cleaned up later. Or instructions that deactivate old picklist values after participant records already exist with those values.

**Why it happens:** LLMs treat picklist cleanup as a routine admin task, not understanding the downstream impact on insurance automation, OmniScript branching, and Connect API behavior when participant role values are changed after records exist.

**Correct pattern:**

```
Participant Role picklist finalization (before creating any participant records):
1. Identify all roles needed: Named Insured, Producer, Driver, Beneficiary, Claimant, etc.
2. Setup > Object Manager > InsurancePolicyParticipant > Fields > Role
3. Add all needed values; deactivate any placeholder/default values
4. Review and approve with the client
5. Document final picklist in the org configuration register

If renaming is required AFTER records exist:
  Use Setup > Object Manager > [Object] > Fields > [Picklist] > Replace
  NOT deactivate — Replace migrates existing record values
  Test all OmniScript branches and automation after replacement
```

**Detection hint:** If generated steps include picklist values like "Agent," "Customer," or "TBD" as placeholder role values, or if deactivation of existing values is suggested after participant records may have been created, this anti-pattern is present.
