# Gotchas: Data Storytelling Design

Non-obvious platform behaviours that break a data story after it is designed. Each gotcha names its source. Claims that could not be confirmed from a fetched source carry an inline `UNVERIFIED (2026-10-03):` marker. "Dashboard JSON Guide" means the Analytics Dashboard JSON Developer Guide (Summer '26, https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/bi_dev_guide_json.pdf); "Setup Guide" means the Analytics Platform Setup Guide (Spring '26).

## Gotcha 1: There Is No "Executive Summary" Widget; The Narrative Is A Text Widget With Bindings

**What happens:** Practitioners search the Analytics Studio widget palette for an "executive summary" or "narrative" widget. The documented widget types are `chart`, `comparetable`, `container`, `dateselector`, `globalfilters`, `filterpanel`, `image`, `link`, `listselector`, `number`, `pillbox`, `rangeselector`, `table`, `text`, and `valuestable`. Teams that miss the `text` widget deliver chart grids, or squeeze the message into chart titles, which are small and static.

**When it occurs:** First executive dashboards, and redesigns of chart-grid dashboards.

**How to avoid:** Build the headline as a `text` widget. Its `text` parameter can carry a binding, as in the guide's example `"Selected symbol: {{ cell(CompaniesList_1.selection, 0, \"value\").asString() }}"`, so the sentence updates with the data. Number and chart widget properties can also be set from another step's selection or results.

**Source:** Dashboard JSON Guide, widgets JSON (`type` list; note on dynamically setting number and chart properties); parameters Properties (`text`, `textAlignment`, `textColor`); apex Step Type example (text widget binding).

---

## Gotcha 2: Einstein Discovery Narratives Come From A REST Resource, Not From The Dashboard

**What happens:** Teams enable Einstein Discovery and expect machine-written insight text to appear in existing dashboards. The narrative is returned by the Einstein Discovery REST API: `POST /services/data/vXX.X/smartdatadiscovery/narrative`, available from API 51.0, which "Returns the narrative data for an Einstein Discovery story." Something has to call it and render the result. This corrects the earlier path in this skill, `/wave/smartdatadiscovery/narratives`, which is not the documented resource.

**When it occurs:** After Einstein Discovery stories are built and someone asks for "the AI summary on the dashboard."

**How to avoid:** Call `/smartdatadiscovery/narrative` from an LWC, Visualforce page, or integration, and show the returned text where the audience reads it. Have a person review generated narrative before it reaches executives. UNVERIFIED (2026-10-03): whether any Analytics Studio widget can display Einstein Discovery narrative natively was not established in a fetched source.

**Source:** Einstein Discovery REST API Developer Guide (Spring '26), local corpus `knowledge/imports/bi-dev-guide-rest-sdd.md`: General Resources table and Narrative Resource (URL `/smartdatadiscovery/narrative`, `POST`, available version 51.0, request body `SmartDataDiscoveryNarrativeInput`). CRM Analytics REST API Developer Guide overview: Einstein Discovery predictions use "the smartdatadiscovery API."

---

## Gotcha 3: Tables In A Story Show 100 Or 2,000 Rows Unless The Query Says Otherwise

**What happens:** A story page ends with "the full list of at-risk accounts." The values table shows the first 100 rows, a compare table the first 2,000, and the narrative claims completeness the widget does not deliver.

**When it occurs:** Drill-down rows at the bottom of a Z-pattern page, and exports from those widgets.

**How to avoid:** Set the row count with a SAQL `limit` statement in the step, state the limit in the text widget ("Top 50 accounts by risk"), and keep long lists for a linked detail page. The dashboard JSON file is capped at 4 MB, which also bounds very wordy stories.

**Source:** Setup Guide, CRM Analytics Limits, Lens and Dashboard Limits ("Default number of rows in a compare table 2000 (To set a different value, use the SAQL limit statement)"; values table 100; "Maximum JSON file size per dashboard 4 MB"; "Maximum number of dashboard components per dashboard 20").

---

## Gotcha 4: The Phone Gets A Different Layout Only If You Build One

**What happens:** A carefully composed 12-column Z-pattern page is unreadable on a phone. Each dashboard holds one or more `gridLayouts`, and CRM Analytics picks one using its `selectors` (for example a Mobile layout with `"maxWidth(599)"`). Without a phone layout, the story depends on automatic rearrangement. Outside the native CRM Analytics mobile app, mobile access is only through Lightning app pages in the Salesforce mobile app; "Embedded CRM Analytics dashboards accessed via mobile browsers aren't supported."

**When it occurs:** Executive stories read on phones before meetings.

**How to avoid:** Add a phone layout with its own page order: headline text first, then two or three numbers, then one chart. Set `mobileDisabled` to `true` for dashboards that should not open on mobile. Avoid `apex` steps on pages meant for Android: "The Android mobile app doesn't support this type of step."

**Source:** Dashboard JSON Guide, Dashboard JSON Properties (`mobileDisabled`), gridLayouts JSON (`name`, `numColumns`, `pages`, `selectors`, `maxWidth`), the Account Analysis example (Default and Mobile layouts), apex Step Type limitations. Setup Guide, CRM Analytics Limitations, CRM Analytics on Mobile Devices.

---

## Gotcha 5: Live External Numbers In The Story Cost API Calls And Do Not Travel In Packages

**What happens:** A designer pulls a live figure (a stock price, an ERP backlog) into the headline through an `apex` step. Each query runs as the logged-in user and "counts against the org's API limits," and "If you include dashboards in a package, apex steps aren't included." The story breaks in the next org and adds API load on every view.

**When it occurs:** Board decks that mix Salesforce data with one external number.

**How to avoid:** Prefer a dataset refreshed on a schedule for external figures. If an `apex` step is unavoidable, migrate the Apex class separately and count its calls in the org's API budget.

**Source:** Dashboard JSON Guide, apex Step Type Properties (query runs as the logged-in user; "Each REST API query counts against the org's API limits"; package and Android limitations).

---

## Gotcha 6: Tableau Story Points Freeze Some Dynamic Features And Follow Their Source Sheets

**What happens:** A Tableau story built for a board meeting loses behaviour the analyst relied on: "Stories don't support dynamic features, such as zone visibility, axis titles, or axis ranges." Each story point stays connected to its original sheet, so a later edit to the sheet silently changes the story; on Tableau Cloud, a source sheet with Pause Auto Updates enabled leaves the story sheet blank.

**When it occurs:** Monthly business reviews built once and reused, and stories authored on a large monitor but presented elsewhere.

**How to avoid:** Duplicate source sheets for a frozen story, set the story size to the size it will be viewed at, and put each takeaway in the story point caption. Check the story in presentation size before the meeting.

**Source:** Tableau Help, Stories (https://help.tableau.com/current/pro/desktop/en-us/stories.htm: story points; dynamic features note) and Create a Story (https://help.tableau.com/current/pro/desktop/en-us/story_create.htm: "Choose the size your story will be viewed at"; story points remain connected to the original sheet; Pause Auto Updates leaves the story sheet blank; captions).

---

## Gotcha 7: Tableau Pulse Digests Are Scheduled, Not Live

**What happens:** A team replaces a daily executive story with Tableau Pulse and expects instant alerts. Pulse sends digests by email, Slack, and Microsoft Teams on the user's schedule, and "checks the metrics that you follow every 24 hours" for alerts. Administrators can turn off the email and Slack channels.

**When it occurs:** Operational metrics that need same-hour attention.

**How to avoid:** Use Pulse for daily or weekly narrative digests. Keep same-hour signals in operational dashboards or notifications. Confirm with the Tableau Cloud administrator that the delivery channel is enabled.

**Source:** Tableau Help, Tableau Pulse Release Notes (https://help.tableau.com/current/online/en-us/pulse_intro.htm: digests in email, Slack, and Microsoft Teams; alert checks every 24 hours; administrator control of channels).

---

## Gotcha 8: "Animated Page Mode" Is Not In The Documented Dashboard Model

**What happens:** The earlier version of this skill said CRM Analytics "animated page mode" locks interactive filters during playback. No animation or presentation-mode property appears in the Dashboard JSON Guide's layout, page, or widget properties, so the behaviour cannot be confirmed. UNVERIFIED (2026-10-03): the animated page mode claim is kept here only as a field report.

**When it occurs:** When a presenter plans to answer questions with live filters during a step-through.

**How to avoid:** Present from the normal dashboard with pages, and rehearse filter changes in the same view the audience will see. If a presentation feature is used, test filter behaviour in it before the meeting.

**Source:** Dashboard JSON Guide, gridLayouts JSON and pages properties (`label`, `name`, `widgets`), widgets JSON (`type` list); a search of the guide for "animat" and "presentation" returned no matches.
