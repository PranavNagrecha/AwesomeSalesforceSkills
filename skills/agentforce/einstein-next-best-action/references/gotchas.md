# Gotchas — Einstein Next Best Action

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

Sources: Object Reference for the Salesforce Platform (Spring '26: Recommendation, RecommendationResponse), Metadata API Developer Guide (Spring '26: RecordActionDeployment, RecommendationStrategy, Flow `processType`), and the Trailhead unit "Set Up Salesforce Flow for Service" (Actions & Recommendations configuration), read on 2026-10-03. help.salesforce.com NBA articles do not render to a fetcher.

## Gotcha 1: Strategy Builder Deprecation Is Claimed but Not Documented in the Sources Read

**What happens:** Practitioners are told Strategy Builder was deprecated in Spring '24 and that new orgs lack it, then find Strategy Builder still referenced in current Trailhead units and the `RecommendationStrategy` metadata type still documented. UNVERIFIED (2026-10-03): earlier versions of this skill stated the Spring '24 deprecation; no source read for this revision confirms it.

**When it occurs:** When an org has existing Strategy Builder strategies and the team must decide whether to migrate.

**How to avoid:** Build new strategies as flows of process type `RecommendationStrategy` ("Build recommendations for your users. A recommendation launches its assigned flow", API 54.0+). Inventory existing `RecommendationStrategy` metadata and plan migration on evidence from current release notes, not on this claim alone.

**Source:** Metadata API Developer Guide, Flow (`processType` values: `RecommendationStrategy`) and RecommendationStrategy type; Trailhead, "Set Up Salesforce Flow for Service" (Strategy Builder steps).

---

## Gotcha 2: ActionReference Points to a Flow, and IsActionActive Tells You When It Breaks

**What happens:** A user clicks the acceptance button and nothing visible occurs because the referenced flow is inactive or misnamed. `Recommendation.ActionReference` is the "Flow referenced for this recommendation". Earlier versions of this skill said it can also reference a quick action; the Object Reference and the Trailhead setup steps ("Select the flow that launches when the recommendation is accepted") only describe flows. The read-only `IsActionActive` field "Indicates whether the flow referenced in the Action field is active".

**When it occurs:** A flow deactivated during a deployment, a typo in the API name, or a packaged flow referenced without its namespace.

**How to avoid:** Query `SELECT Id, Name, ActionReference FROM Recommendation WHERE IsActionActive = false` after every deployment, and filter strategies on `IsActionActive = true` so broken recommendations never reach users.

**Source:** Object Reference, Recommendation (`ActionReference`, `IsActionActive`); Trailhead, "Set Up Salesforce Flow for Service".

---

## Gotcha 3: Actions & Recommendations Shows at Most Four Recommendations

**What happens:** A strategy returns ten recommendations and reps see only a few. The deployment field `maxDisplayRecommendations` "Specifies the maximum number of recommendations to display. Valid values are 1–4." Trailhead's setup steps say "You can show a maximum of 4 recommendations." Earlier versions of this skill said the cap is 25.

**When it occurs:** Strategies that return many recommendations without ranking, or teams that expect a long list.

**How to avoid:** Rank in the strategy (sort, then limit) so the most important recommendations come first, and set `maxDisplayRecommendations` deliberately. UNVERIFIED (2026-10-03): the separate Einstein Next Best Action Lightning component's own display limit was not found in the sources read.

**Source:** Metadata API Developer Guide, RecordActionDeployment (`RecordActionRecommendation.maxDisplayRecommendations`); Trailhead, "Set Up Salesforce Flow for Service".

---

## Gotcha 4: Recommendation Records Are Org-Wide, Not Object-Specific

**What happens:** Recommendations meant for Cases appear on Opportunities. The Recommendation object has no object-type field; its fields are AcceptanceLabel, ActionReference, Description, ExternalId, ImageId, IsActionActive, Name, NetworkId, RecommendationKey, and RejectionLabel.

**When it occurs:** When several strategies query all Recommendation records without filters.

**How to avoid:** Add a custom field such as `Target_Object__c` and filter on it in each strategy. Use the deployment's object contexts (`deploymentContexts`, up to 10 objects) to run an object-specific strategy on each page type.

**Source:** Object Reference, Recommendation (field list); Metadata API Developer Guide, RecordActionDeploymentContext ("We support a maximum of 10 objects that provide context within a deployment").

---

## Gotcha 5: There Is No Standard Expiration Field

**What happens:** A strategy filters on `Recommendation.ExpirationDate` and fails to save, or a data load maps an expiry column to nothing. No such field exists on the standard object. Earlier versions of this skill described ExpirationDate as standard.

**When it occurs:** Time-limited offers designed from memory.

**How to avoid:** Create a custom date field (for example `Expiration_Date__c`), populate it, and filter on it in the strategy. Pair it with a scheduled cleanup if records should be archived.

**Source:** Object Reference, Recommendation (field list).

---

## Gotcha 6: The Strategy Flow's Output Variable Must Be a Recommendation Collection

**What happens:** The strategy flow runs without errors, but the component shows nothing. The component expects the flow to hand back a collection of Recommendation records.

**When it occurs:** When the output variable is a single record, a generic sObject collection, or not marked available for output.

**How to avoid:** Create the output variable as a collection of Record type Recommendation and mark it Available for Output. UNVERIFIED (2026-10-03): that the variable must be named `outputRecommendations` comes from Salesforce Help search snippets, not from a source read for this revision.

**Source:** Carried from earlier revisions; Metadata API Developer Guide, Flow (`RecommendationStrategy` process type).

---

## Gotcha 7: No Deployment Selected Means an Empty Component

**What happens:** The Actions & Recommendations component is on the page but reps see an empty list. Trailhead's setup steps say: "If you don't select a deployment, reps see an empty list when they click Add."

**When it occurs:** When the component is dropped on a page before a deployment exists, or a page is cloned to an org without the deployment.

**How to avoid:** Create the `RecordActionDeployment` first, select it in the component properties, and deploy both together.

**Source:** Trailhead, "Set Up Salesforce Flow for Service" (Configure the Component).

---

## Gotcha 8: Reject Can Launch the Flow Too

**What happens:** A rep rejects a recommendation and the acceptance flow runs anyway. The deployment field `shouldLaunchActionOnReject` is required and, when true, launches the flow when the recommendation is rejected.

**When it occurs:** Deployments copied from an example that set it true, or flows that assume they only run on accept.

**How to avoid:** Set `shouldLaunchActionOnReject` on purpose. If it is true, make the flow branch on the response so a reject does not perform the accept action.

**Source:** Metadata API Developer Guide, RecordActionDeployment (`shouldLaunchActionOnReject`).

---

## Gotcha 9: Creating Recommendations Needs a Specific Permission

**What happens:** An admin or integration user cannot create or edit Recommendation records. The Object Reference says you must have Modify All Data or the Manage Next Best Action Recommendations user permission to create and edit recommendations. Reading or managing `RecommendationResponse` needs Modify All Data, Manage Next Best Action Recommendations, or Manage Next Best Action Strategies.

**When it occurs:** Data loads of recommendations by a restricted integration user, or analysts who need response reports.

**How to avoid:** Grant Manage Next Best Action Recommendations to the people and integration users who maintain the catalog, and plan response reporting access separately.

**Source:** Object Reference, Recommendation and RecommendationResponse (Special Access Rules).
