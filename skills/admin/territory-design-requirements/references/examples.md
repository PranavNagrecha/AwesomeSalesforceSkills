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

User-to-territory ratio: 40 users / 36 leaf territories = 1.1:1
  Action: merge lowest-density state clusters to reach ~3:1;
          target 13-14 leaf territories with 2-3 reps each
```

**Why it works:** The three-level hierarchy enables regional rollups in territory forecasting. Merging low-density states into clusters corrects the sub-1:1 ratio. The catch-all territory ensures no accounts fall outside coverage and go missing from forecasts.

---

## Example 2: Hybrid Model — Geographic Primary Plus Named Account Overlay

**Context:** A SaaS company has 25 geographic reps and 5 enterprise/strategic reps. The enterprise reps own a defined list of 80 named accounts regardless of where those accounts are located. Some named accounts are in territories covered by geographic reps — both reps need access.

**Problem:** An admin attempts to handle named accounts by reassigning account ownership to the enterprise reps. This removes the geographic rep from the account, breaks pipeline attribution, and causes geographic territory assignment rules to stop matching those accounts. Named account reps now have to manually share records individually.

**Solution:**

Document the hybrid design requirements:

```
Coverage model: Hybrid (Geographic Primary + Named Account Overlay)

Territory types:
  - "Geographic" (priority: 10) — primary coverage
  - "Named Account" (priority: 5) — overlay; lower integer = higher priority for OTA

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
  - Named Account type priority (5) overrides Geographic type priority (10)
  - Named account opps roll into enterprise rep territory forecast, not geo forecast

User-to-territory ratio:
  - Geographic: 25 users / 25 geo rep territories = 1:1 at leaf level
    Recommendation: confirm each geo territory has sufficient account volume;
    consolidate if any territory has fewer than 20 accounts
  - Named account: 5 users / 5 named account territories = 1:1 (acceptable for overlay)
```

**Why it works:** Territory membership is additive — both reps gain access without changing account ownership. The priority value on territory types ensures OTA correctly routes named account opportunities to the enterprise rep's forecast. Manual assignment for the named account list is preferred because the list changes quarterly, making rule-based matching expensive to maintain.

---

## Anti-Pattern: Mirroring the Role Hierarchy in Territory Design

**What practitioners do:** The admin exports the role hierarchy (SVP -> VP -> Director -> Manager -> Rep) and creates one territory per role node, naming territories after roles: "VP West," "Director West," "Rep California."

**What goes wrong:**
- The territory hierarchy now has 6+ levels, matching the management org chart rather than the forecast rollup or account coverage structure.
- When a manager changes roles, territory structure must be reorganized to match.
- Territory names reference people, not coverage areas — when reps are reassigned, territory names become misleading.
- Forecast rollups aggregate by territory node, not by person, so "VP West" territory rollup includes all accounts under that territory node regardless of which VP currently holds it.

**Correct approach:** Design territory hierarchy around the geographic or account segmentation structure, not the management org chart. Coverage nodes (West, Northeast, Southwest) should be stable; user membership assignments are what changes when reps are reassigned. The hierarchy should still reflect the management structure for forecast rollup purposes, but territory names should reflect coverage area, not individual people.
