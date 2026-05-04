---
name: salesforce-maps-setup
description: "Use when configuring Salesforce Maps (formerly MapAnything) — territory planning, route optimization, live tracking, geo-grid visualizations, and check-in/check-out workflows for Sales or Service field reps not on Field Service. Covers package installation order (Maps + Maps Advanced + Maps Routing/Live Tracking add-ons), the MapsTerritoryPlan / MapsAdvancedRoute / MapsLayer object family, base-data syncs (Geocoding and Routing services), and integration with Sales and Service Cloud records. Triggers: 'Salesforce Maps setup', 'MapAnything migration', 'territory planning by polygon', 'route optimization for sales reps', 'live tracking field reps', 'plot accounts on a map', 'check-in to the closest account'. NOT for Field Service Lightning territory and scheduling (use admin/fsl-scheduling-optimization-design and data/fsl-territory-data-setup) — Maps and FSL are different products. NOT for Consumer Goods Cloud retail visit planning (use admin/consumer-goods-cloud-setup) — RoutePlan/Visit objects are CG-specific. NOT for Tableau / CRM Analytics geo charts."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - Performance
tags:
  - salesforce-maps
  - mapanything
  - territory-planning
  - route-optimization
  - geocoding
  - live-tracking
  - field-sales
  - geolocation
  - check-in
triggers:
  - "we're setting up Salesforce Maps for our outside sales team"
  - "users want to plot accounts and opportunities on a map and route their day"
  - "migrating from MapAnything to Salesforce Maps after the rebrand"
  - "live tracking for field reps with breadcrumb trails"
  - "designing territory polygons and assigning accounts by geography"
  - "Maps base data sync is failing and accounts are not appearing on the map"
inputs:
  - "Salesforce Maps license type and add-on entitlement (Maps, Advanced, Live Tracking, Routing)"
  - "Source object(s) to plot: Account, Lead, Opportunity, Case, custom"
  - "Geocoding scope: which fields source the address; which records need backfilled geocodes"
  - "Territory model: polygon-based, ZIP-based, or hierarchical assignment rules"
  - "Mobile vs desktop usage profile (Maps Mobile app vs Lightning Maps component)"
outputs:
  - "Installed-package sequence and post-install configuration steps"
  - "Geocoding strategy: real-time vs scheduled, address-source field mapping"
  - "Base data import plan (Geocoding service + Maps Routing service)"
  - "Territory plan with polygon definitions and assignment rules"
  - "Live Tracking enablement plan (if licensed)"
  - "Integration plan with Sales/Service Cloud records (Visit, CheckIn) and Lightning page placement"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-04
---

# Salesforce Maps Setup

This skill activates when a practitioner is configuring **Salesforce Maps** (the rebranded MapAnything product, marketed as Maps for Sales Cloud and Maps for Service Cloud). It covers package installation, geocoding setup, territory polygon design, route optimization, and live tracking — all distinct from Field Service Lightning's territory model and from Consumer Goods Cloud's RoutePlan/Visit. Use it when the question is "how do I configure Salesforce Maps," not "how does FSL territorying work."

---

## Before Starting

Gather this context before working on anything in this domain:

- **Salesforce Maps is a separately licensed paid add-on** with its own managed package(s), not a free Sales Cloud feature. Confirm the customer holds Maps licenses (and which tier — Maps, Advanced, Live Tracking, Routing) before proposing setup work. The license tier dictates which features are available.
- Maps is **not Field Service**. FSL has its own territory model (`ServiceTerritory`, `ServiceTerritoryMember`, `MaintenancePlan`) optimized for dispatching work-order resources. Maps targets a broader Sales / Service field-rep persona — outside reps visiting accounts, distributing leads by geography, optimizing daily call sequences. Mixing the two object models leads to permission and licensing chaos.
- Maps is **not Consumer Goods Cloud**. CG Cloud's `RoutePlan` / `RoutePlanEntry` / `Visit` are CG-specific objects for retail-execution scenarios with cadence-driven store coverage. Maps is the general-purpose mapping product that can plot any object with geocode fields.
- Maps relies on **base data services** (Geocoding, Routing, Live Tracking, Mass Operations). These run as scheduled jobs after package install. Maps is not usable until at least the Geocoding service has run for your source objects.
- Geocoding is **synchronous on insert/update** only when the "Real-Time Geocoding" trigger is enabled per object; otherwise records geocode on the next scheduled batch. New users frequently file "accounts not on map" tickets because they didn't enable real-time geocoding.

---

## Core Concepts

### Package Installation Sequence

Salesforce Maps ships as multiple managed packages that must be installed in order:

1. **Salesforce Maps** (base) — geocoding, plotting, basic visualization, Lightning Maps component.
2. **Salesforce Maps Advanced** — territory planning with polygons, advanced visualizations, dataset-driven layers.
3. **Salesforce Maps Routing** (or Routing & Live Tracking add-on) — daily route optimization, multi-stop routing, ETA, live tracking, breadcrumbs.

The packages have inter-dependencies. Installing Routing without the base Maps package fails; installing Advanced without base also fails. Confirm the licensed tier before downloading any package.

After install, **post-install steps are required** even though the packages are managed. The most common forgotten step: assigning the Maps permission sets (`Salesforce Maps`, `Salesforce Maps Advanced`, `Salesforce Maps Routing`) to the actual users — package install does not auto-assign permissions to existing users.

### The Maps Object Family

Maps adds its own custom object set in the package namespace (`maps__` for the modern packages):

- `MapsTerritoryPlan__c` — top-level container for a territory model
- `MapsTerritory__c` — individual territory (polygon, ZIP cluster, or rule-based)
- `MapsLayer__c` — a styled, filterable visualization of records on the map
- `MapsLayerProperty__c` — per-record style properties
- `MapsRoute__c` (or `MapsAdvancedRoute__c`) — saved route plan with multi-stop sequence
- `LiveTrackingEvent__c` (Routing tier) — breadcrumb events for live tracking

Reports and SOQL against these are how you audit territory coverage, route adherence, and tracking integrity. They are not exposed to users by default — administrators query them.

### Territory Models: Polygon, ZIP, Hierarchical

Maps territories support three model types, each with tradeoffs:

| Model | When to use | Constraint |
|---|---|---|
| Polygon | Custom geo boundaries (e.g., a sales region drawn on the map) | Polygon vertices live in the package; not portable to other systems |
| ZIP / Postal | Coverage by US ZIP-3 / ZIP-5 or international postal | US-centric default; international ZIP support varies by country |
| Rule-based / Hierarchical | Assignment by Account fields (industry, AnnualRevenue) | Not strictly geographic; harder to visualize on the map |

Mixing models in one Territory Plan is supported but operationally fragile — a record matching both a polygon and a rule needs an explicit precedence configured in the Plan. Most production rollouts pick one model per Plan.

### Geocoding: The Silent Failure Mode

Maps cannot plot records without latitude/longitude. The Maps Geocoding service runs as a scheduled batch (default daily) and processes any record with a Maps-tracked address that has no geocode yet. Two failure modes that bite every implementation:

1. **Real-time geocoding is OFF by default per object.** New Accounts created today will not appear on the map until the next batch runs. Enable real-time geocoding under **Maps Setup → Configure Salesforce Maps → Geocoding** for every object users plot.
2. **Geocode failure for incomplete addresses fills the failure log silently.** A record with City but no State, or a Country code Maps doesn't recognize, is logged in `MapsGeocodeFailure__c`-style records (or the Maps "Geocoding Issues" list view) but does not raise a user-visible error. Audit failures weekly.

### Live Tracking Privacy And Permissions

Live Tracking emits breadcrumb events (a new record per location ping at the configured interval). Two operational realities:

1. **Privacy and labor compliance.** Live tracking is regulated in some jurisdictions (e.g., requires explicit employee consent in California, EU). The customer's HR or legal team must approve enablement per region before activating.
2. **Volume.** A 100-rep deployment with 5-minute pings during a 10-hour workday generates ~120,000 breadcrumb records per day. Plan an archival job (Big Object archive or scheduled hard delete after retention period) before turning Live Tracking on org-wide.

---

## Common Patterns

### Pattern 1: First-Time Maps Install For Outside Sales

**When to use:** Customer is licensing Salesforce Maps for the first time to map Accounts and Opportunities for an outside-sales team (no FSL, no Live Tracking).

**How it works:**

1. Install **Salesforce Maps** (base) into a sandbox first; do not install in production until validated.
2. Run the post-install wizard: configure the Geocoding service for `Account` (and `Lead`, if mapped) — set the address-source fields (BillingStreet/City/State/PostalCode/Country) and enable real-time geocoding.
3. Schedule the initial batch geocode for existing records (Setup → Maps → Geocoding → "Geocode All").
4. Validate ≥ 90% geocode success on the sample (50–100 records). Investigate failures: typically missing State or invalid Country.
5. Build a `MapsLayer__c` for "Open Opportunities" and place the Lightning Maps component on the home page or a dedicated tab.
6. Assign the `Salesforce Maps` permission set to the outside-sales profile cohort.
7. Train: 30-minute "How to plot, filter, and route your day from Maps" session before access goes live.

**Why not the alternative:** Activating Maps in production before sandbox validation is a high-volume DML mistake — the initial geocode batch can take hours and fail silently for records with bad addresses. Validate in sandbox; move to production only after the geocode failure rate is understood.

### Pattern 2: Polygon-Based Territory Plan For US Field Reps

**When to use:** Customer needs sales reps assigned to geographic territories drawn as custom polygons (not ZIP-aligned).

**How it works:**

1. Install **Salesforce Maps Advanced** alongside the base Maps package.
2. Create a `MapsTerritoryPlan__c` titled e.g. "FY26 US Sales Territories."
3. Use Maps Advanced UI to draw polygons on the map; each polygon becomes a `MapsTerritory__c` linked to the Plan.
4. Configure assignment rules: when an Account's geocode falls within a polygon, the named user/queue is set as the territory owner. Assignment runs as a scheduled batch (default nightly).
5. Validate via SOQL: `SELECT COUNT() FROM Account WHERE BillingState IN (...) AND Maps_Territory__c = NULL` should be near zero after the first batch.
6. Create reports on `MapsTerritory__c` for territory coverage health (account count, opportunity pipeline, white-space).

**Why not the alternative:** ZIP-based territories are simpler to maintain but cannot represent "the eastern half of New Jersey except this corridor" without splitting ZIPs. Polygon territories handle custom boundaries; the operational cost is the polygon-redraw work each fiscal-year boundary change.

### Pattern 3: Daily Route Optimization For Service Reps

**When to use:** Customer has Maps Routing tier; reps want a one-tap "optimize my day" for visiting 8–15 accounts.

**How it works:**

1. Confirm Maps Routing is licensed (separate from base + Advanced).
2. Configure routing parameters: max stops per day (typically 8–15), service-time-per-stop (e.g., 30 min), start/end location (home or office), travel mode (driving).
3. Build a Maps Filter for "Today's Visits" using a saved list view (e.g., Opportunities with `Visit_Date__c = TODAY AND Owner = $User`).
4. The user opens Maps, selects today's filter, taps "Optimize" — Maps Routing returns an ordered stop sequence and ETA per stop.
5. The user can save the sequence as a `MapsAdvancedRoute__c` for the day; route adherence (actual vs planned) reports off this object.

**Why not the alternative:** Manual day-routing with a spreadsheet costs reps 30–60 minutes per day. Maps Routing's optimization saves the time but does not consider non-Maps constraints (rep's standing meetings, physical health/break needs); always allow user override.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Outside sales reps need to plot accounts and opportunities on a map | Salesforce Maps base + Geocoding configured for those objects | Core Maps use case; doesn't need Advanced or Routing |
| Sales territories need custom polygon boundaries | Add Salesforce Maps Advanced; build polygon-based TerritoryPlan | Polygon support is Advanced-tier; base Maps cannot draw polygons |
| Reps need one-click "optimize my day" multi-stop routing | Add Maps Routing tier; configure routing parameters per profile | Routing engine is a separate licensed component |
| Need to track field-rep location continuously | Live Tracking add-on; HR/legal approval required first | Privacy and volume considerations dominate the technical work |
| Field service workforce with work-order dispatch | Use Field Service (FSL), not Maps | FSL has the dispatch engine; Maps is for sales-style coverage |
| Retail-execution store-cadence visits | Use Consumer Goods Cloud RoutePlan | CG Cloud has retail-specific objects; Maps is general-purpose |
| Customer is migrating from MapAnything | Confirm package version (modern Maps managed package); plan data migration of polygons and saved routes | MapAnything pre-rebrand has different namespace; not a no-op upgrade |
| 100k+ Accounts to geocode in initial batch | Run batch in a low-traffic window; monitor governor-limit consumption; expect partial completion | Batch geocoding can hit org daily API limit on the geocoding callout |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. Confirm license tier. Ask which Maps package(s) the customer holds (Maps, Advanced, Routing, Live Tracking). Match the work plan to the entitlement.
2. Identify source objects. Which records need to plot? (Account is most common; Lead, Opportunity, Case, custom objects also supported.) Capture the address-field mapping per object.
3. Install in sandbox first. Install the package(s) in install order (base → Advanced → Routing). Document any post-install wizard steps the customer's admin must run with their credentials.
4. Configure geocoding per source object. Set address-source fields, enable real-time geocoding, schedule the initial batch geocode. Validate ≥ 90% success on a sample.
5. Build the visualization. `MapsLayer__c` per record set (e.g., "Open Opportunities," "Active Accounts in Territory"); Lightning Maps component on home page or app tab.
6. (If polygon territories) Build TerritoryPlan + polygons in Maps Advanced. Configure assignment rules. Run the assignment batch and validate coverage.
7. (If routing) Configure routing parameters per cohort (max stops, service time, start/end). Train users on the Optimize button.
8. (If live tracking) HR/legal approval first. Configure ping interval and retention. Build the archival job before enablement.
9. Permission-set assignments. The Maps permission set must be assigned to the user cohort — package install does not assign it.
10. Validate end-to-end in sandbox before promoting to production. Run the full user workflow (open Maps → filter → plot → route) with a real cohort member.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Maps license tier is confirmed and matches the planned feature set
- [ ] Package install order followed (base → Advanced → Routing); each install validated in sandbox
- [ ] Geocoding configured per source object with address-field mapping documented
- [ ] Real-time geocoding enabled for objects where new records must plot immediately
- [ ] Initial batch geocode completed; failure rate is < 10% and failure causes are documented
- [ ] `MapsLayer__c` built for each record set users will plot
- [ ] Lightning Maps component placed on the appropriate home pages / app tabs
- [ ] Maps permission sets assigned to the user cohort (verify via SOQL count)
- [ ] (If polygon territories) Territory Plan built; assignment batch run; coverage validated
- [ ] (If routing) Routing parameters configured; optimization tested with real records
- [ ] (If live tracking) HR/legal approval recorded; ping interval and retention agreed; archival job scheduled
- [ ] Maps Geocode Failure log monitored weekly with an alerting threshold

---

## Salesforce-Specific Gotchas

(Detailed entries live in `references/gotchas.md`.)

1. **Real-time geocoding is OFF by default per object** — newly created records do not appear on the map until the next batch.
2. **Geocode failures are silent** — they accumulate in a log; users see "missing pin" without an error.
3. **Permission-set assignment is not automatic** — package install grants nothing to existing users.
4. **Maps and FSL territories are separate object models** — do not assume `ServiceTerritory` and `MapsTerritory__c` interoperate.
5. **Live Tracking volume can overwhelm storage** — plan archival before enablement.
6. **Polygon definitions are package-internal** — they cannot be exported to Tableau or non-Maps systems without manual extraction.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Package install plan | Ordered list of packages, sandbox-first sequence, post-install wizard steps |
| Geocoding configuration matrix | Per object: address fields, real-time on/off, batch schedule |
| `MapsLayer__c` definitions | Per record set: filter, style, fields shown in info-window |
| Territory Plan with polygons (if Advanced) | `MapsTerritoryPlan__c` + child `MapsTerritory__c` records |
| Routing configuration (if Routing) | Max stops, service time, start/end location, travel mode |
| Live Tracking enablement memo (if licensed) | HR/legal approval, ping interval, retention, archival design |
| Permission-set assignment runbook | Maps permission set(s) → user cohort mapping |

---

## Related Skills

- `admin/fsl-scheduling-optimization-design` — Field Service scheduling/optimization (the OTHER product; do not confuse with Maps)
- `data/fsl-territory-data-setup` — FSL service-territory polygon setup (also distinct from Maps territories)
- `architect/fsl-optimization-architecture` — overall FSL optimization architecture
- `admin/consumer-goods-cloud-setup` — CG Cloud RoutePlan/Visit (retail-execution; do not confuse with Maps)
- `integration/file-and-document-integration` — if Maps imports require bulk-load file integration
- `data/data-loader-best-practices` — for the initial batch import of geocoded data
