# LLM Anti-Patterns — FSL Territory Data Setup

Common mistakes AI coding assistants make when generating or advising on FSL Territory Data Setup.

## Anti-Pattern 1: Trying to Load Polygons via Data Loader

**What the LLM generates:** Instructions to add a polygon field to ServiceTerritory and load boundary coordinates via Data Loader CSV.

**Why it happens:** LLMs extrapolate from standard Salesforce geolocation fields without knowing that FSL polygon boundaries are in the managed package FSL__Polygon__c object with a specialized import mechanism.

**Correct pattern:** Use Setup > Field Service > Service Territories > Import Polygon to upload KML files. For Apex-based creation, use `FSL.PolygonUtils` from a Queueable, one territory per job.

**Detection hint:** Any instruction to add a geometry/polygon column to ServiceTerritory or load it via Data Loader is wrong.

---

## Anti-Pattern 2: Missing EffectiveStartDate on ServiceTerritoryMember

**What the LLM generates:** ServiceTerritoryMember CSV template without an EffectiveStartDate column, or insertion code that omits the field.

**Why it happens:** LLMs treat the field as optional because many other junction objects don't require start dates.

**Correct pattern:** EffectiveStartDate is required on ServiceTerritoryMember. Always include it in load CSVs. Default to the go-live date if no historical date is available.

**Detection hint:** Any ServiceTerritoryMember load example without `EffectiveStartDate` is incomplete.

---

## Anti-Pattern 3: Ignoring TerritoryType — Defaulting All Members to Primary

**What the LLM generates:** ServiceTerritoryMember loads with only ServiceTerritoryId, ServiceResourceId, and EffectiveStartDate — omitting TerritoryType.

**Why it happens:** LLMs don't model the business impact of TerritoryType on scheduling preference and resource classification.

**Correct pattern:** Explicitly set TerritoryType for every ServiceTerritoryMember. Primary = home territory; Secondary = overflow or multi-territory resource; Relocation = time-boxed transfer between territories.

**Detection hint:** Any ServiceTerritoryMember bulk load without explicit TerritoryType mapping should be questioned.

---

## Anti-Pattern 4: Loading All Territory Levels in One Batch

**What the LLM generates:** A single Data Loader operation for all ServiceTerritory records (parents and children mixed).

**Why it happens:** LLMs don't model the parent-before-child insert order constraint.

**Correct pattern:** Run three separate loads: top-level territories (no parent), mid-level territories, leaf territories. Verify zero errors at each step.

**Detection hint:** A single-batch ServiceTerritory load without any discussion of hierarchy order is risky.

---

## Anti-Pattern 5: Designing Territories Over 50 Resources

**What the LLM generates:** Territory design that aggregates resources into regional territories for administrative convenience, resulting in 100+ resources per territory.

**Why it happens:** LLMs optimize for administrative simplicity without knowing the FSL optimization engine's per-territory performance limits.

**Correct pattern:** Design territories with a maximum of 50 resources and 1,000 SAs/day. Use sub-territories for geographic segmentation if needed. Document this constraint as an architectural requirement.

**Detection hint:** Any territory design that places more than 50 resources in a single territory without noting the optimization performance impact is missing a key constraint.
