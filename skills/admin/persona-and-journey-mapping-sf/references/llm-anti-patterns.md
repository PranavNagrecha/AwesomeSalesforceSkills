# LLM Anti-Patterns — Persona And Journey Mapping (Salesforce-Anchored)

Common mistakes AI assistants make when generating persona and journey
artifacts. These exist so the consuming agent can self-check its output
before handing off.

---

## Anti-Pattern 1: Generating A Persona Without Org-Artifact Anchors

**What the LLM generates:** a persona block with `name`, `description`,
`goals`, `pain_points`, and a stock photo URL — but no PSG, no record types,
no list views, no dashboards.

**Why it happens:** training data is dominated by generic UX-research
persona templates that don't model the Salesforce platform.

**Correct pattern:**

```json
{
  "persona_id": "outside_sales_rep",
  "psg_assigned": "PSG_Sales_Field",
  "primary_record_types": ["Account.Customer", "Opportunity.Field_Deal"],
  "primary_list_views": ["My_Open_Opps_This_Week"],
  "dashboards": ["Field_Sales_Daily"],
  "mobile_pct": 70,
  "desktop_pct": 30,
  "automation_touched": ["Flow:Visit_After_Save"]
}
```

**Detection hint:** look for a persona artifact with no key matching
`psg_assigned|primary_record_types|primary_list_views|dashboards`. If
all four are missing, it is a UX template, not a Salesforce persona.

---

## Anti-Pattern 2: Inventing Mobile / Desktop Percentages

**What the LLM generates:** `"mobile_pct": 60, "desktop_pct": 40` with no
mention of measurement source. The numbers feel plausible.

**Why it happens:** the model fills in plausible values when not told to
defer. Plausibility is not measurement.

**Correct pattern:**

```json
"mobile_pct": 70,
"desktop_pct": 30,
"posture_source": "EventLogFile UriEvent, 30-day window, 2026-03-01 to 2026-03-31"
```

If measurement is unavailable, return:

```json
"mobile_pct": null,
"desktop_pct": null,
"posture_source": "UNAVAILABLE — request Lightning Usage app enablement before persona finalization"
```

**Detection hint:** `mobile_pct` populated with no `posture_source` adjacent
or in prose. Refuse to fabricate.

---

## Anti-Pattern 3: Skipping Or Inventing Friction Tags

**What the LLM generates:** friction tagged as "slow", "confusing",
"annoying", or no tag at all. Sometimes a sixth invented tag like
"navigation_pain".

**Why it happens:** the model isn't told the enum is fixed; it pattern-matches
to general UX vocabulary.

**Correct pattern:** every friction uses exactly one of:
`cognitive_load`, `click_count`, `mode_switch`, `data_input`, `search`. If
the friction does not fit, capture detail in `notes`, do not invent a tag.

```json
"friction_points": [
  {"step_index": 4, "tag": "data_input", "note": "Visit Type retyped each time; territory not defaulted"}
]
```

**Detection hint:** any `tag` value outside the five-element enum.

---

## Anti-Pattern 4: Conflating Journey Map With Process Flow

**What the LLM generates:** a journey that includes "Apex trigger fires",
"Outbound message sent to ERP", "Approval routes to Manager". These are
system events, not user actions.

**Why it happens:** the model has been trained on flowchart-style process
diagrams and treats "journey" and "flow" as synonyms.

**Correct pattern:** a journey describes only what the *persona* does on a
*surface*. System events are out of scope; route to
`admin/process-flow-as-is-to-be` instead.

```json
{
  "step": "Tap Save",
  "surface": "mobile"
}
```

NOT:

```json
{
  "step": "Trigger fires after save",
  "surface": "system"
}
```

**Detection hint:** any step with `surface: "system"`, or step text
containing "trigger", "callout", "approval routes", "outbound message".

---

## Anti-Pattern 5: Hallucinating Dashboards / List Views Not In The Org

**What the LLM generates:** persona references "Field Sales Daily" dashboard,
"My Hot Leads" list view, "Pipeline Heatmap" report — none of which exist
in the customer's org.

**Why it happens:** the model fills in reasonable-sounding artifact names to
make the persona feel complete.

**Correct pattern:** every named artifact must come from an explicit input
listing of org metadata (Tooling API list, metadata listing, or screenshot
the user provided). If no input listing was given, leave the field as a
placeholder array and flag it:

```json
"dashboards": [],
"_dashboards_status": "PENDING — request dashboard listing from Tooling API before finalization"
```

**Detection hint:** non-empty `dashboards` / `primary_list_views` /
`primary_record_types` arrays without the user having provided an org metadata
listing in the conversation.

---

## Anti-Pattern 6: Journey That Ends At "Save"

**What the LLM generates:** the last step is "Save record" or "Click Save".
There is no `next_task`. The biggest source of `mode_switch` friction is
invisible.

**Why it happens:** the model treats "task complete" as "narrative complete"
and stops. Real users do not stop at save.

**Correct pattern:** every journey has a `next_task` field naming what the
persona does next, and if the next task is on a different surface, an
explicit `mode_switch` friction tag on the transition step.

```json
{
  "task": "Log a customer visit",
  "steps": [ /* ... */, {"step": "Save", "surface": "mobile"} ],
  "next_task": "Drive to next account and repeat"
}
```

**Detection hint:** journey JSON missing `next_task` or with `next_task`
equal to the empty string.

---

## Anti-Pattern 7: Producing 10+ Personas When Asked For "Some Personas"

**What the LLM generates:** one persona per job title — 11 personas, three
of which are basically the same PSG with a different VP-level label.

**Why it happens:** title diversity in the input feels like persona diversity.
It isn't.

**Correct pattern:** cap at 7 per phase. Two roles sharing a PSG and primary
tasks at the same frequency are one persona. VPs and stakeholders without
hands-on system tasks are not personas — route to RACI
(`stakeholder-raci-for-sf-projects`).

**Detection hint:** persona count > 7 in a single deliverable, or two
personas with identical `psg_assigned` and overlapping `primary_record_types`.
