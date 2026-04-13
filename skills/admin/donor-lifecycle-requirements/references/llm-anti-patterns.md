# LLM Anti-Patterns — Donor Lifecycle Requirements

Common mistakes AI coding assistants make when generating or advising on Donor Lifecycle Requirements.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending NPSP for New Nonprofits (Post December 2025)

**What the LLM generates:** Implementation guidance recommending NPSP Engagement Plans, LYBUNT reports, or NPSP Household Account model for a nonprofit client described as "setting up Salesforce for the first time."

**Why it happens:** NPSP is dominant in nonprofit Salesforce training data. LLMs recommend it by default without knowing that new production orgs can no longer be provisioned with NPSP as of December 2025.

**Correct pattern:**

```text
For new nonprofits (org created after December 2025): Nonprofit Cloud (NPC)
For existing legacy orgs: NPSP continues to be supported

When unsure: confirm by checking Installed Packages for "Nonprofit Success Pack"
If absent: assume NPC; design using NPC objects and features

NPC equivalents:
- NPSP Moves Management → NPC Portfolio Management + Actionable Segmentation
- NPSP LYBUNT report → NPC lapsed donor reports with Actionable Segmentation
- NPSP Engagement Plans → NPC Actionable Cadences
```

**Detection hint:** Any guidance recommending NPSP for a "new nonprofit" implementation should be flagged. Check the org creation date or confirm the NPSP package is installed.

---

## Anti-Pattern 2: Conflating NPC Actionable Segmentation with Email Campaign Execution

**What the LLM generates:** Workflow designs where configuring Actionable Segmentation in NPC triggers Marketing Cloud email campaigns, or instructions to "set up segmentation to send the lapsed donor email series."

**Why it happens:** The word "segmentation" in marketing contexts means audience targeting for campaign execution. LLMs apply the marketing meaning without understanding that NPC Actionable Segmentation is a CRM portfolio management feature, not a marketing automation tool.

**Correct pattern:**

```text
NPC Actionable Segmentation:
- Classifies donors into portfolio tiers (Annual Fund, Mid-Level, Major Gifts)
- Assigns donors to portfolio managers (fundraisers)
- Enables fundraiser-specific portfolio views in CRM
- Does NOT send emails, trigger automation, or connect to Marketing Cloud

For donor outreach automation:
- Marketing Cloud + Salesforce connector for email campaigns
- MCAE (Pardot) for mid-level donor nurture sequences
- Manual tasks via Actionable Cadences for high-touch major gift cultivation
```

**Detection hint:** Any design step that says "segmentation triggers email send" or "segmentation connects to Marketing Cloud" is conflation.

---

## Anti-Pattern 3: Using SOQL on Contact.npe01__TotalGifts__c for Real-Time Lapsed Calculations

**What the LLM generates:** Real-time SOQL that calculates lapsed donor status by querying Opportunity records directly (`SELECT COUNT(Id) FROM Opportunity WHERE AccountId = :acctId AND CloseDate >= LAST_N_DAYS:365`), rather than using NPSP rollup fields.

**Why it happens:** SOQL on Opportunity is the obvious programmatic approach. LLMs generate it without knowing NPSP pre-calculates rollup fields (LastOppDate, TotalGifts, NumberOfClosedOpps) on Contact/Account.

**Correct pattern:**

```soql
-- CORRECT: Use NPSP pre-calculated rollup fields
SELECT Id, Name, npsp__LastOppDate__c, npsp__TotalGifts__c, npsp__NumberOfClosedOpps__c
FROM Contact
WHERE npsp__LastOppDate__c < LAST_N_DAYS:365
AND npsp__TotalGifts__c > 0

-- Avoids real-time Opportunity aggregation queries across large datasets
-- npsp__LastOppDate__c is maintained by NPSP CRLP (Customizable Rollups)
-- Use NPSP LYBUNT report template for standard lapsed identification
```

**Detection hint:** Any lapsed donor identification SOQL that aggregates Opportunity records per Contact in real-time (COUNT or SUM in correlated subquery) should be replaced with NPSP rollup fields.

---

## Anti-Pattern 4: Designing Donor Upgrade Paths Without Using Recurring Donation Upgrade Workflows

**What the LLM generates:** Upgrade path designs that require a fundraiser to manually create a new Recurring Donation record when upgrading a donor from one-time to recurring, or manually close the old recurring and create a new one for amount upgrades.

**Why it happens:** LLMs apply generic "create a new record" logic without knowing that ERD (Enhanced Recurring Donations) provides native upgrade workflow: the Edit Recurring Donation action can increase the amount, change frequency, and log the change date — all without closing the existing donation.

**Correct pattern:**

```text
Correct ERD upgrade workflow:
1. Open existing Recurring Donation record
2. Click "Edit Recurring Donation"
3. Increase Amount (ERD logs the change date and previous amount automatically)
4. ERD creates new Opportunity installments at the new amount going forward
5. Historical installment Opportunities retain the original amount

DO NOT: Close the existing Recurring Donation and create a new one
Result of wrong approach: Loss of historical giving streak, incorrect rollups,
duplicate donor record associations
```

**Detection hint:** Any donor upgrade design that involves closing an ERD record and creating a new one should be flagged. Use the Edit Recurring Donation action to modify in place.

---

## Anti-Pattern 5: Building Cultivation Tracking Entirely on Contact Activities

**What the LLM generates:** Moves management designs that use Activity logs (Tasks and Events) on Contact as the sole tracking mechanism, with no Opportunity records until a pledge is received.

**Why it happens:** Activities are the most flexible Salesforce tracking mechanism. LLMs suggest them for "tracking relationship history" without understanding the portfolio visibility requirements of development operations.

**Correct pattern:**

```text
Activity-only cultivation tracking limitations:
- No financial pipeline projection (no Amount, Close Date fields on Activity)
- Cannot produce a major gift pipeline report by stage
- Cannot calculate expected revenue for annual fund projections
- Stage-based portfolio management requires Opportunity records

Correct approach:
- Create Opportunity when prospect enters formal cultivation
- Stage = cultivation stage (In Cultivation, Proposal Drafted, Ask Made)
- Amount = projected ask amount (estimate is acceptable)
- Close Date = expected decision date
- Activities logged on BOTH Contact (relationship history) and Opportunity (cultivation context)

Activities alone are appropriate for relationship logging on non-pipeline prospects.
```

**Detection hint:** Any moves management design that does not include Opportunity record creation for major gift prospects should be flagged for pipeline reporting capability review.
