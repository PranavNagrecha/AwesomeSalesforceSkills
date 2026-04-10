# Examples — FSL Territory Data Setup

## Example 1: Bulk Territory Hierarchy Load with Operating Hours

**Context:** A national utility company sets up FSL for 200 service territories organized in a 3-level hierarchy (Region → District → Territory). Each territory has unique operating hours, and the data team needs to load all territory records before going live.

**Problem:** The team tries to load all 200 ServiceTerritory records in a single batch, including both parent and child territories. Child territory records fail because their parent territories don't exist yet.

**Solution:**
1. Load OperatingHours records first (one per unique schedule pattern — e.g., "M-F 8-5 ET", "M-Sa 7-6 PT"):
   ```
   CSV headers: Name, TimeZone, Legacy_OH_Id__c
   Data Loader: upsert on Legacy_OH_Id__c
   ```
2. Load TimeSlot records referencing OperatingHours External IDs
3. Load Region (top-level) ServiceTerritory records with `ParentTerritory__c = null`
4. Load District ServiceTerritory records with `ParentTerritoryId` mapped to Region External IDs
5. Load Territory (leaf) records with `ParentTerritoryId` mapped to District External IDs

**Why it works:** Each level loads after its parent exists. Data Loader upsert with External IDs on both sides of the parent lookup ensures re-runability.

---

## Example 2: ServiceTerritoryMember with Relocation

**Context:** A field service organization has technicians who occasionally transfer between territories. During migration, they need to preserve the historical assignment dates so that historical appointments report under the correct territory.

**Problem:** The migration team deletes and re-creates ServiceTerritoryMember records when a technician transfers. Historical ServiceAppointment records that referenced the old territory association now show incorrect territory data in reports.

**Solution:**
1. Preserve the old ServiceTerritoryMember record with `EffectiveEndDate` = transfer date
2. Create a new ServiceTerritoryMember record for the destination territory with `EffectiveStartDate` = transfer date + 1 day and `TerritoryType` = Primary
3. Both records coexist in the database — the scheduling engine uses the record with `EffectiveStartDate <= today AND (EffectiveEndDate >= today OR EffectiveEndDate = null)`

**Why it works:** ServiceTerritoryMember records are time-boxed via effective dates. The historical record is preserved for reporting while the new record governs active scheduling.

---

## Anti-Pattern: Loading Child Territories Before Parent Territories

**What practitioners do:** Include all ServiceTerritory records (parent and child) in a single Data Loader batch sorted alphabetically instead of by hierarchy level.

**What goes wrong:** Child territory records that reference parent territories not yet loaded fail with `FIELD_INTEGRITY_EXCEPTION: ParentTerritoryId: id value of incorrect type`. The load fails for all child records, requiring resorting and re-running.

**Correct approach:** Sort the ServiceTerritory CSV by hierarchy depth before loading, or run three separate loads: one for top-level (no parent), one for mid-level, one for leaf. Verify each batch completes before proceeding.
