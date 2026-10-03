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

---

## Example 3: A Z-Pattern Story Page With A Bound Headline And A Phone Layout, As Dashboard JSON

**Context:** The pipeline dashboard from Example 1 must read in 30 seconds on a laptop and on a phone, with the headline sentence quoting the live total. The dataset `Opportunity_Pipeline` already exists.

**Procedure (Dashboard JSON Guide, View or Modify a Dashboard JSON File):**

1. Open the dashboard in Analytics Studio and press CTRL+E (CMD+E on a Mac) to open the JSON editor. This needs the Create and Edit CRM Analytics Dashboards permission.
2. Replace the `steps`, `widgets`, and `gridLayouts` nodes inside `state` with the fragment below, adjusted to the dataset's field names.
3. Click **Done** to preview, then **Save**; edits in the JSON editor are not kept until the dashboard is saved.
4. Retrieve the saved dashboard for source control instead of hand-editing the retrieved file: the Metadata API says "Modifications to the .wdash component are unsupported," and removing steps from it makes deployment fail.

**The `state` fragment:**

```json
{
  "steps": {
    "Pipeline_Total_1": {
      "type": "saql",
      "query": "q = load \"Opportunity_Pipeline\";\nq = filter q by 'IsClosed' == \"false\";\nq = group q by all;\nq = foreach q generate sum('Amount') as 'sum_Amount';",
      "useGlobal": true,
      "numbers": [],
      "groups": [],
      "strings": []
    },
    "Pipeline_By_Week_1": {
      "type": "saql",
      "query": "q = load \"Opportunity_Pipeline\";\nq = filter q by 'IsClosed' == \"false\";\nq = group q by ('CloseDate_Year', 'CloseDate_Week');\nq = foreach q generate 'CloseDate_Year' + \"~~~\" + 'CloseDate_Week' as 'CloseDate_Year~~~CloseDate_Week', sum('Amount') as 'sum_Amount';\nq = order q by 'CloseDate_Year~~~CloseDate_Week' asc;\nq = limit q 2000;",
      "useGlobal": true,
      "numbers": [],
      "groups": [],
      "strings": []
    }
  },
  "widgets": {
    "number_1": {
      "parameters": {
        "step": "Pipeline_Total_1",
        "measureField": "sum_Amount",
        "compact": true,
        "numberColor": "#16325c",
        "textAlignment": "left"
      },
      "type": "number"
    },
    "text_1": {
      "parameters": {
        "text": "Open pipeline is {{ cell(Pipeline_Total_1.result, 0, \"sum_Amount\").asString() }}. Win rate is below target: Q3 conversion is at risk.",
        "fontSize": 16,
        "textAlignment": "left",
        "textColor": "#091A3E"
      },
      "type": "text"
    },
    "chart_1": {
      "parameters": {
        "step": "Pipeline_By_Week_1",
        "visualizationType": "time"
      },
      "type": "chart"
    }
  },
  "gridLayouts": [
    {
      "name": "Default",
      "numColumns": 12,
      "rowHeight": "normal",
      "selectors": [],
      "version": 1,
      "pages": [
        {
          "label": "Summary",
          "name": "summary",
          "widgets": [
            { "name": "number_1", "column": 0, "row": 0, "colspan": 4, "rowspan": 2 },
            { "name": "text_1",   "column": 4, "row": 0, "colspan": 8, "rowspan": 2 },
            { "name": "chart_1",  "column": 0, "row": 2, "colspan": 12, "rowspan": 6 }
          ]
        }
      ]
    },
    {
      "name": "Mobile",
      "numColumns": 2,
      "rowHeight": "normal",
      "selectors": ["maxWidth(599)"],
      "version": 1,
      "pages": [
        {
          "label": "Summary",
          "name": "summary-mobile",
          "widgets": [
            { "name": "text_1",   "column": 0, "row": 0, "colspan": 2, "rowspan": 3 },
            { "name": "number_1", "column": 0, "row": 3, "colspan": 2, "rowspan": 2 },
            { "name": "chart_1",  "column": 0, "row": 5, "colspan": 2, "rowspan": 5 }
          ]
        }
      ]
    }
  ]
}
```

Property names (`type`, `query`, `useGlobal`, `numbers`, `groups`, `strings`, `step`, `measureField`, `compact`, `numberColor`, `textAlignment`, `text`, `fontSize`, `textColor`, `visualizationType`, `gridLayouts`, `numColumns`, `rowHeight`, `selectors`, `version`, `pages`, `colspan`, `rowspan`) and the `"maxWidth(599)"` selector come from the Dashboard JSON Guide. UNVERIFIED (2026-10-03): the guide shows `cell()` with a `.selection` source and `column()` with a `.result` source; `cell(Pipeline_Total_1.result, 0, "sum_Amount")` follows the same pattern but was not shown verbatim. The SAQL field names, the weekly date grouping, and the `time` chart's minimum parameters depend on the dataset; let the designer validate the preview before saving.

**Deployment members** after retrieval (Metadata API, WaveDashboard: suffix `.wdash` in the `wave` folder, `application` required):

| Component | Type | `package.xml` member form |
|---|---|---|
| Story dashboard | `WaveDashboard` | `<members>Pipeline_Story</members><name>WaveDashboard</name>` |
| App that holds it | `WaveApplication` | `<members>Sales_Leadership</members><name>WaveApplication</name>` |
| Dataset definition | `WaveDataset` | `<members>Opportunity_Pipeline</members><name>WaveDataset</name>` |

**Why it works:** the headline is a sentence that quotes the live total, the phone gets its own order (headline, number, trend), the trend query states its row limit, and the deployment path respects the Metadata API rule against editing `.wdash` files by hand.

