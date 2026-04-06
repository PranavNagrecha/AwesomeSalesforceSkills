# Einstein Next Best Action — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `einstein-next-best-action`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- **Permission set license assigned:** Yes / No — confirm "Einstein Next Best Action" PSL is assigned to target users
- **Recommendation object accessible:** Yes / No — confirm users can read Recommendation records
- **Target Lightning page:** (name the record page or app page where the component will be placed)
- **Strategy Builder in use:** Yes / No — if yes, plan migration to Flow Builder (Strategy Builder deprecated Spring '24)
- **Known constraints:** (e.g., number of active recommendations, Flow interview limits, page load time requirements)
- **Failure modes to watch for:** Silent acceptance failures from bad ActionReference; blank component from misconfigured output variable; expired recommendations still displaying

## Recommendation Records

| Name | Description | ActionReference | AcceptanceLabel | RejectionLabel | ExpirationDate |
|---|---|---|---|---|---|
| (recommendation name) | (user-facing description) | (API name of Flow or quick action) | (button text) | (dismiss text) | (YYYY-MM-DD or blank) |
| | | | | | |
| | | | | | |

## Strategy Flow Design

**Flow type:** Autolaunched Flow

**Input variables:**
- (record variable — specify sObject type, e.g., Case, Opportunity, Account)

**Output variables:**
- `recommendations` — Type: Record (Recommendation), Collection: Yes, Available for Output: Yes

**Logic outline:**
1. Get Records: Retrieve Recommendation records WHERE (filter criteria) AND (ExpirationDate >= TODAY OR ExpirationDate = null)
2. Decision: (describe branching logic based on input record fields)
3. Assignment: Add matching recommendations to the output collection
4. (additional Decision/Assignment branches as needed)

## Component Placement

- **Page:** (Lightning record page name)
- **Strategy Flow:** (API name of the strategy Flow)
- **Position on page:** (region/section where the component is placed)

## Acceptance Actions

| Recommendation Name | ActionReference | Action Type | What It Does |
|---|---|---|---|
| (name) | (Flow or quick action API name) | Flow / Quick Action | (describe the action) |
| | | | |

## Checklist

Copy from SKILL.md Review Checklist and tick items as you complete them.

- [ ] Einstein Next Best Action permission set license is assigned to target users
- [ ] All Recommendation records have valid ActionReference values pointing to active Flows or quick actions
- [ ] Strategy Flow defines an output variable of type `List<Recommendation>` (collection, sObject = Recommendation)
- [ ] Strategy Flow filtering logic excludes expired recommendations (ExpirationDate < TODAY)
- [ ] Actions & Recommendations component is placed on the correct Lightning page and configured with the strategy Flow
- [ ] Acceptance actions execute correctly when the user clicks the acceptance button
- [ ] No more than 25 recommendations are returned per strategy invocation
- [ ] AcceptanceLabel and RejectionLabel text is clear and user-friendly

## Notes

Record any deviations from the standard pattern and why.
