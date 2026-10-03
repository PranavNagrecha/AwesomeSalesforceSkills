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

| Name | Description | ActionReference | AcceptanceLabel | RejectionLabel | Expiration_Date__c (custom) |
|---|---|---|---|---|---|
| (recommendation name, max 80) | (user-facing description, max 255) | (API name of the acceptance flow) | (button text, max 80) | (dismiss text, max 80) | (YYYY-MM-DD or blank) |
| | | | | | |
| | | | | | |

## Strategy Flow Design

**Flow type:** Autolaunched Flow

**Input variables:**
- (record variable — specify sObject type, e.g., Case, Opportunity, Account)

**Output variables:**
- `recommendations` — Type: Record (Recommendation), Collection: Yes, Available for Output: Yes

**Logic outline:**
1. Get Records: Retrieve Recommendation records WHERE (filter criteria) AND IsActionActive = true AND (Expiration_Date__c >= TODAY OR Expiration_Date__c = null), sorted and limited to the display count (1–4)
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
| (name) | (flow API name) | Flow | (describe the action) |
| | | | |

## Checklist

Copy from SKILL.md Review Checklist and tick items as you complete them.

- [ ] Einstein Next Best Action permission set license is assigned to target users
- [ ] All Recommendation records have ActionReference values pointing to active flows (IsActionActive = true)
- [ ] Strategy Flow defines an output variable of type `List<Recommendation>` (collection, sObject = Recommendation)
- [ ] Strategy Flow filtering logic excludes expired recommendations (custom Expiration_Date__c < TODAY)
- [ ] Actions & Recommendations component is placed on the correct Lightning page and configured with the strategy Flow
- [ ] Acceptance actions execute correctly when the user clicks the acceptance button
- [ ] Deployment maxDisplayRecommendations set (1–4) and the strategy ranks before that cut
- [ ] AcceptanceLabel and RejectionLabel text is clear and user-friendly

## Notes

Record any deviations from the standard pattern and why.
