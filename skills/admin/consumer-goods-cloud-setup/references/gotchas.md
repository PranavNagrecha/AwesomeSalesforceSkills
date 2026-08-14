# Gotchas — Consumer Goods Cloud Setup

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: There Is No `RoutePlan` Object — Route Planning Lives in the `cgcloud__` Managed Package

**What happens:** A build plan, a data-load spec, or generated Apex references `RoutePlan` and `RoutePlanEntry`. Neither exists. Route planning ships as a managed-package custom object, `cgcloud__Trip_List__c` — "Use Trip List to plan visits based on a predefined sequence of customers." Everything downstream that assumed `RoutePlan` has to be rewritten.

**When it occurs:** Whenever the object model is inferred from the feature name rather than read from the developer guide. "Route Plan" is what the capability is called in conversation, which makes the wrong name feel verified.

**How to avoid:** Treat CG Cloud as two models with one label. Retail Execution ships **standard** objects — `RetailStore`, `Visit`, `AssessmentTask`, `RetailStoreKpi`, `RetailVisitKpi`, `InStoreLocation`, `Assortment`, `Promotion`, `RetailLocationGroup` — while route planning, order taking, and inventory are `cgcloud__` custom objects: `cgcloud__Trip_List__c`, `cgcloud__Visit_Template__c`, `cgcloud__Order__c`, `cgcloud__Inventory__c`, `cgcloud__POS__c`, `cgcloud__Org_Unit__c`. There are roughly 150 objects in the managed package; check the namespace before writing any API name.

---

## Gotcha 2: `RetailStore` Is a Standard Object, Not an Account Record Type

**What happens:** The retail hierarchy is built as Account records with a "Retail Store" record type. Visits, KPIs, store products, and assortments then have nothing to point at, because every one of those objects relates to `RetailStore` — "Create records for physical retail stores associated to business accounts."

**When it occurs:** During the first data load, which is exactly when it is most expensive to unwind: the Accounts are already created, referenced by opportunities and contacts, and cannot simply be retyped.

**How to avoid:** Load `RetailStore` records associated to their business Accounts, and keep the two layers distinct — the Account is the commercial relationship, the `RetailStore` is the physical location a rep walks into. Segment stores for targeting with `RetailLocationGroup` ("Group retail stores based on shared features, such as size, location, or part of a retail chain") and `RetailStoreGroupAssignment`, not with Account record types. Below the store, `InStoreLocation` models "locations within a retail store's layout such as aisles, shelves, or backrooms" — that is the grain planogram compliance actually needs.

---

## Gotcha 3: Targets and Actuals Are Different Objects, and Reporting Silently Compares Nothing

**What happens:** A compliance dashboard is built over visit results and shows every store at 100%, or at zero, because it reads only one side of the comparison. The model deliberately splits them: `AssessmentIndicatorDefinition` defines "parameters that act as markers of compliance for retail tasks to compare target and actual values," `RetailStoreKpi` maps "store groups to assessment indicator definition, products, and in-store location categories and define targets," and `RetailVisitKpi` captures "the actual information during a visit against the defined assessment indicator definition and target values."

**When it occurs:** In the first reporting build, and again whenever a new indicator is added without a corresponding `RetailStoreKpi` target for the store groups it applies to — those visits then record an actual with nothing to score against.

**How to avoid:** Treat an indicator as incomplete until it has both a definition and a target assigned to every store group in scope. Add a pre-go-live check that counts store groups with no `RetailStoreKpi` row for each active indicator, and re-run it whenever an indicator is introduced. Report on the join, never on `RetailVisitKpi` alone.

---

## Gotcha 4: Assortment and Store Product Are Separate Layers, and Only One Is Location-Aware

**What happens:** A rep is asked to check a SKU that the store does not carry, or the planogram check has no shelf to compare against, because the eligibility list and the physical placement were treated as the same data. `Assortment` is "a list of products that are eligible for sale in a store" with `AssortmentProduct` as its membership and `StoreAssortment` associating it "to either a store, a store group, or an account." `StoreProduct` is the different thing: it associates "a product to a retail store or to a specific in-store location."

**When it occurs:** When assortments are loaded but store products are not, which is common because the assortment is the layer the commercial team already maintains. Visits then generate tasks for products with no known location.

**How to avoid:** Load both, in order: assortment (what may be sold here) then store product (where it sits). Where planogram compliance is in scope, `StoreProduct` must carry the `InStoreLocation`, or image recognition has no expected placement to score against. Reps notice this immediately — a task that cannot be completed is the fastest way to lose field adoption.

---

## Gotcha 5: The Mobile App and Its Offline Data Are Not the Standard Salesforce Mobile Experience

**What happens:** Field reps are onboarded onto the standard Salesforce mobile app, and visit execution does not work — the task framework, offline visit capture, and signature steps are not there. `SignatureTask` "Represent the signature-related information that a visitor captures as part of a visit" and `OtherComponentTask` exists specifically to "allow customers to launch components from the task framework," none of which the general-purpose app surfaces.

**When it occurs:** At pilot, after devices have been provisioned and reps trained on the wrong application. Also when a Visitor record has not been created — `Visitor` represents "the sales reps performing visits," and a user without one is not a rep as far as the model is concerned.

**How to avoid:** Include the CG mobile app in the provisioning checklist alongside the licence, and validate on a real device before the pilot cohort is trained. Create `Visitor` records as part of user onboarding, not as a data-load afterthought, and confirm `VisitedParty` ("the contact person at the account that's being visited") is populated so the rep knows who to ask for on arrival. Where vehicles are assigned, `VehicleUserAssignment` represents "the assignment of a vehicle to a driver where vehicle is a moving location" — a separate onboarding step again.
