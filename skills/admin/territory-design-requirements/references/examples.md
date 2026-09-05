# Examples — Territory Design Requirements

## Example 1: Geographic Coverage Model for a Mid-Market Sales Org

**Context:** A 40-rep mid-market sales organization covers the continental United States. Reps own a state or group of states. The VP of Sales wants territory-based forecasting. No named account overlay exists yet.

**Problem:** Without documented design requirements, the ETM administrator builds a flat list of 50 state-level territories with no hierarchy. Forecast rollups cannot aggregate by region, and the VP cannot see a North/South/East/West breakdown. Reps in low-account-density states have almost no pipeline, while California has too many accounts for one rep.

**Solution:**

Gather and document the following requirements before any configuration:

```
Coverage model: Geographic
Hierarchy levels: 3
  Level 1: National (1 territory — forecast root)
  Level 2: Region (4 territories: West, Central, Northeast, Southeast)
  Level 3: Rep Territory (36 territories — individual rep ownership by state or state cluster)

Territory types:
  - "Geographic" (priority: 10)

Assignment rule criteria (examples — leaf level):
  West/California: BillingState = 'CA'
  West/Pacific Northwest: BillingState IN ('OR', 'WA', 'AK', 'HI')
  Central/Texas: BillingState = 'TX'
  ... (one rule set per leaf territory)

Catch-all: "Unassigned US" territory at National level for accounts with blank BillingState

Coverage ratios (metric defined so it can be recomputed):
  territories / users        = 36 / 40 = 0.9   (most reps own exactly one territory)
  accounts per leaf          = 40 - 2,100      (the number that actually decides)
  Action: the ratio is not the finding. Merge the six leaf territories under
          200 accounts into their neighbours, and split the two above 1,500.
          Re-check accounts-per-leaf, not the headcount ratio.
```

**Why it works:** The three-level hierarchy enables regional rollups in territory forecasting. Sizing on accounts per leaf territory, rather than on a headcount ratio, is what corrects both the starved and the overloaded nodes. The catch-all territory ensures no accounts fall outside coverage and go missing from forecasts.

Before sign-off, run the density numbers the design is claiming rather than accepting them:

```sql
-- Accounts that WOULD land in each proposed leaf territory, per the draft criteria.
-- Run this in the current org against the criteria fields, before any territory exists.
SELECT BillingState, COUNT(Id) accounts
FROM   Account
WHERE  BillingState != null
GROUP BY BillingState
ORDER BY COUNT(Id) DESC

-- And the accounts no proposed leaf rule would match, which size the catch-all.
SELECT COUNT(Id)
FROM   Account
WHERE  BillingState = null
OR     BillingCountry = null
```

---

## Example 2: Hybrid Model — Geographic Primary Plus Named Account Overlay

**Context:** A SaaS company has 25 geographic reps and 5 enterprise/strategic reps. The enterprise reps own a defined list of 80 named accounts regardless of where those accounts are located. Some named accounts are in territories covered by geographic reps — both reps need access.

**Problem:** An admin attempts to handle named accounts by reassigning account ownership to the enterprise reps. This removes the geographic rep from the account, breaks pipeline attribution, and causes geographic territory assignment rules to stop matching those accounts. Named account reps now have to manually share records individually.

**Solution:**

Document the hybrid design requirements:

```
Coverage model: Hybrid (Geographic Primary + Named Account Overlay)

Territory types (priority is a unique integer; the HIGHEST wins OTA):
  - "Geographic" (priority: 10) — primary coverage
  - "Named Account" (priority: 20) — overlay; higher integer wins OTA

Geographic hierarchy: unchanged (Country -> Region -> Rep Territory)

Named Account territories:
  - One territory per enterprise rep (5 territories)
  - Assignment: manual account-to-territory assignment for the 80 named accounts
    (rule-based named account matching is not recommended — list changes quarterly)

Access behavior:
  - Named account reps gain Read/Write access to named accounts via territory membership
  - Geographic reps retain access via their geo territory membership
  - Both reps appear as territory members on the account — no account ownership change

Opportunity territory assignment:
  - Named Account type priority (20) beats Geographic type priority (10)
    ("the account-assigned territory whose territory type priority is highest
      is then assigned to the opportunity" - Territory2Type > priority)
  - Named account opps roll into enterprise rep territory forecast, not geo forecast
  - Constraint this design must hold: no account may sit on TWO Named Account
    territories, because two territories of the same type assign NO territory
    to the opportunity at all

Coverage ratios:
  - Geographic: 25 territories / 25 users = 1.0 territories per user at leaf level
    Recommendation: confirm each geo territory has sufficient account volume;
    consolidate if any territory has fewer than 20 accounts
  - Named account: 5 territories / 5 users = 1.0 (acceptable for an overlay layer)
```

**Why it works:** Territory membership is additive — both reps gain access without changing account ownership, and the two assignment paths stay distinguishable afterwards because a manual assignment lands as `ObjectTerritory2Association.AssociationCause = Territory2Manual` while a rule-driven one lands as `Territory2AssignmentRule`. The higher priority integer on the Named Account type routes named-account opportunities to the enterprise rep's forecast. Manual assignment for the named account list is preferred because the list changes quarterly, making rule-based matching expensive to maintain.

---

## Anti-Pattern: Mirroring the Role Hierarchy in Territory Design

**What practitioners do:** The admin exports the role hierarchy (SVP -> VP -> Director -> Manager -> Rep) and creates one territory per role node, naming territories after roles: "VP West," "Director West," "Rep California."

**What goes wrong:**
- The territory hierarchy now has 6+ levels, matching the management org chart rather than the forecast rollup or account coverage structure.
- When a manager changes roles, territory structure must be reorganized to match.
- Territory names reference people, not coverage areas — when reps are reassigned, territory names become misleading.
- Forecast rollups aggregate by territory node, not by person, so "VP West" territory rollup includes all accounts under that territory node regardless of which VP currently holds it.

**Correct approach:** Design territory hierarchy around the geographic or account segmentation structure, not the management org chart. Coverage nodes (West, Northeast, Southwest) should be stable; user membership assignments are what changes when reps are reassigned. The hierarchy should still reflect the management structure for forecast rollup purposes, but territory names should reflect coverage area, not individual people.
