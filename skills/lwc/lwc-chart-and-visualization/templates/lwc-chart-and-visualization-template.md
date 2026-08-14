# LWC Chart and Visualization — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `lwc-chart-and-visualization`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Answers to the Before Starting questions from SKILL.md:

- Data volume at the point of render, and the volume before aggregation:
- Interactivity required (static, tooltip, drill, pan/zoom/brush):
- Accessibility obligation for this surface:
- Library and bundle size against the 5 MB static-resource ceiling:

## Approach

Library choice and why; whether a `lightning-datatable` would communicate this better:

## Checklist

From the review checklist in SKILL.md, plus the failure modes in `references/gotchas.md`:

- [ ] Chart constructed once behind a boolean guard in `renderedCallback`
- [ ] Instance destroyed in `disconnectedCallback`
- [ ] `this.template.querySelector` used — never `document`
- [ ] `lwc:dom="manual"` present if and only if the library appends DOM
- [ ] Data aggregated server-side; transport measured before renderer tuning
- [ ] Hidden data table plus `aria-describedby`; series not encoded by colour alone
- [ ] Static resource is Private and version-named

## Notes

Deviations from the standard pattern, and the reason for each:

