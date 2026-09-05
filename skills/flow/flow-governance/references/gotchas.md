# Gotchas - Flow Governance

The first four are operational patterns. The rest are platform behaviours that make a
governance standard either enforceable or decorative, each grounded in the Metadata API
Developer Guide (`api_meta.txt`), the Object Reference (`object_reference.txt`) or the
Apex Developer Guide (`apexdev.txt`) by line.

## Weak Names Survive Longer Than Anyone Plans

**What happens:** Temporary or copied names remain in production for months or years.

**When it occurs:** Teams postpone naming cleanup because the flow "works for now."

**How to avoid:** Enforce naming standards before activation rather than as optional cleanup afterward.

---

## Inactive Versions Still Distort Understanding

**What happens:** Operators waste time comparing versions or copied flows because the real production path is unclear.

**When it occurs:** The org accumulates stale versions with no retirement review.

**How to avoid:** Review and retire ambiguity on a regular schedule instead of waiting for a crisis.

---

## Interview Labels Are Part Of Supportability

**What happens:** Logs and user-reported failures point to unhelpful interview names.

**When it occurs:** Teams focus only on builder labels and ignore how runtime history will be read later.

**How to avoid:** Use interview labels and descriptions as operational metadata, not just decoration. `interviewLabel` is a documented Flow field whose value "appears in the Paused Flow Interviews component on the user's Home tab and in the list of paused flow interviews in Setup" (`api_meta.txt` L68168–68172), and it lands on `FlowInterview.InterviewLabel` (`object_reference.txt` L139939–139948) where the inventory query in `references/metadata-examples.md` §5(c) can read it.

---

## Unowned Flows Become Incident Risks

**What happens:** Production issues stall because no team has clear responsibility for a flow.

**When it occurs:** Ownership exists informally but is never recorded in the governance process.

**How to avoid:** Require an owning team or accountable maintainer for every production flow, and back it with `enableFlowUseApexExceptionEmail` (below) so the error mail reaches that team rather than the last editor.

---

## `enableFlowDeployAsActiveEnabled` Makes "Deploy" And "Activate" Two Different Events

**What happens:** A change set or Metadata API deploy succeeds, the reviewer ticks it off, and nothing in production changed — the flow landed Draft. Or, with the setting on, the deploy is rolled back by a test failure in code nobody in the change touched.

**When it occurs:** In production only. "The default value is `false` for production orgs and is `true` for non-production orgs such as scratch, sandbox, and developer orgs" (`api_meta.txt` L116877–116886), so every sandbox rehearsal exercises the opposite behaviour from the production run. When the setting is `false`, "all processes and flows are deployed as inactive." When it is `true`, "deploying an active process or flow in a production org causes your Apex tests to run. If Apex tests don't launch your org's required percentage of active processes and autolaunched flows, the deployment is rolled back."

**How to avoid:** Deploy `settings/Flow.settings` as step 2 of the deploy order, before the flows, and assert `FlowDefinitionView.IsActive` after the release rather than trusting the deploy result. The guide does not give the required percentage a number. **UNVERIFIED (2026-09-05): the "required percentage of active processes and autolaunched flows" is not quantified in `api_meta.txt` or `apexdev.txt`; the 75% at `api_meta.txt` L2550 is Apex code coverage, a different rule.** Treat the requirement as a gate, not a metric.

---

## A `FlowDefinition` In The Tree Silently Overrides Every `<status>` In Your Diff

**What happens:** The reviewer reads `<status>Active</status>` on version 4 of a flow, approves it, and version 3 goes live.

**When it occurs:** Whenever a `flowDefinitions/` directory survives in the repo alongside modern version-number-free flow files. "If you deploy with flow definitions, the active version numbers in the flow definitions override the status fields in the flows. For example, the active version number in the flow definition is version 3, and the latest version of the flow is version 4 with the status field as `Active`. After you deploy your flow, the active version is version 3" (`api_meta.txt` L73929–73932, restated at L73203–73206). The guide's own recommendation since API 44.0 is to "discontinue using the FlowDefinition object to activate or deactivate a flow" (L73925–73928), and its upgrade checklist asks that "the flowDefinitions directory is empty" (L73189).

**How to avoid:** Declare one activation authority in `flow-governance-policy.yaml` (`activation_control: flow_status` or `flow_definition`) and let `scripts/check_flow_governance.py` fail the build when the tree contradicts it. A repo carrying both is a repo where the diff no longer tells you what will be live.

---

## A Flow With No `<status>` Element Deploys As Draft, Not As "Unchanged"

**What happens:** A hand-edited or generated flow file omits `<status>`, deploys cleanly, and the automation is off.

**When it occurs:** After a merge that drops the element, or when a tool writes a partial flow. The upgrade guidance is explicit: "For each active flow, the `status` field is `Active`. **Any flow without a `status` value is deployed or retrieved with a `status` value of `Draft`**" (`api_meta.txt` L73187–73188).

**How to avoid:** Make `<status>` mandatory in the policy's `versions.allowed_status` and let the checker WARN on its absence. Absence is a decision the platform makes for you, and it makes the quiet one.

---

## You Cannot Delete A Flow Version That Has Paused Interviews

**What happens:** The retirement deploy fails, or the destructive change silently leaves the version behind, and the quarterly cleanup shows no progress two quarters running.

**When it occurs:** Any org where `enableFlowPauseEnabled` is `true` (`api_meta.txt` L116935) or where scheduled paths and Wait elements are in use. "You can delete a flow version if it isn't active and doesn't have any paused interviews. If the flow version has paused interviews, wait for those interviews to resume and finish, or delete them" (`api_meta.txt` L68041–68042).

**How to avoid:** Make the retirement gate a query, not a calendar entry. Run `FlowInterview` filtered to `InterviewStatus IN ('Paused','VersionPaused','Error')` joined on `FlowVersionViewId` before the destructive change (`references/metadata-examples.md` §5(c)); `VersionPaused` means "this flow version is paused. No more records are processed until the flow is resumed" and is available in API 60.0 and later (`object_reference.txt` L139966–139969). Then run `FlowRecordRelation` to see which business records those interviews are holding (L143526–143529) — deleting the interview to unblock the deploy abandons someone's in-flight process.

---

## `enableFlowInterviewSharingEnabled` Is A Record-Access Decision Wearing A Flow Label

**What happens:** A user resumes a paused interview belonging to someone else and sees data they have no access to on the record itself.

**When it occurs:** By default. "By default (`true`), users can resume interviews that are shared with them, either directly or via the role hierarchy. When the value is `false`, each paused interview can be resumed only by the interview owner or a flow admin who has view access to the interview" (`api_meta.txt` L116918–116927). Interviews are shareable objects in their own right — `FlowInterview` carries both `FlowInterviewOwnerSharingRule` and `FlowInterviewShare` (`object_reference.txt` L140044–140049) — and `FlowInterview.OwnerId` notes "only this user or an admin can resume the interview" (L140003–140006).

**How to avoid:** Decide this with the sharing model, not with the Flow team, and record the decision in `Flow.settings` so it is reviewable. See `standards/decision-trees/sharing-selection.md` for who owns the call.

---

## `enableFlowFieldFilterEnabled` Turns A Fault Path Into Silence

**What happens:** A Create or Update Records element writes some fields and skips others, the flow reports success, and the data is quietly wrong.

**When it occurs:** When the setting is `true`. By default (`false`) "the Create Records or Update Records element fails and executes the fault path if it has one. When the value is `true`, the element sets only the fields that the running user can edit. **No notification is sent when some fields aren't updated**" (`api_meta.txt` L116889–116898).

**How to avoid:** Govern it to `false` unless a written exception exists. This is the one setting that can make an otherwise-correct `flow/fault-handling` implementation unable to see the failure — the fault connector `scripts/check_flow_faults.py` verifies never fires, because nothing raises.

---

## `runInMode` Is A Governance Setting That Looks Like A Build Detail

**What happens:** A flow authored by a delivery team runs as `SystemModeWithoutSharing` and reads every record in the org, and nobody in the release review notices because the value is one line in a 900-line XML file.

**When it occurs:** Any autolaunched or record-triggered flow, since API version 48.0 (`api_meta.txt` L68374–68390). `SystemModeWithSharing` "respects org-wide default settings, role hierarchies, sharing rules, manual sharing, teams, and territories" but "doesn't respect object permissions, field-level access, or other permissions of the running user." `SystemModeWithoutSharing` — "the flow can access all data", API 49.0+. `DefaultMode` means "how the flow is launched determines whether the flow runs in user context or in system context."

**How to avoid:** Put the allow-list in `versions.allowed_run_in_mode` and make an exception a security review with a named approver. Note the platform's own asymmetry: `FlowVersionView.RunInMode` documents only `DefaultMode` and `SystemModeWithSharing` (`object_reference.txt` L145251–145262), so the mode you most want to find in an inventory query is the one the view's documented enum does not list. Read it from the metadata, not only from SOQL.

---

## `FlowVersionView` Cannot Be Swept — The Portfolio Query Has To Be Two-Stage

**What happens:** The inventory script returns nothing, and the team concludes the org has no version drift.

**When it occurs:** On any unfiltered `SELECT … FROM FlowVersionView`. "A query must be filtered by `DurableId` or `FlowDefinitionViewId` to get results" (`object_reference.txt` L145295–145296).

**How to avoid:** Drive it from `FlowDefinitionView`, which is freely queryable (API 46.0+, `object_reference.txt` L139267–139273), then loop per definition. Version-level facts — `Status`, `ApiVersion`, `ApiVersionRuntime`, `RunInMode` — exist only at that second stage, so "how many old versions does this flow have" is structurally a two-query answer.

---

## API-Version Drift Changes Run-Time Behaviour, Not Just The Label

**What happens:** Two record-triggered flows on the same object behave differently in the same save, and the difference does not appear anywhere in either flow's logic.

**When it occurs:** Whenever flows are cloned across years without an API floor. `Flow.apiVersion` is "the API version that defines the execution behavior of the flow", available in API version 50.0 and later; "flows created before API version 50.0 show an API version of 0 on the Flows list view in Setup" (`api_meta.txt` L68075–68082). `FlowVersionView` splits it in two: `ApiVersion` is the version at creation, while `ApiVersionRuntime` "determines which versioned run-time behavior improvements are adopted by the flow version. If not specified when the flow or flow version is created, the latest available API version is used" (`object_reference.txt` L144985–145008). These are different numbers and the second one is the one that runs.

**How to avoid:** Set `versions.min_api_version` in the policy and let the checker fail the build. Query §5(e) for the flows already below it, and note that an `ApiVersion` of 0 in Setup means the flow predates 50.0 entirely.

---

## The Save Order Does Not Rank Flows Within Its Own Steps

**What happens:** Two after-save flows on the same object both fire, one overwrites the other's field, and the behaviour flips between orgs or after an unrelated deploy.

**When it occurs:** As soon as a second record-triggered flow lands on an object. The Apex order of execution names "Executes record-triggered flows that are configured to run before the record is saved" as step 3 and "Executes record-triggered flows that are configured to run after the record is saved" as step 14 (`apexdev.txt` L15440, L15466) — single steps, with no ordering stated among multiple flows inside them. `triggerOrder` (int, "the run order of a record-triggered flow, from 1 to 2,000", API 54.0 and later, `api_meta.txt` L68438) is what supplies it, and it is nullable.

**How to avoid:** Make `triggerOrder` mandatory whenever two or more Active flows share an object plus `triggerType`, and give every one a distinct value — the checker enforces both. **UNVERIFIED (2026-09-05): what the platform does when two flows declare the *same* `triggerOrder` is not stated in `api_meta.txt`, `object_reference.txt` or `apexdev.txt`; the guide defers to "Guidelines for Defining the Run Order of Record-Triggered Flows for an Object" in Salesforce Help, which cannot be fetched.** Treat a tie as undefined and fix it rather than reasoning about it.

---

## Managed-Package Flows Are Outside The Manifest, So They Are Outside Every Check

**What happens:** The governance checker reports a clean portfolio while an installed package contributes several active record-triggered flows to the same objects.

**When it occurs:** Always, in any org with installed automation. "You can't use Metadata API to access a flow installed from a managed package unless the flow is a template" (`api_meta.txt` L68035). A `FlowDefinition`'s `masterLabel` "in managed packages… inherits the flow's active version name. To change this label from a subscriber's org, edit the packaged flow name" (L73944–73946).

**How to avoid:** Inventory them from SOQL rather than from source. `FlowDefinitionView` exposes `InstalledPackageName` (`object_reference.txt` L139372–139378), `NamespacePrefix` (L139454–139460) and `ManageableState` with values `installed`, `installedEditable`, `released`, `unmanaged` and others (L139437–139452). A tie-detection query that filters those out is measuring the wrong portfolio.

---

## Two `FlowSettings` Fields In The Guide's Own Sample Are Deprecated

**What happens:** A team copies the sample `Flow.settings` from the documentation, deploys it, and ships two fields that the current API version no longer honours — including one that used to be the org's Apex-access control for flows.

**When it occurs:** Whenever the guide's Declarative Metadata Sample Definition (`api_meta.txt` L117063–117081) is used as a starting point. `isAccessToInvokedApexRequired` — "indicates whether flows can invoke Apex classes only when the running users' profiles or permission sets include access to those Apex classes. When the value is `false`, Apex class security doesn't apply to flows" — is "available in API versions 47.0 to 58.0. The field is deprecated in API version 59.0 and later" (L116988–117001). `isFlowApexContextRetired` carries the same deprecation window (L117016–117024), and `enableFlowCustomPropertyEditor` was deprecated at 50.0 (L116870–116875).

**How to avoid:** Deploy the field list in `references/metadata-examples.md` §1, not the guide's sample; the checker ERRORs on all three. Governing who may run a flow that calls Apex is now the permission set's job — `classAccesses` alongside `flowAccesses`, plus `isAdditionalPermissionRequiredToRun` on the flow (`api_meta.txt` L68162).

---

## Spaces In A Flow File Name Fail At Deploy, Quietly Or Loudly

**What happens:** A deploy errors on a flow that opens fine in Flow Builder, or a flow name changes shape between the repo and the org.

**When it occurs:** When a flow file name carries spaces. "Spaces in a flow file name can lead to errors when you deploy the flow. You can include spaces at the beginning or end of a name, but these spaces are removed when you deploy the flow" (`api_meta.txt` L68036–68037). Separately, the `fullName` rules require "a unique name for the flow that contains only underscores and alphanumeric characters. The name must be unique across the org, begin with a letter, not include spaces, not end with an underscore, and not contain two consecutive underscores" (L68139–68147).

**How to avoid:** The naming regex in the policy file is not cosmetic — it is the only place those `fullName` rules are checked before a deploy attempt. Run the checker on the retrieved tree, not on what Flow Builder shows you.

---

## Editing Retrieved Process Builder Metadata Makes It Unopenable

**What happens:** A "governance cleanup" pass reformats or renames inside a retrieved process, it deploys, and the process can no longer be opened in the target org.

**When it occurs:** On flow components whose `processType` is `Workflow` or `InvocableProcess` — the two values Process Builder produces. The guide raises this as a Warning: "Don't edit the metadata of retrieved Process Builder processes… If you deploy process metadata that you edited, you can't open the process in the target org" (`api_meta.txt` L68044–68046).

**How to avoid:** Exclude `processType` `Workflow` and `InvocableProcess` from any bulk rename, reformat or description-backfill. Migrate them instead — `Flow.migratedFromWorkflowRuleName` records the origin, API 54.0 and later (`api_meta.txt` L68215–68217) — and route the decision through `standards/decision-trees/automation-selection.md`.
