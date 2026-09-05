# Examples — Sales Process Mapping

## Example 1: Enterprise SaaS — New Logo vs. Renewal Stage Mapping

**Context:** A mid-market SaaS company with a field sales team and a separate Customer Success team runs two distinct selling motions: new logo acquisition (8–14 stage sales cycle) and annual renewal (3-stage motion). Both are tracked on the Opportunity object. The admin was asked to "set up the stages" without a mapping document.

**Problem:** Without a prior mapping exercise, the admin created a single sales process with twelve stages that blended new-logo and renewal language. Renewal opportunities were stuck at "Demo Scheduled" because that stage had no meaning for a renewal. Forecast categories were wrong because the renewal team's "In Negotiation" stage was mapped to Pipeline instead of Commit. The VP of Sales could not trust the forecast.

**Solution — new logo stage sequence (mapping output):**

```
Stage               | Entry Criteria                        | Exit Criteria                         | Forecast Category | Probability
--------------------|---------------------------------------|---------------------------------------|-------------------|------------
Prospecting         | Lead qualified by SDR, BANT screened  | Discovery call booked                 | Pipeline          | 10%
Discovery           | Discovery call held, pain identified  | Champion identified, MEDDIC M+E filled| Pipeline          | 20%
Evaluation          | Champion confirmed, evaluation plan   | Technical win confirmed               | Best Case         | 40%
Proposal            | Technical win, economic buyer engaged | Proposal submitted and acknowledged   | Best Case         | 60%
Negotiation         | Economic buyer reviewing proposal     | Legal review initiated or verbal agree| Commit            | 80%
Contract Review     | Legal red-line in progress            | Contract fully signed                 | Commit            | 90%
Closed Won          | Contract signed by both parties       | —                                     | Closed            | 100%
Closed Lost         | Prospect chose competitor or no deal  | —                                     | Closed            | 0%
```

**Renewal stage sequence (separate Sales Process):**

```
Stage               | Entry Criteria                        | Exit Criteria                         | Forecast Category | Probability
--------------------|---------------------------------------|---------------------------------------|-------------------|------------
Renewal Outreach    | Renewal date within 90 days           | Renewal call held, intent confirmed   | Pipeline          | 70%
Renewal Negotiation | Pricing discussed                     | Contract sent                         | Commit            | 90%
Closed Won          | Signed renewal contract received      | —                                     | Closed            | 100%
Closed Lost         | Customer churned or downgraded        | —                                     | Closed            | 0%
```

**Why it works:** Separating the motions produces two Sales Processes and two Record Types in Salesforce. Renewal opportunities never appear at discovery stages. Forecast category assignments reflect the actual confidence levels of each motion independently. The handoff brief to the opportunity-management skill specifies exactly two processes, their stage names (as exact picklist strings), and their ForecastCategoryName assignments.

---

## Example 2: Manufacturing — MEDDIC Components as Entry Criteria

**Context:** A capital equipment manufacturer with a direct sales team adopted the MEDDIC methodology in their sales training but had not translated it into their Salesforce stage definitions. Reps had been trained on MEDDIC but CRM stages were generic ("Qualified", "Proposal", "Won/Lost") with no criteria. Stage data was meaningless for forecasting.

**Problem:** The mapping exercise revealed that reps interpreted "Qualified" very differently. Some moved opportunities to Qualified after a single cold call. Others required a confirmed budget conversation. The result: the Qualified stage held 40% of the pipeline with less than 5% ever closing.

**Solution — MEDDIC mapped to entry criteria:**

```
Stage           | MEDDIC Component(s) Required as Entry Criteria
----------------|------------------------------------------------
Qualified       | M — Metrics identified (business impact quantified)
                | E — Economic buyer identified by name and title
Discovery       | D — Decision criteria documented (formal or informal)
                | D — Decision process steps known (who, timeline)
Technical Win   | I — Implicated pain confirmed by champion (verbally or in writing)
Proposal        | C — Champion identified and willing to sponsor deal internally
Contract        | All MEDDIC components confirmed; verbal agreement on commercial terms
Closed Won      | Signed contract received
Closed Lost     | MEDDIC component that was never confirmed — documented in Loss Reason field
```

**Win/loss taxonomy produced in the same exercise:**

```
Win reasons: Competitive Pricing, Superior Technical Fit, Stronger Champion, Faster Delivery, Incumbent Advantage
Loss reasons: Lost to Competitor (Price), Lost to Competitor (Product), No Decision / Status Quo, Budget Eliminated, Wrong Stakeholder Engaged, Evaluation Criteria Shifted
```

**The same mapping, as the machine-readable artefact handed to configuration.** MEDDIC letters become field requirements, which is what makes the entry criterion testable rather than a coaching note. This is the shape `scripts/check_sales_process_mapping.py --map` lints — the excerpt stops before the terminal stages, so the checker warns about the missing Closed Won; that warning belongs to the excerpt, not to the design. The full seven-stage inbound SaaS ladder with forecast categories and swim lanes is in `references/worked-examples.md` §2.

```yaml
process: Capital Equipment - Direct
object: Opportunity
methodology: MEDDIC
stages:
  - name: Qualified
    entry: "Metrics quantified and the economic buyer named"
    exit: "Decision criteria captured from the buyer, not inferred"
    forecast_category: Pipeline
    probability: 15
    owner: AE
    meddic: [M, E]
    required_fields: [Business_Impact_Value__c, Economic_Buyer__c]
  - name: Discovery
    entry: "Decision criteria documented and the decision process steps known"
    exit: "Implicated pain confirmed by the champion in writing"
    forecast_category: Pipeline
    probability: 30
    owner: AE
    meddic: [D, D]
    required_fields: [Decision_Process_Steps__c]
  - name: Technical Win
    entry: "Champion has confirmed the implicated pain"
    exit: "Champion has agreed to sponsor the deal internally"
    forecast_category: Best Case
    probability: 50
    owner: Sales Engineer
    meddic: [I]
    required_fields: [Implicated_Pain__c, Champion_Name__c]
```

`meddic:` is a project-specific key, not something the platform or the checker knows about — the checker ignores unknown keys, which is what lets a methodology column ride along in the same artefact. What it will not ignore is a stage that drops the `required_fields` list, and a MEDDIC letter with no field behind it is exactly that: the letter goes in the deck, nothing goes on the record, and the stage gate is back to being a label.

**Why it works:** Anchoring each stage's entry criteria to a named MEDDIC component makes the criteria objective and verifiable. Reps know exactly what they must confirm before advancing. The loss reason "Wrong Stakeholder Engaged" maps directly to the MEDDIC "C" (Champion) failure mode, giving the business a signal to improve champion-building coaching.

---

## Anti-Pattern: Treating Stage Naming as the Whole Exercise

**What practitioners do:** They ask the sales leader for a list of stage names, receive a whiteboard list, and hand it directly to the admin to configure in Setup > Opportunity Stages. The configuration takes 20 minutes. The stages go live with no documented criteria.

**What goes wrong:** Within 60 days, stage distribution looks like a parking lot — 60–70% of pipeline sits in one or two stages because reps use stages as labels, not gates. Win rates are inconsistent across reps because "Proposal" means different things. Win/loss data is never captured because no one defined when to require it. The admin is asked to "fix the stages" 6 months later, which requires migrating existing records.

**Correct approach:** Treat stage naming as the last step, not the first. Run the discovery sessions first to capture entry/exit criteria. Let the criteria drive the stage boundary definitions. Name stages only after the gates are understood. The names should describe the state of the deal from the buyer's perspective, not the rep's activity ("Proposal Sent" describes rep activity; "Under Evaluation" describes buyer state — the latter ages better).
