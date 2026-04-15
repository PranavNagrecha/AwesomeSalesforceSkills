# LLM Anti-Patterns — Industries Cloud Selection

Common mistakes AI coding assistants make when generating or advising on Industries Cloud Selection.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Assuming Industry Standard Objects Are Available Without Confirming the License

**What the LLM generates:** "You can use the `InsurancePolicy` object to store policy records" or "Query `ServicePoint` to retrieve utility service locations" — stated without any mention that these objects require a specific Salesforce Industries license and are not present in a standard Salesforce org.

**Why it happens:** LLMs are trained on Salesforce documentation that discusses vertical cloud standard objects in the context of their respective clouds. The training data may not emphasize the license gating clearly enough, leading the model to treat these objects as if they were universally available standard Salesforce objects like `Account` or `Contact`.

**Correct pattern:**

```
Verify before recommending:
- InsurancePolicy → requires Insurance Cloud license (+ FSC base)
- ServicePoint    → requires Energy & Utilities Cloud license
- BillingAccount  → requires Communications Cloud license
- ClinicalEncounter → requires Health Cloud license

Always state: "This object is only available if the org holds the [X] 
Industries license. Confirm licensing before beginning development."
```

**Detection hint:** Look for any reference to a vertical cloud standard object without an accompanying license confirmation statement. If `InsurancePolicy`, `ServicePoint`, `BillingAccount`, `EnterpriseProduct`, `ClinicalEncounter`, `SalesAgreement`, or `Vehicle` appear in a recommendation without a license caveat, flag it.

---

## Anti-Pattern 2: Treating FSC and Insurance Cloud as Alternatives

**What the LLM generates:** "For this insurance use case, you could use Financial Services Cloud or Insurance Cloud — FSC is cheaper and provides most of the same functionality."

**Why it happens:** Both FSC and Insurance Cloud appear in financial services contexts, and LLMs may conflate them as competing alternatives based on co-occurrence in training data. The critical architectural fact — that Insurance Cloud is layered on top of FSC and requires FSC as a base license — is often absent from the generated recommendation.

**Correct pattern:**

```
Insurance Cloud and FSC are NOT alternatives. They are additive:
- FSC provides: FinancialAccount, FinancialHolding, household data model
- Insurance Cloud provides: InsurancePolicy, InsurancePolicyCoverage, 
  InsurancePolicyParticipant — AND requires FSC as base

A valid Insurance Cloud implementation requires BOTH licenses.
Recommending FSC-only for an insurance policy use case will result in 
missing objects (InsurancePolicy) that FSC does not provide.
```

**Detection hint:** Any recommendation that presents Insurance Cloud and FSC as "either/or" choices, or that says "FSC covers most insurance needs," should be flagged. The correct framing is always additive: Insurance Cloud builds on FSC.

---

## Anti-Pattern 3: Recommending OmniStudio Managed Package for New Orgs on Spring '26+

**What the LLM generates:** "Install the OmniStudio managed package from AppExchange to enable OmniScripts and FlexCards in your Industries implementation."

**Why it happens:** A large portion of OmniStudio documentation and practitioner content predates the Spring '26 platform-native adoption. LLMs trained on this older content default to the managed-package installation pattern, which was correct for pre-Spring '26 orgs but is no longer the appropriate path for new orgs.

**Correct pattern:**

```
As of Spring '26, new orgs provisioned with a Salesforce Industries license 
receive OmniStudio as a platform-native feature — no AppExchange managed 
package installation is required or recommended.

For new orgs (Spring '26+):
- OmniStudio components are available natively
- Components are deployable via Metadata API
- No managed package namespace to manage

For existing orgs with managed-package OmniStudio:
- Document the packaging model before planning any component work
- Migration to platform-native is one-way (irreversible per component)
- Existing managed-package components continue to work without migration
```

**Detection hint:** Any recommendation to "install the OmniStudio managed package" for a new org implementation after Spring '25 should be questioned. Confirm the org's provisioning date and OmniStudio model before proceeding.

---

## Anti-Pattern 4: Suggesting Custom Objects as a Direct Substitute for Industry Standard Objects

**What the LLM generates:** "If you don't have the Insurance Cloud license, you can create a custom object `InsurancePolicy__c` and replicate the same functionality" or "Build a `ServicePoint__c` custom object to avoid the additional licensing cost."

**Why it happens:** LLMs are trained to solve problems pragmatically and often suggest custom object workarounds when platform constraints are mentioned. In many areas of Salesforce this is a valid pattern. In Industries, however, the standard objects carry significant pre-built behavior — OmniStudio component integrations, pre-built automation, industry-standard data model relationships, and upgrade compatibility — that a custom object substitute cannot provide.

**Correct pattern:**

```
Custom objects do NOT substitute for industry standard objects:
- Pre-built OmniStudio components reference standard objects by API name
  — they cannot be redirected to custom objects without rebuilding every component
- Standard object relationships (InsurancePolicy → InsurancePolicyCoverage)
  are built into the platform — custom objects require custom relationship fields
- Future Salesforce product updates (new features, AI capabilities) target 
  standard objects — custom object substitutes are permanently excluded

The correct response to a licensing constraint is:
1. Re-evaluate whether the license cost is justified for the use case
2. Descope the feature set to what standard Salesforce objects support
3. Recommend the correct license — not a custom object workaround
```

**Detection hint:** Any suggestion to create custom objects whose names mirror vertical cloud standard objects (e.g., `Policy__c`, `ServicePoint__c`, `BillingAccount__c`) in the context of an Industries implementation should be flagged as a potential anti-pattern.

---

## Anti-Pattern 5: Treating the OmniStudio Standard Designer Migration as Reversible

**What the LLM generates:** "You can try migrating your OmniScript to the platform-native model in the Standard Designer, and if it doesn't work you can revert it back to the managed package" or "Opening a component in the Standard Designer is just a preview — you can always go back."

**Why it happens:** LLMs tend to model most software migration operations as reversible because the majority of software operations are reversible. The one-way nature of the OmniStudio Standard Designer migration is a specific, counterintuitive platform behavior that may not be represented clearly in training data.

**Correct pattern:**

```
Opening a managed-package OmniStudio component in the Standard Designer 
is IRREVERSIBLE. Once opened:
- The component is converted to platform-native metadata
- It is removed from the managed-package designer permanently
- There is no rollback, even if the session is closed without saving

This is not a "preview" — it is a one-way state change.

Before any Standard Designer migration:
1. Document all components to be migrated
2. Confirm all downstream dependencies are platform-native compatible
3. Obtain formal project sign-off on the migration plan
4. Never open components in production as a test
```

**Detection hint:** Any recommendation that describes the Standard Designer migration as "reversible," "a test," "a preview," or "something you can undo" should be corrected. The migration is one-way and permanent. Governance and planning must precede it.

---

## Anti-Pattern 6: Recommending "Salesforce Industries" as a Single License That Covers All Verticals

**What the LLM generates:** "Purchase Salesforce Industries to get access to all vertical cloud objects" or "With an Industries license, you'll have access to Communications Cloud, Health Cloud, and Insurance Cloud features."

**Why it happens:** The term "Salesforce Industries" is used as both a portfolio brand name and colloquially to mean any Industries vertical cloud product. LLMs trained on marketing and overview content may conflate the brand with a unified license. In practice, each vertical cloud (Communications, Health, Insurance, Energy & Utilities, etc.) is a separately licensed product.

**Correct pattern:**

```
"Salesforce Industries" is a portfolio brand — NOT a single license.
Each vertical cloud is separately licensed:
- Communications Cloud: separate license
- Health Cloud: separate license  
- Insurance Cloud: separate license (+ requires FSC)
- Energy & Utilities Cloud: separate license
- Financial Services Cloud: separate license

A multi-vertical solution (e.g., bank + insurance subsidiary) requires 
MULTIPLE Industries licenses purchased separately. Confirm each required 
vertical cloud appears as a distinct line item on the order form.
```

**Detection hint:** Any statement like "an Industries license gives you access to [multiple vertical clouds]" without specifying separate licenses for each should be flagged. Each vertical requires its own license purchase.
