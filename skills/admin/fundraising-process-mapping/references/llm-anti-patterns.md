# LLM Anti-Patterns — Fundraising Process Mapping

Common mistakes AI coding assistants make when generating or advising on fundraising process mapping in Salesforce nonprofit implementations.

## Anti-Pattern 1: Recommending NPSP Engagement Plan Setup on NPC Orgs

**What the LLM generates:** When asked to design stewardship automation for a Nonprofit Cloud (NPC) org, the LLM recommends creating `npsp__Engagement_Plan_Template__c` records, navigating to NPSP Settings > Engagement Plans, and configuring engagement plan templates.

**Why it happens:** Training data contains a high volume of NPSP documentation and community content about Engagement Plans for stewardship. The LLM conflates "nonprofit Salesforce" with "NPSP" and does not distinguish between the NPSP managed package and Nonprofit Cloud. The NPSP Engagement Plans feature is well-documented and commonly recommended; the NPC divergence is a more recent and less-represented fact.

**Correct pattern:**

```
For Nonprofit Cloud (NPC) orgs:
- Do NOT reference npsp__Engagement_Plan_Template__c or NPSP Settings > Engagement Plans
- The Engagement Plans feature exists only in the NPSP managed package
- For stewardship task automation in NPC, use:
  1. Salesforce Flow (Record-Triggered or Scheduled Path) to generate Task records
  2. Sales Engagement Cadences if the org has that license
  3. Custom Flow templates designed around the GiftTransaction or Opportunity objects in NPC
```

**Detection hint:** Any response containing `npsp__Engagement_Plan` in an NPC context, or recommending navigation to "NPSP Settings > Engagement Plans" when the org is post-December 2025 or confirmed as NPC.

---

## Anti-Pattern 2: Assuming NPSP Is Installed Without Verification

**What the LLM generates:** Guidance that directly references NPSP namespace fields (`npsp__Amount_Outstanding__c`, `npsp__Soft_Credit_Amount__c`), NPSP-specific Setup menus, or NPSP-managed objects for any nonprofit org, without first confirming NPSP is installed.

**Why it happens:** "Nonprofit Salesforce" is strongly associated with NPSP in training data. The LLM defaults to NPSP-specific guidance without considering that the org may be on NPC, a blank Salesforce org, or a standard Sales Cloud instance with custom nonprofit fields.

**Correct pattern:**

```
Before any NPSP-specific guidance:
1. Verify: Setup > Installed Packages > search for "Nonprofit Success Pack" or namespace "npsp"
2. If NPSP is present → apply NPSP-specific guidance
3. If NPSP is absent AND org was created before Dec 2025 → investigate what platform is in use
4. If org was created after December 2025 → assume NPC unless NPSP namespace is confirmed present
```

**Detection hint:** Any response that recommends `npsp__` namespace fields or NPSP Setup menus without a preceding verification step.

---

## Anti-Pattern 3: Recommending Generic Sales Stage Names for Nonprofit Fundraising

**What the LLM generates:** When asked to configure Opportunity stages for a nonprofit's fundraising pipeline, the LLM recommends standard commercial Salesforce stage names: "Prospecting," "Qualification," "Needs Analysis," "Value Proposition," "Id. Decision Makers," "Perception Analysis," "Proposal/Price Quote," "Negotiation/Review," "Closed Won," "Closed Lost."

**Why it happens:** These stages are the Salesforce out-of-the-box defaults and are heavily represented in Salesforce documentation and training data. The LLM maps "pipeline stages" to the commercial default without recognizing the nonprofit fundraising lifecycle as a distinct domain.

**Correct pattern:**

```
For nonprofit major gift fundraising, stages should reflect the donor cultivation lifecycle:
- Identification (prospect identified)
- Qualification (capacity and interest confirmed)
- Cultivation (relationship building; strategy active)
- Solicitation (formal ask delivered)
- Verbal Commitment (donor says yes before paperwork)
- Pledged / Closed Won (signed pledge agreement)
- Closed Lost (donor declines)

For grants, stages should reflect the grant calendar:
- Letter of Inquiry
- Application Submitted
- Under Review
- Awarded / Closed Won
- Declined / Closed Lost

Stage names must come from the development team, not from Salesforce defaults.
```

**Detection hint:** Any response that includes "Needs Analysis," "Value Proposition," "Perception Analysis," or "Id. Decision Makers" in a nonprofit fundraising context.

---

## Anti-Pattern 4: Treating Stage Rename as a Zero-Impact Operation

**What the LLM generates:** When asked how to rename an Opportunity stage value, the LLM says to go to Setup > Object Manager > Opportunity > Stage Field > Edit the picklist value > change the label. It presents this as complete, with no mention of the impact on existing records, reports, or automation.

**Why it happens:** The LLM describes the UI action correctly but fails to reason about the downstream consequences. Picklist value renaming in Salesforce updates the picklist definition only — it does not mass-update existing records. The LLM does not model the gap between "the picklist value was renamed" and "all records using the old value are now updated."

**Correct pattern:**

```
Stage rename process (safe sequence):
1. Query records using the old stage name to understand data volume:
   SELECT StageName, COUNT(Id) FROM Opportunity WHERE StageName = 'OldName' GROUP BY StageName
2. Plan a data update job (Dataloader or Bulk API) to replace OldName with NewName on all records
3. Execute data update in sandbox first; validate report results
4. Update all Flows, Process Builder processes, validation rules, and Apex that reference OldName by value
5. Rename the picklist value in Setup
6. Deactivate (do not delete) the old picklist value
7. Confirm all reports and automation are functioning correctly
```

**Detection hint:** Any stage rename guidance that does not mention a data update job or does not address existing records.

---

## Anti-Pattern 5: Conflating Fundraising Process Design with Engagement Plan Implementation

**What the LLM generates:** When asked to "map the fundraising process" or "design the cultivation-to-stewardship workflow," the LLM immediately jumps to implementation guidance — how to create Engagement Plan Templates, how to configure task cadences, how to build Flow automation for stage changes. It skips the upstream design step entirely.

**Why it happens:** The LLM defaults to actionable implementation steps because that is what most Salesforce guidance documents cover. Process design documentation (stage maps, entry/exit criteria, role assignments) is an upstream activity that appears less frequently in technical training data. The LLM optimizes for appearing helpful by immediately producing implementation artifacts.

**Correct pattern:**

```
Fundraising process mapping is a DESIGN activity, not an implementation activity.
The correct sequence is:
1. Document the stage map (names, probabilities, entry criteria, exit criteria, responsible roles)
2. Get development leadership sign-off on the stage vocabulary
3. THEN pass the approved design to implementation for:
   - Salesforce stage picklist configuration
   - Engagement Plan templates (NPSP only)
   - Flow automation
   - Report and dashboard design

Do not build Engagement Plans, Flows, or picklist configurations until the stage design document is approved.
```

**Detection hint:** Any response to a "map the process" or "design the workflow" prompt that jumps directly to implementation steps (Engagement Plan setup, Flow configuration) without first producing a stage design document.

---

## Anti-Pattern 6: Ignoring NPSP's Four Distinct Sales Processes

**What the LLM generates:** When a nonprofit needs fundraising stage configuration, the LLM recommends creating a single "Fundraising" Opportunity Record Type with a single "Fundraising" Sales Process containing all stage values from all program types combined.

**Why it happens:** The LLM may not be aware that NPSP ships four separate sales processes for distinct program types, or may over-simplify for brevity. Consolidation seems administratively simpler but destroys the per-program-type stage separation that makes pipeline reporting meaningful.

**Correct pattern:**

```
NPSP ships four pre-configured Opportunity sales processes — maintain them separately:
- Donation process: annual fund, direct mail, unrestricted gifts
- Grant process: institutional grants (foundation, government, corporate)
- In-Kind process: non-cash donations
- Major Gift process: major donor cultivation (Moves Management)

Each process has stage values appropriate to its lifecycle. Do NOT merge these into a
single process. If the org does not run all four program types, inactive record types
can be hidden from users, but the separation should be preserved for future use.
```

**Detection hint:** Any recommendation to create a single combined fundraising Sales Process or to merge all program types into one Opportunity Record Type.
