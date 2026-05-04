# Gotchas — Salesforce Maps Setup

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Real-Time Geocoding Is OFF By Default Per Object

**What happens:** A rep creates a new Account in Salesforce. The Account does not appear on the map. The rep refreshes Maps. Still missing. The Account only appears the next morning, after the scheduled batch geocode.

**When it bites you:** Day-of-go-live for outside-sales teams who create accounts during their day. The reps see the geocode lag and assume Maps is broken.

**How to handle:** In **Maps Setup → Configure Salesforce Maps → Geocoding**, enable "Real-Time Geocoding" for every object users create that needs immediate plotting. Caveat: real-time geocoding adds a small synchronous callout to insert/update; in extreme high-volume orgs, monitor governor-limit consumption.

---

## Gotcha 2: Geocode Failures Are Silent

**What happens:** A bulk import of 5,000 Accounts runs. The Maps geocode batch completes. 600 Accounts have no geocode and don't appear on the map. No error is raised; users see "my map is missing accounts."

**When it bites you:** Initial-load and any subsequent CSV import that injects messy address data.

**How to handle:** Maps writes geocode failures to a managed-package log object (typically a "Geocoding Issues" list view in the Maps app). Schedule a weekly review of this log. Common failure causes: missing State/Province field, free-text Country instead of ISO code, PO Box-only address (geocodes to ZIP centroid, which the team may not consider a "real" plot). Build an alerting threshold (e.g., > 5% failure rate triggers an admin email).

---

## Gotcha 3: Package Install Doesn't Assign Permission Sets

**What happens:** Admin installs Salesforce Maps in production, enables the geocode batch, configures layers. Reps log in: no Maps tab, no Maps component visible. Admin reports "the package didn't install correctly."

**When it bites you:** Day-of-go-live, immediately. The package install creates the permission sets (`Salesforce Maps`, `Salesforce Maps Advanced`, `Salesforce Maps Routing`) but does not assign them to any user.

**How to handle:** After package install, the deployment runbook's next step is **PermissionSetAssignment** records for the user cohort. This is easy to script:

```bash
sf data create record --sobject PermissionSetAssignment \
  --values "AssigneeId=<userId> PermissionSetId=<mapsPSId>" \
  --target-org prod
```

Or build a permission-set group that bundles the Maps permission sets with the cohort's other permission sets, then assign the group.

---

## Gotcha 4: Maps Territories And FSL ServiceTerritories Are Different Object Models

**What happens:** A customer with both products assumes "territory" is the same concept. They build automation that copies `MapsTerritory__c` changes to `ServiceTerritory` (or vice versa). The first time a polygon edit triggers, the FSL dispatch board breaks because `ServiceTerritory.Address` was overwritten with polygon-vertex JSON.

**When it bites you:** Orgs with both FSL and Maps that try to unify the two without architectural boundary discipline.

**How to handle:** Treat the two as separate products with different personas. FSL = work-order dispatch to scheduled resources. Maps = outside-rep plotting and routing. Document the persona boundary; do not write automation that crosses it. If the customer truly needs unified territory governance, the unification happens in a custom mapping table — not in the package objects.

---

## Gotcha 5: Live Tracking Volume Can Overwhelm Storage

**What happens:** A 200-rep deployment enables Live Tracking with 5-minute pings during a 10-hour workday. Within 90 days, the org has 6 million breadcrumb records. Storage limits start triggering reminders; reports against the breadcrumb object slow to a crawl.

**When it bites you:** Several months post-Live-Tracking enablement, when the volume catches up to org limits.

**How to handle:** Before enabling Live Tracking, plan archival:
- Define retention (e.g., 90 days hot, then archive to a Big Object).
- Schedule a Batch Apex job that hard-deletes breadcrumbs older than the retention window after archive.
- For compliance retention longer than 90 days, use Big Objects (`MapsLiveTrackingArchive__b`) with the index keyed on `(UserId, EventDate)`.
- Increase the ping interval (e.g., 15 min instead of 5 min) if the use case allows; volume scales linearly.

---

## Gotcha 6: Polygon Definitions Are Package-Internal And Hard To Export

**What happens:** Leadership asks "show me a Tableau dashboard of pipeline by territory polygon." You discover that `MapsTerritory__c.maps__Polygon__c` stores the polygon as a package-encoded string that Tableau cannot interpret natively.

**When it bites you:** Reporting and analytics workstreams that assume Maps data is queryable like any other Salesforce object.

**How to handle:** For non-Maps consumers (Tableau, CRM Analytics, external BI), build an export job that converts polygon data to GeoJSON via a custom Apex method. The Maps Advanced UI can also export to KML/Shapefile for one-shot use. Plan the export pipeline before promising "we'll just show territory polygons in Tableau."

---

## Gotcha 7: Modern Maps And Legacy MapAnything Have Different Namespaces

**What happens:** A customer on legacy MapAnything (`ma__` namespace) "upgrades" by installing modern Salesforce Maps (`maps__` namespace), assuming Salesforce will migrate data. They don't. Both packages are now installed; reports break; users are confused which app to open.

**When it bites you:** During the rebrand-era migrations (2022 onward). Many orgs still run on the legacy package.

**How to handle:** Migration is a planned project, not an in-place upgrade. Run both packages in parallel during the migration window; export polygons and saved routes from the legacy package; import into the modern package; cut over permissions; uninstall the legacy package after a stabilization period. Plan 4–8 weeks for a 200+ territory migration.
