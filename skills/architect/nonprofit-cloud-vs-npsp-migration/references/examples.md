# Examples — Nonprofit Cloud vs NPSP Migration

## Example 1: A mapping sheet whose target column is copied, not recalled

**Context:** An NPSP org with 400,000 gifts is being scoped for a move to Nonprofit Cloud. The first deliverable is the
object and field mapping.

**Problem:** The target column gets filled from memory, and the names are close enough to survive review. The
best-known example: NPSP's Program Management Module has `pmdm__ProgramEngagement__c`, and everyone writes
`ProgramEngagement` in the target column. The Nonprofit Cloud object is `ProgramEnrollment`. Both read as correct in a
spreadsheet; only one exists in the org, and the error is not discovered until something is built against it.

**Solution:** Make the mapping machine-checkable. Every target row carries the exact API name and the API version it
became available in, so the sheet doubles as a sequencing constraint.

```yaml
# docs/migration/npsp-to-nonprofit-cloud-mapping.yaml
source_org:   npsp
target_org:   nonprofit-cloud
target_api:   "67.0"

fundraising:
  - source: Opportunity                       # NPSP models a gift as an Opportunity
    target: GiftTransaction                   # "a completed transaction from a gift"
    target_available_from: "59.0"
    disposition: convert
    note: Not a rename. Field semantics differ; reconcile per campaign and period.

  - source: npe03__Recurring_Donation__c
    target: GiftCommitment                    # "the commitment made by a donor"
    target_available_from: "59.0"
    disposition: convert
    children:
      - target: GiftCommitmentSchedule        # "the schedule for fulfilling the commitment"
        target_available_from: "59.0"

  - source: npsp__Partial_Soft_Credit__c      # contact soft credits; npsp__Account_Soft_Credit__c for organizations
    target: GiftSoftCredit                    # RecipientId (Account), Role (8 restricted values), PartialAmount
    target_available_from: "59.0"
    disposition: convert
    exclude_if: generated_by_recurrence_engine
    note: >-
      GiftDefaultSoftCredit (62.0+) covers soft credits the recurrence engine
      creates for commitment transactions. Migrating those as data double-counts
      exactly the attributions fundraising reports on.

program_management:
  - source: pmdm__ProgramEngagement__c
    target: ProgramEnrollment                 # NOT ProgramEngagement — that name is NPSP's
    target_available_from: "57.0"
    disposition: convert

  - source: pmdm__Program__c
    target: Program
    target_available_from: "57.0"
    disposition: convert

  - source: pmdm__ServiceDelivery__c
    target: BenefitDisbursement
    target_available_from: "57.0"
    disposition: convert
    note: >-
      Benefit / BenefitAssignment / BenefitDisbursement is a three-object model.
      A one-to-one field map from a single NPSP object will not fit it.

environment_constraints:
  - module: fundraising
    editions: [Enterprise, Unlimited, Developer]
  - module: program-management
    editions: [Enterprise, Unlimited]         # Developer Edition is NOT listed
    implication: >-
      A Developer Edition scratch org cannot host the program-management
      prototype. Provision the pilot on an edition that lists the module.
```

**Why it works:** Two columns do the real work. `target_available_from` turns "does Nonprofit Cloud support this?" into
a number that can be compared against the target org, and `environment_constraints` catches the failure that otherwise
costs a week — prototyping Program Management in a Developer Edition org where the objects are not available.
`disposition: convert` rather than `map` sets the expectation correctly: these are shape changes, not renames.

---

## Example 2: The namespace inventory that sizes the migration on day one

**Context:** Leadership wants an estimate before committing to a migration programme.

**Problem:** Estimates get built from data volume, which is the part that is easy to count and rarely the part that
costs. What costs is the customisation layer: every custom trigger, formula, validation rule, report type, list-view
filter, and integration payload that references an NPSP package namespace. None of those namespaces exist in a
Nonprofit Cloud org, so every reference is rework.

**Solution:** Count the references before estimating anything. It takes minutes and predicts effort better than record
counts.

```bash
#!/usr/bin/env bash
# scripts/npsp-namespace-inventory.sh — run against a retrieved metadata tree
set -euo pipefail
SRC="${1:-force-app/main/default}"

echo "=== NPSP namespace references by metadata type ==="
for NS in npsp__ npe01__ npe03__ npe4__ npe5__ npo02__ pmdm__; do
  COUNT=$(grep -rl "$NS" "$SRC" 2>/dev/null | wc -l | tr -d ' ')
  printf '%-10s %s file(s)\n' "$NS" "$COUNT"
done

echo
echo "=== Where they live (the expensive part is not Apex) ==="
grep -rl -E 'npsp__|npe0[135]__|npe[45]__|npo02__|pmdm__' "$SRC" 2>/dev/null \
  | sed -E 's#.*/([^/]+)/[^/]+$#\1#' \
  | sort | uniq -c | sort -rn

echo
echo "=== Formula and validation references (silent breaks at cutover) ==="
grep -rn -E '<formula>|<errorConditionFormula>' "$SRC" 2>/dev/null \
  | grep -E 'npsp__|npe0[135]__|pmdm__' \
  | cut -c1-160
```

**Why it works:** The second block is the one that changes estimates. Apex references are found by the compiler at
deploy time; formula fields, validation rules, report types, and list-view filters are not, and neither is an external
system's field mapping. Producing the breakdown by metadata type on day one converts "how long will this take?" from
an argument into a count, and it identifies the integrations that need a partner conversation months before cutover.

---

## Anti-Pattern: Treating the migration as a load rather than a conversion

**What practitioners do:** Extract NPSP Opportunities, rename the columns, and upsert them into `GiftTransaction`,
then move on to the next object.

**What goes wrong:** The two models do not correspond field-for-field, and the mismatch concentrates in the data the
organisation is most sensitive about. Recurring donations are not one object in the target — `GiftCommitment` holds the
commitment and `GiftCommitmentSchedule` holds the fulfilment plan. Soft credits are their own standard object,
`GiftSoftCredit`, and some of them are generated by the platform's recurrence engine rather than migrated. Program
delivery expands from one NPSP object into `Benefit`, `BenefitAssignment`, and `BenefitDisbursement`. A column-rename
load produces records that exist, report incorrectly, and cannot be un-migrated once fundraising has been running on
them.

**Correct approach:** Convert per entity, with a reconciliation report that fundraising signs off on before the next
entity starts.

```text
Per-entity conversion gate (repeat for constituents, gifts, commitments, soft credits, programs)

1. Extract  — source records + the reconciliation dimensions the business reports on
              (donor, campaign, designation, fiscal period)
2. Convert  — into the target shape, including objects with no NPSP counterpart
3. Load     — into a sandbox on the target edition, with the recurrence engine's
              generated records EXCLUDED from the input
4. Reconcile— totals by every dimension in step 1, source vs target, signed off by
              the fundraising lead — not by the migration team
5. Gate     — a variance that cannot be explained blocks the next entity

Cutover rehearsal runs all five for every entity end to end, measured, before the
real one is scheduled.
```

The sign-off in step 4 is the load-bearing part. A migration team can verify that records arrived; only the fundraising
lead can tell you that the attribution is right, and attribution is where this particular migration fails.

---

## Example 3: Decision Record, Release Manifest, And Reconciliation Queries For A Phased Migration

**Context:** A community foundation runs NPSP (Enterprise Edition, 120 users) with Recurring Donations, Allocations, Customizable Rollups, and 400,000 Opportunities. Grants are tracked in the Outbound Funds Module. The board approved a move to Nonprofit Cloud in a new Enterprise Edition org.

**The decision record** at `docs/adr/0031-npsp-to-nonprofit-cloud.md`:

```markdown
# ADR-0031: Migrate fundraising and households from NPSP to Nonprofit Cloud in a new org

## Status
Accepted (2026-10-03), Programme Board

## Context
- Namespace inventory (Example 2): 1,140 files reference npsp__, npe01__,
  npo02__, npe03__, npe4__, npe5__, or outfunds__; 212 are formulas,
  validation rules, report types, or list views.
- Target org: Enterprise Edition, API 67.0. Fundraising objects need the
  Fundraising Access licence and Fundraising User permission. Record
  Rollup Definitions need the Record Aggregation permission set licence.
- Program Management is not used; grants are in outfunds__ objects.

## Decision
1. New org, not in-place: NPSP package objects and Nonprofit Cloud
   objects never coexist for the same entity.
2. Households: one Account plus one PartyRelationshipGroup per NPSP
   household; members as AccountContactRelation; the NPSP primary contact
   carried as a PartyRoleRelation role.
3. Gifts: Opportunity (Closed Won) -> GiftTransaction (Status = Paid);
   npe03__Recurring_Donation__c -> GiftCommitment + GiftCommitmentSchedule;
   npsp__Allocation__c -> GiftTransactionDesignation against GiftDesignation
   rows built from npsp__General_Accounting_Unit__c.
4. Soft credits: npsp__Partial_Soft_Credit__c and npsp__Account_Soft_Credit__c
   -> GiftSoftCredit, Role mapped by a reviewed table; recurrence-engine
   soft credits excluded.
5. Rollups: rebuild the 14 Customizable Rollups as Record Rollup
   Definitions; no rollup values loaded as data.
6. Grants: outfunds__Funding_Request__c -> Application Form model
   (Individual Application gets no future enhancements).
7. Freeze NPSP data changes for the final extraction weekend.

## Consequences
### Positive
- One data model per entity; Nonprofit Cloud features apply from day one.
### Negative
- Every NPSP-dependent report, formula, and integration mapping is rebuilt.
- Payment processor re-points to GiftTransaction and GiftCommitment.
- Licence cost for Fundraising Access and Record Aggregation.

## Alternatives Considered
### Stay on NPSP
Rejected: board decision to adopt Nonprofit Cloud fundraising features.
### Install Nonprofit Cloud next to NPSP in the same org
Rejected: two household and gift models, dual writes, conflicting rollups.

## Date
2026-10-03
```

**Reconciliation queries, run before sign-off of each entity.** Source org, Closed Won gift totals by year:

```soql
SELECT CALENDAR_YEAR(CloseDate) giftYear, COUNT(Id) gifts, SUM(Amount) total
FROM Opportunity
WHERE IsWon = true
GROUP BY CALENDAR_YEAR(CloseDate)
ORDER BY CALENDAR_YEAR(CloseDate)
```

Target org, the same totals from paid gift transactions:

```soql
SELECT CALENDAR_YEAR(TransactionDate) giftYear, COUNT(Id) gifts, SUM(OriginalAmount) total
FROM GiftTransaction
WHERE Status = 'Paid'
GROUP BY CALENDAR_YEAR(TransactionDate)
ORDER BY CALENDAR_YEAR(TransactionDate)
```

`GiftTransaction.Status` values (Canceled, Failed, Fully Refunded, Paid, Pending, and others) and `OriginalAmount` ("includes donor cover and excludes the transaction fees") come from the NPC Guide. UNVERIFIED (2026-10-03): whether `TransactionDate` is a date or datetime field (the `CALENDAR_YEAR` function accepts both) and whether refunded NPSP gifts should be excluded on both sides must be confirmed against the org before the numbers are compared.

**Release manifest members for the target org** (types from the Metadata API and the NPC Guide; member names are this org's):

| Component | Type | `package.xml` member form |
|---|---|---|
| Lifetime giving rollup | `RecordAggregationDefinition` | `<members>Donor_Lifetime_Giving</members><name>RecordAggregationDefinition</name>` |
| Fundraising user access | `PermissionSetGroup` | `<members>Fundraising_Users</members><name>PermissionSetGroup</name>` |
| Migration external Id on GiftTransaction | `CustomField` | `<members>GiftTransaction.NPSP_Opportunity_Id__c</members><name>CustomField</name>` |
| Migration external Id on GiftCommitment | `CustomField` | `<members>GiftCommitment.NPSP_Recurring_Donation_Id__c</members><name>CustomField</name>` |

`RecordAggregationDefinition` (API 59.0+, `.RecordAggregationDefinition` suffix in the `RecordAggregationDefinitions` folder) is from the NPC Guide's Record Rollup Definitions chapter. UNVERIFIED (2026-10-03): that custom external Id fields can be added to `GiftTransaction` and `GiftCommitment` was not confirmed in the NPC Guide; if not, keep the source Id in a load-staging object instead.

**Why it works:** each decision names the exact source and target objects, the licences the target needs, and the reconciliation that proves the conversion, so the board approves a plan whose risks are written down.

