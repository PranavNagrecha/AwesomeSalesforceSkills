# LLM Anti-Patterns — Campaign Planning And Attribution

Common mistakes AI coding assistants make when generating or advising on Campaign Planning And Attribution. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Treating Standard Campaign Influence and Customizable Campaign Influence as the Same Feature

**What the LLM generates:** Advice like "enable Campaign Influence in Setup and configure your attribution model" — conflating the legacy auto-association system with CCI. Or code that queries `CampaignInfluence` while assuming standard influence rules are producing the records, when CCI was actually the intended framework.

**Why it happens:** Both features are called "Campaign Influence" in documentation and the Setup menu. Training data contains references to both without clearly distinguishing them. LLMs pattern-match on the shared name and merge the two systems into one conceptual model.

**Correct pattern:**

```
Standard Campaign Influence (legacy):
- Automatically creates CampaignInfluence records based on time-window rules
- Only one model active at a time
- Configured via: Setup > Campaign Influence > Auto-Association Rules

Customizable Campaign Influence (CCI):
- Requires explicit enablement: Setup > Campaign Influence > Customizable Campaign Influence
- Supports multiple simultaneous models (first-touch, last-touch, even, custom)
- Standard influence auto-association should be DISABLED before CCI is used
- CampaignInfluence records include a ModelId field to distinguish which model produced them
```

**Detection hint:** If the response describes attribution models but does not mention "Customizable Campaign Influence" by name, or does not reference the `ModelId` field on `CampaignInfluence`, it may be conflating the two systems.

---

## Anti-Pattern 2: Advising That Campaign Hierarchy Rollup Fields Update in Real Time

**What the LLM generates:** Statements like "when you close an opportunity linked to a child campaign, the parent campaign's `AmountWonOpportunities` will immediately reflect the new total" — or automation designs that trigger from a parent Campaign rollup field change expecting real-time behavior.

**Why it happens:** LLMs understand that rollup fields aggregate child data but often fail to distinguish between formula fields (which recalculate on read) and scheduled-batch rollup fields (which update asynchronously). Campaign Hierarchy rollups fall into the latter category, but this is a non-obvious platform constraint that does not surface prominently in general Salesforce documentation.

**Correct pattern:**

```
Campaign Hierarchy rollup fields (AmountWonOpportunities, ActualCost, NumberOfLeads, etc.)
are updated by Salesforce's batch scheduler — NOT in real time.

- Do NOT build automation that depends on these fields as real-time event sources
- Do NOT tell stakeholders that parent Campaign totals are live during active campaigns
- For real-time opportunity revenue, query the Opportunity object directly
- For real-time campaign spend, query child Campaign ActualCost directly
- Use parent Campaign rollups for historical/retrospective program-level reporting only
```

**Detection hint:** Any response that says "immediately reflects," "updates automatically when," or "triggers on parent Campaign change" in the context of Campaign Hierarchy rollup fields is likely incorrect.

---

## Anti-Pattern 3: Claiming CCI Works Without Contact Roles on Opportunities

**What the LLM generates:** CCI setup instructions that describe enabling the feature and configuring models, but omit any mention of Contact Role requirements. Or debugging advice that checks CCI model configuration without checking for missing Contact Roles on the Opportunity.

**Why it happens:** Contact Role is a separate related list on the Opportunity and its role as a prerequisite for CCI attribution is easy to overlook. Training data emphasizes model configuration steps (the "how to set up CCI" path) more than the Contact Role dependency (the "why is CCI not producing records" path).

**Correct pattern:**

```
CCI attribution chain:
Opportunity -> OpportunityContactRole -> Contact -> CampaignMember -> Campaign

If any link in this chain is missing, CampaignInfluence records are NOT created.

Prerequisite check before assuming CCI is misconfigured:
SELECT Id, Name, (SELECT ContactId FROM OpportunityContactRoles)
FROM Opportunity
WHERE Id = '<opportunity_id>'

If OpportunityContactRoles is empty -> no CampaignInfluence records will exist.
Fix: add Contact Role, then re-run influence calculation.
```

**Detection hint:** CCI setup guidance that does not mention "Contact Role" or `OpportunityContactRole` is likely incomplete.

---

## Anti-Pattern 4: Suggesting More Than 5 Campaign Hierarchy Levels

**What the LLM generates:** Campaign Hierarchy designs with 6 or more levels (e.g., Global > Region > Country > Business Unit > Program > Campaign > Tactic), or advice to "add as many hierarchy levels as your program structure needs."

**Why it happens:** LLMs extrapolate from tree/hierarchy concepts in software without knowing Salesforce's hard platform limit. The 5-level restriction is not obvious from general Salesforce documentation and is rarely mentioned in attribution-focused training material.

**Correct pattern:**

```
Campaign Hierarchy: maximum 5 levels (root + 4 child levels)
- Salesforce enforces this at the API and UI layer — there is no configuration to increase it
- Design hierarchies with this constraint in mind from the start

Recommended level mapping (example):
Level 1: Program (e.g., Q1 Pipeline Drive)
Level 2: Channel (e.g., Events, Email, Paid)
Level 3: Tactic (e.g., Specific Webinar, Specific Email Series)

Use Campaign custom fields (Region, Product Line, Segment) to encode additional dimensions
instead of burning hierarchy levels on dimensional attributes.
```

**Detection hint:** Any Campaign Hierarchy design with more than 4 "->" arrows (indicating 5+ levels) exceeds the platform limit.

---

## Anti-Pattern 5: Treating MCAE Multi-Touch Attribution Model Outputs as Queryable Salesforce Records

**What the LLM generates:** SOQL queries against `CampaignInfluence` filtering by a "time-decay" or "U-shaped" model, or advice to build Flows/automation that use MCAE multi-touch attribution scores from standard Salesforce objects.

**Why it happens:** CCI's `CampaignInfluence` object and MCAE's Multi-Touch Attribution App are both described as "attribution" systems. LLMs merge them into a single model where all attribution data is queryable via SOQL. The key distinction — that MCAE multi-touch models are CRM Analytics reporting-layer constructs, not Salesforce database records — is subtle and easily missed.

**Correct pattern:**

```
MCAE Multi-Touch Attribution (time-decay, U-shaped / position-based):
- Results exist ONLY in CRM Analytics datasets (B2B Marketing Analytics)
- They are NOT written to CampaignInfluence records in Salesforce
- They CANNOT be queried via SOQL
- They CANNOT be used in native Salesforce reports or Flows
- Access point: CRM Analytics dashboards only

For queryable attribution records -> use CCI (CampaignInfluence object)
  Supported models: first-touch, last-touch, even-distribution, custom Apex models
  Not supported natively: time-decay, U-shaped

If time-decay or U-shaped data is needed outside CRM Analytics:
  Export via Data Cloud or CRM Analytics scheduled dataflow
```

**Detection hint:** Any response that includes a SOQL query on `CampaignInfluence` with a `ModelId` referencing "time-decay" or "U-shaped" does not reflect how MCAE multi-touch attribution works.

---

## Anti-Pattern 6: Recommending CCI Configuration Without Disabling Standard Campaign Influence First

**What the LLM generates:** Step-by-step CCI setup that begins with "go to Setup > Campaign Influence and enable Customizable Campaign Influence" without first checking whether standard Campaign Influence auto-association rules are active.

**Why it happens:** CCI setup documentation focuses on the new feature's configuration steps. The prerequisite of disabling the legacy auto-association system is a migration concern that is treated as a footnote, and LLMs often omit footnotes from generated setup guides.

**Correct pattern:**

```
Before enabling CCI:
1. Navigate to Setup > Campaign Influence > Auto-Association Rules
2. Note any active rules (screenshot or document them for reference)
3. DISABLE all active auto-association rules
4. Verify existing CampaignInfluence records — decide whether to archive or leave them
5. NOW enable Customizable Campaign Influence
6. Configure CCI models from scratch

Rationale: With both systems active, CampaignInfluence records from the legacy system
and from CCI models co-exist with no clear visual distinction in reports.
Attribution figures become unreliable and difficult to audit.
```

**Detection hint:** CCI setup guidance that does not mention "Auto-Association Rules" or "disable standard Campaign Influence" is likely skipping this prerequisite step.
