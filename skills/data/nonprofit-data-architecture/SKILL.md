---
name: nonprofit-data-architecture
description: "Use this skill when designing or querying the NPSP data model — constituent 360, household accounts, giving history rollups, and program participation. Trigger keywords: NPSP data model, household account, constituent record, giving rollups, CRLP, program engagement, ServiceDelivery, npo02__ fields. NOT for standard data model design, Nonprofit Cloud (NPC) data model, FSC household groups, or platform data modeling outside the NPSP context."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
  - Operational Excellence
triggers:
  - "How do I store giving history and total donation amounts for a nonprofit contact?"
  - "What objects connect a constituent to their household and program participation in NPSP?"
  - "My rollup fields like npo02__TotalOppAmount__c are not updating after a donation is recorded"
  - "How is NPSP household data model different from Nonprofit Cloud or Financial Services Cloud?"
  - "Where does program enrollment and service delivery data live in NPSP?"
tags:
  - npsp
  - nonprofit-data-architecture
  - household-account
  - constituent-360
  - crlp
  - pmm
  - giving-history
  - program-management
inputs:
  - "NPSP installed package version (namespace npo02__, npsp__, npe01__, npe03__, npe4__, npe5__)"
  - "Constituent model in use: HH Account vs One-to-One vs Individual"
  - "Program Management Module (PMM) package installed (namespace pmdm__)"
  - "CRLP (Customizable Rollups) enabled or legacy rollup mode"
  - "Existing custom fields or triggers on Contact, Account, or Opportunity"
outputs:
  - "Data model diagram describing three-layer NPSP constituent architecture"
  - "SOQL query patterns for giving history and rollup fields"
  - "PMM object relationship map (pmdm__Program__c, pmdm__ProgramEngagement__c, pmdm__ServiceDelivery__c)"
  - "CRLP configuration checklist for custom rollup requirements"
  - "Guidance on namespace-aware field references for NPSP objects"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-12
---

# Nonprofit Data Architecture

Use this skill when working with the NPSP (Nonprofit Success Pack) data model, including constituent 360 design, household account configuration, giving history rollup fields, and program participation tracking via the Program Management Module (PMM). This skill does NOT cover the Nonprofit Cloud (NPC) data model, FSC household groups, or generic Salesforce data modeling patterns.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Which constituent model is active?** NPSP supports three models: Household Account (recommended, most common), One-to-One, and Individual (deprecated bucket account). Household Account is almost always what you are working with in modern NPSP orgs.
- **Is PMM installed?** The Program Management Module is a separate managed package with its own `pmdm__` namespace. It is NOT part of NPSP core (namespaces `npo02__`, `npsp__`, `npe01__`, `npe03__`, `npe4__`, `npe5__`). Many orgs have NPSP but not PMM.
- **Is CRLP enabled?** Customizable Rollups (CRLP) replaced legacy rollup behavior. When CRLP is enabled, rollup fields are calculated by Rollup__mdt custom metadata records, not by the legacy batch job. Mixing CRLP and legacy rollups in the same org causes silent duplicate or zeroed rollup values.
- **Is this NPSP or Nonprofit Cloud?** NPSP and NPC are two entirely different products built on different foundational objects. Never apply NPSP patterns to an NPC org. Confirm via installed packages before proceeding.

---

## Core Concepts

### The Three-Layer Constituent 360 Model

NPSP models a constituent as three interconnected layers:

1. **HH_Account (Household Account)** — A standard `Account` record with the `HH_Account` record type (API name `HH_Account`). The household groups one or more related Contacts (family members, partners). The account is the financial unit: `Opportunity` and `npo02__OppPayment__c` records link to the Account, not to individual Contacts. Rollup summary fields on the Household Account aggregate giving totals across all members.

2. **Contact** — The individual constituent. NPSP adds the `npe01__Primary_Address_Type__c`, `npe01__Home_Address__c`, and related address management fields. A Contact's `AccountId` points to their Household Account. The `npe01__Primary_Contact__c` field on the Account identifies the primary contact for the household.

3. **npo02__ rollup fields on Contact and Account** — NPSP drives a constellation of rollup fields under the `npo02__` namespace. Key fields include:
   - `npo02__TotalOppAmount__c` — lifetime total giving
   - `npo02__LastOppAmount__c` — most recent gift amount
   - `npo02__LastCloseDate__c` — most recent gift close date
   - `npo02__OppAmountLastYear__c` — giving in the prior calendar year
   - `npo02__ConsecutiveYearsGiven__c` — streak counter
   
   These fields exist on both `Contact` and `Account`. The values are recalculated by either the CRLP engine or the legacy Household Rollup batch job, not by standard rollup summary fields.

### Customizable Rollups (CRLP) Engine

CRLP is the modern NPSP rollup calculation engine introduced in NPSP 3.x. It replaces the nightly `RLLP_OppRollup_BATCH` with a near-real-time engine driven by `Rollup__mdt` custom metadata type records. Each `Rollup__mdt` record defines:

- The source object (Opportunity or npe01__OppPayment__c)
- The filter group (which Opportunities count)
- The operation (SUM, COUNT, AVERAGE, FIRST, LAST, LARGEST, SMALLEST)
- The target object and field

Adding custom rollup fields requires creating new `Rollup__mdt` and `Filter_Group__mdt` records through the CRLP UI (Setup > Nonprofit Success Pack > Customizable Rollups). Direct API manipulation of these metadata records without understanding the required lookup relationships will break rollup calculations silently.

### Program Management Module (PMM) Object Model

PMM is a separate managed package (`pmdm__` namespace) that tracks program enrollment and service delivery. Its core objects are:

- **`pmdm__Program__c`** — The program itself (e.g., "Youth Tutoring"). Has `pmdm__Status__c`, `pmdm__StartDate__c`, `pmdm__EndDate__c`.
- **`pmdm__ProgramEngagement__c`** — The enrollment junction between a Contact and a Program. Has `pmdm__Contact__c`, `pmdm__Program__c`, `pmdm__Stage__c` (Active, Waitlisted, Completed, Withdrawn), and `pmdm__StartDate__c`.
- **`pmdm__ServiceDelivery__c`** — An individual unit of service delivered to a Contact within an Engagement. Has `pmdm__Contact__c`, `pmdm__ProgramEngagement__c`, `pmdm__DeliveryDate__c`, `pmdm__Quantity__c`, and `pmdm__Service__c`.

PMM objects are related to NPSP Contacts but PMM does not share namespace or package dependencies with NPSP core. An org can run PMM without NPSP, though this is rare.

---

## Common Patterns

### Constituent 360 Query: Full Giving and Program History for a Contact

**When to use:** Building a constituent summary view, reporting dashboard, or data migration validation that requires giving history, rollup totals, and program participation.

**How it works:**

```soql
-- Get constituent giving summary (rollup fields live on both Contact and HH Account)
SELECT
    Id,
    Name,
    AccountId,
    Account.Name,
    npo02__TotalOppAmount__c,
    npo02__LastOppAmount__c,
    npo02__LastCloseDate__c,
    npo02__ConsecutiveYearsGiven__c,
    npo02__OppAmountLastYear__c
FROM Contact
WHERE Id = :contactId

-- Get individual gift transactions for this constituent's household
SELECT Id, Name, Amount, CloseDate, StageName, npsp__Primary_Contact__c
FROM Opportunity
WHERE AccountId = :householdAccountId
  AND IsWon = true
ORDER BY CloseDate DESC

-- Get program participation
SELECT
    Id,
    pmdm__Program__r.Name,
    pmdm__Stage__c,
    pmdm__StartDate__c
FROM pmdm__ProgramEngagement__c
WHERE pmdm__Contact__c = :contactId

-- Get service deliveries
SELECT
    Id,
    pmdm__DeliveryDate__c,
    pmdm__Quantity__c,
    pmdm__Service__r.Name,
    pmdm__ProgramEngagement__r.pmdm__Program__r.Name
FROM pmdm__ServiceDelivery__c
WHERE pmdm__Contact__c = :contactId
ORDER BY pmdm__DeliveryDate__c DESC
```

**Why not the alternative:** Querying only the Contact record misses the gift transactions on the Household Account. Rollup fields may lag real-time transactions by the CRLP recalculation window; always query raw Opportunities for authoritative transaction data.

### Custom Rollup via CRLP Configuration

**When to use:** An org needs a rollup value not covered by NPSP's default rollup fields (e.g., total giving to a specific campaign, major gift count above a threshold).

**How it works:**

1. In Setup, navigate to Nonprofit Success Pack > Customizable Rollups.
2. Create a new `Filter_Group__mdt` record defining the criteria (e.g., `Type = 'Major Gift'`).
3. Create a new `Rollup__mdt` record pointing to the filter group, source field (`Amount`), operation (`SUM`), target object (`Contact`), and target field (a custom currency field you pre-create).
4. Run the Recalculate All Rollups batch job to populate historical data.
5. After enabling, CRLP will update the field in near-real-time on new and changed Opportunities.

**Why not the alternative:** Standard Salesforce rollup summary fields on Account do not understand the Contact-to-Household Account relationship for per-Contact aggregation. Formula fields cannot aggregate across multiple records. Custom Apex triggers on Opportunity are fragile and conflict with NPSP's own Opportunity trigger framework.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need lifetime giving total for a Contact | Read `npo02__TotalOppAmount__c` on Contact | Maintained by CRLP; faster than aggregate SOQL for display purposes |
| Need authoritative real-time total | Aggregate SOQL on Opportunity WHERE AccountId = HH Account | Rollup fields may lag by CRLP recalculation window |
| Need program enrollment history | Query `pmdm__ProgramEngagement__c` WHERE pmdm__Contact__c | PMM junction object; requires pmdm__ package installed |
| Need to add a custom donation rollup | Create Rollup__mdt + Filter_Group__mdt via CRLP UI | Safest extension path; avoids conflicts with NPSP trigger framework |
| Org is on Nonprofit Cloud (NPC), not NPSP | Stop — use NPC data model skill instead | NPC and NPSP use incompatible foundational objects; NPSP patterns do not apply |
| Org has FSC Household Groups alongside NPSP | Confirm packages; treat as separate architectures | FSC uses AccountContactRelationship-based Household Group object, not HH_Account record type |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Verify the installed package set.** Confirm `npo02__` namespace is queryable (NPSP core), whether `pmdm__` is installed (PMM), and whether `npsp__` settings records exist. Run `SELECT Id, Name FROM npo02__Household_Settings__c LIMIT 1` — if it returns data, NPSP is installed and active.
2. **Identify the constituent model.** Query `SELECT Id, Name FROM RecordType WHERE SObjectType = 'Account' AND Name = 'Household Account'` to confirm the HH_Account record type is present. If absent, the org may be on One-to-One or Individual model — do not assume HH_Account model.
3. **Check CRLP status.** Navigate to NPSP Settings > Rollup Settings to confirm CRLP is enabled or disabled. In CRLP-enabled orgs, do not modify `npo02__Settings__c.npo02__Rollup_N_Day_Value__c` or related legacy fields — they are ignored by the CRLP engine and changes create confusion.
4. **Design queries using the three-layer model.** For giving data, join Contact → Account (HH_Account) → Opportunity. For program data, join Contact → pmdm__ProgramEngagement__c → pmdm__Program__c and pmdm__ServiceDelivery__c. Never query Opportunity.ContactId for NPSP gift records — NPSP stores the primary contact via `npsp__Primary_Contact__c` on Opportunity, not via a standard contact role in all configurations.
5. **Validate rollup field values against raw transactions.** Before trusting any `npo02__` rollup field in a report or migration, verify it matches an aggregate SOQL query on the underlying Opportunities. Stale rollups from legacy batch mode or a failed CRLP job are a common source of data quality defects.
6. **Document namespace dependencies in any solution.** Any SOQL, Flow, or Apex that references `npo02__`, `npsp__`, `npe01__`, or `pmdm__` fields will fail in orgs without those packages. Add an org-detection guard at the start of any script that accesses these fields.
7. **Run the NPSP Health Check before any schema change.** Available under Nonprofit Success Pack > System Tools > NPSP Health Check. Identifies configuration problems that would cause your changes to behave unexpectedly.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Confirmed org is NPSP (not Nonprofit Cloud / NPC) before applying any guidance from this skill
- [ ] Verified constituent model is HH_Account and not One-to-One or Individual
- [ ] CRLP enabled/disabled status documented and respected in any rollup-related work
- [ ] PMM package presence confirmed before referencing any `pmdm__` objects or fields
- [ ] All SOQL queries use `AccountId` on Opportunity (pointing to HH Account) rather than ContactId for gift queries
- [ ] Rollup field values validated against aggregate SOQL on raw Opportunity records
- [ ] Namespace dependencies documented for any solution that will be deployed to other orgs

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Opportunities link to the Household Account, not to the Contact** — In the NPSP Household Account model, `Opportunity.AccountId` points to the HH_Account, not to the individual Contact. The relationship to the primary constituent is stored in `npsp__Primary_Contact__c` (a lookup to Contact on the Opportunity object). Code or reports that filter `Opportunity.ContactId IS NOT NULL` to find constituent gifts will return no results or incorrect results.

2. **CRLP and legacy rollup mode cannot safely coexist** — Orgs that partially migrate to CRLP without disabling the legacy `RLLP_OppRollup_BATCH` scheduled job will run both engines simultaneously. The result is unpredictable: rollup fields may be doubled, zeroed, or overwritten in alternating directions. Always confirm one engine is fully disabled before enabling the other.

3. **PMM is a separate managed package from NPSP core** — The `pmdm__` namespace is the Program Management Module package, installed separately from NPSP. It is common to encounter NPSP orgs where PMM is not installed. Any code, Flow, or SOQL referencing `pmdm__ServiceDelivery__c`, `pmdm__ProgramEngagement__c`, or `pmdm__Program__c` will throw errors in NPSP orgs without PMM. Always check installed packages before assuming PMM objects are available.

4. **HH Account record type name is configurable** — The default record type for household accounts is named "Household Account" but NPSP allows it to be renamed. Queries using `RecordType.Name = 'Household Account'` will break in orgs where the record type was renamed. Use `RecordType.DeveloperName = 'HH_Account'` (the developer name is fixed) for reliable filtering.

5. **npo02__ rollup fields exist on Contact AND on Account — with different scopes** — Rollup fields on the Contact aggregate gifts where `npsp__Primary_Contact__c` equals that Contact. Rollup fields on the Household Account aggregate all gifts linked to that Account, regardless of primary contact. Both sets have the same field names (e.g., `npo02__TotalOppAmount__c`). Using the wrong object in a report produces systematically wrong totals without any error.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Constituent 360 data model diagram | Three-layer NPSP model: HH_Account → Contact → npo02__ rollup fields, with Opportunity and PMM objects mapped |
| SOQL query library | Namespace-aware queries for giving history, rollup validation, and program participation |
| CRLP configuration checklist | Steps to add or validate a custom rollup via Rollup__mdt and Filter_Group__mdt |
| PMM availability guard | Python/Apex pattern to detect PMM installation before accessing pmdm__ objects |

---

## Related Skills

- `data/npsp-data-model` — Overlapping skill covering NPSP object relationships; this skill focuses specifically on constituent 360 and rollup architecture
- `admin/npsp-household-accounts` — Household Account configuration, naming formats, and primary contact designation
- `architect/npsp-vs-nonprofit-cloud-decision` — Decision framework for orgs choosing between NPSP and NPC; must be resolved before applying this skill
