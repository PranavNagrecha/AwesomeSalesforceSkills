# Gotchas — Persona And Journey Mapping (Salesforce-Anchored)

Non-obvious behaviors and authoring traps that produce broken or unaudible
persona artifacts.

---

## Gotcha 1: Persona With No PSG Anchor (Just A Title)

**What happens:** the persona looks complete in a slide deck but cannot be
audited against the org. Six months later the PSG roster has shifted, the
persona still says "Sales Rep", and nobody can tell which users it covers.

**When it occurs:** when persona work happens before PSG design, or when
imported from a generic UX template.

**How to avoid:** require `psg_assigned` to be present and resolvable to a
real (or planned and named) PSG. If the PSG does not yet exist, write the
PSG sketch first; do not invent a persona without one. The skill checker
fails this case.

---

## Gotcha 2: Mobile vs Desktop Posture Assumed, Not Measured

**What happens:** the team writes "60/40 mobile" because it sounds right, the
record page is built for it, and the actual measurement (after launch) is
85/15. Reps abandon the mobile flow. UAT didn't catch it because UAT was
desktop-only.

**When it occurs:** when Lightning Usage app is left at default settings (no
mobile session reporting), or when EventLogFile UriEvent is not enabled.

**How to avoid:** before publishing personas, pull the real split from
Lightning Usage app (after enabling Mobile App usage) or EventLogFile
UriEvent / LightningPerformance. The persona schema requires
`mobile_pct + desktop_pct ≈ 100` and the source of measurement should be
named in adjacent prose.

---

## Gotcha 3: Journey Maps Happy Path Only

**What happens:** the journey ends at "saves record successfully". Reality:
half the time there's a validation rule fault, a permission error, or a
required-field-missing message. Friction in those error paths is what users
actually complain about, but it is invisible.

**When it occurs:** when journey maps are built from idealized flow diagrams
rather than from observed user sessions.

**How to avoid:** for any journey with `frequency: daily`, also model the
top-1 fault path (validation rule fires, permission denied, field locked).
Tag the friction. Routes to `audit-validation-rules` if validation messages
are user-hostile.

---

## Gotcha 4: Missing The After-Task Step

**What happens:** journey ends at "Save". The biggest friction
(`mode_switch`) is the user trying to figure out where to go next — back
to a list view, to a different object, to a dashboard? — and it never gets
captured.

**When it occurs:** every time a journey is written linearly without
asking "and then what?".

**How to avoid:** the journey schema requires a `next_task` field. The
checker fails journeys that omit it. If the persona's next task is on a
different surface (mobile→desktop), tag the transition `mode_switch`.

---

## Gotcha 5: Persona Drift (Fictional vs Real Users)

**What happens:** two months in, the personas describe an idealized "future
state" workforce, not the current one. Decisions are made on personas, but
the org is still serving the old user mix. The record page optimizes for
nobody who exists today.

**When it occurs:** when persona work happens during requirements gathering
and is never re-validated against the actual user base after rollout.

**How to avoid:** every persona should name a real (anonymized) sample
user count from the user table, plus the PSG members count. If the gap
between persona-defined headcount and PSG actual headcount exceeds 20%, the
persona is drifting — flag for review.

---

## Gotcha 6: Too Many Personas (>7 In A Phase)

**What happens:** 12 personas were written, each with a journey. Nobody on
the team can keep them straight; downstream agents get a routing list with
40+ friction items; backlog grooming stalls; the deliverable becomes
shelfware.

**When it occurs:** when stakeholders insist every job title becomes a
persona ("we have a persona for VP of Sales!").

**How to avoid:** cap personas at 7 per phase. If two roles share a PSG and
have the same primary tasks at the same frequency, they are the same
persona — merge them. Stakeholders can be RACI participants
(`stakeholder-raci-for-sf-projects`), they don't all need personas.

---

## Gotcha 7: Hallucinated Dashboards / List Views

**What happens:** the persona doc says "consumes the Field Sales Daily
dashboard" but no such dashboard exists. The persona looks polished; the
audit fails on day one.

**When it occurs:** when the author writes from intuition rather than from
the org metadata listing.

**How to avoid:** every dashboard, list view, and record type named in a
persona must resolve to a real metadata API name. The skill checker
validates structural presence of these arrays; pair with an org-metadata
probe (Tooling API or Metadata API listing) to validate the names exist.

---

## Gotcha 8: Friction Free-Text Tags

**What happens:** friction tags drift to free-text ("annoying", "slow",
"confusing"). Downstream agents have no routing key. The friction backlog
becomes unactionable.

**When it occurs:** when the author hasn't internalized the fixed enum, or
when "just one quick custom tag" is allowed.

**How to avoid:** enforce the five-value enum (`cognitive_load`,
`click_count`, `mode_switch`, `data_input`, `search`). The checker rejects
any other tag. If a friction does not fit the enum, capture it in `notes`,
do not invent a sixth tag.
