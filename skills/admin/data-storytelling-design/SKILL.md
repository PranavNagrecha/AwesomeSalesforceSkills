---
name: data-storytelling-design
description: "Designing data stories and narrative-driven analytics in Salesforce: structuring CRM Analytics dashboards for executive communication, text widgets and conditional highlights for annotation, sequential narrative in Tableau Story sheets, and Einstein Discovery narrative REST endpoints. Trigger keywords: data storytelling dashboard, executive analytics narrative, CRM Analytics text widget annotation, Tableau story sheet, smart data discovery narrative API. NOT for building the Einstein Discovery story or prediction definition - use admin/einstein-discovery-setup. NOT for choosing between Reports, CRM Analytics and Tableau - use admin/einstein-analytics-basics."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
triggers:
  - "how do I design a CRM Analytics dashboard that tells a story for executives"
  - "what layout should I use for an executive summary dashboard in CRM Analytics"
  - "how do I add narrative text annotations to a Salesforce analytics dashboard"
  - "how do I use Tableau Story sheets to create a sequential data narrative"
  - "can Einstein Discovery automatically generate narrative text for my analytics report"
  - "how do I highlight a key metric in a CRM Analytics dashboard to draw attention to it"
  - "turn our chart-grid dashboard into a one-page story executives can read in 30 seconds"
  - "add a headline sentence that updates with the data on a CRM Analytics dashboard"
tags:
  - crm-analytics
  - tableau
  - data-storytelling
  - dashboard-design
  - analytics
  - einstein-discovery
inputs:
  - "Target audience: executive, operational, frontline, or self-service"
  - "Available analytics surface: CRM Analytics, Tableau, or both"
  - "Existing dataset and KPI definitions"
  - "Key insight or decision the story must drive"
outputs:
  - "Narrative dashboard layout plan with Z-pattern structure"
  - "Text widget content and conditional highlight strategy"
  - "Storytelling surface selection guidance (CRM Analytics vs Tableau vs Smart Data Discovery)"
  - "Executive annotation blueprint"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
---

# Data Storytelling Design

Use this skill when designing analytics experiences in Salesforce tools that go beyond charts — specifically when you need to guide the viewer toward a decision, frame an insight with context, or create a sequential narrative. Applies to CRM Analytics dashboard annotation, Tableau Story sheets, and Einstein Discovery narrative REST API for machine-generated insight text.

---

## Before Starting

Gather this context before working on anything in this domain:

- What decision should the audience make after viewing this story? Without a clear call to action, storytelling design defaults to decoration.
- Who is the audience: executives requiring 3-second insight comprehension, operational managers needing drill-down, or frontline users acting on recommendations?
- Which platform is in scope: CRM Analytics (text widgets, animated pages), Tableau (Story sheets), or Smart Data Discovery API (embedded programmatic narrative)?
- Are KPIs already defined? Data storytelling design assumes KPI definitions exist — if not, use `analytics-kpi-definition` first.

---

## Questions to Ask Before Configuring

Each question traces to a gotcha in `references/gotchas.md`.

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "What should the audience decide after reading this, in one sentence?" | The only narrative vehicle is a text widget, and it needs a message to bind (Gotcha 1) | A headline sentence and the steps whose values it quotes | The page leads with a conclusion instead of a chart grid |
| "Where will people read it: desktop, CRM Analytics mobile app, Salesforce mobile app, or a phone browser?" | Phones get a separate layout only if one is built, and phone browsers are not supported for embedded dashboards (Gotcha 4) | A layout per device and a page order for the phone | The story survives the device it is read on |
| "Does any list in the story need to be complete?" | Values tables show 100 rows and compare tables 2,000 by default (Gotcha 3) | A stated row limit or a linked detail page | No headline claims completeness the widget does not deliver |
| "Does the story include machine-written insight from Einstein Discovery?" | The narrative comes from a REST resource someone must call and render (Gotcha 2) | The surface (LWC, Visualforce, integration) and a human review step | Generated text appears where the audience reads it, after review |
| "Will any number come live from outside Salesforce?" | Apex steps cost API calls and are not packaged (Gotcha 5) | A scheduled dataset for external figures, or an accepted API cost | The story deploys to other orgs and does not load the API budget |
| "Is this a recurring review in Tableau, and must past versions stay frozen?" | Story points follow their source sheets and lose some dynamic features (Gotcha 6) | Duplicated source sheets and a fixed story size | The board sees the story that was approved, at the size it was designed for |

What proper configuration adds over "just building a dashboard": one message per page that updates with the data, a layout per device, and limits stated where the audience can see them.

## Core Concepts

### The Salesforce CRM Analytics Design Framework

Salesforce's CRM Analytics design guidance defines three principles (UNVERIFIED (2026-10-03): the Trailhead units cited for this framework and the Z-pattern returned HTTP 404 on 2026-10-03, so the wording below could not be re-checked):
1. **Clarity** — One primary message per page. Eliminate visual noise. Prioritize the insight over the mechanism.
2. **Efficiency** — Minimize the number of interactions to reach the key insight. Pre-compute answers rather than asking users to calculate mentally.
3. **Consistency** — Use the same color, layout, and interaction patterns across all pages. Do not alternate chart types for the same metric category.

The prescribed layout is a **Z-pattern**: summary metric tiles at top-left, supporting context to the right, detail charts below-left, and filter/action controls below-right. This matches natural reading patterns for left-to-right audiences and ensures executives see the headline number first.

### Storytelling Surfaces Are Bifurcated by Tool

Salesforce has three distinct storytelling surfaces with different builder toolchains:

1. **CRM Analytics**: Narrative is built via **text widgets** (static or dynamic text bound to step selections or results), **conditional highlights** (number and chart properties such as `numberColor` set from another step's results through bindings), and **pages** within each layout. The documented widget types include no "executive summary" type, so all narrative is built with text widgets and layout discipline. UNVERIFIED (2026-10-03): the earlier "animated pages (step-through presentation mode)" feature does not appear in the Dashboard JSON Guide.

2. **Tableau**: Has dedicated **Story sheets** — a separate workbook tab type that arranges a sequence of views with captioned navigation. Story sheets support annotations directly on chart views. Tableau Pulse (part of Tableau Cloud) delivers automated narrative digests to Slack and email based on metric subscriptions.

3. **Einstein Discovery / Smart Data Discovery**: The Einstein Discovery REST API returns narrative data for a story from `POST /services/data/vXX.X/smartdatadiscovery/narrative` (API 51.0+). These narratives must be surfaced in custom Visualforce pages, LWC components, or Experience Cloud; nothing in the documentation places them in CRM Analytics dashboards automatically.

### CRM Analytics Text Widgets for Contextual Annotation

A text widget in CRM Analytics can contain:
- Static narrative text (titles, definitions, caveats)
- Dynamic values bound to dataset queries (e.g., "Revenue is {value} this quarter")
- Conditional formatting based on step results

The most common storytelling mistake is omitting text widgets entirely, leaving dashboards as chart grids with no context. The text widget is the primary vehicle for executive framing in CRM Analytics.

---

## Common Patterns

### Pattern: Z-Pattern Executive Summary Dashboard

**When to use:** When building a CRM Analytics dashboard for C-suite or VP-level audiences requiring a 30-second status read.

**How it works:**
1. Row 1 (full width): 3–5 metric tiles with KPI names, current period values, and conditional highlights (green/yellow/red thresholds).
2. Row 1, rightmost: A text widget with the single-sentence narrative — the headline insight.
3. Row 2: Two supporting charts (trend and breakdown) that explain the headline metrics.
4. Row 3: Drill-down table or filter controls for managers who need detail.

**Why not a chart grid without text:** a chart grid leaves the viewer to find the message. UNVERIFIED (2026-10-03): the earlier statement that Salesforce's Trailhead content "establishes" this comes from Trailhead units that returned HTTP 404 on 2026-10-03.

### Pattern: Tableau Story Sheet for Sequential Narrative

**When to use:** When the insight requires building up context across multiple views — problem, root cause, recommendation.

**How it works:**
1. Build individual Tableau worksheets for each step of the story.
2. Create a Story sheet (New Story in Tableau Cloud/Desktop).
3. Add each worksheet as a Story Point with a caption telling the viewer what to conclude.
4. Use annotations on chart points to call out specific data moments.

**Why not multiple dashboard tabs:** Dashboard tab navigation requires the viewer to discover the sequence. Story sheets enforce guided sequence and are presentation-mode compatible.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Executive CRM Analytics dashboard | Z-pattern layout + text widgets + conditional highlights | Official design framework prescribes this pattern |
| Sequential narrative presentation | Tableau Story sheets | Designed for guided sequential narrative |
| Machine-generated insight text in a custom LWC | Smart Data Discovery narrative REST API | Programmatic narrative endpoint for embedding in custom surfaces |
| Frontline user dashboard with action triggers | Compact metric tiles + filter controls | Efficiency principle: minimize clicks to action |
| Automated narrative digest in Slack | Tableau Pulse metric subscriptions | Pulse delivers AI-generated digest summaries to Slack/email |
| Chart-type selection for a specific metric | Use analytics-dashboard-design skill | That skill covers chart type, binding, and faceting mechanics |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Define the audience and decision** — Write one sentence: "After viewing this story, [audience] will [take this action or make this decision]." If this sentence cannot be written, design has not started.
2. **Select the platform surface** — Choose CRM Analytics, Tableau Story sheets, or Smart Data Discovery API based on tool access and delivery channel.
3. **Design the layout** — For CRM Analytics: apply the Z-pattern. For Tableau: plan the Story Point sequence. Map each visual element to evidence supporting the primary message.
4. **Write narrative text first** — Draft text widget content for CRM Analytics or Story Point captions for Tableau before building charts. Narrative-first design prevents "chart soup."
5. **Configure conditional highlights** — In CRM Analytics metric tiles, set color thresholds matching the business definition of on-track, at-risk, and critical. Use the same threshold values across all KPI tiles on a page.
6. **Validate with target audience** — Do a 30-second test: show the dashboard for 30 seconds, then ask what action the viewer would take. Revise the narrative structure if they cannot answer clearly.
7. **Build the phone layout and check the limits**: add a Mobile `gridLayouts` entry with its own page order, set row limits on tables, and compare against the worked dashboard JSON in `references/examples.md`, Example 3.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Primary call to action defined and reflected in layout
- [ ] Z-pattern applied (CRM Analytics) or Story Point sequence defined (Tableau)
- [ ] Text widget narrative present on CRM Analytics dashboard pages
- [ ] Conditional highlights configured with business-meaningful thresholds
- [ ] Consistent color and layout patterns across all pages/sheets
- [ ] 30-second readability test passed with a representative viewer

---

## Salesforce-Specific Gotchas

The full list with sources is in `references/gotchas.md`. The ones that most often break a story:

| Gotcha | Consequence |
|---|---|
| No executive summary widget (Gotcha 1) | The headline must be a text widget, ideally bound to step values |
| Narrative comes from `/smartdatadiscovery/narrative` (Gotcha 2) | Custom code calls and renders it; the earlier `/wave/smartdatadiscovery/narratives` path was wrong |
| Default table rows 100 or 2,000 (Gotcha 3) | Lists look complete but are truncated unless the step sets a limit |

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Layout blueprint | Z-pattern or Story Point sequence diagram for the target surface |
| Text widget content | Narrative text for each page, bound to dataset values where applicable |
| Conditional highlight thresholds | Color threshold definitions per KPI metric |
| Storytelling surface decision | Documents which platform surface was chosen and why |

---

## Related Skills

- `admin/analytics-dashboard-design` — Use for chart type selection, binding, faceting, and SAQL step configuration — the technical layer below storytelling
- `admin/analytics-kpi-definition` — Use to define KPI formulas and metric logic before designing the narrative around them
- `admin/analytics-requirements-gathering` — Use to elicit stakeholder requirements before designing any analytics experience
- `agentforce/einstein-discovery-development` — Use for Einstein Discovery story creation and narrative REST API integration
