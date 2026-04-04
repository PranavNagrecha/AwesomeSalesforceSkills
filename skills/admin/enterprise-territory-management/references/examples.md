# Examples — Enterprise Territory Management

## Example 1: Geographic Territory Model for a North America Field Sales Team

**Context:** A B2B SaaS company has 40 field sales reps covering the United States and Canada. Sales leadership wants automated account assignment based on billing state/province, and wants territory-based forecasting so each regional VP can roll up pipeline by territory independently of account ownership.

**Problem:** Without ETM, accounts are assigned by ownership only. Reps inherit pipeline visibility through the role hierarchy, but leadership cannot report on territory performance independently of who owns the account. There is no clean way to distinguish "Southeast territory pipeline" from "this specific rep's pipeline." When reps leave, unowned accounts fall out of territory visibility.

**Solution:**

Territory Type configuration:
- Type Name: "Geographic" — priority value: 10

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

Account Assignment Rule example for "US Southeast":
- Rule Name: Southeast States
- Criteria: `BillingState EQUALS "VA", "NC", "SC", "GA", "FL", "AL", "MS", "TN", "KY", "WV", "AR", "LA", "DE", "MD"`
- IsActive: true (auto-runs on account create/update)

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
- "Geographic" — priority: 10
- "Named Account" — priority: 5 (lower integer = higher priority; named account territories win OTA tie-breaking over geo)

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
- Criteria: Custom field `Named_Account_Owner__c EQUALS "Rep 1"` (set on account record)
  OR: Account Name EQUALS "Acme Corp", "Global Dynamics", ... (explicit list)
- IsActive: true

Each strategic rep is assigned as a territory member of their individual named account territory leaf. They are not added to geographic territories.

Forecast configuration:
- Forecast Type 1: "Geographic Sales" — uses the geographic branch of the hierarchy.
- Forecast Type 2: "Named Account Sales" — uses the Named Accounts branch.

**Why it works:** Named account reps access their accounts through their territory membership regardless of billing state. Geographic reps still cover those same accounts through geo territory membership. The two Forecast Types produce separate forecast rollups — pipeline for named account VP rolls up cleanly through the Named Accounts hierarchy without appearing in the geo forecast. The territory type priority ensures opportunities on named accounts get assigned to the Named Account territory in OTA.

---

## Anti-Pattern: Running Assignment Rules Territory-by-Territory After Model Activation

**What practitioners do:** After activating a new territory model, admins run assignment rules one territory at a time from each territory's detail page, working through the hierarchy as they have time.

**What goes wrong:** Accounts that should be assigned to multiple territories end up in an inconsistent state — assigned to the territories whose rules have been run but not yet to others. Reports and forecast data are unreliable until all rules have been run. The partial-run state can persist for days in large orgs, creating confusion about whether accounts are correctly assigned.

**Correct approach:** After model activation (or any significant structural rule change), run assignment rules at the Territory Model level — from the Territory Model detail page, click "Run Assignment Rules." This evaluates all rules across all territories in a single background job and produces consistent assignments. Territory-level rule runs are appropriate only for incremental, isolated changes to a single territory after initial assignment is complete.
