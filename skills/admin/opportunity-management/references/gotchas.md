# Gotchas — Opportunity Management

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Deleting a Stage Picklist Value Silently Corrupts Active Records

**What happens:** When a Stage picklist value is deleted while Opportunity records still carry that value, Salesforce removes the picklist entry without issuing a blocking error. The Stage field on affected records becomes blank — not replaced with a default, not flagged in a report. Existing records are silently corrupted. <!-- UNVERIFIED (2026-09-04): the "becomes blank, no blocking error" behaviour is carried from the previous revision of this skill; neither api_meta.txt nor object_reference.txt documents what happens to records on picklist-value deletion. What the Object Reference does state is the deactivation path: inactive stage values "are not available in the picklist and are retained for historical purposes only" (object_reference.txt:195512–195514). Deactivate; the delete-time behaviour is the part to confirm in a sandbox before relying on it. -->

**When it occurs:** Any time an admin deletes (not deactivates) an Opportunity Stage value from Setup > Opportunity Stages while records with that stage exist. This includes sandbox refreshes where stage values are pruned without checking record counts.

**How to avoid:** Before deleting any Stage value:
1. Query: `SELECT COUNT() FROM Opportunity WHERE StageName = 'Old Stage Name'`
2. If count > 0, bulk-reassign those records to an active stage before proceeding.
3. Prefer deactivating the value (unchecking "Active") over deleting it. Deactivation removes it from the picklist dropdown for new records while preserving it on historical closed records.
4. Only hard-delete a Stage value if zero records reference it.

---

## Gotcha 2: ForecastCategoryName Labels Are Platform-Fixed and Cannot Be Renamed

**What happens:** Admins expect to rename forecast category labels (e.g., "Best Case" → "Upside") via Setup > Opportunity Stages or the picklist editor. Both `OpportunityStage.ForecastCategoryName` and `Opportunity.ForecastCategoryName` are **restricted picklists** with a fixed value list — `Best Case`, `Closed`, `Commit`, `Most Likely`, `Omitted`, `Pipeline` (object_reference.txt:195499–195505, 192491–192497). Note that there are six, not five: `Most Likely` is routinely omitted from stage-design documents and then discovered mid-implementation. <!-- UNVERIFIED (2026-09-04): "restricted picklist with a fixed value list" is grounded; the specific failure mode on a rename attempt (hard error vs. silent revert) is carried from the previous revision and is not described in either guide. -->

**When it occurs:** During implementations where business stakeholders want custom forecast category names that match their internal terminology. The category labels visible in forecast reports and the Forecast tab always display the platform values: Pipeline, Best Case, Commit, Closed, Omitted.

**How to avoid:** Communicate to stakeholders early that these five labels are fixed. Use stage names and Path guidance text to express the org's internal terminology. Document the mapping between internal terms and platform labels in training materials. Do not attempt to rename ForecastCategoryName via metadata deploys — the deploy will either fail or be ignored.

---

## Gotcha 3: Opportunity Splits Cannot Be Disabled Once Data Exists

**What happens:** After enabling Opportunity Splits and saving even one split record on an opportunity, the feature cannot be turned off. The "Disable Splits" option in Setup is either removed or non-functional once split data exists. This is permanent for that org.

**When it occurs:** Admins who enable splits in production for a pilot, then try to roll back because the pilot failed or the business process changed.

**How to avoid:** Treat enabling Opportunity Splits in production as a one-way door. Always:
1. Pilot splits in a full sandbox first.
2. Get explicit sign-off from business stakeholders that the split model is permanent.
3. Confirm that Team Selling is enabled before enabling Splits — the platform dependency is hard.
4. Never enable splits in production speculatively or for testing purposes.

---

## Gotcha 4: Team Selling Must Be Enabled Before Opportunity Splits

**What happens:** Attempting to enable Opportunity Splits without first enabling Opportunity Teams (Team Selling) results in a platform error. The Splits Setup page may be inaccessible or show an error message requiring Teams to be enabled first.

**When it occurs:** When an admin enables Splits directly without following the documented setup order, typically when working from memory or an incomplete runbook.

**How to avoid:** The correct order is: (1) Setup > Opportunity Team Settings > Enable Opportunity Teams, then (2) Setup > Opportunity Settings > Enable Opportunity Splits. Never reverse this order. Include this as a step in any deployment runbook involving splits.

---

## Gotcha 5: Path Settings Do Not Enforce Stage Progression

**What happens:** Admins configure Path with stages in a logical order and assume this prevents reps from skipping stages or saving at an unexpected stage. Path is visual guidance only — it has no save-blocking behavior. Reps can freely jump from stage 1 to stage 7 without triggering any error from Path.

**When it occurs:** Any time Path is the sole mechanism relied upon for stage compliance. This is especially common after an admin demonstrates Path in a UAT session where reps manually follow the stages — the UAT passes, but enforcement was never real.

**How to avoid:** Pair Path with validation rules for any progression requirement that must be enforced. Clearly document in the business requirements which stage transitions are required vs. guided. Validation rules using `PRIORVALUE(StageName)` and `ISPICKVAL()` are the correct enforcement mechanism.

---

## Gotcha 6: Stages Assigned to a Sales Process Must Exist Globally First

**What happens:** Admins try to add a new stage directly inside a Sales Process without first creating it in the global Opportunity Stages picklist. The platform requires the stage to exist globally before it can be added to a process. Attempting to bypass this produces an error.

**When it occurs:** When admins confuse the Sales Process editor with the global picklist editor, particularly when onboarding new business units that need custom stages.

**How to avoid:** Always create and configure new Stage values in Setup > Opportunity Stages first (including setting IsClosed, IsWon, Probability, and ForecastCategoryName). Only then return to Setup > Sales Processes to add the new stage to the relevant process.

---

## Gotcha 7: Overlay Split Totals Are Not Validated Against 100%

**What happens:** Revenue splits enforce a total of exactly 100% — the platform blocks saving if the total is not 100%. Overlay splits have no such constraint. Overlay split totals can be 50%, 150%, or 300% — the platform accepts any value. This is by design but surprises admins who expect consistent validation behavior across split types.

**When it occurs:** When admins test overlay splits and expect the same 100% validation they see on revenue splits. Also occurs when auditing overlay data and finding unexpected totals.

**How to avoid:** The behaviour is a property of the split *type*, not of the words "revenue" and "overlay": `OpportunitySplitType.IsTotalValidated` — "If true, the split must total 100%. If false, the split can total any percentage" (object_reference.txt:195329–195334) — decides it, and `SplitPercentage` accepts 0–100 on a validated type and 0–1,000 on an unvalidated one (object_reference.txt:195208–195212). Read the flag before predicting the behaviour; a custom type named "Revenue Split" with `IsTotalValidated = false` validates nothing. Document the difference clearly in user training. For orgs that want to cap overlay credit, implement a custom validation rule or Flow that checks overlay split totals per opportunity if the business requires a limit.

---

## Gotcha 8: A Stage Removed From a Sales Process Stays on Every Record That Already Has It

**What happens:** An admin retires "Demo Scheduled" from the Renewal sales process and considers the stage gone for renewals. It is not. A `BusinessProcess` is a display filter over the global value set — the guide describes it as a way to "display different picklist values for users based on their profile" (api_meta.txt:42956–42957). Removing a value from the process removes it from the *picklist* for record types bound to that process. Every renewal opportunity already sitting in "Demo Scheduled" keeps that `StageName`, keeps its `IsClosed`/`IsWon`/`ForecastCategoryName`, keeps rolling into the forecast, and keeps appearing in reports grouped by stage — but no rep can now move it forward through the picklist, because the value they would pass through is no longer offered.

**When it occurs:** Any stage-ladder consolidation done by editing sales processes instead of migrating records. It is invisible in a sandbox seeded with fresh data and obvious in production the morning after.

**How to avoid:** Treat "remove from process" and "retire the value" as two separate jobs with two separate audits.
1. Before editing the process, count the records: `SELECT StageName, COUNT(Id) FROM Opportunity WHERE IsClosed = FALSE GROUP BY StageName`.
2. Migrate open records off the stage first.
3. Then remove it from the process. Closed records may keep the value — that is what deactivation on the value set is for later.
4. If the value is being retired org-wide, deactivate it on the `OpportunityStage` standard value set rather than deleting it; inactive values are "not available in the picklist and are retained for historical purposes only" (object_reference.txt:195512–195514).

---

## Gotcha 9: Changing the Stage Silently Overwrites a Probability or Forecast-Category Override

**What happens:** `Probability` and `ForecastCategoryName` are per-record overridable — the Object Reference says each is "implied, but not directly controlled, by the `StageName` field. You can override this field to a different value than is implied by the `StageName` value" (object_reference.txt:192487–192489). So a deal desk sets a bespoke 65% on a stage whose default is 50%, or moves a stage into `Commit` for one strategic deal. The next stage change wipes it: "If the `StageName` is updated, then the `ForecastCategoryName`, `IsClosed`, `IsWon`, and `Probability` are automatically updated based on the stage-category mapping" (object_reference.txt:192903–192905).

**When it occurs:** Constantly, and worst in integrations. A middleware update that sets `StageName` and `Probability` in the same record payload has no defined winner from the caller's point of view — the stage-derived value is what lands. The same applies to a Flow or trigger that sets `Probability` before the stage assignment in the same transaction.

**How to avoid:**
1. Inventory every writer of `Probability` and `ForecastCategoryName` before changing the ladder — Apex, Flow, integration users, Data Loader templates.
2. Where an override must survive, apply it in an `after`-context step that runs once the stage-derived values are in place, or in a second update.
3. Detect drift with query 8b in `references/metadata-examples.md` §8: any row whose `Opportunity.ForecastCategoryName` differs from the stage's own default is an override. A handful is deal desk; thousands is a broken integration.
4. `ExpectedRevenue` follows from this — it is "equal to the product of the opportunity `Amount` field and the `Probability`" (object_reference.txt:192406–192408), so a reset Probability silently restates every expected-revenue figure on the record.

---

## Gotcha 10: Marking an Opportunity Private Deletes the Team, the Splits, and the Sharing

**What happens:** `IsPrivate` looks like a visibility checkbox. It is destructive. The Object Reference: "If true, only the opportunity owner, users above that role in the hierarchy, and admins can view the opportunity or query it via the API. **When you mark opportunities as private, opportunity teams, opportunity splits, and sharing are removed**" (object_reference.txt:192598–192604). Not hidden — removed. Unchecking the box afterwards does not bring the split rows or team members back.

**When it occurs:** On sensitive deals (M&A, executive accounts) where someone reaches for Private as a quick confidentiality control, on a team-selling org where those are exactly the deals with the most split credit attached. Also on data loads that carry a stale `IsPrivate` column.

**How to avoid:**
1. In any org running team selling or splits, decide explicitly who may set `IsPrivate`, and remove the field from layouts everywhere else.
2. Never include `IsPrivate` in a data-load template unless the load is specifically about it.
3. Where confidentiality is genuinely needed on a deal that also needs a team, use restricted OWD plus explicit sharing instead — `IsPrivate` and team selling are mutually exclusive designs, not layered ones.
4. Forecast impact follows automatically: a private opportunity's splits no longer exist, so split-based forecast types lose that deal's credit entirely.

---

## Gotcha 11: Split Types Cannot Be Created or Deleted Through Any API, and Their 100% Rule Is Frozen at Creation

**What happens:** A team builds splits in a sandbox, then finds there is nothing to deploy. There is no `OpportunitySplitType` metadata type — the Metadata API guide mentions splits only as a *reference* from `ForecastingType.opportunitySplitType` and `ForecastingSettings` (api_meta.txt:75253, 75256, 117757). The `OpportunitySplitType` object is no better: its supported calls are `describeSObjects()`, `query()`, `retrieve()`, `update()` — **no `create()`, no `delete()`** (object_reference.txt:195284–195285). Every org needs the split types hand-built in Setup, by a human, in the right order relative to team selling.

Worse, the flag that decides the 100% rule is not updateable. `IsTotalValidated` — "If true, the split must total 100%. If false, the split can total any percentage" — is `Create, Defaulted on create, Filter, Group, Sort` (object_reference.txt:195329–195334). There is no `Update`. A split type created without validation cannot later be made to enforce 100%.

**When it occurs:** At the sandbox-to-production step of every splits rollout, and again years later when someone tries to "tighten up" an overlay type.

**How to avoid:**
1. Put split-type creation in the deployment runbook as a manual Setup step, with the exact `MasterLabel`, `DeveloperName`, `SplitField` and `IsTotalValidated` value written down per org.
2. Decide `IsTotalValidated` once, deliberately. Revenue credit that must sum to the deal → `true`. Overlay credit → `false`.
3. Remember what `false` actually permits: `SplitPercentage` "If the split type is validated to a 100% total, this number can range from 0 to 100. If the total isn't validated, this number can range from 0 to 1,000" (object_reference.txt:195208–195212). Overlay totals of 300% are legal data, not corruption.
4. `update()` is available, so a script can flip `IsActive` or relabel a type. That is the full extent of what automation can do here.

---

## Gotcha 12: `OpportunityHistory` Is Not a Stage-History Table

**What happens:** Someone builds "days in stage" reporting on `OpportunityHistory` row counts and gets numbers that are too high. The object "represents the history of a change to the **Amount, Probability, Stage, or Close Date** fields of an Opportunity" (object_reference.txt:193618–193619) — one row is written whenever *any* of those four changes, and "the then-current values of all of these major fields are saved in the newly-generated object" (object_reference.txt:193624–193626). An opportunity re-quoted four times without moving stage produces four rows all showing the same `StageName`.

The inverse trap is just as bad: "if an opportunity's Amount, Probability, Stage, or Close Date fields have not changed, nothing will be returned in the `OpportunityHistory` objects" (object_reference.txt:193621–193623). A deal that has sat untouched has no history rows at all, so a report built on this object drops exactly the stalled deals a pipeline review is looking for.

**When it occurs:** Any pipeline-velocity or stage-duration report built without reading the object's Usage section. Also on migrations, since the record "is automatically deleted if its parent Opportunity is deleted" (object_reference.txt:193628–193629) — a delete-and-reload migration destroys the history it was meant to preserve.

**How to avoid:**
1. For stage age, prefer `Opportunity.LastStageChangeDate` and `LastStageChangeInDays` (object_reference.txt:192706–192724, v52.0+, and `LastStageChangeInDays` requires Pipeline Inspection enabled).
2. If you must use `OpportunityHistory`, deduplicate on stage transitions rather than counting rows: group by `OpportunityId, StageName` and take the earliest row per group.
3. For anything outside those four fields, use `OpportunityFieldHistory`, and turn field history tracking on **before** the ladder ships — `enableOpportunityFieldHistoryTracking` defaults to `true` (api_meta.txt:123321–123323), but history is never backfilled.
4. Never plan a delete-and-reload migration on Opportunity if stage history matters.

---

## Gotcha 13: The Metadata Forecast-Category Vocabulary Is Not the SOQL One

**What happens:** An engineer reads `ForecastCategoryName = 'Commit'` off a stage in an org, writes `<forecastCategory>Commit</forecastCategory>` into the `standardValueSet` file, and the deploy fails on an invalid enumeration value. <!-- UNVERIFIED (2026-09-04): that an out-of-enumeration value produces a deploy failure rather than being ignored is an inference from the field being typed as the ForecastCategories enumeration (api_meta.txt:47578-47580); the guide does not state the error behaviour. The enumeration membership itself is grounded. --> The metadata element takes a different token set. `forecastCategory` is typed as the `ForecastCategories` enumeration with exactly these members: `Omitted`, `Pipeline`, `BestCase`, `Forecast`, `Closed` (api_meta.txt:47578–47586). What the UI and SOQL call **Commit** is `Forecast` in metadata; `BestCase` loses its space; and `Most Likely` — a legitimate `ForecastCategoryName` value (object_reference.txt:195499–195505) — has no metadata token at all.

**When it occurs:** Every time a stage ladder is round-tripped through a spreadsheet or an LLM, because the query output and the deploy input use different strings for the same concept, and nothing in either file signals the difference.

**How to avoid:**
1. Keep one mapping table in the design doc and never let the two vocabularies mix in the same column:

   | Metadata `forecastCategory` | `ForecastCategoryName` (SOQL/UI) |
   |---|---|
   | `Pipeline` | Pipeline |
   | `BestCase` | Best Case |
   | `Forecast` | **Commit** |
   | `Closed` | Closed |
   | `Omitted` | Omitted |
   | *(no token)* | Most Likely |

2. Author stage values from a retrieved `standardValueSet` file, never from a SOQL export.
3. `scripts/check_opportunity_management.py` validates stage `forecastCategory` against the metadata enum for exactly this reason — a checker built against the SOQL vocabulary flags every correct file.
4. `Opportunity.ForecastCategory` is a third variant (`BestCase`, `Closed`, `Forecast`, `MostLikely`, `Omitted`, `Pipeline`, object_reference.txt:192474–192481) and is derived: "the value of this field is automatically set based on the value of the `ForecastCategoryName` and can't be updated any other way" (object_reference.txt:192462–192463). Never write it.

---

## Gotcha 14: One Path Per Record Type — and `recordTypeName` Cannot Be Edited

**What happens:** An admin wants two guidance experiences on the same record type (one for the enterprise team, one for SMB) and finds there is no way to build the second. The guide is unambiguous: "**Only one path can be created per record type for each object, including `__Master__` record type**" (api_meta.txt:94496). Path has no profile, permission-set or division axis.

The second half bites during refactors: `entityName`, `fieldName` and `recordTypeName` are all documented as "not updateable" (api_meta.txt:94513–94530). Editing `recordTypeName` in the XML and redeploying does not repoint the Path; the change is either rejected or ignored, and the org keeps the original binding.

**When it occurs:** During record-type consolidation, when a Path built on a retired record type needs to move to its replacement.

**How to avoid:**
1. Treat "two guidance experiences" as a record-type requirement, and price it as one — see `admin/record-type-strategy-at-scale` before adding record types purely for Path.
2. Repointing a Path is delete-then-create, not edit. Sequence it in the runbook so the new Path exists before the old record type is deactivated.
3. Do not read a green Path deploy as a working Path: "the preference does not need to be on to retrieve or deploy PathAssistant" (api_meta.txt:94498), and the Path component still has to be placed on the Lightning record page separately.
4. A stage with no `pathAssistantSteps` entry still shows as a chevron — "a missing step in the .xml file means it has not been configured, not that it doesn't exist" (api_meta.txt:94524–94526). An unconfigured step is not a hidden step.

---

## Gotcha 15: Opportunity Contact Roles Are Not a Sharing Mechanism, and the Query Leaks Rows

**What happens:** Teams reach for `OpportunityContactRole` to express "who at the customer is involved", then assume the object's access mirrors the contact's. It does not, in either direction. The Object Reference on `ContactId`: "The API applies user access rights to the associated Opportunity for this object, but not to the associated Contact. The API may return rows from a query on this object that include this field's values for contacts to which the user does not have sufficient access rights. It may also return values for this field for contacts that have been deleted" (object_reference.txt:193162–193167).

So a user who can see the opportunity can enumerate contact IDs they have no right to see, and can see IDs for contacts that no longer exist. Adding a contact role also grants that contact's owner nothing on the opportunity — it is a relationship record, not an access grant.

**When it occurs:** In any report, integration or LWC that joins `OpportunityContactRole` to `Contact` and trusts the result; and in access designs that list "contact roles" as a way to give partner or channel users visibility.

**How to avoid:**
1. The guide states the remedy explicitly: "the client must perform a query on the contact table for this field's value to determine whether the Contact is accessible to the user and has not been deleted" (object_reference.txt:193166–193167). Re-query `Contact` by ID rather than trusting the join.
2. For access, use the mechanisms that actually grant it: `OpportunityTeamMember.OpportunityAccessLevel` (`Read`, `Edit`, `All` — object_reference.txt:195697–195700), sharing rules, or the role hierarchy.
3. Do not put anything sensitive in a contact-role picklist value; the same reasoning the guide applies to business processes applies here.

---

## Gotcha 16: Changing the Owner via the API Silently Leaves the Old Owner on the Team

**What happens:** An ownership realignment — territory change, rep departure, book-of-business rebalance — is run through Data Loader. The new owner is set. The old owner does not lose access: "when you change the owner of an opportunity using the API, the previous owner's access becomes Read Only or the access specified in your organization-wide default for opportunities, **whichever is greater**" (object_reference.txt:195762–195764). The same note appears on `OpportunitySplit`: "If you change the opportunity owner using the API, the old owner remains on the opportunity team with either Read-only access, or the level of access specified in your organization-wide defaults" (object_reference.txt:195258–195261).

The UI behaves differently: "performing this same action in the user interface allows you to select the access level for the previous owner when the previous owner is on an opportunity team" (object_reference.txt:195764–195766). So a change tested by hand in Setup does not reproduce what the bulk job does.

**When it occurs:** Every bulk owner reassignment in a team-selling org. It is invisible unless someone audits `OpportunityTeamMember` afterwards, because nothing errors and the new owner's access looks correct.

**How to avoid:**
1. Pair every bulk owner change with a follow-up pass over `OpportunityTeamMember` for the departing owners, and delete the rows that should not persist.
2. Note that `OpportunityTeamMember` deletion does not go to the Recycle Bin: "An `OpportunityTeamMember` that is deleted isn't moved to the Recycle Bin and can't be undeleted, unless the record was cascade-deleted when deleting a related Opportunity. For directly deleted `OpportunityTeamMember` records, don't use the `isDeleted` field to detect deleted records in SOQL queries. Instead, use `getDeleted()`" (object_reference.txt:195669–195671, 195683). Get the list right before you run it.
3. Do not validate an API-driven ownership change by performing it once in the UI — the two paths have different documented behaviour.

---

## Gotcha 17: A `<default>` Inside an Opportunity Business Process Fails the Deploy

**What happens:** The business process is authored the way every other picklist-bearing element is authored — the first stage gets `<default>true</default>`, the rest get `<default>false</default>` — and the deploy comes back:

> Cannot specify a default on: Opportunity

Org-verified 2026-09-18 against `sfskills-dev` (validate-only deploy at API 62.0, `.sfskills/builds/northwind-sales/reports/MOCK-DEPLOY-M1.md` run 1, `BusinessProcess Opportunity.Enterprise_Sales_Process`).

**When it bites you:** On the first deploy of any hand-written or generated Opportunity business process. The `BusinessProcess` entry in the Metadata API guide does not carry the restriction, and the `values` element is a `PicklistValue`, which *does* have a `default` child — so the shape parses, validates locally, and is refused by the platform. The element is also what almost every worked example on the internet shows.

**Why the platform is right:** a business process says *which* stages a record type exposes and in what order. Which stage a new record opens at is a property of the record type's `picklistValues` entry for `StageName`, not of the process. Two different elements, one of which the org accepts.

**How to avoid it:**
- Emit no `<default>` child — neither `true` nor `false` — inside `businessProcesses/values` on Opportunity.
- `scripts/check_opportunity_management.py` catches it as `OM-BP-DEFAULT-01` (ERROR, exit 1). Fixtures: `scripts/fixtures/bp-default-positive/`, `scripts/fixtures/bp-default-negative/`.
- **Only Opportunity is verified.** The org message names the object, and Lead, Case and Solution business processes have never been put to this org. `OM-BP-DEFAULT-01` deliberately stays silent on them, and the negative fixture pins that behaviour with a Case process that *does* carry a default. Do not generalise without a dry run — `UNVERIFIED (2026-09-18)` for the other three objects.
- The record type's own `picklistValues` default for `StageName` is a different element the org has not judged: `UNVERIFIED (2026-09-18)`. Leave it as it is.

