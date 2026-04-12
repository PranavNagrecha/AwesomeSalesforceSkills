# LLM Anti-Patterns — B2B vs D2C Commerce Requirements

Common mistakes AI coding assistants make when generating or advising on B2B vs D2C Commerce platform selection.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Confusing Salesforce B2C Commerce (SFCC) with D2C Commerce (Lightning WebStore)

**What the LLM generates:** Recommendations that mix SFCC infrastructure (Business Manager, SFRA cartridges, Site Cartridge Path, quota management) with D2C Commerce Lightning concepts (WebStore, LWR, Experience Cloud), treating them as interchangeable or as layers of the same platform.

**Why it happens:** Training data contains large volumes of Salesforce B2C Commerce (SFCC) documentation, developer guides, and community content. When users say "B2C Commerce" or "consumer storefront," LLMs frequently conflate this with SFCC content, especially when the request does not explicitly disambiguate. The naming similarity ("B2C Commerce" vs. "D2C Commerce") amplifies the confusion.

**Correct pattern:**

```
Salesforce B2C Commerce (SFCC):
  - Hosted platform, separate from the core Salesforce org
  - Administered via Business Manager
  - Customized via SFRA cartridges
  - Admin skill: admin/b2c-commerce-store-setup

D2C Commerce (Lightning-based):
  - Runs inside the core Salesforce org
  - Administered via the Salesforce Commerce app
  - Built on WebStore + LWR + Experience Cloud
  - Admin skill: this skill (b2b-vs-b2c-requirements) for decision; 
    then admin/b2b-commerce-store-setup for implementation
```

**Detection hint:** If the response mentions "Business Manager," "SFRA," "cartridge path," or "site cartridge" in the context of a Lightning-based Commerce project, the LLM has conflated SFCC with D2C Commerce.

---

## Anti-Pattern 2: Recommending BuyerGroup Setup on a D2C Commerce WebStore

**What the LLM generates:** Instructions to create `BuyerGroup` and `CommerceEntitlementPolicy` records in a D2C Commerce context, treating these as standard Commerce objects available on all WebStore types.

**Why it happens:** B2B Commerce documentation dominates Salesforce Commerce developer content (it predates D2C Commerce). LLMs trained on this content apply B2B entitlement patterns universally, without distinguishing by store type or license.

**Correct pattern:**

```
D2C Commerce:
  - No BuyerGroup object (requires B2B Commerce license)
  - No CommerceEntitlementPolicy object (requires B2B Commerce license)
  - Catalog access: open to all authenticated buyers or guests
  - Segmentation: price books, promotions, or custom logic only

B2B Commerce:
  - BuyerGroup + CommerceEntitlementPolicy are the native catalog-gating mechanism
  - Both objects are required for account-gated catalog access
```

**Detection hint:** If the response includes `BuyerGroup`, `CommerceEntitlementPolicy`, or `BuyerGroupMember` in the context of a D2C or consumer Commerce project, the LLM has applied B2B entitlement logic to the wrong store type.

---

## Anti-Pattern 3: Claiming B2B Commerce Supports Guest Checkout by Default

**What the LLM generates:** Setup instructions for B2B Commerce that include guest or anonymous checkout as a default-on feature, without flagging that this requires explicit enablement and was only added in Winter '24.

**Why it happens:** Post-Winter '24 Salesforce documentation describes guest purchasing as a B2B Commerce capability. LLMs trained on this documentation may not distinguish between "this capability exists" and "this capability is enabled by default," or may not surface the release version dependency.

**Correct pattern:**

```
B2B Commerce guest checkout:
  - Not available before Winter '24 (org must be on Winter '24 release or later)
  - Requires explicit enablement in WebStore settings:
      WebStore.IsGuestBrowsingEnabled = true (via Commerce app or API)
  - Requires Guest User profile configuration in the associated Experience Cloud site
  - Is NOT enabled by default even on Winter '24+ orgs

D2C Commerce guest checkout:
  - Designed as a first-class scenario
  - Requires explicit enablement (Guest User profile), but is the intended default flow
```

**Detection hint:** If the response describes guest checkout on a B2B store without mentioning Winter '24 or explicit enablement steps, the LLM is overstating the default state of the platform.

---

## Anti-Pattern 4: Treating WebStore Store Type as Mutable After Creation

**What the LLM generates:** Instructions to "convert" or "reconfigure" a B2B WebStore to a D2C WebStore (or vice versa) after the store has been created, treating the store type as an editable property.

**Why it happens:** LLMs generalize from other Salesforce metadata types that can be updated post-creation (e.g., Experience Cloud site type changes in some scenarios, or record type changes on custom objects). They do not surface the WebStore-specific constraint that the `StoreType` field is set at creation and is immutable.

**Correct pattern:**

```
WebStore.StoreType is set at record creation.
It cannot be changed via UI, API, or metadata deployment after the record exists.

If the wrong store type was selected:
  1. Export all configuration data (product catalog, BuyerGroups, price books)
  2. Delete the existing WebStore and associated Experience Cloud site
  3. Create a new WebStore with the correct store type
  4. Recreate configuration from exported data

Prevention: Complete platform selection (this skill) before creating any WebStore record.
```

**Detection hint:** If the response includes phrases like "change the store type," "convert the WebStore," or "reconfigure from B2B to D2C," the LLM is treating an immutable property as editable.

---

## Anti-Pattern 5: Recommending a Single WebStore for a Hybrid B2B2C Requirement

**What the LLM generates:** A design that uses a single WebStore to serve both business account buyers (needing BuyerGroup entitlement) and individual consumers (needing guest checkout), treating B2B2C as a single-store configuration rather than a two-store architecture.

**Why it happens:** LLMs pattern-match on "B2B2C" as a single concept and attempt to satisfy all requirements within a single storefront. They may not surface the platform constraint that a WebStore is either B2B or D2C in type, and that serving both buyer types natively requires two separate WebStore instances.

**Correct pattern:**

```
B2B2C hybrid (supported pattern):
  - Two WebStore instances: one B2B (store type = B2B), one D2C (store type = B2C)
  - Two Experience Cloud sites, one per store
  - Both B2B Commerce and D2C Commerce licenses required
  - Routing logic (e.g., different URLs, authentication-aware redirects) directs 
    buyers to the appropriate storefront
  - Shared back-office data: single product catalog, shared Order Management

B2B2C anti-pattern:
  - Single WebStore attempting to serve both buyer types
  - Not natively supported — requires heavy custom entitlement logic
  - No platform-level security guarantees for the custom logic
```

**Detection hint:** If the response proposes a single WebStore handling both account-gated B2B purchasing and open consumer/guest D2C purchasing without a routing layer and two store instances, the LLM has mismodeled the B2B2C architecture.
