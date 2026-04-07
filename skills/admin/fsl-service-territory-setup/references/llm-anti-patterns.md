# LLM Anti-Patterns — FSL Service Territory Setup

Common mistakes AI coding assistants make when generating or advising on FSL Service Territory Setup.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Confusing ServiceTerritory (FSL) with Territory2 (ETM)

**What the LLM generates:** Instructions to navigate to "Setup > Territory Models" or SOQL queries against `Territory2`, `UserTerritory2Association`, or `ObjectTerritory2Association` when the user asked about Field Service service territories.

**Why it happens:** Both objects are called "territories" in Salesforce. Training data contains substantial documentation for both, and ETM documentation is widely referenced. LLMs retrieve both and blend the guidance without distinguishing which product applies.

**Correct pattern:**

```
FSL territories use: ServiceTerritory, ServiceTerritoryMember, ServiceTerritoryPolygon
ETM territories use: Territory2, UserTerritory2Association, ObjectTerritory2Association

Setup path for FSL: Setup > Field Service > Service Territories
Setup path for ETM: Setup > Territories > Territory Models

SOQL for FSL: SELECT Id, Name FROM ServiceTerritory WHERE IsActive = true
SOQL for ETM: SELECT Id, Name FROM Territory2
```

**Detection hint:** Any mention of `Territory2`, `TerritoryModel`, `UserTerritory2Association`, or "Territory Models" in the context of a Field Service territory question is a sign of ETM bleed.

---

## Anti-Pattern 2: Creating Relocation Memberships Without EffectiveStartDate and EffectiveEndDate

**What the LLM generates:** A `ServiceTerritoryMember` insert with `MemberType = 'Relocation'` but without `EffectiveStartDate` or `EffectiveEndDate` fields populated.

**Why it happens:** LLMs model Relocation as a variant of Primary or Secondary and treat the date fields as optional metadata rather than scheduling-critical inputs. The Salesforce API does not reject the record, reinforcing the assumption that dates are optional.

**Correct pattern:**

```apex
ServiceTerritoryMember stm = new ServiceTerritoryMember();
stm.ServiceTerritoryId = relocTerrId;
stm.ServiceResourceId = technicianResourceId;
stm.MemberType = 'Relocation';
stm.EffectiveStartDate = Date.today();           // required for routing
stm.EffectiveEndDate = Date.today().addDays(30); // required for routing
insert stm;
```

**Detection hint:** Any `MemberType = 'Relocation'` insert or upsert that does not include both `EffectiveStartDate` and `EffectiveEndDate` is incorrect.

---

## Anti-Pattern 3: Assuming Secondary Membership Satisfies Hard Boundary Work Rules

**What the LLM generates:** "Add the technician as a Secondary member of the territory so they can receive appointments there" — presented as equivalent to Primary membership for scheduling purposes.

**Why it happens:** LLMs generalize from the concept that Secondary membership makes a resource "available" in a territory, without knowing that the Hard Boundary work rule specifically excludes Secondary members. This nuance is buried in FSL scheduling policy documentation rather than in the object reference.

**Correct pattern:**

```
For Hard Boundary compliance, a technician must have:
  MemberType = 'Primary'    (exactly one active per resource)
  or
  MemberType = 'Relocation' (with valid EffectiveStartDate and EffectiveEndDate)

Secondary membership alone does NOT satisfy Hard Boundary.
A technician with only Secondary membership in a territory will not appear
as a scheduling candidate when Hard Boundary is active.
```

**Detection hint:** If the recommendation is to use Secondary membership as the sole basis for scheduling eligibility in a territory where Hard Boundary is configured, it is incorrect.

---

## Anti-Pattern 4: Generating SOQL That Checks ServiceTerritory.IsActive Without Filtering Memberships

**What the LLM generates:** Queries that check `ServiceTerritory.IsActive = true` to find active territories but do not filter `ServiceTerritoryMember` records by `EffectiveStartDate <= TODAY AND (EffectiveEndDate >= TODAY OR EffectiveEndDate = null)`.

**Why it happens:** LLMs focus on the top-level object's `IsActive` flag and overlook that membership records have their own effective date range. A territory can be active while having many stale or future-dated members that should not be included in current scheduling counts.

**Correct pattern:**

```soql
SELECT Id, ServiceTerritoryId, ServiceResourceId, MemberType
FROM ServiceTerritoryMember
WHERE ServiceTerritory.IsActive = true
  AND EffectiveStartDate <= TODAY
  AND (EffectiveEndDate >= TODAY OR EffectiveEndDate = null)
```

**Detection hint:** Any ServiceTerritoryMember query that checks territory `IsActive` but does not include date range filters on the membership itself is likely to return stale records.

---

## Anti-Pattern 5: Advising a Single OperatingHours Record for Territories Across Multiple Time Zones

**What the LLM generates:** "Create one OperatingHours record for '8am-5pm business hours' and link it to all your territories to keep configuration simple."

**Why it happens:** LLMs optimize for apparent simplicity and do not account for the FSL constraint that the `TimeZone` field on `OperatingHours` governs all child TimeSlots. The limitation is not obvious from the object schema and is only documented in FSL setup guides.

**Correct pattern:**

```
Create separate OperatingHours records per time zone:

OperatingHours: Pacific Business Hours  | TimeZone: America/Los_Angeles
OperatingHours: Eastern Business Hours  | TimeZone: America/New_York
OperatingHours: Central Business Hours  | TimeZone: America/Chicago

Link each ServiceTerritory to the OperatingHours matching its geographic time zone.
Do NOT share a single OperatingHours record across territories in different time zones.
```

**Detection hint:** Any advice to share a single OperatingHours record across territories without confirming they are all in the same time zone is a potential source of scheduling window errors.
