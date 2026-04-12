# Examples — Fundraising Process Mapping

## Example 1: Mapping the Major Gift Lifecycle for a University Foundation (NPSP)

**Context:** A university foundation runs NPSP and has a major gifts program targeting prospects with capacity of $100,000 or more. Gift officers manage 50–150 prospects each and need a consistent pipeline stage vocabulary before the team builds gift officer dashboards and forecasting reports.

**Problem:** The org has seven active gift officers who each use different stage names. Some use "Cultivation 1" and "Cultivation 2" as separate stages; others skip directly to "Ask." Pipeline reports are unreliable because stage values are inconsistent, and probability percentages were never set. Leadership cannot forecast major gift revenue.

**Solution:**

First, inventory the Major Gift sales process in NPSP Setup and document all current stage values. Then convene the development team to agree on a single stage vocabulary aligned to Moves Management phases:

```
Stage Name          | Probability | Entry Criteria                              | Exit Criteria
--------------------|-------------|---------------------------------------------|-----------------------------
Identification      |  5%         | Prospect identified via wealth screening    | Qualification call scheduled
Qualification       | 10%         | First contact made; capacity confirmed      | Cultivation strategy set
Cultivation         | 25%         | Strategy defined; relationship active       | Gift discussion initiated
Solicitation        | 60%         | Formal ask proposal delivered               | Decision received
Verbal Commitment   | 75%         | Donor verbally agrees to gift               | Written pledge signed
Pledged             | 100%        | Signed pledge agreement received            | Payment schedule confirmed
Stewardship         | 100%        | Gift closed; recognition/reporting active   | (Post-close stage; no exit)
Closed Lost         |  0%         | Donor declines or prospect disqualified     | —
```

Once development leadership approves this map, the Salesforce admin updates the Major Gift Sales Process picklist to match exactly. Probability values are set per stage. Automation (stage-change Flows, engagement plan triggers) is then built against these agreed stage names.

**Why it works:** The stage map is produced as a documented design artifact before any Salesforce configuration happens. Leadership sign-off prevents post-configuration disputes. The Moves Management alignment gives gift officers a shared language — "Cultivation" means the same thing to everyone on the team. Probability values enable pipeline forecasting in standard Salesforce reports without custom calculation fields.

---

## Example 2: Stage Audit Before NPSP-to-NPC Migration for a Human Services Nonprofit

**Context:** A human services nonprofit has used NPSP since 2018. They are migrating to Nonprofit Cloud (NPC). Their current NPSP org has three Opportunity Record Types in active use: Donation, Grant, and Major Gift. They have 2,400 active Opportunity records across all three types.

**Problem:** The migration team assumed NPSP stage names would transfer to NPC automatically. In the sandbox migration test, reports broke because NPC uses different stage field mappings, and two Flows that triggered on "Solicitation" stage failed silently because the stage value did not exist in the NPC environment.

**Solution:**

Before any sandbox migration work begins, run a stage audit:

1. Export NPSP Opportunity stage picklist values per Record Type using Salesforce Setup > Object Manager > Opportunity > Fields & Relationships > Stage > Values.
2. Query active Opportunity records to count records per stage per Record Type:

```sql
SELECT StageName, RecordType.Name, COUNT(Id) cnt
FROM Opportunity
WHERE IsClosed = false
GROUP BY StageName, RecordType.Name
ORDER BY RecordType.Name, cnt DESC
```

3. Build a mapping table:

```
NPSP Stage          | NPSP Record Type | NPC Equivalent       | Notes
--------------------|------------------|----------------------|------------------------------
Prospecting         | Donation         | Prospect             | Name change only
Cultivation         | Donation         | Engaged              | Rename + confirm probability
Solicitation        | Donation         | Solicited            | Rename + update Flow references
Closed Won          | Donation         | Committed            | Automation references must update
Letter of Inquiry   | Grant            | LOI Submitted        | Rename
Under Review        | Grant            | Under Review         | No change needed
Awarded             | Grant            | Committed            | Merged with Donation Won — review
Identification      | Major Gift       | (no NPC equivalent)  | Must create new stage
```

4. For any NPSP stage with no NPC equivalent, flag it for the implementation team to create or map.
5. Identify all Flows, Process Builder processes, and Apex triggers that reference stage names by value. Update the dependency list.

**Why it works:** The audit surfaces stage mismatches before data migration. The query gives the team a data-grounded view of which stages carry active pipeline records — those are high-priority items that cannot be dropped. The dependency list prevents broken automation from making it to production.

---

## Anti-Pattern: Designing Fundraising Stages to Match CRM Vendor Defaults

**What practitioners do:** An admin inherits an NPSP org and, rather than designing stages around the fundraising team's actual workflow, keeps the Salesforce defaults ("Prospecting," "Needs Analysis," "Value Proposition," "Perception Analysis") or uses generic sales stage names because they are already in the system.

**What goes wrong:** Gift officers do not recognize sales stage names designed for commercial deals. "Needs Analysis" has no meaning in major gift fundraising. "Value Proposition" does not map to any phase of donor cultivation. The pipeline report becomes a reporting artifact that no one trusts or updates. Probability values are arbitrary. Development leadership stops using Salesforce for forecasting and reverts to spreadsheets.

**Correct approach:** The fundraising stage vocabulary must come from the development team, not from Salesforce defaults. The stage design process starts with the gift officers and development leadership agreeing on stage names before any Salesforce configuration is touched. NPSP's Major Gift sales process stages are a reasonable starting point for major gifts but should be reviewed, not accepted blindly. The Donation and Grant sales processes provide more appropriate defaults for those program types.
