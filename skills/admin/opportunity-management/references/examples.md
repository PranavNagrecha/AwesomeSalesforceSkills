# Examples — Opportunity Management

## Example 1: Configuring a Two-Process Org (New Logo + Renewal)

**Context:** A Sales Cloud org serves both direct new logo sales and renewal/expansion motions. Each motion has distinct stages and different forecast expectations. Currently both use a single "Default" Sales Process with 12 stages — reps skip stages, and forecast rollups are noisy.

**Problem:** Without separate Sales Processes, the renewal record type exposes new-logo stages like "Demo Scheduled" and "Proof of Concept" that are irrelevant to renewals. Reps leave these stages blank, creating gaps in forecast data and invalid stage sequences.

**Solution:**

```text
Step 1 — Define all Stage picklist values globally (Setup > Opportunity Stages):
  New Logo stages:
    Prospecting          | IsClosed=false | IsWon=false | ForecastCategory=Pipeline    | Prob=10
    Discovery            | IsClosed=false | IsWon=false | ForecastCategory=Pipeline    | Prob=20
    Demo Scheduled       | IsClosed=false | IsWon=false | ForecastCategory=Pipeline    | Prob=30
    Proposal Sent        | IsClosed=false | IsWon=false | ForecastCategory=Best Case   | Prob=50
    Negotiation          | IsClosed=false | IsWon=false | ForecastCategory=Commit      | Prob=75
    Closed Won           | IsClosed=true  | IsWon=true  | ForecastCategory=Closed      | Prob=100
    Closed Lost          | IsClosed=true  | IsWon=false | ForecastCategory=Omitted     | Prob=0

  Renewal-specific stages:
    Renewal Identified   | IsClosed=false | IsWon=false | ForecastCategory=Pipeline    | Prob=60
    Renewal Proposed     | IsClosed=false | IsWon=false | ForecastCategory=Best Case   | Prob=75
    Renewal Committed    | IsClosed=false | IsWon=false | ForecastCategory=Commit      | Prob=90
    Renewal Won          | IsClosed=true  | IsWon=true  | ForecastCategory=Closed      | Prob=100
    Renewal Lost         | IsClosed=true  | IsWon=false | ForecastCategory=Omitted     | Prob=0

Step 2 — Create Sales Processes:
  "New Logo Process": Prospecting, Discovery, Demo Scheduled, Proposal Sent,
                      Negotiation, Closed Won, Closed Lost
  "Renewal Process":  Renewal Identified, Renewal Proposed, Renewal Committed,
                      Renewal Won, Renewal Lost

Step 3 — Assign Sales Processes to Record Types:
  Record Type "New Logo Opportunity"  → New Logo Process
  Record Type "Renewal Opportunity"   → Renewal Process

Step 4 — Configure Path Settings for each record type separately.
```

> The `ForecastCategory=` column above uses the **UI / SOQL** vocabulary (`Best Case`, `Commit`, `Most Likely`,
> `Pipeline`, `Closed`, `Omitted`). The `standardValueSet` file that builds these stages takes a different token
> set — `BestCase`, `Forecast`, `Pipeline`, `Closed`, `Omitted` — with metadata `Forecast` meaning UI **Commit**.
> See `references/gotchas.md` Gotcha 13 before transcribing this table into XML.

**Why it works:** Sales Processes act as stage filters. Each record type only exposes the stages relevant to its motion, keeping forecast rollups clean and stage sequences meaningful. The global picklist still owns all values — the process just constrains which values are visible per record type.

---

## Example 2: Enabling Revenue Splits for Split-Credit Forecasting

**Context:** An inside sales org has account executives (AEs) and solution engineers (SEs) who co-close deals. AEs own quota; SEs receive overlay credit. The org needs individual forecast rollups for both roles from the same opportunity.

**Problem:** Without splits, the full opportunity amount rolls up to the opportunity owner only. The SE's contribution is invisible in forecasting, and managers cannot track overlay performance.

**Solution:**

```text
Step 1 — Enable Team Selling:
  Setup > Opportunity Team Settings > Enable Opportunity Teams

Step 2 — Enable Opportunity Splits:
  Setup > Opportunity Settings > Enable Opportunity Splits
  Configure two split types:
    "Revenue Split"  — type: Revenue  — must total 100% per opportunity
    "Overlay Split"  — type: Overlay  — no 100% constraint

Step 3 — Configure Collaborative Forecasting:
  Setup > Forecasts Settings
  Forecast Type 1: "AE Revenue"    — source: Opportunity Splits (Revenue type)
                                   — assign to AE profile
  Forecast Type 2: "SE Overlay"    — source: Opportunity Splits (Overlay type)
                                   — assign to SE profile

Step 4 — Usage on a record:
  Opportunity: Acme Deal — $100,000
  Sales Team:
    AE Jane  → Revenue Split: 100%  → rolls $100,000 to Jane's AE Revenue forecast
    SE Mark  → Overlay Split: 100%  → rolls $100,000 to Mark's SE Overlay forecast
```

**Why it works:** Revenue and overlay splits are distinct objects. Revenue splits enforce the 100% total rule and feed quota-based forecast types. Overlay splits do not enforce a cap and feed separate overlay forecast types. Both roll up independently, so the AE and SE forecasts are distinct without double-counting on the AE side.

---

## Example 3: Adding Stage Progression Enforcement via Validation Rule

**Context:** After configuring Path, the sales ops team discovers reps are skipping from "Prospecting" directly to "Closed Won" to game their stage metrics. Path guidance was in place but did not prevent the skip.

**Problem:** Path is visual-only. No platform mechanism in Path Settings blocks a save at an out-of-order stage.

**Solution:**

```text
Validation Rule: "Require_CloseDate_Before_Proposal"
Object: Opportunity
Active: true

Error Condition Formula:
  AND(
    ISPICKVAL(StageName, "Proposal Sent"),
    ISBLANK(CloseDate)
  )

Error Message: "Close Date is required before moving to Proposal Sent."
Error Location: Stage field
```

```text
Validation Rule: "Block_Skip_To_ClosedWon_Without_Proposal"
Object: Opportunity
Active: true

Error Condition Formula:
  AND(
    ISPICKVAL(StageName, "Closed Won"),
    NOT(ISPICKVAL(PRIORVALUE(StageName), "Negotiation")),
    NOT(ISPICKVAL(PRIORVALUE(StageName), "Closed Won"))
  )

Error Message: "Opportunities must pass through Negotiation before being marked Closed Won."
Error Location: Stage field
```

**Why it works:** Validation rules fire on save regardless of Path. `PRIORVALUE()` compares the new stage value against the previous saved value, catching illegal transitions without requiring a custom trigger.

---

## Anti-Pattern: Deleting a Stage Value Without Reassigning Records

**What practitioners do:** Go to Setup > Opportunity Stages, find a deprecated stage like "Verbal Commit", and click Delete.

**What goes wrong:** If any Opportunity records still have `StageName = 'Verbal Commit'`, Salesforce deletes the picklist value without reassigning or blocking those records. The Stage field on affected records becomes blank. These records then fail any validation rule that checks `ISBLANK(StageName)`, break SOQL queries relying on StageName, and drop out of all forecast rollups. <!-- UNVERIFIED (2026-09-04): the delete-time behaviour is carried from an earlier revision of this skill; neither api_meta.txt nor object_reference.txt documents what happens to records when a picklist value is deleted. What is grounded is the deactivation path — inactive stage values "are not available in the picklist and are retained for historical purposes only" (object_reference.txt:195512–195514). See references/gotchas.md Gotcha 1. -->

**Correct approach:** Run the audit below before touching the value set. It separates the two populations
that need different treatment — open records that must be migrated, and closed records that should keep the
historical value — and it is the query the checker's INFO finding tells you to run.

```sql
-- 1. Blast radius, split by open vs closed. Non-zero "Open" means migrate before you touch anything.
SELECT StageName, IsClosed, COUNT(Id) Records, MIN(CloseDate) Earliest, MAX(CloseDate) Latest
FROM Opportunity
WHERE StageName = 'Verbal Commit'
GROUP BY StageName, IsClosed

-- 2. The exact open records to migrate, exported as the Data Loader update file.
SELECT Id, Name, OwnerId, RecordType.DeveloperName, StageName, Amount, CloseDate
FROM Opportunity
WHERE StageName = 'Verbal Commit' AND IsClosed = FALSE
ORDER BY RecordType.DeveloperName, CloseDate

-- 3. Post-migration proof. Must return zero rows before the value is deactivated.
SELECT COUNT(Id) FROM Opportunity WHERE StageName = 'Verbal Commit' AND IsClosed = FALSE
```

The update file for step 2 needs two columns only — the platform derives the rest:

| Id | StageName |
|---|---|
| 0065g00000AbCdEAAV | Negotiation/Review |
| 0065g00000AbCdFAAV | Negotiation/Review |

Do not add `Probability`, `ForecastCategoryName`, `IsClosed` or `IsWon` to that file. `IsClosed` and `IsWon`
cannot be set at all, and any `Probability` or `ForecastCategoryName` you supply is overwritten by the new
stage's defaults in the same transaction (`references/gotchas.md` Gotcha 9).

Then, and only then:
1. Deactivate the picklist value on the `OpportunityStage` standard value set rather than deleting it —
   inactive values stay readable on the closed records that still carry them.
2. Remove it from any `BusinessProcess` that still lists it, and from any `PathAssistant` step whose
   `picklistValueName` points at it. The checker flags the second one as a WARN.
3. Only hard-delete if the step-3 count is zero **and** no closed record needs the historical value.
