# Gotchas — FSL Service Territory Setup

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Hard Boundary Work Rule Ignores Secondary Memberships

**What happens:** When the Hard Boundary work rule is active in the scheduling policy, the optimizer and dispatcher only consider technicians with `MemberType = Primary` or `MemberType = Relocation` in the target territory. Technicians with only a `MemberType = Secondary` membership are excluded from scheduling in that territory — silently, with no error message.

**When it occurs:** Any time a scheduling policy uses the Hard Boundary work rule and technicians are assigned as Secondary members expecting full eligibility. This frequently surfaces during user acceptance testing when technicians do not appear as candidates in the Dispatcher Console.

**How to avoid:** Audit all territory member records before go-live. Confirm that each technician who needs to be schedulable in a territory has a Primary (or Relocation for temporary assignments) membership. Use Secondary memberships only for territories where the Hard Boundary rule is not in effect or where the technician's eligibility is genuinely advisory.

---

## Gotcha 2: Relocation Memberships Without Dates Are Silently Ignored

**What happens:** A `ServiceTerritoryMember` with `MemberType = Relocation` that is missing `EffectiveStartDate` or `EffectiveEndDate` is not evaluated by the routing engine. No validation error is thrown during save. The technician simply does not appear as a scheduling candidate for the relocation territory during the intended period.

**When it occurs:** Data migrations or bulk inserts that copy existing Primary or Secondary membership records and change the `MemberType` to Relocation without setting date fields. Also occurs when administrators create Relocation memberships via the UI and skip the date fields.

**How to avoid:** Enforce date population at the application layer. When inserting Relocation memberships via data loader or API, add a pre-load validation step that checks `EffectiveStartDate IS NOT NULL AND EffectiveEndDate IS NOT NULL` for all Relocation records. Consider adding a validation rule to the ServiceTerritoryMember object if the org allows custom validation on that junction object.

---

## Gotcha 3: Duplicate Active Primary Memberships Are Not Blocked by the API

**What happens:** Salesforce allows creating a second active `MemberType = Primary` membership for the same ServiceResource via the API, even though only one is valid for scheduling. The routing engine's behavior with two active Primary memberships is undefined and can produce unpredictable scheduling results.

**When it occurs:** Bulk data loads that create or update territory member records in batches, particularly when migrating from one territory to another. The old Primary membership is not end-dated before the new one is created, leaving both active simultaneously.

**How to avoid:** Before inserting a new Primary membership for a resource, query for existing active Primary memberships (`MemberType = 'T'` in the API, or `MemberType = Primary` in SOQL on the picklist value). End-date the existing Primary membership before activating the new one. Build this check into any migration or integration script that touches ServiceTerritoryMember.

---

## Gotcha 4: FSL ServiceTerritory and Sales Cloud Territory2 Are Completely Different Objects

**What happens:** Practitioners or LLMs conflate Field Service `ServiceTerritory` (the FSL scheduling object) with `Territory2` (the Sales Cloud Enterprise Territory Management object). Configuration steps, permission sets, SOQL queries, and API names are entirely different. Actions taken on one have no effect on the other.

**When it occurs:** When searching setup guides or asking AI assistants about "service territories in Salesforce" without specifying FSL. ETM documentation is prominent and may surface before FSL-specific content.

**How to avoid:** Always specify "Field Service Lightning" when searching for territory setup documentation. In SOQL, FSL territories use the `ServiceTerritory` object; ETM territories use `Territory2`. In Setup, FSL territories are under Field Service > Service Territories. ETM territories are under Territories > Territory Models.

---

## Gotcha 5: OperatingHours Time Zone Applies to All TimeSlots — Cannot Mix Time Zones

**What happens:** The `TimeZone` field on `OperatingHours` applies to every `TimeSlot` child record in that record. If a territory spans a time zone boundary, all TimeSlots are interpreted in the single time zone of the parent OperatingHours record, causing appointments near the boundary to be scheduled at the wrong local time.

**When it occurs:** When a single `OperatingHours` record is shared between territories in different time zones, or when a territory is initially configured in one time zone and later expanded to cover a neighboring time zone.

**How to avoid:** Create separate `OperatingHours` records for each distinct time zone in the territory portfolio. Do not reuse an OperatingHours record across territories in different time zones even if the business hours appear identical.
