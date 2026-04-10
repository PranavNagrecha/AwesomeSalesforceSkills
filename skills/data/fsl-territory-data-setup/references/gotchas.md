# Gotchas — FSL Territory Data Setup

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Polygons Are in the FSL Managed Package — Not Standard Objects

**What happens:** Teams try to use Data Loader or Bulk API to load polygon boundary data into ServiceTerritory, expecting a geometry or polygon field. No such field exists on the standard ServiceTerritory object.

**When it occurs:** Any implementation requiring geographic boundary-based territory lookup for appointment booking.

**How to avoid:** Polygon boundaries are stored in `FSL__Polygon__c` (managed package object). Import them via Setup > Field Service > Service Territories > Import Polygon using KML files. Apex creation via `FSL.PolygonUtils` is available but must be done queueable per territory due to governor limits.

---

## Gotcha 2: TerritoryType Defaults to Primary — Misclassifying Contractors

**What happens:** When `TerritoryType` is omitted from a ServiceTerritoryMember insert, Salesforce defaults to `Primary`. Contractors who should be Secondary members are treated as Primary, affecting scheduling preference and territory ownership calculations.

**When it occurs:** Bulk loads that don't explicitly map TerritoryType from source data.

**How to avoid:** Always explicitly set `TerritoryType` to Primary, Secondary, or Relocation. Never rely on the default. Map source system contractor vs. employee designations to TerritoryType values before loading.

---

## Gotcha 3: Territory Polygons Crossing Timezone Boundaries Break Appointment Booking

**What happens:** A service territory whose polygon boundary spans a timezone line (e.g., covers both Eastern and Central time zones) causes `Book Appointment` to return time slots that don't correspond to local customer time. The OperatingHours timezone governs slot calculation, but the polygon's geographic center may be in a different timezone.

**When it occurs:** Territory design in regions with geographic timezone boundaries (US Mountain/Pacific, Central/Eastern border areas).

**How to avoid:** Ensure service territory polygon boundaries do not cross timezone lines. If coverage spans a timezone, create separate territories per timezone, each with its own OperatingHours record specifying the correct timezone.

---

## Gotcha 4: ServiceTerritoryMember EffectiveStartDate Is Required

**What happens:** Inserting a ServiceTerritoryMember record without `EffectiveStartDate` throws `REQUIRED_FIELD_MISSING: Required fields are missing: [EffectiveStartDate]`.

**When it occurs:** Migration loads that assume EffectiveStartDate is optional because UI-based territory member addition does not always surface this field prominently.

**How to avoid:** Always include EffectiveStartDate in ServiceTerritoryMember load CSVs. Use the go-live date or a historical start date from source data.

---

## Gotcha 5: Exceeding 50 Resources Per Territory Causes Optimization Timeout

**What happens:** FSL Global optimization has a 2-hour hard timeout. Territories with more than 50 assigned resources and 1,000+ daily SAs consistently exceed this timeout, resulting in partial optimization or silent cancellation.

**When it occurs:** Territory design that aggregates large numbers of resources into a single broad territory for administrative simplicity.

**How to avoid:** Design territories to stay under 50 resources and 1,000 SAs/day. Split large territories into geographic sub-territories if needed. Optimization runs per territory — smaller territories run faster and more reliably.
