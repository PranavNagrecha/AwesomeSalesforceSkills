# LLM Anti-Patterns — Marketing Reporting Requirements

Common mistakes AI coding assistants make when generating or advising on Marketing Reporting Requirements.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Choosing the Attribution Model After Describing the Dashboard

**What the LLM generates:** A detailed dashboard design with campaign ROI tiles, pipeline charts, and email engagement metrics — and then, at the end, asks "which attribution model do you want to use?" or picks First Touch by default without flagging the decision.

**Why it happens:** LLMs are trained on tutorial content that starts with the visible artifact (the dashboard) rather than the upstream decision that determines the data model. Attribution model selection feels like a configuration detail but is actually a prerequisite that determines which report types, objects, and features are available.

**Correct pattern:**

```
Step 1: Attribution model decision
  - Present four options with feature requirements
  - Confirm license availability
  - Get explicit business rationale and sign-off
  - Document: chosen model, required Salesforce feature,
    prerequisites (Contact Roles, CCI, lookback window)

Step 2: KPI definition register
  - Map each KPI to a Salesforce source given the chosen model

Step 3: Report type selection and dashboard design
```

**Detection hint:** Look for any marketing reporting response that describes dashboard components or report types before explicitly stating the attribution model. If the attribution decision appears after any reporting design work, the order is wrong.

---

## Anti-Pattern 2: Conflating Marketing-Sourced and Marketing-Influenced Pipeline

**What the LLM generates:** A single report or dashboard component labeled "Marketing Pipeline" that mixes Opportunities where the Primary Campaign Source is set (sourced) with Opportunities that appear in Campaign Influence records (influenced). The number reported is neither metric accurately.

**Why it happens:** LLMs see both metrics described in Salesforce documentation and consolidate them into a single concept to simplify the answer. The distinction between "sourced" (first touch only, one campaign gets full credit) and "influenced" (any touch, one or more campaigns get credit) requires careful reading of the Campaign Influence documentation.

**Correct pattern:**

```
Marketing-Sourced Pipeline:
  Source: Opportunity.Primary_Campaign_Source__c IS NOT NULL
  Report type: Opportunities with Campaigns
  Attribution: First Touch — one campaign per opportunity

Marketing-Influenced Pipeline:
  Source: CampaignInfluence object records
  Report type: Opportunities with Campaign Influence
  Attribution: All campaigns with a CI record on the Opportunity
  Requires: Campaign Influence enabled, Contact Roles populated

These are SEPARATE dashboard tiles with SEPARATE report types.
Never sum or combine them in the same metric.
```

**Detection hint:** Look for any report or dashboard tile that references both "Primary Campaign Source" and "Campaign Influence" as inputs to the same metric. Also flag any response that uses the term "marketing pipeline" without specifying sourced vs influenced.

---

## Anti-Pattern 3: Recommending Campaign Influence Without Checking Contact Role Population

**What the LLM generates:** Instructions to enable Campaign Influence or Customizable Campaign Influence in Setup, configure a model, and then build attribution reports — without first verifying that Opportunity Contact Roles are consistently populated.

**Why it happens:** The Salesforce documentation describes Campaign Influence setup as a configuration task (enable the feature, set the lookback window, choose a model). The dependency on Opportunity Contact Roles is documented separately and LLMs frequently omit it when generating setup instructions.

**Correct pattern:**

```
Pre-enablement check for Campaign Influence:
1. Run a report: Opportunities (all time)
   Group by: Has Contact Role (custom formula or Related field)
   Check: What % of Opportunities have at least one Contact Role?
   
   If < 80%: Campaign Influence will return incomplete data.
   Remediation required before enablement makes sense.

2. Only after Contact Role population is confirmed ≥ 80%:
   Setup > Campaign Influence > Enable
   Set lookback window to match sales cycle length
   Select attribution model
```

**Detection hint:** Any Campaign Influence setup recommendation that does not include a Contact Role population check is missing a critical prerequisite. Flag responses that jump directly to "go to Setup > Campaign Influence."

---

## Anti-Pattern 4: Treating the Campaign Performance Report as a Full Attribution Report

**What the LLM generates:** A recommendation to use the Campaign Performance Report as the primary marketing attribution report, with "Value Won" described as "revenue attributed to marketing campaigns."

**Why it happens:** The Campaign Performance Report is the most prominent native report type in the Campaigns module and its "Value Won" column appears to answer the attribution question. LLMs trained on Salesforce help content frequently reference it as the answer to "how do I measure campaign ROI." The report is useful, but "Value Won" reflects first-touch Opportunity amount on the Primary Campaign Source only — it is not influenced revenue and does not capture multi-touch attribution.

**Correct pattern:**

```
Campaign Performance Report — What it actually measures:
  - Leads, Contacts added to campaign
  - Opportunities where this campaign = Primary Campaign Source
  - Won Opportunities (Primary Campaign Source, first touch only)
  - Value Won = sum of Opportunity Amount, first touch only

For influenced revenue (any touch):
  - Use the Opportunities with Campaign Influence report type
  - Source: CampaignInfluence.Revenue field
  - Requires Customizable Campaign Influence enabled

Label "Value Won" as "First-Touch Revenue" in any dashboard
to prevent stakeholder misinterpretation.
```

**Detection hint:** Any response that describes "Value Won" from the Campaign Performance Report as "marketing attribution revenue" or "campaign ROI numerator" without qualification. Also flag recommendations to use Campaign Performance Report for multi-touch or influenced pipeline metrics.

---

## Anti-Pattern 5: Recommending B2B Marketing Analytics Plus as the Default for All Marketing Reporting

**What the LLM generates:** A recommendation to use MCAE B2B Marketing Analytics Plus (Einstein Analytics / CRM Analytics) for all marketing KPIs, including basic ones like email open rate, cost per lead, and campaign performance — regardless of whether the org has the license or whether native reports would suffice.

**Why it happens:** LLMs associate "marketing analytics" with "advanced analytics tools" and recommend the most capable-sounding option. B2B Marketing Analytics Plus is the most sophisticated Salesforce marketing analytics product, so it gets recommended as a universal solution. The license cost ($$$), dataset refresh lag (daily by default), and implementation complexity are not factored in.

**Correct pattern:**

```
Native Salesforce reports cover (no add-on required):
  - Campaign Performance Report: leads, contacts, opps, value won
  - Campaign Member status reports: email engagement (open, click)
  - Opportunities with Campaign Influence: influenced pipeline (CCI)
  - Cost per lead: Campaign Cost / Campaign Member count (formula)

B2B Marketing Analytics Plus adds (separate license required):
  - Time-decay and position-based multi-touch attribution
  - Engagement score trend dashboards
  - Cross-object blended datasets with scheduled refresh
  - Einstein Attribution AI model

Recommendation rule:
  If KPIs are first-touch or single-touch influenced → native reports
  If KPIs require time-decay or position-based multi-touch → B2B MA+
  Document the license requirement before recommending B2B MA+
```

**Detection hint:** Any recommendation for B2B Marketing Analytics Plus that does not mention the separate license requirement, or that recommends it for KPIs that are available natively (email open rate, campaign performance, first-touch pipeline).

---

## Anti-Pattern 6: Not Distinguishing MC Next Campaign Intelligence from Standard Salesforce Reports

**What the LLM generates:** Instructions for accessing "Marketing Campaign Intelligence Dashboards" without clarifying whether the org has Marketing Cloud Next (MC Growth) provisioned. The LLM treats Campaign Intelligence dashboards as a standard Salesforce feature available to all orgs.

**Why it happens:** Salesforce help documentation describes Marketing Campaign Intelligence Dashboards in the context of MC Next / MC Growth, but LLMs conflate this with the broader Salesforce reporting ecosystem. Orgs without MC Next provisioning cannot access these dashboards, and attempting to navigate to them produces errors.

**Correct pattern:**

```
Marketing Campaign Intelligence Dashboards:
  Availability: Marketing Cloud Next (MC Growth) only
  NOT available in: standard Salesforce + MCAE setups
  
For orgs WITHOUT MC Next:
  Email engagement: Campaign Member status-based reports
  Conversion rates: Campaign Performance Report with formulas
  Revenue influenced: CCI-backed Opportunity reports

Verify before recommending:
  Does the org have MC Next / MC Growth provisioned?
  If yes: Campaign Intelligence dashboards are available
  If no: Use native Salesforce report types instead
```

**Detection hint:** Any response that recommends "Marketing Campaign Intelligence Dashboards" without first confirming MC Next provisioning status.
