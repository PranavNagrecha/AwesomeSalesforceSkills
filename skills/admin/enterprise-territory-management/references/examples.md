# Examples — Enterprise Territory Management

## Example 1: Geographic Territory Model for a North America Field Sales Team

**Context:** A B2B SaaS company has 40 field sales reps covering the United States and Canada. Sales leadership wants automated account assignment based on billing state/province, and wants territory-based forecasting so each regional VP can roll up pipeline by territory independently of account ownership.

**Problem:** Without ETM, accounts are assigned by ownership only. Reps inherit pipeline visibility through the role hierarchy, but leadership cannot report on territory performance independently of who owns the account. There is no clean way to distinguish "Southeast territory pipeline" from "this specific rep's pipeline." When reps leave, unowned accounts fall out of territory visibility.

**Solution:**

Territory Type configuration:
- Type Name: "Geographic" — `priority` 10 (only one type in play, so the value is uncontested; it matters in Example 2)

Territory Model: "FY26 North America" (created in Planning state)

Territory hierarchy:
```
North America (root)
├── US East
│   ├── US Northeast  (NY, NJ, PA, MA, CT, RI, VT, NH, ME)
│   └── US Southeast  (VA, NC, SC, GA, FL, AL, MS, TN, KY, WV, AR, LA, DE, MD)
├── US Central
│   ├── US Midwest    (OH, IN, IL, MI, WI, MN, IA, MO, ND, SD, NE, KS)
│   └── US South Central (TX, OK)
├── US West
│   ├── US Mountain   (CO, UT, NV, AZ, NM, ID, MT, WY)
│   └── US Pacific    (CA, OR, WA, AK, HI)
└── Canada
    ├── Canada East   (ON, QC, NB, NS, PE, NL)
    └── Canada West   (BC, AB, SK, MB, NT, NU, YT)
```

Account Assignment Rule example for "US Southeast" — one `Territory2Rule` in the model's `rules` folder, associated to the US Southeast territory through `ruleAssociations`:
- Rule Name: Southeast States
- Criteria: `BillingState equals VA,NC,SC,GA,FL,AL,MS,TN,KY,WV,AR,LA,DE,MD`
- `active`: true (auto-runs on account create/update, except on accounts where `IsExcludedFromRealign` is true)

The 14 states fit in a single rule item, so no `booleanFilter` is needed. A rule is capped at 10 rule items, which is the real constraint on how many *distinct fields* one rule can test — not how many values one field can match.

Deployment sequence:
1. Build hierarchy and rules in Planning state.
2. Run assignment rules in preview mode to validate distribution.
3. Activate the model (triggers background recalculation — monitor Territory2AlignmentLog).
4. In Setup > Forecasts Settings, add a Forecast Type using the territory hierarchy.
5. Assign regional VPs as territory managers at the US East, US Central, US West, and Canada nodes.

**Why it works:** Accounts are assigned based on billing address regardless of ownership. Regional VPs are territory managers at their branch node and see forecast rollups from all sub-territories. Every rep gains Read access to all accounts in their territory regardless of account owner — eliminating blind spots when accounts are unowned or reassigned.

---

## Example 2: Named Account Overlay Model

**Context:** The same company from Example 1 also has 8 strategic named account reps who each own a curated list of 50–100 enterprise accounts. These accounts span geographies — a strategic rep might manage accounts in New York and California simultaneously. The company needs the named account team's pipeline forecast to roll up separately from the geographic forecast.

**Problem:** Adding named account reps to geographic territories pollutes the geo forecast with named account pipeline and double-counts opportunities. A second territory model cannot be Active simultaneously — so a separate model for named accounts is not an option.

**Solution:** Add a second territory type and a named account overlay branch within the same active territory model.

Territory Types (updated):
- "Geographic" — `priority` 10
- "Named Account" — `priority` 20

The direction matters and is easy to get backwards. The Metadata API guide states that "the account-assigned territory whose territory type priority is **highest** is then assigned to the opportunity," and the reference Apex filter keeps the territory with the numerically greater priority. So Named Account needs the **larger** integer (20) to beat Geographic (10). The two values must also be distinct — priority is required to be unique per type — and if an account somehow lands in two territories tied at the top priority, the documented outcome is that the opportunity gets no territory at all.

Territory hierarchy addition to the FY26 North America model:
```
North America (root)
├── [Geographic sub-tree as in Example 1]
└── Named Accounts (overlay root)
    ├── Strategic Rep 1 Named Accounts
    ├── Strategic Rep 2 Named Accounts
    └── [one leaf territory per named account rep]
```

Assignment rule for "Strategic Rep 1 Named Accounts":
- Criteria: custom field `Named_Account_Owner__c equals Rep 1` (set on the account record)
- `active`: true

Prefer the custom-field form over an explicit account-name list. A name list burns rule items — ten is the cap — and every roster change becomes a metadata deploy rather than a data edit.

Each strategic rep is assigned as a territory member of their individual named account territory leaf. They are not added to geographic territories.

Forecast configuration:
- Forecast Type 1: "Geographic Sales" — uses the geographic branch of the hierarchy.
- Forecast Type 2: "Named Account Sales" — uses the Named Accounts branch.

**Why it works:** Named account reps access their accounts through their territory membership regardless of billing state. Geographic reps still cover those same accounts through geo territory membership. The two Forecast Types produce separate forecast rollups — pipeline for named account VP rolls up cleanly through the Named Accounts hierarchy without appearing in the geo forecast. The territory type priority ensures opportunities on named accounts get assigned to the Named Account territory in OTA.

---

## Anti-Pattern: Running Assignment Rules Territory-by-Territory After Model Activation

**What practitioners do:** After activating a new territory model, admins run assignment rules one territory at a time from each territory's detail page, working through the hierarchy as they have time.

**What goes wrong:** Accounts that should be assigned to multiple territories end up in an inconsistent state — assigned to the territories whose rules have been run but not yet to others. Reports and forecast data are unreliable until all rules have been run. The partial-run state can persist for days in large orgs, creating confusion about whether accounts are correctly assigned.

**Correct approach:** After model activation (or any significant structural rule change), run assignment rules once at the **model** level. That evaluates all rules across all territories in a single background job and produces consistent assignments. Territory-level runs are for incremental, isolated changes to one territory after initial assignment is complete.

**How to tell which happened.** `Territory2AlignmentLog.Territory2Id` is documented as null when "the assignment rule run was for the territory model" and populated when it was for a single territory. That one field distinguishes the two patterns after the fact:

```sql
-- A healthy post-activation run: ONE row, Territory2Id null, Status finished.
-- The territory-by-territory anti-pattern shows up as many rows with Territory2Id
-- populated, spread over hours or days, and no model-level row at all.
SELECT Id,
       Territory2ModelId,
       Territory2Id,
       Territory2.Name,
       Status,
       StartTime,
       EndTime,
       RunAsId
FROM Territory2AlignmentLog
WHERE Territory2ModelId = '0MIxx0000004CDbGAM'
  AND StartTime = LAST_N_DAYS:7
ORDER BY StartTime DESC

-- Cross-check against the model itself. LastRunRulesEndDate should be recent
-- and later than the newest account data change you care about.
SELECT Id, DeveloperName, State, ActivatedDate, LastRunRulesEndDate
FROM Territory2Model
WHERE State = 'Active'
```

Read the result this way: no rows at all means the deploy landed and nothing was ever run — Metadata API cannot run rules, so a clean deploy is not evidence of assignment. Rows with a null `Territory2Id` are model-level runs. A scatter of rows with populated `Territory2Id` and no model-level row is the anti-pattern in progress, and territory assignment should be treated as unreliable until a model-level run completes.
