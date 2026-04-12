# Gotchas — B2B vs D2C Commerce Requirements

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Guest Checkout on B2B Commerce Was Not Available Before Winter '24

**What happens:** A team builds a B2B Commerce WebStore and adds a guest checkout requirement mid-project, assuming it is a standard configuration option. In orgs on Summer '23 or earlier, guest purchasing simply does not exist on B2B WebStores — there is no setting to enable it. In orgs on Winter '24+, guest access exists but requires explicit enablement in both the WebStore settings and the Experience Cloud Guest User profile configuration. Teams discover this gap late because the storefront otherwise appears fully functional during authenticated buyer testing.

**When it occurs:** Any time a B2B Commerce project adds anonymous or guest checkout as a late requirement, or when a project begins on a pre-Winter '24 org without checking the Commerce release version first.

**How to avoid:** During requirements gathering, confirm the org's Salesforce release version before committing to a guest checkout capability on a B2B WebStore. If guest checkout is a firm requirement and the org is pre-Winter '24, the platform decision defaults to D2C Commerce. If the org is Winter '24+, document the explicit enablement steps needed and include them in the implementation plan rather than assuming they are on by default.

---

## Gotcha 2: Both B2B and D2C Commerce Use the WebStore Object — But Store Type Is Set at Creation and Cannot Be Changed

**What happens:** Because both B2B Commerce and D2C Commerce are built on the `WebStore` object, it is tempting to assume that a WebStore can be reconfigured from B2B to D2C type (or vice versa) after creation if the requirements change. This is not supported. The store type (`B2B` vs. `B2C`) is set when the WebStore record is created and is immutable. Attempting to change it via API or metadata deployment fails silently or with a generic error. The only path to changing store type is to delete the WebStore and create a new one, which loses all configuration data.

**When it occurs:** When a project starts with one Commerce type and the business requirements shift (e.g., a B2B store is asked to support consumer purchasing as a second channel), practitioners assume the existing WebStore can be converted.

**How to avoid:** Confirm the store type during the pre-build requirements decision — that is the purpose of this skill. Once a WebStore is created, treat the store type as immutable. If a hybrid B2B and D2C channel is needed, plan for two separate WebStore instances (one per type) from the beginning, which also requires both B2B and D2C Commerce licenses.

---

## Gotcha 3: D2C Commerce License Does Not Provision BuyerGroup or CommerceEntitlementPolicy Objects

**What happens:** An org has only a D2C Commerce license. A developer attempts to reference `BuyerGroup`, `CommerceEntitlementPolicy`, or `CommerceEntitlementBuyerGroup` in Apex, Flow, or SOQL queries — believing these are standard Commerce objects available on all Commerce-licensed orgs. These objects are not present. SOQL queries return "sObject type not found" errors. Apex classes referencing these types fail to compile. Flows referencing these objects fail at activation.

**When it occurs:** When a project team conflates B2B Commerce and D2C Commerce licenses, or when code from a B2B Commerce implementation is reused in a D2C Commerce org without verifying object availability.

**How to avoid:** Before writing any code or automation that references Commerce objects, verify the org's license type by checking the WebStore creation dialog — only licensed store types appear. If `BuyerGroup` or `CommerceEntitlementPolicy` are not visible in the Schema Builder or via `DESCRIBE` calls, the org does not have a B2B Commerce license. Do not reference these objects in D2C Commerce implementations.

---

## Gotcha 4: "B2B Commerce" in Legacy Orgs May Refer to B2B Commerce for Visualforce (Aura), Not the Modern LWR WebStore

**What happens:** Some Salesforce orgs, particularly those licensed before 2021, use B2B Commerce for Visualforce — a legacy implementation that predates the modern LWR-based WebStore architecture. These orgs have B2B Commerce licenses and may have running storefronts, but the admin interface, data model details, and upgrade path are different from the current LWR-based B2B Commerce. When practitioners assume "B2B Commerce license = modern WebStore," they plan configurations (such as LWR theme customization or Commerce APIs) that do not apply to the legacy platform.

**When it occurs:** When assessing an existing org's Commerce implementation without first checking the storefront type. The Salesforce UI does not prominently label a store as "B2B Commerce for Visualforce" — it must be identified by examining the Experience Cloud site type and the WebStore record's storefront framework.

**How to avoid:** During requirements assessment, ask whether the existing Commerce implementation uses Aura/Visualforce or LWR. Check the Experience Cloud site template type — Aura-based Commerce sites are clearly labeled. If the org is on B2B Commerce for Visualforce, note that the upgrade to LWR-based B2B Commerce is a migration project, not a configuration change, and factor that into the platform decision timeline.

---

## Gotcha 5: Hybrid B2B2C Requires Both Licenses and Two Separate WebStore Instances

**What happens:** A project is scoped as "B2B2C" — meaning the platform must serve both business accounts (with account-gated pricing) and individual consumers (with guest checkout). Practitioners assume this can be achieved in a single WebStore by enabling both B2B and D2C features. This is not how the platform works. There is no single "B2B2C" WebStore type. A single WebStore is either B2B or D2C. A hybrid model requires two separate WebStore instances, two separate Experience Cloud sites, two separate license entitlements, and a data strategy that correctly routes buyers to the appropriate storefront based on their identity.

**When it occurs:** When the phrase "B2B2C" appears in requirements without a clear definition of whether it means two separate storefronts or a single storefront serving both buyer types. This is a common requirements ambiguity that, if unresolved before implementation begins, results in a store that cannot serve one of the two buyer personas.

**How to avoid:** When a B2B2C scenario is raised, immediately clarify whether the requirement is for a single storefront (not natively achievable without heavy customization) or two separate storefronts with shared back-office data (the supported pattern). If two storefronts are acceptable, confirm that both B2B Commerce and D2C Commerce licenses are active or can be procured. Document the routing logic that directs business buyers to the B2B store and consumers to the D2C store.
