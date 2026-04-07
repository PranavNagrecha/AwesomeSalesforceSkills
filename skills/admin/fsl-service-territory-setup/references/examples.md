# Examples — FSL Service Territory Setup

## Example 1: Basic Territory with Operating Hours and Primary Members

**Context:** A utility company is deploying Field Service for the first time. They have a "Southwest District" covering three cities, with 12 technicians who work Monday–Friday 07:00–16:00 Pacific Time.

**Problem:** Without correctly linked operating hours and Primary memberships, the scheduling optimizer cannot assign appointments in this territory — it has no open time windows to work with and no eligible resources.

**Solution:**

Step 1 — Create the OperatingHours record via Setup or data load:

```
Object: OperatingHours
Name: Southwest District Hours
TimeZone: America/Los_Angeles
```

Step 2 — Create TimeSlot child records for each working day:

```
Object: TimeSlot
OperatingHoursId: [id from step 1]
DayOfWeek: Monday
StartTime: 07:00
EndTime: 16:00
Type: Normal
```
Repeat for Tuesday through Friday.

Step 3 — Create the ServiceTerritory:

```
Object: ServiceTerritory
Name: Southwest District
OperatingHoursId: [id from step 1]
IsActive: true
```

Step 4 — Create ServiceTerritoryMember records for each technician:

```
Object: ServiceTerritoryMember
ServiceTerritoryId: [id from step 3]
ServiceResourceId: [technician's ServiceResource id]
MemberType: Primary
EffectiveStartDate: [today or go-live date]
EffectiveEndDate: [leave blank for open-ended]
```

**Why it works:** The scheduler requires a valid `OperatingHoursId` on the territory to know when appointments can be booked. The Primary membership is the routing engine's reference point for travel time calculations originating from the technician's home base. Without Primary memberships, the Hard Boundary work rule (if active) also rejects these technicians as candidates.

---

## Example 2: Territory Hierarchy with Parent-Child for Regional Structure

**Context:** A national HVAC company organizes its field operations into three regions (East, Central, West), each containing multiple local dispatch zones. Leadership wants region-level reporting while technicians are scheduled at the local zone level.

**Problem:** Without a `ParentTerritoryId` relationship, territories are flat and there is no way to aggregate dispatching data by region in standard Salesforce reporting without workarounds.

**Solution:**

Step 1 — Create the parent (region-level) territories first, with no parent of their own:

```
Object: ServiceTerritory
Name: East Region
OperatingHoursId: [shared or region-level hours]
IsActive: true
ParentTerritoryId: [blank]
```
Repeat for Central Region and West Region.

Step 2 — Create child (local zone) territories pointing to the correct parent:

```
Object: ServiceTerritory
Name: Boston Metro
OperatingHoursId: [Boston-specific hours with Eastern Time zone]
IsActive: true
ParentTerritoryId: [East Region territory id]
```

Step 3 — Assign technicians to local territories only:

```
Object: ServiceTerritoryMember
ServiceTerritoryId: [Boston Metro id]
ServiceResourceId: [technician id]
MemberType: Primary
EffectiveStartDate: [go-live date]
```

Step 4 — Use reports filtered on `ServiceTerritory.ParentTerritoryId = East Region` to aggregate metrics across Boston Metro, New York Metro, and Philadelphia Metro.

**Why it works:** `ParentTerritoryId` creates a traversable hierarchy that standard Salesforce reports can filter and group by. Keeping operating hours at the local level allows each zone to have its own time zone and schedule, which is necessary when a region spans multiple time zones. Technicians assigned only to local territories are still visible in regional reporting via the parent lookup.

---

## Anti-Pattern: Assigning All Members as Secondary to Avoid the "One Primary" Constraint

**What practitioners do:** To simplify data loading or avoid conflict errors, teams create all `ServiceTerritoryMember` records with `MemberType = Secondary`, leaving no Primary memberships.

**What goes wrong:** The Hard Boundary work rule (if configured in the scheduling policy) only considers technicians with Primary or Relocation memberships in the target territory. Technicians with Secondary memberships are excluded from work in that territory when Hard Boundary is active, even though they are listed as members. Additionally, the routing engine has no travel origin reference for technicians without a Primary territory, producing inaccurate travel time estimates for scheduling.

**Correct approach:** Assign each technician exactly one Primary territory membership representing their home dispatch zone. Use Secondary memberships only for territories where the technician occasionally provides coverage. Use Relocation memberships with explicit date ranges for temporary assignments to a different zone.
