# LLM Anti-Patterns — B2B vs B2C Commerce Architecture

Common mistakes AI coding assistants and architecture advisors make when advising on Salesforce B2B vs B2C Commerce platform decisions.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Conflating B2B Commerce (Lightning/Core) with B2C Commerce (SFCC/Separate Infrastructure)

**What the LLM generates:** Advice that mixes B2B Commerce on Core concepts (BuyerGroup, CommerceEntitlementPolicy, WebStore, Apex, Flow checkout) with SFCC concepts (SFRA cartridges, Business Manager, OCAPI) as if they were features of the same platform. For example: "You can configure BuyerGroups in Business Manager and extend checkout using Commerce Extensions in your SFRA cartridges."

**Why it happens:** Training data contains the term "Salesforce Commerce" across both products. The model learns surface-level associations (both involve storefronts, both involve Salesforce) without learning the hard architectural boundary between a Core-platform native application and a separate hosted infrastructure.

**Correct pattern:**
```
B2B Commerce on Core: WebStore (Core object), BuyerGroup, CommerceEntitlementPolicy, Apex,
Flow (CheckoutFlow type), LWC, Commerce Extensions (sfdc_checkout.CartExtension).
All run inside the Salesforce org.

SFCC: Business Manager, SFRA cartridges (Node.js), OCAPI/SCAPI (REST APIs),
dw.* script API, hooks, pipelines, code versions.
Runs on a separate hosted infrastructure. No Salesforce org, no Apex, no Flow.

These share no objects, no APIs, and no data. Treat them as separate systems.
```

**Detection hint:** Flag any output that mentions both `BuyerGroup` and `Business Manager` or both `CommerceEntitlementPolicy` and `SFRA` in the same recommendation without explicitly separating them as features of different platforms.

---

## Anti-Pattern 2: Recommending Commerce Extensions for SFCC Checkout Customization

**What the LLM generates:** "To customize tax calculation in your Salesforce B2C Commerce checkout, implement the `sfdc_checkout.CartExtension` interface in Apex and register it in the WebStore's Commerce Extension settings."

**Why it happens:** Commerce Extensions are well-documented in the Salesforce developer docs. SFCC checkout customization is documented separately in the B2C Commerce SFRA docs. The model does not reliably classify which set of docs applies to the project described.

**Correct pattern:**
```
Commerce Extensions (Apex, sfdc_checkout.CartExtension) = B2B Commerce / D2C Commerce ON CORE only.
SFCC checkout tax customization = SFRA cartridge override of checkout controller,
or third-party tax cartridge (e.g., Avalara SFCC cartridge),
or dw.order.TaxMgr configuration in Business Manager.

Never recommend sfdc_checkout.CartExtension for an SFCC project.
```

**Detection hint:** Flag any output that uses `sfdc_checkout` or `CartExtension` in the context of a project described as using Business Manager, SFRA, or Salesforce Commerce Cloud (SFCC).

---

## Anti-Pattern 3: Assuming SFCC Order Data Is Automatically Available in Salesforce Order Management

**What the LLM generates:** "Orders placed in your Salesforce B2C Commerce storefront will automatically appear in Salesforce Order Management for fulfillment processing."

**Why it happens:** The model correctly associates Salesforce Order Management with order fulfillment and correctly associates SFCC with order placement, but hallucinates a native data connection between them because both are Salesforce products.

**Correct pattern:**
```
SFCC stores orders in its own database.
Salesforce Order Management stores orders in OrderSummary objects in the Salesforce org.
These are separate data stores with no native sync.

Integration options:
- Salesforce Connector for B2C Commerce (managed solution, async)
- Custom integration via SFCC OCAPI/SCAPI order export + Salesforce Platform Events or API
Always design and scope this integration explicitly.
```

**Detection hint:** Flag any recommendation that says SFCC order data "automatically" appears in Salesforce Order Management or that the two are "natively integrated" without describing a specific connector or integration mechanism.

---

## Anti-Pattern 4: Treating B2B Commerce Checkout Flow Customization as Equivalent to SFCC Checkout Cartridge Customization

**What the LLM generates:** "The checkout customization approach is similar on both platforms — you override the default steps with your custom logic" without distinguishing that B2B Commerce checkout customization is Flow Builder (declarative/Apex) and SFCC checkout customization is SFRA cartridge controllers (Node.js code).

**Why it happens:** "Override the checkout" is a valid description of both approaches at a high level. The model elides the critical detail that the implementation model, required skills, and DevOps tooling are completely different.

**Correct pattern:**
```
B2B Commerce on Core checkout customization:
- Checkout is a Salesforce Flow (CheckoutFlow type)
- Steps are Flow elements; override with custom Screen components or LWC
- Business logic in Apex; Commerce Extensions for pricing/tax/shipping/inventory callouts
- Deployed via SFDX, tested in scratch orgs

SFCC checkout customization:
- Checkout is an SFRA cartridge controller chain (Node.js)
- Override by creating a custom cartridge that extends the base SFRA CheckoutController
- Business logic in server-side JavaScript using dw.* API
- Deployed by uploading cartridge zip to Business Manager, activating code version

These require different skills, different tools, and produce different artifacts.
```

**Detection hint:** Flag any output that describes checkout customization for both platforms using the same terms or that estimates implementation effort without distinguishing which platform's model is being described.

---

## Anti-Pattern 5: Recommending B2B Commerce on Core for High-Volume Anonymous Consumer Traffic Without a Capacity Analysis

**What the LLM generates:** "Since you already have a Salesforce org, just use B2B Commerce on Core — it's simpler than standing up a separate SFCC infrastructure." This recommendation is made without asking about expected peak concurrent sessions or evaluating platform limits.

**Why it happens:** The model correctly identifies that B2B Commerce on Core has a lower operational overhead when an org already exists. It does not reliably apply the constraint that Salesforce platform governor limits (concurrent API requests, per-transaction CPU time) are binding constraints for consumer-scale anonymous traffic.

**Correct pattern:**
```
B2B Commerce on Core is appropriate for:
- Authenticated, account-based buyers
- B2B transaction volumes (hundreds to low thousands of concurrent sessions)
- Workloads requiring deep CRM data access at checkout

SFCC or D2C Commerce with CDN caching is appropriate for:
- Anonymous consumer traffic at e-commerce scale
- Peak concurrent sessions in the thousands or tens of thousands
- Workloads where infrastructure independence from the Salesforce org is required

Always ask: "What is the expected peak concurrent session count and annual order volume?"
before recommending B2B Commerce on Core for any storefront with anonymous traffic.
```

**Detection hint:** Flag any platform recommendation that does not include an assessment of peak concurrent session volume. A recommendation that defaults to B2B Commerce on Core without asking about traffic scale is likely missing a critical non-functional requirement.

---

## Anti-Pattern 6: Stating That B2B Commerce and D2C Commerce Are Different Platforms

**What the LLM generates:** "B2B Commerce and D2C Commerce are two separate platforms — B2B Commerce runs on Core and D2C Commerce runs on a different infrastructure."

**Why it happens:** The model may confuse D2C Commerce (Lightning-based, Core-platform) with Salesforce B2C Commerce (SFCC, separate infrastructure), or may over-apply the "B2B vs B2C" framing to mean different infrastructure stacks.

**Correct pattern:**
```
B2B Commerce (on Core) and D2C Commerce (on Core) are both Lightning platform applications.
They both use WebStore, LWR, Experience Cloud, Apex, and Flow.
They run in the same Salesforce org.
The difference is the buyer-entitlement model (BuyerGroup for B2B vs. Individual/Person Account for D2C).

Salesforce B2C Commerce (SFCC) is a separate infrastructure platform.
It is NOT the same as D2C Commerce on Core.

"D2C Commerce" = Lightning-based consumer storefront inside the Salesforce org.
"B2C Commerce" or "SFCC" = Salesforce Commerce Cloud, separate hosted platform.
```

**Detection hint:** Flag any output that describes D2C Commerce as running on separate infrastructure from B2B Commerce, or that equates "D2C Commerce" with "SFCC" or "Commerce Cloud."
