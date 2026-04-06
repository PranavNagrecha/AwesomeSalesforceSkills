# Examples — Einstein Next Best Action

## Example 1: Service Case Deflection Recommendations

**Context:** A support org wants to suggest self-service resources to agents when they open a Case, reducing handle time and encouraging knowledge article sharing with customers.

**Problem:** Without NBA, agents manually search for knowledge articles or rely on memory to suggest resources. High-priority cases get the same generic treatment as simple how-to inquiries, and there is no tracking of which suggestions agents accept or dismiss.

**Solution:**

```text
Recommendation Records:
  - Name: "Share Password Reset Article"
    ActionReference: Share_KB_Article_Flow
    AcceptanceLabel: "Send to Customer"
    RejectionLabel: "Not Relevant"
    Description: "Send the password reset knowledge article to the case contact."

  - Name: "Escalate to Tier 2"
    ActionReference: Escalate_Case_Flow
    AcceptanceLabel: "Escalate Now"
    RejectionLabel: "Dismiss"
    Description: "Escalate this case to Tier 2 support based on complexity indicators."

Strategy Flow (Autolaunched):
  1. Input: Case record variable
  2. Get Records: All active Recommendation records
  3. Decision: If Case.Type = 'Password Reset' → assign "Share Password Reset Article" to output list
  4. Decision: If Case.Priority = 'High' AND Case.Escalated__c = false → add "Escalate to Tier 2"
  5. Output: List<Recommendation> collection variable
```

**Why it works:** The strategy Flow uses the Case record's fields to filter recommendations contextually. Agents see only relevant actions, and every acceptance triggers a concrete Flow (sending an article or escalating). Acceptance and rejection data can be reported on to measure adoption and refine recommendations over time.

---

## Example 2: Opportunity Upsell and Cross-Sell Recommendations

**Context:** A B2B sales org wants to surface upsell and cross-sell recommendations on Opportunity record pages based on the Account's industry and the Opportunity's current stage.

**Problem:** Sales reps miss upsell opportunities because they do not know which products pair well with the current deal. Marketing creates campaigns, but reps rarely check campaign membership from the Opportunity page.

**Solution:**

```text
Recommendation Records:
  - Name: "Add Premium Support Package"
    ActionReference: Add_Product_to_Opportunity
    AcceptanceLabel: "Add Product"
    RejectionLabel: "Skip"
    Description: "This account's industry benchmarks show high adoption of premium support."
    ExpirationDate: 2026-06-30

  - Name: "Schedule Executive Business Review"
    ActionReference: Create_EBR_Event_Flow
    AcceptanceLabel: "Schedule EBR"
    RejectionLabel: "Not Now"
    Description: "Opportunities in Negotiation stage benefit from an executive touchpoint."

Strategy Flow (Autolaunched):
  1. Input: Opportunity record variable
  2. Get Records: Retrieve Recommendation records where ExpirationDate >= TODAY or ExpirationDate = null
  3. Decision: If Opportunity.Amount > 50000 AND Account.Industry = 'Technology'
       → add "Add Premium Support Package" to output
  4. Decision: If Opportunity.StageName = 'Negotiation'
       → add "Schedule Executive Business Review" to output
  5. Sort output list by Recommendation.Name ascending (deterministic order)
  6. Output: List<Recommendation> collection variable
```

**Why it works:** ExpirationDate ensures time-limited promotions disappear automatically. The Flow's Decision elements encode business rules that marketing and sales leadership can adjust without developer help. The acceptance Flows perform concrete actions (adding a product, creating an event) rather than just displaying information.

---

## Anti-Pattern: Building Strategies in Strategy Builder

**What practitioners do:** They create NBA strategies using the legacy Strategy Builder interface, defining recommendation logic with the drag-and-drop strategy canvas including Load, Filter, Sort, and Output elements.

**What goes wrong:** Strategy Builder was deprecated in Spring '24. New orgs may not have it available. Existing strategies in Strategy Builder will not receive platform updates or bug fixes. Salesforce documentation now directs all strategy authoring to Flow Builder, and any Trailhead or community content referencing Strategy Builder is outdated.

**Correct approach:** Build all NBA strategies as Autolaunched Flows. Define a `List<Recommendation>` output collection variable. Use Get Records, Decision, Assignment, and Loop elements to replicate any logic previously built in Strategy Builder. Migrate existing Strategy Builder strategies to Flow before they become unsupported.
