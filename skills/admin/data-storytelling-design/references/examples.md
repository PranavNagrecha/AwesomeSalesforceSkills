# Examples — Data Storytelling Design

## Example 1: Z-Pattern Executive Pipeline Dashboard in CRM Analytics

**Context:** A VP of Sales requested a weekly "pipeline health" dashboard that executives could review in under 30 seconds.

**Problem:** The existing dashboard was a 12-chart grid with no text context. Executive reviewers spent 5+ minutes reading it and still could not quickly identify actions. There was no narrative — just charts.

**Solution:** Applied the official CRM Analytics Z-pattern:
- Row 1: 4 metric tiles (Pipeline Total, Forecast vs. Target, Win Rate, Avg Deal Size) with conditional highlights (green/yellow/red)
- Row 1 right: Text widget "Pipeline is on track. Win rate is below target — Q3 conversion at risk."
- Row 2: Trend chart (pipeline by week) + Stage distribution chart
- Row 3: Drill-down table filtered by owner

After the redesign, executive review time dropped to under 2 minutes and 3 actionable decisions were made in the first week.

**Why it works:** The Z-pattern places the headline number top-left (where the eye lands first), the narrative context top-right, and supporting detail below. Text widgets force the designer to articulate the insight before placing the chart.

---

## Example 2: Tableau Story Sheet for Monthly Business Review Presentation

**Context:** A data analyst needed to present a monthly business review covering customer acquisition, churn, and revenue trend to a board audience.

**Problem:** Previous presentations used multiple separate dashboard tabs. Presenters had to manually navigate between tabs, disrupting the narrative flow and giving audience members time to drill into tangential details rather than following the story.

**Solution:** Created a Tableau Story sheet with 5 Story Points:
1. "Customer Acquisition is Up 12% MoM" — acquisition trend chart with annotation on the spike
2. "But Churn Increased in Enterprise Segment" — churn rate by segment chart
3. "Enterprise Revenue at Risk: $2.4M" — revenue-at-risk calculation
4. "Root Cause: Onboarding Completion Rate Dropped" — onboarding funnel chart
5. "Recommendation: Dedicated CS for Enterprise Onboarding" — action summary

**Why it works:** Story Points enforce the presenter's intended sequence. Each point has a single caption that tells the audience what to conclude. The board followed the argument without getting lost in chart interactions.
