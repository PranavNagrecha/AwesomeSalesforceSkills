# Gotchas — Path and Guidance

Non-obvious Salesforce platform behaviors that cause real production problems with Path configuration.

---

## Gotcha 1: The Org-Level Path Toggle Is Off After a Scratch Org or Deployment

**What happens:** Paths are created and activated, but the chevron bar never appears on any record page. Everything looks correct in Path Settings — paths are active, the component is on the Lightning page — but the UI shows nothing.

**When it occurs:** Most commonly after a scratch org is spun up from a package, after a sandbox refresh, or when metadata is deployed without the org preference. The individual path records deploy but the org-level "Enable Path" setting in Setup > Path Settings does not deploy as a metadata change in the same way.

**How to avoid:** Always verify the org-level Path toggle in Setup > Path Settings as the first debugging step when Path is missing. The mechanism is stated in the guide: "The preference does not need to be on to retrieve or deploy PathAssistant" (api_meta.txt L94498) — so the deploy reports success into an org where nothing will render. The toggle is deployable: `PathAssistantSettings.pathAssistantEnabled`, shipped as `settings/PathAssistant.settings-meta.xml` with manifest member `PathAssistant` under `<name>Settings</name>` (api_meta.txt L124206, L108368–108369). Include it in the package rather than enabling it by hand. See `references/metadata-examples.md` § 3 and Gotcha 11 for the edition-dependent default that makes this bite hardest in scratch orgs.

---

## Gotcha 2: Long Text Area and Encrypted Fields Cannot Be Key Fields

**What happens:** An admin tries to add a long text area field (e.g., Description, a custom rich-text area) as a key field for a stage. The field does not appear in the available field list in Path Settings. If the admin expects it to be there based on seeing it on the page layout, they may spend time searching for it.

**When it occurs:** Any time the designed key fields include long text area, encrypted, or certain relationship fields that Path does not support inline.

**How to avoid:** Before designing key fields, know the restriction: only short text, number, currency, percent, date, datetime, checkbox, email, phone, URL, and lookup (read-only display) fields are supported as key fields. UNVERIFIED (2026-09-05): the Metadata API guide describes `fieldNames` only as "All the fields in entityName that will display in this step" (api_meta.txt L94545) and states no type restriction, and the Developer Limits and Allocations Quick Reference contains no Path entry at all — this supported-type list comes from prior skill content, not from the extracted guides. Confirm the exact list against the field picker in Setup > Path Settings before you commit a design to it. Long text area fields, rich text area fields, encrypted fields, and formula fields are either excluded or read-only. Design the stage key field list around supported types, or accept that rich content belongs in the guidance text block rather than a key field.

---

## Gotcha 3: Missing Stages in Path Are a Sales Process Problem, Not a Path Problem

**What happens:** An admin expects a specific Stage picklist value (e.g., "Verbal Commit") to appear in the Path chevron bar but it is absent. The value exists in the global picklist, but Path does not show it.

**When it occurs:** When the Stage value is not included in the Sales Process assigned to the Opportunity record type. Path only renders stages that are in the underlying picklist value set available to the record type. If the Sales Process filters out a value, Path will not show it.

**How to avoid:** Before editing Path stages, verify the Sales Process assigned to the target record type (Setup > Sales Processes). In metadata the Sales Process is the `BusinessProcess` type, defined inside the object file, and `RecordType.businessProcess` binds it — a field the guide marks as required "in record types for lead, opportunity, solution, and case" (api_meta.txt L42969, L45006–45012). Confirm every expected stage value is in the business process `values` list and in the record type's `picklistValues` block for that field. If a stage is missing from Path, add it there first, then return to Path Settings. Verify with `SELECT Id, DeveloperName, BusinessProcessId FROM RecordType WHERE SobjectType = 'Opportunity'` — `BusinessProcessId` is required for Opportunity and Lead record types (object_reference.txt L244515–244521).

---

## Gotcha 4: Confetti Does Not Fire on Automation-Driven Stage Changes

**What happens:** A Flow or Process Builder advances the Stage picklist to "Closed Won" automatically (e.g., when a related contract is activated). Reps expected to see confetti but the animation never fires.

**When it occurs:** Any time the stage change that should trigger confetti is performed by automation (Flow, Process Builder, Apex, API) rather than by the user manually clicking through the Path component UI. UNVERIFIED (2026-09-05): celebration behaviour is a runtime UI behaviour and appears nowhere in the Metadata API guide, the Object Reference, or the limits cheat sheet — the only `enableConfettiEffect` in the Metadata API belongs to `TrailheadSettings` and governs the Guidance Center, not Path (api_meta.txt L127903–127906). What the guides *do* establish is Gotcha 8: no celebration element exists in `PathAssistant` at all.

**How to avoid:** Document clearly that confetti is a UI interaction reward, not an event-driven trigger. If reps will always advance the stage through automation, confetti is not achievable for that transition. If mixed (sometimes manual, sometimes automated), confetti fires only on the manual interactions. Consider managing expectations by noting this in the Path guidance text itself, or by having a separate Flow send a Chatter congratulations post when Stage = Closed Won, regardless of how the change happened.

---

## Gotcha 5: Path Metadata Deploys Without the Lightning Page Update

**What happens:** Path configurations are deployed to production (path records, key fields, guidance text), but the Path component was added to the Lightning page in the source org via Lightning App Builder and the Lightning page metadata was not included in the deployment. Production shows no Path component on the record page.

**When it occurs:** When the change set or package includes Path metadata but not the Lightning page metadata (`FlexiPage` type in the Metadata API). This is a common oversight in iterative deployments where the page was changed manually.

**How to avoid:** When deploying Path changes, always check whether the associated Lightning page (`FlexiPage` metadata) also needs to be included. The thing you are looking for inside that FlexiPage is `<componentName>runtime_sales_pathassistant:pathAssistant</componentName>` (api_meta.txt L67774) — grep the retrieved `.flexipage-meta.xml` for that exact string; if it is absent, the page will not show a Path no matter how the path itself is configured. If the Path component was added or repositioned in Lightning App Builder in the source org, retrieve and deploy the `FlexiPage` for that object's record page along with the path metadata. Verify in Lightning App Builder on production after deployment.

---

## Gotcha 6: Path Renders Incorrectly Inside Narrow Columns or Tabs

**What happens:** The Path component is placed inside a two-column layout or inside a tab on the record page. The chevron labels overlap, truncate aggressively, or the component renders as a collapsed bar with no visible stage names.

**When it occurs:** Any time the Path component is constrained to less than full page width, such as inside a 50%-width column, inside a sub-tab, or stacked with other components in a sidebar.

**How to avoid:** Always place the Path component in a full-width, one-column region at the top of the record Lightning page. The guide's own FlexiPage sample puts it in the region named `subheader` on a page built from the `flexipage:recordHomeWithSubheaderTemplateDesktop` template (api_meta.txt L67766–67779, L67993–67996) — that is the canonical placement, and a record page built on a template with no `subheader` region has nowhere correct to put it. UNVERIFIED (2026-09-05): the specific rendering degradation inside narrow columns is a UI observation; the extracted guides state the canonical region but not the failure mode. Avoid embedding Path inside tabs, accordions, or multi-column sections. If the page layout cannot accommodate a full-width header region, reconsider whether Path is the right component for this page.

---

## Gotcha 7: `entityName`, `fieldName`, and `recordTypeName` Are Not Updateable — Re-Pointing a Path Is a Delete

**What happens:** A path was built on `Opportunity` / `StageName` for the `Master` record type. The org introduces record types, and the admin edits the deployed `.pathAssistant-meta.xml` to change `recordTypeName` (or moves a custom object's path onto a different driver picklist). The deploy either fails or lands without effect, and the org keeps the old binding.

**When it occurs:** Any redesign that changes which object, which driver picklist field, or which record type a path serves. The Metadata API field table marks all three fields **not updateable**: `entityName` "This field is not updateable" (api_meta.txt L94515), `fieldName` "This field is not updateable" (api_meta.txt L94521), `recordTypeName` "This field is not updateable" (api_meta.txt L94529). Only `active`, `masterLabel`, and `pathAssistantSteps` can change in place.

**How to avoid:** Treat a change to those three fields as delete-and-recreate, not an edit. Plan it as: deploy the new `PathAssistant` under a new `fullName`, verify it renders, then remove the old one with a `destructiveChanges.xml` in a separate deploy. Because only one path can exist per record type per object (Gotcha 9), the two cannot both target the same record type at once — sequence the destructive step first for the same record type, or stage the change through a sandbox where the outage is acceptable.

---

## Gotcha 8: Celebration Configuration Has No Metadata Representation and Does Not Deploy

**What happens:** A path with confetti configured in a sandbox is retrieved, reviewed, and deployed to production. The steps, key fields, and guidance all arrive. The celebration does not. Nobody notices until a rep closes a deal in production and nothing happens.

**When it occurs:** Every promotion of a path between orgs. The `PathAssistant` field table is exactly `active`, `entityName`, `fieldName`, `masterLabel`, `pathAssistantSteps`, `recordTypeName`, and `PathAssistantStep` is exactly `fieldNames`, `info`, `picklistValueName` (api_meta.txt L94510–94529, L94545–94549). There is no celebration, animation, or confetti element in either table. The only `enableConfettiEffect` field in the whole Metadata API belongs to `TrailheadSettings` and governs Guidance Center milestones, an unrelated feature (api_meta.txt L127903–127906).

**How to avoid:** Put celebration re-enablement on the manual post-deploy checklist for every org, alongside anything else that lives outside source control. Record which step carries it in the deploy notes and in `templates/path-and-guidance-template.md`, because a source-format diff will never show you that it went missing. Do not write CI assertions against celebration state — there is nothing in the retrieved metadata to assert on.

---

## Gotcha 9: One Path Per Record Type Per Object — Including `__Master__`

**What happens:** An admin plans two active paths on the same object and record type — one driven by `StageName`, another by a custom `Fulfilment_Stage__c`, or two paths differentiated by user group. The second one cannot be created, or the deploy of the second overwrites expectations set by the first.

**When it occurs:** Any design that tries to differentiate paths by something other than record type. The guide is unambiguous: "Only one path can be created per record type for each object, including `__Master__` record type" (api_meta.txt L94496). The constraint is on the object + record type pair, **not** on the driver picklist field — two paths on the same record type using different fields is not a supported escape hatch, and neither is differentiation by profile or permission set.

**How to avoid:** Record type is the only differentiator available. If two audiences need genuinely different key fields or guidance on the same records, the choices are: introduce a record type that reflects the real business distinction, accept one path written for the broadest audience, or move the audience-specific content to In-App Guidance (`admin/in-app-guidance-and-walkthroughs`), which does target by profile. When an org has record types, count them — an object with eight record types needs up to eight `.pathAssistant-meta.xml` files, each a separate maintenance surface.

---

## Gotcha 10: The Path Renders Collapsed on Every Page Load Unless You Ship the Override

**What happens:** The path deploys, activates, and renders — as a bare chevron bar. The key fields and the guidance text the team spent two workshops writing are hidden behind a click, on every record, every page load. Adoption metrics show the guidance is never read, and the conclusion drawn is "users ignore Path".

**When it occurs:** In any org that has not set `canOverrideAutoPathCollapseWithUserPref`. The guide states the default and the consequence: "Default value is false for all editions. When set to false, the user's path is collapsed when the page loads" (api_meta.txt L124216–124221). Setting it to `true` "keeps a user's path expanded to show guidance and key fields on all their records" until the user collapses it themselves. The field is API 47.0 and later.

**How to avoid:** Ship `<canOverrideAutoPathCollapseWithUserPref>true</canOverrideAutoPathCollapseWithUserPref>` in `settings/PathAssistant.settings-meta.xml` alongside the path itself, not as a follow-up. For the single-user variant of the same complaint, the state is a per-user field: `SELECT Id, Username, UserPreferencesPathAssistantCollapsed FROM User` — "When true, Sales Path appears collapsed or hidden to the user", available API 35.0 and later (object_reference.txt L296509–296515). Against API 33.0–34.0 the field was `UserPreferencesProcessAssistantCollapsed`; in 35.0+ that one is superseded (object_reference.txt L296517–296524). Check the user's own preference before re-debugging the configuration.

---

## Gotcha 11: The Path Preference Defaults to Off in Every Edition Except Enterprise

**What happens:** A path validated in a full sandbox is deployed into a Developer Edition scratch org, a trial org, or a Professional Edition org for a demo. Nothing renders. The path is active, the FlexiPage has the component, the steps are correct — and the org toggle was never on.

**When it occurs:** Whenever the target org is not Enterprise Edition. `pathAssistantEnabled` "Determines whether the preference is enabled for Path. Default value is `true` for Enterprise Edition and `false` for other editions" (api_meta.txt L124222–124224). Combined with "The preference does not need to be on to retrieve or deploy PathAssistant" (api_meta.txt L94498), the deploy is green and the feature is invisible — the two facts compound into a failure with no error message anywhere.

**How to avoid:** Always include `Settings:PathAssistant` in the deploy manifest with `pathAssistantEnabled` explicitly `true`, so the preference is asserted rather than inherited from an edition default. In scratch org definition files, treat Path as a feature that must be turned on rather than one that comes on. Do not use "it worked in the sandbox" as evidence — sandboxes inherit the production edition, so an EE sandbox will never reproduce this. Ignore `pathAssistantForOpportunityEnabled`; it is API 34.0 **and earlier** (api_meta.txt L124226–124228).

---

## Gotcha 12: A Step Omitted From the XML Is "Not Configured", Not Deleted

**What happens:** An admin retrieves a path, hand-edits it to remove the two steps they wanted to strip guidance from, and deploys. The chevrons for those two stages are still there. The guidance is gone. Nobody removed a stage; someone removed the *configuration* of a stage, and the chevron bar now has silent holes in it.

**When it occurs:** Any partial edit or partial retrieve of `pathAssistantSteps`. The guide states it directly: "Note that a missing step in the .xml file means it has not been configured, not that it doesn't exist" (api_meta.txt L94525–94526). The chevrons come from the picklist values available to the record type, not from the file. The file only supplies `fieldNames` and `info`.

**How to avoid:** Read a `.pathAssistant-meta.xml` as a sparse overlay on the record type's picklist values, never as the list of stages. To remove a stage from the bar, remove the value from the record type's `picklistValues` (or deactivate it in the value set) — editing the path cannot do it. To audit for holes, diff the `picklistValueName` set in the file against `SELECT ApiName, IsActive FROM OpportunityStage ORDER BY SortOrder`; the checker in `scripts/check_path_and_guidance.py` does exactly this comparison against the manifest.

---

## Gotcha 13: A Stage Deployed via StandardValueSet Does Not Reach the Record Type by Itself

**What happens:** A new stage is added to `OpportunityStage` and deployed. The value exists — it is visible in the value set in Setup, and the deploy succeeded. A Path step is configured for it. It never appears in the chevron bar for any user.

**When it occurs:** Whenever a picklist value arrives through the Metadata API rather than through the record type UI. The `StandardValueSet` note is explicit: "When setting `standardValue` on Record Types, including person account record types, new picklist values loaded into your organization through the Metadata API don't display in the picklist UI by default. For users to see the new values, go to the Record Types list for the object containing the picklist field, click Edit, and add the new value to the Selected Fields list" (api_meta.txt L130774–130779).

**How to avoid:** Deploy the record type's `picklistValues` block in the same change as the value set, so the value is both defined and selected — see `references/metadata-examples.md` § 1, where the same five values appear in both the business process and the record type. Then verify from the record side, not the value-set side: `SELECT ApiName, MasterLabel, IsActive FROM OpportunityStage ORDER BY SortOrder` shows what exists, but only the record type's selected list decides what a user of that record type can pick — and therefore what the Path can render.
