# Flow Open A Page Action — Work Template

Use this template when designing, reviewing, or migrating navigation in a Screen Flow with the
Summer '26 **Open a Page** action.

## Scope

**Skill:** `flow-open-a-page-action`

**Request summary:** (fill in what the user asked for)

## Context Gathered

- **Is it a Screen Flow?** (Open a Page requires screens — a background flow can't navigate):
- **Navigation target:** ☐ Salesforce record ☐ External web page (URL)
- **Where does the target value come from?** (e.g. `{!newCase.Id}` after Create Records; a
  formula-built URL):
- **Desired open location** (fill Where to Open Page; read the actual option labels in Flow
  Builder — do not assume a "current page"/same-tab option exists):
- **Surfaces the flow runs on:** ☐ Desktop LEX ☐ Console ☐ Mobile ☐ Experience Cloud
- **Existing redirect being replaced?** ☐ Custom LWC (`NavigationMixin`) ☐ `navigateToUrl` local
  action ☐ retURL / finish-URL hack ☐ none

## Navigation Decision (pick one, cite the reason)

| Choice | Use when | Reason |
|---|---|---|
| ☐ Native Open a Page action | Open a record or URL, common case | Declarative, supported, no code |
| ☐ Custom LWC (`NavigationMixin`) | Related-tab targeting, current-page reuse, reactive UX | Action can't express these (open IdeaExchange requests) |
| ☐ Finish behavior / retURL | Behavior only needed at interview completion | Legacy; prefer the action unless finish-only is required |

## Configuration Plan

```text
<earlier element that produces the target, e.g. Create Records -> {!record.Id}>
Action: Open a Page
    - Target:            <record {!record.Id}  |  external URL {!urlResource}>
    - Where to Open Page: <open-location value confirmed in Flow Builder>
    - Placement:         <after the value exists; behind a Decision if conditional>
```

## Checklist

Copy the review checklist from SKILL.md and tick items as you complete them.

- [ ] Flow has screens (it's a Screen Flow); action isn't in a background flow
- [ ] Target value (record Id / URL) is guaranteed populated when the action runs
- [ ] Where to Open Page set intentionally; option behavior confirmed in Flow Builder
- [ ] Record-access reality tested (no-access user sees insufficient-access, not data)
- [ ] Legacy redirect fully removed, dead variables deleted
- [ ] No GA/Beta/Pilot claim made that the release notes don't state
- [ ] Open location verified on every surface the flow runs

## Validation

Run the skill checker against your metadata tree:

```bash
python3 scripts/check_flow_open_a_page_action.py --manifest-dir force-app/main/default
# --strict also fails on legacy-redirect migration candidates (INFO -> failure)
```

## Notes

(Record any deviations from the standard pattern and why — e.g. a related-tab requirement that
forced a custom component instead of the action.)
