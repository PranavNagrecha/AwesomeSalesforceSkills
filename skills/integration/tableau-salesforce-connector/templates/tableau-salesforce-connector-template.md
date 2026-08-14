# Tableau ↔ Salesforce Connector — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `tableau-salesforce-connector`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Answers to the Before Starting questions from SKILL.md:

- Workbook name, audience, and the decision it supports:
- Tolerated staleness, stated in minutes (there is no live mode on the CRM connector):
- Objects and fields required, with formula fields flagged separately:
- Current org API headroom from `/services/data/vXX.0/limits`:

## Approach

Source per workbook (CRM connector extract or Data Cloud), refresh interval, and the API cost that buys:

## Checklist

From the review checklist in SKILL.md, plus the failure modes in `references/gotchas.md`:

- [ ] Formula fields and >4096-character text fields audited — they are excluded from extracts
- [ ] Joins expressible as left or inner with equality only
- [ ] Refresh schedule forecast against measured calls-per-refresh, staggered off the hour
- [ ] Connection uses a least-privilege integration user with ApiEnabled, not a cloned admin
- [ ] Embedded views on record pages only, if dynamic filtering is required

## Notes

Deviations from the standard pattern, and the reason for each:

