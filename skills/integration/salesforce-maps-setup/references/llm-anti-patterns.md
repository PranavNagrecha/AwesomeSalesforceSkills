# LLM Anti-Patterns — Salesforce Maps Setup

Common mistakes AI coding assistants make when generating or advising on Salesforce Maps Setup.

## Anti-Pattern 1: Confusing Salesforce Maps With Field Service Lightning

**What the LLM generates:** "To configure territories in Salesforce Maps, create `ServiceTerritory` records and assign `ServiceTerritoryMember` rows for each rep."

**Why it happens:** The model has more training data on FSL than on Salesforce Maps (Maps is a smaller, paid add-on). It defaults to the better-known territory model and assumes "territory" is a single concept across products.

**Correct pattern:**

```
Salesforce Maps territory model:
  - MapsTerritoryPlan__c (parent container)
  - MapsTerritory__c (polygon, ZIP, or rule-based)
  - Polygon vertices stored in package-internal field

FSL territory model (DIFFERENT product):
  - ServiceTerritory (with Address, ServiceTerritoryMember junction)
  - Used by FSL Optimization Engine for dispatch
```

**Detection hint:** If the answer says "create a `ServiceTerritory`" in the context of Salesforce Maps, the model is mixing products. Ask which product is licensed.

---

## Anti-Pattern 2: Assuming Geocoding Is Real-Time By Default

**What the LLM generates:** "Salesforce Maps geocodes new records automatically when you save them. You don't need to configure anything."

**Why it happens:** "Salesforce auto-handles X" is a frequent training-data pattern. The model doesn't know that real-time geocoding is OFF by default per object — it assumes the convenient behavior.

**Correct pattern:**

```
Per object that needs immediate plotting:
  Maps Setup → Configure Salesforce Maps → Geocoding
    → enable "Real-Time Geocoding" for the object
    → confirm the address-source field mapping is correct
Without this, new records geocode on the next batch (typically next day).
```

**Detection hint:** If the answer says new records appear on the map "immediately" or "automatically" without mentioning the real-time toggle, the model is wrong about Salesforce Maps default behavior.

---

## Anti-Pattern 3: Treating Maps Polygon Data As Standard Salesforce Geometry

**What the LLM generates:** "Query the polygon vertices with `SELECT Polygon__c FROM MapsTerritory__c` and pass them to your Tableau/PostGIS/D3 visualization."

**Why it happens:** The model assumes Salesforce stores polygon data in a standard format like WKT or GeoJSON. It doesn't — Maps stores polygons in a package-internal encoded string that is not interoperable.

**Correct pattern:**

```apex
// To export polygons for non-Maps consumers, write a one-time Apex
// converter that reads the package field and emits GeoJSON. Or use
// Maps Advanced UI's "Export to KML/Shapefile" feature.
// Do NOT try to query the polygon field directly and assume it's WKT.
```

**Detection hint:** If the answer assumes Maps polygon data is queryable as standard geometry without a conversion step, the model is wrong about the package's data format.

---

## Anti-Pattern 4: Forgetting Permission-Set Assignment Post-Install

**What the LLM generates:** "Install the Salesforce Maps package, configure geocoding, and your users will see Maps in the App Launcher."

**Why it happens:** Most managed-package install flows the model has seen include "users see the new tabs immediately." Maps installs the permission sets but does not assign them to anyone — an important operational detail not in standard install documentation.

**Correct pattern:**

```
Post-install runbook:
  1. Install package (sandbox first, then production).
  2. Configure geocoding per object.
  3. CRITICAL: Assign permission sets to user cohort.
     - PermissionSet: "Salesforce Maps"
     - PermissionSet: "Salesforce Maps Advanced" (if Advanced licensed)
     - PermissionSet: "Salesforce Maps Routing" (if Routing licensed)
  4. Validate by logging in as a sample user; confirm the Maps tab appears.
```

**Detection hint:** If the answer omits the permission-set assignment step, the recommendation is incomplete and Day-1 will fail.

---

## Anti-Pattern 5: Recommending Live Tracking Without Privacy / Volume Caveats

**What the LLM generates:** "Enable Live Tracking under Maps Setup. Reps will be tracked at 5-minute intervals automatically."

**Why it happens:** The model treats Live Tracking as a feature toggle rather than a regulated capability with operational and legal implications. It doesn't surface the privacy and volume tradeoffs that should gate enablement.

**Correct pattern:**

```
Live Tracking enablement requires THREE prerequisites:
  1. HR/legal approval per region (privacy-regulated in CA, EU, others).
  2. Volume planning: N reps × pings/hour × work-hours = breadcrumb records/day.
     Plan archival (Big Object) before crossing org storage limits.
  3. Ping interval that matches the use case — 15 min is usually enough; 5 min
     is rarely justified.
```

**Detection hint:** If the answer recommends Live Tracking without mentioning privacy, volume, or interval-tradeoff, the model is treating a regulated capability like a casual feature toggle.
