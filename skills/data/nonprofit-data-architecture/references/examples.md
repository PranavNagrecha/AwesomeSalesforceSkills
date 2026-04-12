# Examples — Nonprofit Data Architecture

## Example 1: Constituent 360 Summary — Giving History with Program Participation

**Scenario:** A nonprofit needs to display a donor's complete profile including lifetime giving, most recent gift, year-to-date giving, and all active program enrollments on a single Lightning record page.

**Problem:** A developer unfamiliar with NPSP queries `Opportunity` using `ContactId` and finds no records, even though the Contact has a giving history. A second developer queries only the Contact's `npo02__TotalOppAmount__c` rollup field and misses a same-day gift that has not yet been rolled up. Neither approach produces an accurate, real-time constituent 360.

**Solution:**

```soql
-- Step 1: Fetch rollup summary fields from Contact (fast, cached by CRLP)
SELECT
    Id,
    Name,
    AccountId,
    npo02__TotalOppAmount__c,
    npo02__LastOppAmount__c,
    npo02__LastCloseDate__c,
    npo02__OppAmountLastYear__c,
    npo02__OppAmountThisYear__c,
    npo02__ConsecutiveYearsGiven__c
FROM Contact
WHERE Id = :constituentContactId

-- Step 2: Fetch authoritative transactions from Household Account
-- (Opportunities link to HH Account, not to Contact directly)
SELECT
    Id,
    Name,
    Amount,
    CloseDate,
    StageName,
    npsp__Primary_Contact__r.Name,
    CampaignId,
    Campaign.Name
FROM Opportunity
WHERE AccountId = :householdAccountId
  AND IsWon = true
ORDER BY CloseDate DESC
LIMIT 200

-- Step 3: Fetch program participation (requires pmdm__ package)
SELECT
    Id,
    pmdm__Program__r.Name,
    pmdm__Stage__c,
    pmdm__StartDate__c,
    (
        SELECT
            Id,
            pmdm__DeliveryDate__c,
            pmdm__Quantity__c,
            pmdm__Service__r.Name
        FROM pmdm__ServiceDeliveries__r
        ORDER BY pmdm__DeliveryDate__c DESC
        LIMIT 10
    )
FROM pmdm__ProgramEngagement__c
WHERE pmdm__Contact__c = :constituentContactId
  AND pmdm__Stage__c = 'Active'
```

**Why it works:** Step 1 uses NPSP's pre-calculated rollup fields for display performance. Step 2 queries raw Opportunity records linked to the HH Account (the authoritative financial unit in NPSP) to catch any gaps between real-time gifts and rollup recalculation. Step 3 uses the PMM sub-query relationship `pmdm__ServiceDeliveries__r` defined by the PMM package to pull recent service delivery records in a single query.

---

## Example 2: Validating Stale CRLP Rollup Fields Before a Data Migration

**Scenario:** A nonprofit is migrating from NPSP to a new platform. The migration team needs to export constituent giving totals and wants to use the pre-calculated `npo02__TotalOppAmount__c` field to avoid running aggregate SOQL across millions of rows. The data team needs to confirm whether the rollup fields are reliable or whether they should compute totals from raw transactions.

**Problem:** In a large NPSP org that recently upgraded from legacy rollup mode to CRLP, some Contacts have `npo02__TotalOppAmount__c` values that differ from the actual sum of their Household Account's Opportunities. The CRLP backfill batch job was interrupted and never restarted.

**Solution:**

```python
# stdlib-only Python to cross-check rollup vs. raw total
# Run against a Salesforce export CSV: Contacts with npo02__TotalOppAmount__c
# and a second CSV: Opportunities grouped by AccountId with SUM(Amount)

import csv
import sys
from decimal import Decimal

def load_rollup_totals(filepath):
    """Load Contact rollup totals: {AccountId: npo02__TotalOppAmount__c}"""
    totals = {}
    with open(filepath, newline='') as f:
        for row in csv.DictReader(f):
            acct_id = row['AccountId']
            raw = row.get('npo02__TotalOppAmount__c', '0') or '0'
            totals[acct_id] = Decimal(raw.replace(',', ''))
    return totals

def load_opportunity_totals(filepath):
    """Load summed Opportunity amounts: {AccountId: sum(Amount)}"""
    totals = {}
    with open(filepath, newline='') as f:
        for row in csv.DictReader(f):
            acct_id = row['AccountId']
            raw = row.get('Amount', '0') or '0'
            totals[acct_id] = totals.get(acct_id, Decimal('0')) + Decimal(raw.replace(',', ''))
    return totals

def find_discrepancies(rollup_file, opp_file, threshold=Decimal('0.01')):
    rollup = load_rollup_totals(rollup_file)
    opp_totals = load_opportunity_totals(opp_file)
    discrepancies = []
    for acct_id, rollup_val in rollup.items():
        opp_val = opp_totals.get(acct_id, Decimal('0'))
        if abs(rollup_val - opp_val) > threshold:
            discrepancies.append({
                'AccountId': acct_id,
                'rollup': float(rollup_val),
                'opp_sum': float(opp_val),
                'delta': float(opp_val - rollup_val)
            })
    return discrepancies

if __name__ == '__main__':
    results = find_discrepancies(sys.argv[1], sys.argv[2])
    print(f"{len(results)} accounts with rollup discrepancies")
    for r in results[:20]:
        print(r)
```

**Why it works:** The script compares NPSP rollup fields to aggregate Opportunity totals at the Household Account level — the same unit NPSP uses for financial aggregation. Any delta above the threshold indicates a stale or failed CRLP recalculation. Migration teams can use the discrepancy list to trigger a targeted CRLP batch recalculation before export, ensuring the migrated totals are accurate.

---

## Anti-Pattern: Querying Opportunity via ContactId in NPSP

**What practitioners do:** They write `SELECT Id, Amount FROM Opportunity WHERE ContactId = :constituentId` expecting to retrieve a constituent's donation history, following the standard Salesforce pattern for contact-linked activities.

**What goes wrong:** In the NPSP Household Account model, `Opportunity.AccountId` points to the HH_Account, not to an individual Contact. The `ContactId` field on Opportunity is not populated by NPSP's gift creation process. The query returns zero rows even when the Contact has a full giving history. This mistake is particularly difficult to diagnose because no error is thrown — the query simply returns an empty result set.

**Correct approach:** Query Opportunities via the Household Account: `SELECT Id, Amount FROM Opportunity WHERE AccountId = :contact.AccountId`. If you need only the gifts where this specific Contact is the primary donor, add `AND npsp__Primary_Contact__c = :constituentId` to filter by NPSP's primary contact lookup.
