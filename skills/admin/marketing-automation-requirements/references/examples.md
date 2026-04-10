# Examples — Marketing Automation Requirements

## Example 1: Documenting a Score + Grade MQL for a B2B SaaS Org

**Context:** A B2B SaaS company is implementing MCAE for the first time. The marketing team has been manually reviewing leads in a spreadsheet. The sales team complains that marketing sends over unqualified contacts. The project team needs a requirements document before the MCAE implementation team can configure scoring and automation rules.

**Problem:** The initial requirements draft from the marketing manager specifies only "score >= 100" as the MQL threshold and leaves the sales SLA blank. The implementation team has no way to know what grade Profile criteria to configure, how decay should work, or what CRM field updates should fire on handoff. Without a grade gate, a competitor doing competitive research or a student writing a thesis could easily score 100+ points from email opens and page views.

**Solution:**

Requirements document excerpt (scoring model specification section):

```
SCORING SOURCES AND WEIGHTS
Activity                    Points      Rationale
--------------------------  ----------  ------------------------------------------
Demo request form fill      +75         High-intent gate; single fill qualifies alone
Pricing page view           +10         Overrides default page view weight (1 pt)
Content download (any)      +10         Indicates evaluation phase
Email link click            +5          Standard engagement signal
Email open                  +1          Weak signal; counted only in absence of clicks
Tracked page view (other)   +1          Default; background engagement
Webinar registration        +15         Intent to learn; strong signal
Unsubscribe                 -50         Disqualification signal
Hard bounce                 -75         Data quality failure; remove from scoring

SCORE DECAY RULES
Rule 1: -10 points after 30 days of no tracked activity
Rule 2: -20 additional points after 60 days of no tracked activity
Decay does not reduce score below 0.

CEILING SCORE: 200 points. No additional points awarded above 200.

GRADE PROFILE: Enterprise Technology Segment
Positive criteria:
  - Title contains "VP", "Director", "Head of", "C-level"  → +20 grade points
  - Industry = Technology OR Software OR SaaS              → +15 grade points
  - NumberOfEmployees >= 200                               → +10 grade points
  - Annual Revenue >= 10,000,000                           → +10 grade points
Negative criteria:
  - Title contains "Student", "Intern", "Researcher"       → -20 grade points
  - Industry = Education OR Non-profit                     → -15 grade points
  - Country not in {US, CA, GB, AU, DE}                   → -10 grade points

MQL THRESHOLD (agreed and signed off):
Score >= 100 AND Grade >= B
Sign-off: Jane Smith (VP Marketing) and Tom Brown (VP Sales) — 2026-04-05

HANDOFF MECHANISM:
- MCAE Automation Rule fires when threshold is crossed
- CRM field updates: Is_MQL__c = true, MQL_Date__c = today, Lifecycle_Stage__c = "MQL"
- Creates CRM Task on Lead: Subject = "New MQL: [Prospect Name] — follow up within 24h"
- Sends alert email to assigned Sales rep via MCAE Notification
- Assigns Lead to "Enterprise SDR Queue"

SALES SLA:
- Accept or recycle within 1 business day
- Recycle requires Recycle_Reason__c selection (Picklist: Timing / Wrong Persona / Competitor / No Budget)
- Recycled leads return to MCAE nurture program "Recycle - Re-Engagement"
```

**Why it works:** This specification gives the MCAE implementation team every value they need to configure scoring rules, decay, the grade Profile, the Automation Rule, and the CRM field update actions without making judgment calls. The sign-off record prevents scope creep or threshold renegotiation after go-live.

---

## Example 2: Distinguishing MCAE Engagement Studio from MCE Automation Studio in Requirements

**Context:** A retail financial services company is migrating from a manual email process to a hybrid MCAE + Marketing Cloud Engagement setup. The project manager writes a requirements document that describes "automation" using terms from both platforms interchangeably, creating confusion about which engine handles which process.

**Problem:** The requirements document states: "When a prospect scores >= 75, use Automation Studio to run a SQL query that updates the lead's status and assigns it to the inside sales queue." This is technically incorrect: Automation Studio in MCE does not evaluate individual prospect scores in real time and cannot perform CRM record updates through a SQL query. The MCE Automation Studio SQL activity runs against Marketing Cloud data extensions, not Salesforce CRM records. Attempting to implement this requirement as written would require a multi-step custom integration that was not in scope.

**Solution:**

The requirements document must be corrected to separate the two automation scopes:

```
MCE AUTOMATION STUDIO SCOPE (batch, scheduled):
- Nightly data extract: sync Contact opt-out status from CRM to Marketing Cloud
- Weekly data import: refresh suppression list from CRM Campaign members
- Scheduled SQL activity: aggregate email engagement stats into Engagement_Summary__c
  data extension for B2B Marketing Analytics reporting
These activities run on a scheduled cadence (nightly/weekly). They do not
evaluate individual prospect scores and do not perform real-time routing.

MCAE ENGAGEMENT STUDIO / AUTOMATION RULES SCOPE (prospect-level, near-real-time):
- Automation Rule: fires when Prospect Score >= 75 AND Grade >= B
  Actions: Assign to Sales Queue, Create CRM Task, Update Is_MQL__c = true,
           Update MQL_Date__c, Send rep alert email
- Engagement Studio Program: 8-week nurture sequence for prospects with Score < 50
  Logic: wait 7 days → check Score → if Score >= 50 send "hot" email → else send
         standard nurture email → repeat
These activities evaluate individual prospects in near-real-time and perform
direct CRM record updates through the MCAE CRM connector.
```

**Why it works:** Separating the two automation scopes eliminates the ambiguity that caused the original error. The MCAE implementation team knows exactly which engine handles each process type. The MCE configuration team knows their scope is batch data operations, not real-time lead routing.

---

## Anti-Pattern: Setting MQL Threshold Without Sales Alignment

**What practitioners do:** The marketing operations manager, under time pressure, sets the MQL threshold at Score >= 80 based on the platform default and the team's intuition, then launches the automation program without a formal sign-off session with the Sales leadership.

**What goes wrong:** The Sales team finds the quality of inbound MQLs too low — many are low-fit contacts who engaged with gated content for research purposes. Sales stops accepting MQLs from the queue, marketing continues sending them, and the MQL acceptance rate drops to below 10%. Both teams blame the platform rather than the requirements process. The project is considered a failure despite correct technical implementation.

**Correct approach:** Requirements gathering must include a dedicated MQL alignment session with both VP of Marketing and VP of Sales (or their designees) as mandatory attendees. The session outputs a written threshold agreement with approver names and date. The requirements document is not complete — and implementation cannot begin — until this sign-off is obtained. If agreement cannot be reached, escalate to shared leadership rather than defaulting to a marketing-set threshold.
