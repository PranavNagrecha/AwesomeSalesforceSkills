# Acceptance Criteria — Northwind Enterprise sales process

Compiled by `agents/build-doc-keeper`'s `M4-S03` compile run. Given/When/Then shape: `skills/admin/acceptance-criteria-given-when-then/references/worked-examples.md` §§ 1, 3 and 5. **This build has no story backlog** (no `story-drafter` step in `plan.json`), so no criterion carries a story id. The criteria come from three sources, and none of them is new:

1. **Milestone goals** (`plan.json` `milestones[].goal`), split on their own Then clauses: 17 criteria.
2. **Manual acceptance tests** on every step and milestone (`acceptance_tests[]` where `type` is `manual`), split on their own Given/when/then wording: 48 criteria (41 at the first compile, the five `plan.json steps[M4-S04].amendments[0]` added, and the two that `amendments[2]` (2026-10-02T19:17:05Z) split out of compound tests). 1 of them fails the outcome rule and is listed separately below, outside the lintable record.
3. **Open items in `decisions.md`** whose close condition is a human check and which no criterion above already states: 22 criteria, worded from the entry's own remedy text and from values the workbook rows record (error messages, field names). Each one names its entry.

Ids follow § 1: `AC-<requirement number>.<n>`, numbered within each requirement in the order above. The five criteria the incremental re-run added (AC-004.3, AC-010.3, AC-016.3, AC-017.2, AC-018.2) take the next free number in their requirement rather than their source-order position, so no existing id moves. The final re-run follows the same rule: AC-017.3 and AC-018.3 are the halves `plan.json steps[M4-S04].amendments[2]` (2026-10-02T19:17:05Z) split out of the two compound tests, while AC-017.2 and AC-018.2 keep their ids on the negative halves; AC-004.4, AC-024.5 and AC-024.6 come from M4-S04's open items. Some criteria serve no single requirement (the documents, the deploy deny-list, the nine prerequisites). Each of these is keyed by the rule printed beside it, and the requirements it spans are listed.

Lint: `python3 skills/admin/acceptance-criteria-given-when-then/scripts/check_ac_format.py --manifest-dir artefacts/M4-S03` (from the build directory).

## Background (shared by every criterion)

- **Sandbox: UNVERIFIED (2026-10-02).** No UAT sandbox or target org is named anywhere in `plan.json`. The build is design-only, and its org evidence comes from checkOnly runs against alias `sfskills-dev` (`reports/MOCK-DEPLOY-M1.md` to `-M4.md`), which is not a UAT environment.
- **P-REP:** an Enterprise rep. Profile `Sales User` with the org's Sales Cloud permission set (Q19; the set's name is not on file), plus the `Enterprise_Sales_Record_Types` permission set (M2-S02). Role Enterprise Rep. Does not hold `Sales_Ops_Validation_Bypass`.
- **P-MGR:** an Enterprise manager. As P-REP, with role Enterprise Manager (above Enterprise Rep, Q19), and a member of the `Enterprise_Managers` public group once the sales-ops admin adds them (A32).
- **P-OPS:** the sales-ops admin, holding the `Sales_Ops_Validation_Bypass` permission set. Q19 records this seat's profile as the org's administrator profile. Every criterion that runs as P-OPS is paired with a P-REP control, so a pass can be attributed to the custom permission and not to the profile.
- **Build reviewer:** for criteria whose oracle is a build file read at a milestone gate. Uses no Salesforce seat.
- Opportunity's org-wide default is not on file. Q4 implies it is public; decisions.md O-M4S02-06 asks for it to be confirmed.

## Criteria by requirement

### REQ-001 — The eight Enterprise and Renewal stage values exist as active `OpportunityStage` picklist values, each carrying the probability and forecast category the VP Sales Ops signed off on, without deactivating any stage the SMB team's generic pipeline already runs on (`requirement.md` item 6)

- **AC-001.1** - milestone goal, `plan.json milestones[M1].goal`.
  *Given* an org where every Opportunity sits on one generic pipeline; *when* the M1 artefacts are deployed; *then* the eight new stage values carry the probabilities and forecast buckets the VP signed off.
- **AC-001.2** - milestone goal, `plan.json milestones[M4].goal` — keyed: names no requirement; keyed by the fallback rule to the lowest-numbered requirement the compiled documents cover.
  *Given* the build works; *when* the M4 artefacts are deployed; *then* the sales-ops admin holds one workbook, one traceability matrix, one UAT pack, one manifest and one runbook that together name every prerequisite, every assumption and every step that shipped nothing.
- **AC-001.3** - manual acceptance test, `plan.json steps[M1-S01].acceptance_tests[5]`.
  *Given* D1 and assumption A24; *when* artefacts/M1-S01/deploy-order.md is read; *then* its first instruction is to run sf project retrieve start --metadata StandardValueSet:OpportunityStage against the target org and merge the retrieved active values into the shipped file, and it states in the same paragraph that a partial file deactivates every value it omits - including the SMB team's stages.
- **AC-001.4** (negative) - manual acceptance test, `plan.json steps[M1-S01].acceptance_tests[6]`.
  *Given* Q5 and Q6; *when* the eight standardValue blocks are read; *then* Qualify/Discover/Propose/Negotiate carry 10/25/50/75 and Pipeline/Pipeline/BestCase/Forecast, Renewal Review and Renewal Proposed carry 60/85 and Pipeline/Forecast, Closed Won carries 100 with won and closed true, Closed Lost carries 0 with forecastCategory Omitted - and the word 'Commit' appears nowhere in the file.
- **AC-001.5** - manual acceptance test, `plan.json steps[M4-S03].acceptance_tests[4]` — keyed: names no single requirement; keyed to the requirement of the first prerequisite its own text names (A24, the OpportunityStage union, constrains M1-S01 / REQ-001).
  *Given* 30 informational clarifications were left unanswered at G1 and eleven org facts nobody supplied; *when* the workbook's assumptions section is read; *then* all 43 assumption rows appear with a named owner who can close each one and the step ids each constrains, and the three rows carrying risk high - which are exactly the three pre-deploy prerequisites: A24 the OpportunityStage union, A28 the report column codes and A29 the dashboard runningUser - are called out rather than buried in the list.
- **AC-001.6** (negative) - manual acceptance test, `plan.json steps[M4-S04].acceptance_tests[3]` — keyed: names no requirement at all; keyed by the fallback rule to the lowest-numbered requirement in the build-level manifest the runbook governs.
  *Given* section 5's deploy deny-list and this layer's rule that it never deploys; *when* artefacts/M4-S04/deploy-order.md is read; *then* it contains no sf project deploy start without --dry-run anywhere, and the only org-facing command it offers is scripts/mock_deploy.py <plan.json> --org-alias <alias> --milestone <id>, which a release owner may choose to run.
- **AC-001.7** - manual acceptance test, `plan.json steps[M4-S04].acceptance_tests[5]` — keyed: spans nine prerequisites; keyed to the requirement of the first one its text names (retrieve and merge OpportunityStage, REQ-001).
  *Given* Q8, Q17, Q25, Q26 and the eight assumptions this step carries; *when* the cutover runbook section is read; *then* each of the nine post-deploy or pre-deploy prerequisites has a named owner and an ordered position - retrieve and merge OpportunityStage, discover the layout-required fields, retrieve the products related-list name, confirm the report column codes, set the dashboard runningUser, populate the Enterprise Managers group, set approval process order, reassign the 140 open Enterprise deals, and record every bypass use in Chatter.
- **AC-001.8** - manual acceptance test, `plan.json milestones[M1].acceptance_tests[2]`.
  *Given* assumption A24 at risk high; *when* the M1 gate is reached; *then* a named owner confirms the OpportunityStage file about to be deployed is the union of the org's currently active stage values and the eight new ones - because a partial file deactivates every value it omits, which is the single way this milestone could break the SMB pipeline it is designed to leave alone.
- **AC-001.9** - manual acceptance test, `plan.json milestones[M4].acceptance_tests[3]` — also serves REQ-025, REQ-026; keyed: spans nine prerequisites; keyed to the requirement of the first of the three blocking ones its text names (the OpportunityStage union, REQ-001).
  *Given* the nine pre-deploy and post-deploy prerequisites this plan discovered; *when* the M4 gate is reached; *then* each has a named owner in the cutover runbook and the three that would silently produce a wrong result if skipped - the OpportunityStage union, the report column codes and the dashboard runningUser - are marked as blocking the deploy rather than as follow-ups.
- **AC-001.10** - open item, `decisions.md O-M1S01-02` — keyed: assumption A4 constrains M1-S01; keyed to its first requirement (REQ-001, the stage values whose movement Q39 asks to measure).
  *Given* Q39 is still open and assumption A4 relies on OpportunitySettings.enableOpportunityFieldHistoryTracking defaulting to true, with no OpportunitySettings file shipped anywhere in this build; *when* the target org's Opportunity settings are read before go-live; *then* Opportunity field history tracking is on, so stage movement can be measured from day one - Opportunity field history cannot be backfilled.

### REQ-002 — The Enterprise motion runs its own six-stage sequence (Qualify, Discover, Propose, Negotiate, Closed Won, Closed Lost), separate from Renewal and from the SMB team's generic process

- **AC-002.1** (negative) - milestone goal, `plan.json milestones[M1].goal` — also serves REQ-001, REQ-014.
  *Given* an org where every Opportunity sits on one generic pipeline; *when* the M1 artefacts are deployed; *then* the SMB team's record type, stages, list views and report are untouched.
- **AC-002.2** (negative) - manual acceptance test, `plan.json milestones[M1].acceptance_tests[3]` — also serves REQ-001, REQ-014.
  *Given* requirement.md item 6 and Q9; *when* the whole M1 artefact tree is listed; *then* no file anywhere names the SMB record type, either SMB list view, or the SMB pipeline report - the milestone is additive by construction rather than by promise.
- **AC-002.3** - open item, `decisions.md O-M1S01-04` — also serves REQ-003.
  *Given* neither BusinessProcess carries a default stage after the N3-F-01 repair (D-M1S01-05), and no cited skill documents a per-process default-stage mechanism for Opportunity; *when* a new Enterprise and a new Renewal Opportunity are created after deploy and the post-deploy SOQL in artefacts/M1-S01/deploy-order.md section 4 is run; *then* the stage each record opens on is read from the query and is a member of its own process's stage set (Enterprise: Qualify, Discover, Propose, Negotiate, Closed Won, Closed Lost; Renewal: Renewal Review, Renewal Proposed, Closed Won, Closed Lost).

### REQ-004 — Enterprise deals are identifiable and driven by their own Sales Process through a dedicated record type

- **AC-004.1** - milestone goal, `plan.json milestones[M1].goal` — also serves REQ-005, REQ-002, REQ-003.
  *Given* an org where every Opportunity sits on one generic pipeline; *when* the M1 artefacts are deployed; *then* two record types exist with their own Sales Processes and stage sets.
- **AC-004.2** - manual acceptance test, `plan.json milestones[M4].acceptance_tests[4]`.
  *Given* Q8; *when* the cutover runbook is read; *then* the reassignment of about 140 open Enterprise deals to the Enterprise record type is an ordered step with an owner and a stated position relative to the deploy, and it is described as a one-time data update rather than as a migration - which is what requirement.md item 6 rules out.
- **AC-004.3** (negative) - manual acceptance test, `plan.json steps[M4-S04].acceptance_tests[7]`.
  *Given* a user holding neither Enterprise_Sales_Record_Types nor a profile grant for the new types; *when* they create an Opportunity after deploy; *then* neither Enterprise nor Renewal is offered on the New dialog and the SMB default is unchanged - a UAT step, recorded in the runbook's post-deploy checks.
  Source note: added by `plan.json steps[M4-S04].amendments[0]` (2026-10-02T18:52:18Z); moved to UAT after the first deploy, not the M4 gate, by `amendments[2]` (2026-10-02T19:17:05Z).
- **AC-004.4** (negative) - open item, `decisions.md O-M4S04-02, O-M4S04-06` — also serves REQ-019.
  *Given* none of the generic pipeline's open stages exists in Enterprise_Sales_Process, values missing from the new record type are cleared on a record-type change (admin/record-types-and-page-layouts Gotcha 1), and mapping them fires M2-S04's product gate on about twenty product-less deals (Q16); *when* the VP and the Sales Operations lead settle the stage mapping before P-8 and the one-time update reassigns the roughly 140 open deals Q8 names to the Enterprise record type; *then* every reassigned deal carries a mapped Enterprise stage rather than a cleared one, the count the runbook's SOQL returned is recorded beside the mapping, and every save that passed the product gate through the bypass carries a Chatter post on the record (Q17).

### REQ-006 — The rep-entered overall deal discount lives as a header field on the Opportunity, not on line items, ready for the 20% discount-cap rule and the manager-approval process later milestones add

- **AC-006.1** - milestone goal, `plan.json milestones[M1].goal` — also serves REQ-007.
  *Given* an org where every Opportunity sits on one generic pipeline; *when* the M1 artefacts are deployed; *then* Discount__c and Approval_Status__c exist on Opportunity.

### REQ-008 — The Enterprise Opportunity record type has its own page layout carrying the standard fields Q20 names (`Name`, `AccountId`, `StageName`, `CloseDate`, `Amount`), the discount amount editable, and the approval outcome visible but not rep-editable

- **AC-008.1** - milestone goal, `plan.json milestones[M1].goal` — also serves REQ-009.
  *Given* an org where every Opportunity sits on one generic pipeline; *when* the M1 artefacts are deployed; *then* each record type has a layout carrying both.
- **AC-008.2** (negative) - manual acceptance test, `plan.json steps[M1-S02].acceptance_tests[4]` — also serves REQ-009.
  *Given* assumption A25; *when* both layout files are read; *then* each carries Name, AccountId, StageName, CloseDate and Amount, plus Discount__c editable and Approval_Status__c read-only, and deploy-order.md records that the platform's layout-required set for Opportunity is unverified and is discovered by iterating scripts/mock_deploy.py --dry-run, one field per run.

### REQ-010 — Reps can add product lines from the Standard Price Book to an Enterprise opportunity via the Opportunity Products related list, present on the layout

- **AC-010.1** - manual acceptance test, `plan.json steps[M1-S02].acceptance_tests[3]`.
  *Given* assumption A26; *when* artefacts/M1-S02/deploy-order.md is read; *then* it names the exact sf project retrieve start --metadata "Layout:Opportunity-Opportunity Layout" command, says to copy the Opportunity Products relatedLists block verbatim from what the retrieve emits, and states that hand-authoring the related-list name is what the instruction exists to prevent.
- **AC-010.2** (negative) - open item, `decisions.md O-M1S02-01`.
  *Given* the Opportunity Products relatedLists element has been retrieved from the target org's Opportunity Layout and pasted verbatim into both layouts before deploy (O-M1S02-01, assumption A26); *when* a rep opens an Enterprise opportunity and adds a product line from the Standard Price Book; *then* the Opportunity Products related list is on the page and the product line saves, and the relatedLists element in each shipped layout diffs empty against the retrieved file - no hand-typed related-list name.
- **AC-010.3** - manual acceptance test, `plan.json steps[M4-S04].acceptance_tests[6]`.
  *Given* assumption A26 (REQ-010: the Opportunity Products related list is retrieved from the org's current Opportunity layout and copied into both Enterprise and Renewal layouts, never hand-authored); *when* deploy-order.md's cutover runbook is read; *then* it carries that retrieve-and-copy as a pre-deploy step with a named owner before the Layout deploy, and the M4 gate records REQ-010 as covered by this runbook step rather than by metadata - the related list has had no artefact and no test since M1.
  Source note: added by `plan.json steps[M4-S04].amendments[0]` (2026-10-02T18:52:18Z).

### REQ-012 — The `Sales_Ops_Validation_Bypass` permission set grants the bypass to the sales-ops admin, and carries no other access

- **AC-012.1** (negative) - milestone goal, `plan.json milestones[M2].goal` — also serves REQ-011, REQ-015.
  *Given* the M1 data model is accepted; *when* the M2 artefacts are deployed; *then* the sales-ops admin is the only person who can save past that rule.
- **AC-012.2** (negative) - manual acceptance test, `plan.json steps[M2-S01].acceptance_tests[4]`.
  *Given* Q13 and Q17; *when* artefacts/M2-S01/permissionsets/Sales_Ops_Validation_Bypass.permissionset-meta.xml is read; *then* it grants exactly one custom permission, carries no objectPermissions, no fieldPermissions and no userPermissions, and its description names the sales-ops admin as the only intended holder - so approving this gate is approving one bypass and nothing else.
- **AC-012.3** - manual acceptance test, `plan.json milestones[M2].acceptance_tests[5]` — also serves REQ-013.
  *Given* both M2 access steps carry their own step gate; *when* the M2 gate is reached; *then* the person approving it can name every person who gains the bypass permission (the sales-ops admin, and nobody else) and every person who gains the two record types (the 12 reps, the 2 managers and the sales-ops admin).

### REQ-013 — The Enterprise and Renewal Opportunity record types are visible to the Sales User persona (14 reps and managers), closing the selectability gap `decisions.md` O-M1S01-03 named at the M1 gate

- **AC-013.1** - milestone goal, `plan.json milestones[M2].goal` — also serves REQ-014.
  *Given* the M1 data model is accepted; *when* the M2 artefacts are deployed; *then* the 12 reps and 2 managers can select both new record types and get the right layout.
- **AC-013.2** (negative) - manual acceptance test, `plan.json steps[M2-S02].acceptance_tests[5]`.
  *Given* Q19; *when* the two files are read together; *then* reps and managers reach both record types through the permission set while the sales-ops admin (System Administrator) needs no row in either file, and the manager-versus-rep distinction appears nowhere in this step - it is a role-hierarchy fact, which is what decision D7 records.

### REQ-014 — The Sales User profile overlay assigns each record type its `M1-S02` page layout, and leaves the org's existing default Opportunity record type and its layout untouched

- **AC-014.1** (negative) - manual acceptance test, `plan.json steps[M2-S02].acceptance_tests[4]`.
  *Given* Q4 and Q9; *when* artefacts/M2-S02/profiles/Sales User.profile-meta.xml is read; *then* it contains exactly two layoutAssignments blocks, one per new record type, and no recordTypeVisibilities block at all - visibility for Enterprise and Renewal is granted by the Enterprise_Sales_Record_Types permission set, because a profile block that lists visible types must name a default and naming one would move the SMB team's default (org finding N3-F-05, MOCK-DEPLOY-M2 run 1) - and it carries no userPermissions, objectPermissions, fieldPermissions, applicationVisibilities or classAccesses, so deploying it changes nothing for the SMB team except that the two new record types have their layouts.
- **AC-014.2** - open item, `decisions.md O-M2S02-03`.
  *Given* the Profile member and file stem are written Sales User, with its space, on Q19's phrase alone (UNVERIFIED (2026-09-19) in artefacts/M2-S02/deploy-order.md); *when* the target org's profiles are listed before deploy; *then* a profile whose Name is exactly Sales User exists, or the file stem and package member are corrected before deploy - a mismatch is an INVALID_CROSS_REFERENCE_KEY on the profile half only.

### REQ-015 — A discount above 20% on an Enterprise or Renewal Opportunity cannot be saved to Closed Won without manager approval, except by the sales-ops-admin bypass

- **AC-015.1** (negative) - milestone goal, `plan.json milestones[M2].goal`.
  *Given* the M1 data model is accepted; *when* the M2 artefacts are deployed; *then* an Enterprise or Renewal deal above a 20% discount cannot be set to Closed Won without an approved approval.
- **AC-015.2** (negative) - manual acceptance test, `plan.json steps[M2-S03].acceptance_tests[3]`.
  *Given* D8 and assumption A35; *when* the errorConditionFormula is read; *then* the discount comparison is 'Discount__c > 0.20' and not '> 20', the bypass clause NOT($Permission.Bypass_Opportunity_Sales_Validation) is the first argument of the outer AND, and the record-type gate compares RecordType.DeveloperName with = rather than ISPICKVAL.
- **AC-015.3** - manual acceptance test, `plan.json steps[M2-S03].acceptance_tests[4]`.
  *Given* Q15; *when* errorMessage is read; *then* it is Q15's sentence verbatim, is 255 characters or fewer, and errorDisplayField is Discount__c so the error lands on the field the rep has to change rather than at the top of the page.
- **AC-015.4** (negative) - open item, `decisions.md O-M2S03-02`.
  *Given* assumption A8 assumes no legacy automation writes StageName, Amount, Discount__c or Approval_Status__c after save, and a custom validation rule does not re-run after a workflow field update re-saves the record; *when* the target org's workflow rules and other automation on Opportunity are listed before go-live; *then* no pre-existing automation on Opportunity writes StageName, Amount, Discount__c or Approval_Status__c after save; any that does is recorded as a gap against the discount cap before go-live.
- **AC-015.5** (negative) - open item, `decisions.md O-M2S03-03` — also serves REQ-021.
  *Given* the discount cap ships active, the approval process is the only non-bypass path to satisfy it, and G4 decided that M3-S02 deploys in the same release as M2-S03; *when* the release's deploy order and manifest are read before go-live; *then* Opportunity_Discount_Requires_Approval is not deployed to the target org ahead of Opportunity.Discount_Approval - both are in the same release.

### REQ-016 — The Enterprise Opportunity Path carries the correct key fields and exit-criteria guidance at every stage the Enterprise motion uses

- **AC-016.1** - milestone goal, `plan.json milestones[M2].goal` — also serves REQ-017.
  *Given* the M1 data model is accepted; *when* the M2 artefacts are deployed; *then* reps see a stage path carrying the exit criteria and key fields for each stage.
- **AC-016.2** - manual acceptance test, `plan.json steps[M2-S05].acceptance_tests[4]`.
  *Given* Q2 and Q11; *when* the Enterprise path's four pathAssistantSteps are read; *then* the Discover step's info text names 'at least one product line added from the price book' and a booked Next Step, the Propose step's info text names a primary contact with the Decision Maker contact role, and the Negotiate step's key fields are Discount__c, Approval_Status__c and CloseDate - so every exit criterion the requester dictated is visible to a rep even though M2-S04 cannot enforce the product one.
- **AC-016.3** (negative) - manual acceptance test, `plan.json steps[M4-S04].acceptance_tests[8]`.
  *Given* an Opportunity of the SMB record type; *when* its record page is opened after deploy; *then* the Enterprise Path's stages and key fields do not render for it - the Path is bound to the Enterprise record type only.
  Source note: added by `plan.json steps[M4-S04].amendments[0]` (2026-10-02T18:52:18Z); moved to UAT after the first deploy, not the M4 gate, by `amendments[2]` (2026-10-02T19:17:05Z).

### REQ-017 — The Renewal Opportunity Path carries the correct key fields and exit-criteria guidance at every stage the Renewal motion uses

- **AC-017.1** - open item, `decisions.md O-M2S05-04, O-M3S05-03 (operator entry, line 1375), O-M3S05-04 (renderer entry, line 1408)`.
  *Given* M3-S05 builds the Enterprise record page only, and the org default it writes is not record-type-scoped (ActionOverride on CustomObject has no recordType field); *when* the org's existing FlexiPages are retrieved and searched for the Path component before deploy, and a rep opens a Renewal opportunity after deploy; *then* the page the Renewal opportunity resolves to carries runtime_sales_pathassistant:pathAssistant and shows the Renewal path (Renewal Review, Renewal Proposed).
- **AC-017.2** (negative) - manual acceptance test, `plan.json steps[M4-S04].acceptance_tests[9]`.
  *Given* an Opportunity of the Enterprise record type; *when* its record page is opened after deploy; *then* the Renewal Path's two stages do not render for it - the Renewal Path is bound to the Renewal record type only.
  Source note: added by `plan.json steps[M4-S04].amendments[0]` (2026-10-02T18:52:18Z); split, and moved to UAT after the first deploy, by `amendments[2]` (2026-10-02T19:17:05Z). The former second clause is AC-017.3; this id keeps the negative half.
- **AC-017.3** - manual acceptance test, `plan.json steps[M4-S04].acceptance_tests[10]`.
  *Given* the Renewal record type falls through to the org's existing Opportunity record page (O-M2S05-04); *when* the cutover runbook is read; *then* it carries the retrieve-and-grep of that page for runtime_sales_pathassistant:pathAssistant as a pre-deploy step with a named owner, and names the decision if the component is absent (add it to that page, or accept that the Renewal Path does not render).
  Source note: split out of the former compound test 10 by `amendments[2]` (2026-10-02T19:17:05Z).

### REQ-018 — Path is explicitly enabled in the org preference (not left to the Enterprise Edition default) and the auto-collapse override is available, so a scratch org or Developer Edition rehearsal is not silently Path-off

- **AC-018.1** - manual acceptance test, `plan.json steps[M2-S05].acceptance_tests[5]` — also serves REQ-016, REQ-017.
  *Given* admin/path-and-guidance's rule that a path is not evidence the feature is on; *when* artefacts/M2-S05/deploy-order.md is read; *then* it states that a green PathAssistant deploy proves neither that Path is enabled nor that the component is on the record page, and points at M3-S05 as the step that puts it there.
- **AC-018.2** (negative) - manual acceptance test, `plan.json steps[M4-S04].acceptance_tests[11]`.
  *Given* the PathAssistant org setting is deployed with the user-preference override enabled (artefacts/M2-S05/settings/PathAssistant.settings-meta.xml, canOverrideAutoPathCollapseWithUserPref true); *when* a user collapses the Path and reopens the record; *then* it stays collapsed for that user and expanded for others.
  Source note: added by `plan.json steps[M4-S04].amendments[0]` (2026-10-02T18:52:18Z); split, and moved to UAT after the first deploy, by `amendments[2]` (2026-10-02T19:17:05Z), which also states the override value the compound text left open. The former rehearsal clause is AC-018.3; this id keeps the negative half.
- **AC-018.3** - manual acceptance test, `plan.json steps[M4-S04].acceptance_tests[12]`.
  *Given* a scratch-org or sandbox rehearsal is part of the cutover runbook; *when* the runbook is read; *then* it states that the PathAssistant setting member deploys with M2-S05 and that a rehearsal without it shows neither Path - the setting is load-bearing, not a default.
  Source note: split out of the former compound test 11 by `amendments[2]` (2026-10-02T19:17:05Z).

### REQ-019 — An Enterprise Opportunity with no product lines cannot advance into Propose, Negotiate or Closed Won, except through the sales-ops-admin bypass (`requirement.md` item 2 / Q11's product-gate half — Q11's separate "and Next Step" half is carried by no step in this build)

- **AC-019.1** - manual acceptance test, `plan.json steps[M2-S04].acceptance_tests[3]`.
  *Given* the two claims the step note carried as UNVERIFIED (2026-09-15) - formula-context availability of HasOpportunityLineItem, and the official-source conflict on re-firing after a line-item deletion; *when* artefacts/M2-S04/deploy-order.md is read at the M2 gate; *then* section 2.1 records the first as org-verified by MOCK-DEPLOY-M2 run 1 (2026-09-19, the formula compiled under checkOnly), and section 2.2 records the second as still unverified with 'forward gate only' stated, because a checkOnly deploy exercises no deletion.
- **AC-019.2** - manual acceptance test, `plan.json steps[M4-S03].acceptance_tests[5]`.
  *Given* M2-S04 ships nothing in this release; *when* traceability.md is read; *then* its row for the product-before-Propose requirement names M2-S04 with its blocked_reason verbatim rather than being silently absent, and the workbook's Validation Rules section carries the same row rather than only the rule that did ship.
  Source note: corrected after G5 by the prose-only amendment `plan.json steps[M4-S03].amendments[1]` (2026-10-02T18:52:43Z), which appends: M2-S04 was unblocked on 2026-09-15 and shipped Opportunity.Opportunity_Products_Required_At_Propose as an org-validated rule (MOCK-DEPLOY-M2 run 3); read every clause that assumes a blocked or empty M2-S04 as satisfied by that rule's presence - the exclusion it describes does not apply.
- **AC-019.3** - manual acceptance test, `plan.json steps[M4-S04].acceptance_tests[4]`.
  *Given* M2-S04 was unblocked on 2026-09-15 and shipped Opportunity.Opportunity_Products_Required_At_Propose as an org-validated rule (MOCK-DEPLOY-M2 run 3); *when* package.xml and deploy-order.md are read together; *then* that rule appears exactly once as a ValidationRule member with its file behind it, and deploy-order.md lists it in the validation-rule position after M2-S01's custom permission.
  Source note: reworded after G5 by `plan.json steps[M4-S04].amendments[0]` (2026-10-02T18:52:18Z): the original text assumed a blocked step and would have dropped a shipped rule from the manifest. No longer a negative criterion.
- **AC-019.4** - manual acceptance test, `plan.json milestones[M2].acceptance_tests[4]`.
  *Given* M2-S04 was unblocked on 2026-09-15 and shipped the product-before-Propose gate as a validation rule (not as Path guidance); *when* the M2 gate is reached; *then* the approver has read artefacts/M2-S04/deploy-order.md sections 2.1 (org-verified: HasOpportunityLineItem compiles in formula context) and 2.2 (still unverified: re-firing after a line-item deletion is a forward gate only) and has recorded that no deferred owner for a library gap is needed.
  Source note: Amended after G4: the original text described a blocked step.
- **AC-019.5** (negative) - open item, `decisions.md O-M2S04-05`.
  *Given* an Enterprise opportunity at Discover with no product lines, owned by a rep who does not hold Sales_Ops_Validation_Bypass; *when* the rep changes the stage to Propose and saves; *then* the save is rejected with “Add at least one product before moving this opportunity to Propose.” on the Stage field, and the stage stays Discover.
- **AC-019.6** - open item, `decisions.md O-M2S04-05` — also serves REQ-012.
  *Given* the same Enterprise opportunity with no product lines, and a user holding Sales_Ops_Validation_Bypass; *when* that user changes the stage to Propose and saves; *then* the save succeeds and the stage reads Propose.

### REQ-020 — The manager's approval request and the rep's approved/rejected notifications are sent from Classic text templates in a Sales Approvals folder, with the rejection pointing the rep at the approval comments

- **AC-020.1** (negative) - manual acceptance test, `plan.json steps[M3-S01].acceptance_tests[3]`.
  *Given* Q33 and assumption A27; *when* Discount_Rejected.email is read; *then* it names the Approval History related list as where the manager's comments are, rather than attempting to merge them into the body, and Discount_Approved.email and Discount_Rejected.email each address the opportunity owner rather than the manager.
- **AC-020.2** - manual acceptance test, `plan.json steps[M3-S01].acceptance_tests[4]`.
  *Given* that a Lightning email template is not packageable and the rule engine cannot reference one; *when* the three .email-meta.xml files are read; *then* each carries uiType Aloha, type text, available true and encodingKey UTF-8, and each subject is 230 characters or fewer.
- **AC-020.3** - open item, `decisions.md O-M3S01-03` — also serves REQ-021.
  *Given* Q33 puts the field update and the alert in the same approval action block, no cited skill fixes their order, and the bodies carry no % sign after Discount__c (UNVERIFIED (2026-09-19)); *when* each of the three templates is sent once in UAT - one submit, one approval and one rejection; *then* the approved and rejected bodies show Approval_Status__c as Approved and Rejected respectively, or the line is deleted from the template, and the rendered Discount__c value is recorded as it appears in each body.

### REQ-021 — An Enterprise or Renewal opportunity above a 20% discount can be submitted for approval to the owner's manager; submitting locks the record, approving or rejecting writes Approval_Status__c and emails the owner, recalling clears it; closed records are excluded from entry

- **AC-021.1** - milestone goal, `plan.json milestones[M3].goal` — also serves REQ-022.
  *Given* the guardrails are accepted; *when* the M3 artefacts are deployed; *then* submitting routes the request to their manager and locks the record.
- **AC-021.2** - milestone goal, `plan.json milestones[M3].goal` — also serves REQ-020.
  *Given* the guardrails are accepted; *when* the M3 artefacts are deployed; *then* approving or rejecting writes the status back and emails the rep.
- **AC-021.3** - milestone goal, `plan.json milestones[M3].goal`.
  *Given* the guardrails are accepted; *when* the M3 artefacts are deployed; *then* recalling clears it.
- **AC-021.4** (negative) - manual acceptance test, `plan.json steps[M3-S02].acceptance_tests[3]`.
  *Given* Q31 and Q33; *when* the approval process file is read; *then* recordEditability is AdminOnly, allowRecall is true, finalApprovalRecordLock and finalRejectionRecordLock are both false, allowedSubmitters carries exactly one entry of type owner, and recallActions fires a field update whose operation is Null so a recalled record shows a blank Approval Status rather than Rejected.
- **AC-021.5** - manual acceptance test, `plan.json steps[M3-S02].acceptance_tests[4]`.
  *Given* D9 and assumption A34; *when* artefacts/M3-S02/deploy-order.md is read; *then* it states that the process ships active true, that approval process ORDER is not in the metadata and must be set in Setup after deploy, and that the Apex in M3-S03 names the process explicitly so order affects only the standard Submit for Approval button.
- **AC-021.6** - manual acceptance test, `plan.json steps[M3-S02].acceptance_tests[5]`.
  *Given* admin/email-templates-and-alerts/references/gotchas.md:70 records an empty recipient set as a silent failure - 'A .workflow file whose alert carries a template, a description and a senderType but an empty recipient set deploys successfully, appears in Setup, is selectable from Flow - and delivers nothing. There is no runtime error and no entry in the debug log to look for.'; *when* artefacts/M3-S02/workflows/Opportunity.workflow-meta.xml is read; *then* each of Notify_Owner_Discount_Approved and Notify_Owner_Discount_Rejected carries a non-empty recipients block of <type>owner</type>, which is the opportunity owner and therefore the rep Q32 named.
  Source note: This is a manual line because neither declared checker reads recipients: check_approval_design.py resolves workflow actions by name only, and check_email_templates.py is declared at --manifest-dir artefacts/M3-S01 and never sees this step's workflow file.
- **AC-021.7** (negative) - manual acceptance test, `plan.json milestones[M3].acceptance_tests[3]` — also serves REQ-020.
  *Given* Q33's four outcomes; *when* the M3 artefacts are read end to end; *then* submit writes Pending and locks, approve writes Approved and unlocks and emails the rep, reject writes Rejected and unlocks and emails the rep, recall clears the field and sends nothing - and the one clause that is not delivered as asked, the manager's comments inside the rejection email, is visible as assumption A27 rather than as a silent substitution.
- **AC-021.8** (negative) - open item, `decisions.md O-M3S02-01`.
  *Given* the approval step reads the Manager field on the record owner (useApproverFieldOfRecordOwner true), and a blank Manager is a run-time submission failure no deploy catches; *when* the Manager of every Enterprise and Renewal opportunity owner is listed before go-live; *then* no Enterprise or Renewal opportunity owner has a blank Manager; each owner who does is fixed before go-live or recorded against a fallback-approver decision.

### REQ-022 — A rep or a Flow can submit one Opportunity into the Discount_Approval process from Apex (service, Aura-enabled controller, invocable action), with a refused second submission reported as a failed result rather than an exception

- **AC-022.1** - manual acceptance test, `plan.json steps[M3-S03].acceptance_tests[5]` — fails the outcome rule - see below.
  *Given* no offline Apex compiler exists in the sf CLI; *when* this step is reviewed; *then* every non-platform identifier in the emitted code is quoted from admin/approval-process-apex-patterns/references/metadata-examples.md or from templates/apex/tests/TestDataFactory.cls - Approval.ProcessSubmitRequest, setObjectId, setProcessDefinitionNameOrId, setSubmitterId, setSkipEntryCriteria, setComments, Approval.process(req, false), isSuccess, getInstanceStatus, getErrors, Database.Error.getStatusCode/getMessage, and TestDataFactory.createAccounts / createOpportunities with their documented signatures - and TestDataFactory.cls in this step diffs empty against templates/apex/tests/TestDataFactory.cls, and TestDataFactory.cls-meta.xml diffs empty against templates/apex/tests/TestDataFactory.cls-meta.xml and therefore carries <apiVersion>67.0</apiVersion> while OpportunityApprovalService, OpportunityApprovalController, OpportunityApprovalSubmitAction and OpportunityApprovalServiceTest carry 62.0 - a deliberate split recorded in this step's note, not a slip.
  Source note: Ticking this line is also what records the template's provenance, because this step declares no deploy-order.md.
- **AC-022.2** (negative) - manual acceptance test, `plan.json steps[M3-S03].acceptance_tests[6]`.
  *Given* Q35; *when* OpportunityApprovalServiceTest.cls is read; *then* one method asserts that a ProcessInstance with Status Pending exists for the opportunity after a submit, and a second asserts that a second submit while pending returns success false with a non-null failure message and creates no second pending instance.
- **AC-022.3** - manual acceptance test, `plan.json milestones[M3].acceptance_tests[4]` — also serves REQ-023, REQ-021; keyed: names no single requirement; keyed to the requirement of the first artefact its text names (the Apex, M3-S03 / REQ-022).
  *Given* no offline Apex compiler and no Jest runner exist in this layer; *when* the M3 gate is reached; *then* a reviewer confirms that scripts/mock_deploy.py has been run for M3 and that its summary.md is attached to the gate - because three green checkers over Apex, an LWC and an approval process prove shape and not compilation.
  Source note: Where the alias comes from: this build is build_mode design-only and plan.json carries no org key, so no alias is on file and mock_deploy.py requires --org-alias. The human supplies one at this point, from an org of their own choosing - the run is validation, not deploy (the script hard-codes checkOnly true and has no deploy option), and section 5 makes its summary.md the evidence a gate rests on. M4-S04's runbook repeats the command.

### REQ-023 — On an Enterprise or Renewal opportunity a rep sees a panel showing the discount and the approval status with a Submit button enabled only above the threshold and disabled while a request is pending, and submitting reports success or the refusal reason

- **AC-023.1** - milestone goal, `plan.json milestones[M3].goal`.
  *Given* the guardrails are accepted; *when* the M3 artefacts are deployed; *then* a rep on an Enterprise or Renewal opportunity with a discount above 20% sees a panel showing the discount and the approval status with an enabled Submit button.
- **AC-023.2** (negative) - manual acceptance test, `plan.json steps[M3-S04].acceptance_tests[3]`.
  *Given* Q35; *when* __tests__/discountApprovalPanel.test.js is read; *then* four cases stub the getRecord wire and assert the button's disabled property: true at a discount of 20, false at 25 with no approval status, true at 25 with Approval_Status__c Pending, and true at 25 with Approved - so the rule the requester described is pinned in both directions rather than only on the happy path.
- **AC-023.3** (negative) - manual acceptance test, `plan.json steps[M3-S04].acceptance_tests[4]`.
  *Given* D8 and assumption A35; *when* discountApprovalPanel.js-meta.xml is read; *then* discountThreshold is a design attribute with default 20 and a description naming the Opportunity_Discount_Requires_Approval validation rule, supportedFormFactors are Large and Small only, and the component targets lightning__RecordPage scoped to the Opportunity object.
- **AC-023.4** - open item, `decisions.md O-M3S04-01`.
  *Given* the 16 Jest cases in __tests__/discountApprovalPanel.test.js have been reviewed but never run, because no Node harness exists in this build (G5 accepted the suite as reviewed; a Jest harness is a release item); *when* sfdx-lwc-jest is run against the bundle in a project that has the harness; *then* all 16 cases pass, including the four button-state cases Q35 asked for.
- **AC-023.5** - open item, `decisions.md O-M3S04-02`.
  *Given* the panel compares Discount__c against 20 through the UI API while the validation rule and the approval entry criteria compare 0.20 in formula context (assumption A35, UNVERIFIED (2026-09-19)); *when* one Enterprise opportunity with Discount__c entered as 20% is opened on the record page in UAT; *then* the panel receives the value 20, not 0.20, and the Submit button is disabled at exactly 20%.

### REQ-024 — Enterprise opportunities open on a Lightning record page that carries the Path and the discount approval panel, activated as the org default for Opportunity

- **AC-024.1** - milestone goal, `plan.json milestones[M3].goal`.
  *Given* the guardrails are accepted; *when* the M3 artefacts are deployed; *then* all of it renders on one record page alongside the stage path.
- **AC-024.2** (negative) - manual acceptance test, `plan.json steps[M3-S05].acceptance_tests[3]`.
  *Given* D10 and assumption A38; *when* the object file is read; *then* it carries exactly two actionOverrides blocks - actionName View, type Flexipage, content Opportunity_Enterprise_Record_Page, formFactor Large and Small - and nothing else, and artefacts/M3-S05/deploy-order.md states that an app with its own Opportunity record page wins over this org default and must be re-pointed in Setup if Northwind runs one.
- **AC-024.3** - manual acceptance test, `plan.json steps[M3-S05].acceptance_tests[4]`.
  *Given* requirement.md item 4; *when* the flexipage file is read; *then* the Path component sits in the subheader region with hideUpdateButton false, the discountApprovalPanel sits in the sidebar region with its discountThreshold property set to 20, and every componentInstance carries an identifier of 120 characters or fewer.
- **AC-024.4** (negative) - open item, `decisions.md O-M3S05-02 (operator entry, line 1368), O-M3S05-03 (renderer entry, line 1402)`.
  *Given* an app with its own Opportunity record page outranks the org default this build writes, and nobody has enumerated which Lightning apps expose Opportunity at Northwind (assumption A38); *when* the org's CustomApplication metadata is retrieved and read before the M4 deploy, per artefacts/M3-S05/deploy-order.md section 3.1; *then* no app the reps use carries its own Opportunity record page assignment, or each one that does is re-pointed to Opportunity_Enterprise_Record_Page in Setup before go-live.
- **AC-024.5** (negative) - open item, `decisions.md O-M4S04-01, O-M4S04-05`.
  *Given* M3-S05 ships a two-element Opportunity object file (the two View actionOverrides), and admin/object-creation-and-design Gotcha 10 says a partial object file replaces the whole object definition on deploy - UNVERIFIED (2026-10-02): no validate-only run can settle it; *when* the deploy copy for request 1 is prepared; *then* CustomObject:Opportunity has been retrieved alone from the target org and the two actionOverrides merged into it in the deploy copy before request 1 starts, the artefact file itself is unchanged, and no request carries the two-element file unmerged.
- **AC-024.6** (negative) - open item, `decisions.md O-M4S04-03, O-M4S04-07`.
  *Given* the org-default record page M3-S05 activates has no record-type dimension (D-M3S05-01), the discount approval panel carries no record-type check, and requirement.md item 6 asks that the SMB team be left alone; *when* an SMB-team user opens an Opportunity of the SMB record type after deploy; *then* the record opens on a page other than Opportunity_Enterprise_Record_Page, through an app-level assignment scoped to the Enterprise record type, unless the VP's acceptance that SMB records open the Enterprise page is on record from A-8.

### REQ-025 — Before the Enterprise pipeline report type and report are deployed, the org's report folders, the SMB report's type and the new type's column codes are retrieved and confirmed by the runbook, never guessed

- **AC-025.1** - manual acceptance test, `plan.json steps[M4-S01].acceptance_tests[0]`.
  *Given* Q26 and assumption A28; *when* artefacts/M4-S01/deploy-order.md is read; *then* it names the three sf commands verbatim, lists each of the six column codes M4-S02 uses (Opportunity$Name, Opportunity$StageName, Opportunity$Amount, Opportunity$Discount__c, Opportunity$CloseDate, Opportunity$Approval_Status__c) as provisional, states that RPT-COL-01 in check_report_inventory.py reports every one of them as unverifiable offline by design, and says that the retrieve is a pre-deploy prerequisite rather than a build step.
  Source note: Tickable from this file alone - no org and no later artefact is needed.
- **AC-025.2** - manual acceptance test, `plan.json steps[M4-S01].acceptance_tests[1]`.
  *Given* Q54's default; *when* the same file is read; *then* it also states that a NEW Enterprise-scoped report type is built rather than editing whatever report type the SMB pipeline report uses, and names checking the SMB report's report type as part of the same retrieve so the decision can be confirmed rather than assumed.
- **AC-025.3** - open item, `decisions.md O-M4S01-02`.
  *Given* M4-S02's report type and column codes are provisional until the org confirms them (assumption A28, Q26); *when* Phase A in artefacts/M4-S01/deploy-order.md section 2 is run against the target org before M4-S02 deploys; *then* the org's report folders and the SMB pipeline report's report type are recorded in the runbook, closing U2 (and U3 if the SMB type is standard).
- **AC-025.4** (negative) - open item, `decisions.md O-M4S01-01, O-M4S01-03, O-M4S02-03, O-M4S02-05` — also serves REQ-026.
  *Given* a report on a custom report type created in the same deployment cannot be validated by checkOnly (N4-F-06), and the six column codes stay provisional until the org confirms them; *when* the M4 deploy is split - Group, ReportType, folders and the M1-S01 fields first - and a throwaway report is retrieved and compared before the Report and Dashboard deploy; *then* section 4's confirmed-code column in artefacts/M4-S01/deploy-order.md is filled for every code, any replaced code reaches M4-S02 through a rebuild rather than a hand edit, and the record-type criterion code is present in the report - it never ships absent.

### REQ-026 — Enterprise managers open a report of open Enterprise pipeline by stage with amount and discount, the VP's dashboard shows the Enterprise pipeline by close month, both shared to the Enterprise_Managers group in their own folders

- **AC-026.1** - milestone goal, `plan.json milestones[M4].goal`.
  *Given* the build works; *when* the M4 artefacts are deployed; *then* each Enterprise manager can open a report of their own reps' open pipeline by stage with amount and discount.
- **AC-026.2** - milestone goal, `plan.json milestones[M4].goal`.
  *Given* the build works; *when* the M4 artefacts are deployed; *then* the VP's dashboard shows the whole Enterprise pipeline by close month.
- **AC-026.3** (negative) - manual acceptance test, `plan.json steps[M4-S02].acceptance_tests[3]`.
  *Given* Q25 and assumption A32; *when* the two folder files are read; *then* each is accessType Shared with a single folderShares entry granting View to the Enterprise_Managers group, and artefacts/M4-S02/deploy-order.md states that the group ships with no members and that the sales-ops admin adds the two managers and the VP in Setup - because Group metadata carries no membership.
  Source note: Approving this gate is approving who can read deal amounts and discounts.
- **AC-026.4** (negative) - manual acceptance test, `plan.json steps[M4-S02].acceptance_tests[4]`.
  *Given* Q24, assumption A29 and decision D7; *when* the dashboard file is read; *then* dashboardType is SpecifiedUser, no runningUser element is present, and deploy-order.md names setting runningUser to the VP's username as a mandatory pre-deploy step, stating that the platform otherwise substitutes the deploying user's and that a SpecifiedUser dashboard shows every viewer the running user's data regardless of their own security settings.
- **AC-026.5** (negative) - manual acceptance test, `plan.json steps[M4-S02].acceptance_tests[5]`.
  *Given* Q23 and M2-S04's block; *when* the report file is read; *then* it carries no product-count column and deploy-order.md records why - the same line-item count M2-S04 is blocked on - and states that a join to Opportunity Product was rejected because it returns one row per line item and would double-count Amount.
  Source note: corrected after G5 by the prose-only amendment `plan.json steps[M4-S02].amendments[0]` (2026-10-02T18:52:43Z), which appends: M2-S04 was unblocked on 2026-09-15 and shipped Opportunity.Opportunity_Products_Required_At_Propose as an org-validated rule (MOCK-DEPLOY-M2 run 3); read every clause that assumes a blocked or empty M2-S04 as satisfied by that rule's presence - the exclusion it describes does not apply.
- **AC-026.6** - open item, `decisions.md O-M4S02-01, O-M4S02-06`.
  *Given* Q4 implies a public Opportunity org-wide default and forbids tightening it, Q24 asks that each manager sees only their own reps' pipeline on the report, and the report carries no scope element (D7); *when* the target org's Opportunity org-wide default is read and a manager runs the open-pipeline report; *then* the org-wide default is recorded; if it is public, the report shows each manager the whole Enterprise pipeline and a human ranks Q4 against Q24 before go-live (artefacts/M4-S02/deploy-order.md section 8); if it is private, the manager sees only their own reps' open deals.
- **AC-026.7** (negative) - open item, `decisions.md O-M4S02-02, O-M4S02-07`.
  *Given* the dashboard ships as SpecifiedUser with no runningUser element, and the VP's username is not on file in any source (assumption A29); *when* the deploy copy of the dashboard is prepared for a target org; *then* runningUser carries the VP's username for that org, or the gate records the decision to use a service user - never the deploying user's, which the platform substitutes when the element is absent.
- **AC-026.8** - open item, `decisions.md O-M4S02-11`.
  *Given* the Enterprise_Managers public group ships with no members because Group metadata carries no membership (assumption A32); *when* the sales-ops admin adds the members after deploy; *then* the group holds the two Enterprise managers and the VP, and P-MGR can open the Enterprise_Sales report and dashboard folders.

## Source criteria that fail the outcome rule

- **AC-022.1** - `plan.json steps[M3-S03].acceptance_tests[5]` (manual test M3-S03-T6). Its Then names Apex classes and `.cls` files. That makes it a code-provenance review, not an observable outcome, which is what `skills/admin/acceptance-criteria-given-when-then` gotcha 3 and the checker's Then rule forbid. It is compiled here with the gap named, and it stays out of the lintable record below. Put inside the record on a scratch copy during this run, it produced, at exit 1: '`then` names an Apex class role — a Then names the observable outcome, not the tool that produced it (references/gotchas.md gotcha 3).' The test itself is unchanged and is UAT case `TC-M3-S03-T6`. The fix belongs to the plan: an `amend-step --prose-only` that moves the identifiers into the When or into a note.

## Coverage - each criterion and the UAT cases that exercise it

| ac_id | source | UAT cases |
|---|---|---|
| AC-004.1 | milestone goal | none |
| AC-001.1 | milestone goal | none |
| AC-006.1 | milestone goal | none |
| AC-008.1 | milestone goal | none |
| AC-002.1 | milestone goal | none |
| AC-016.1 | milestone goal | none |
| AC-015.1 | milestone goal | TC-O-M2S03-04A |
| AC-012.1 | milestone goal | TC-O-M2S01-01, TC-O-M2S03-04B |
| AC-013.1 | milestone goal | none |
| AC-023.1 | milestone goal | none |
| AC-021.1 | milestone goal | none |
| AC-021.2 | milestone goal | none |
| AC-021.3 | milestone goal | none |
| AC-024.1 | milestone goal | none |
| AC-026.1 | milestone goal | none |
| AC-026.2 | milestone goal | none |
| AC-001.2 | milestone goal | none |
| AC-001.3 | manual acceptance test | TC-M1-S01-T6 |
| AC-001.4 | manual acceptance test | TC-M1-S01-T7 |
| AC-010.1 | manual acceptance test | TC-M1-S02-T4 |
| AC-008.2 | manual acceptance test | TC-M1-S02-T5 |
| AC-012.2 | manual acceptance test | TC-M2-S01-T5 |
| AC-014.1 | manual acceptance test | TC-M2-S02-T5 |
| AC-013.2 | manual acceptance test | TC-M2-S02-T6 |
| AC-015.2 | manual acceptance test | TC-M2-S03-T4 |
| AC-015.3 | manual acceptance test | TC-M2-S03-T5 |
| AC-019.1 | manual acceptance test | TC-M2-S04-T4 |
| AC-016.2 | manual acceptance test | TC-M2-S05-T5 |
| AC-018.1 | manual acceptance test | TC-M2-S05-T6 |
| AC-020.1 | manual acceptance test | TC-M3-S01-T4 |
| AC-020.2 | manual acceptance test | TC-M3-S01-T5 |
| AC-021.4 | manual acceptance test | TC-M3-S02-T4 |
| AC-021.5 | manual acceptance test | TC-M3-S02-T5 |
| AC-021.6 | manual acceptance test | TC-M3-S02-T6 |
| AC-022.1 | manual acceptance test | TC-M3-S03-T6 |
| AC-022.2 | manual acceptance test | TC-M3-S03-T7 |
| AC-023.2 | manual acceptance test | TC-M3-S04-T4 |
| AC-023.3 | manual acceptance test | TC-M3-S04-T5 |
| AC-024.2 | manual acceptance test | TC-M3-S05-T4 |
| AC-024.3 | manual acceptance test | TC-M3-S05-T5 |
| AC-025.1 | manual acceptance test | TC-M4-S01-T1 |
| AC-025.2 | manual acceptance test | TC-M4-S01-T2 |
| AC-026.3 | manual acceptance test | TC-M4-S02-T4 |
| AC-026.4 | manual acceptance test | TC-M4-S02-T5 |
| AC-026.5 | manual acceptance test | TC-M4-S02-T6 |
| AC-001.5 | manual acceptance test | TC-M4-S03-T5 |
| AC-019.2 | manual acceptance test | TC-M4-S03-T6 |
| AC-001.6 | manual acceptance test | TC-M4-S04-T4 |
| AC-019.3 | manual acceptance test | TC-M4-S04-T5 |
| AC-001.7 | manual acceptance test | TC-M4-S04-T6 |
| AC-010.3 | manual acceptance test | TC-M4-S04-T7 |
| AC-004.3 | manual acceptance test | TC-M4-S04-T8 |
| AC-016.3 | manual acceptance test | TC-M4-S04-T9 |
| AC-017.2 | manual acceptance test | TC-M4-S04-T10 |
| AC-017.3 | manual acceptance test | TC-M4-S04-T11 |
| AC-018.2 | manual acceptance test | TC-M4-S04-T12 |
| AC-018.3 | manual acceptance test | TC-M4-S04-T13 |
| AC-001.8 | manual acceptance test | TC-M1-T3 |
| AC-002.2 | manual acceptance test | TC-M1-T4 |
| AC-019.4 | manual acceptance test | TC-M2-T5 |
| AC-012.3 | manual acceptance test | TC-M2-T6 |
| AC-021.7 | manual acceptance test | TC-M3-T4 |
| AC-022.3 | manual acceptance test | TC-M3-T5 |
| AC-001.9 | manual acceptance test | TC-M4-T4 |
| AC-004.2 | manual acceptance test | TC-M4-T5 |
| AC-001.10 | open item | TC-O-M1S01-02 |
| AC-002.3 | open item | TC-O-M1S01-04 |
| AC-010.2 | open item | TC-O-M1S02-01 |
| AC-014.2 | open item | TC-O-M2S02-03 |
| AC-015.4 | open item | TC-O-M2S03-02 |
| AC-015.5 | open item | TC-O-M2S03-03 |
| AC-019.5 | open item | TC-O-M2S04-05A |
| AC-019.6 | open item | TC-O-M2S04-05B |
| AC-017.1 | open item | TC-O-M2S05-04 |
| AC-020.3 | open item | TC-O-M3S01-03 |
| AC-021.8 | open item | TC-O-M3S02-01 |
| AC-023.4 | open item | TC-O-M3S04-01 |
| AC-023.5 | open item | TC-O-M3S04-02 |
| AC-024.4 | open item | TC-O-M3S05-02 |
| AC-025.3 | open item | TC-O-M4S01-02 |
| AC-025.4 | open item | TC-O-M4S02-05 |
| AC-026.6 | open item | TC-O-M4S02-06 |
| AC-026.7 | open item | TC-O-M4S02-07 |
| AC-026.8 | open item | TC-O-M4S02-11 |
| AC-024.5 | open item | TC-O-M4S04-01 |
| AC-004.4 | open item | TC-O-M4S04-02 |
| AC-024.6 | open item | TC-O-M4S04-03 |

15 criteria have no case: AC-004.1, AC-001.1, AC-006.1, AC-008.1, AC-002.1, AC-016.1, AC-013.1, AC-023.1, AC-021.1, AC-021.2, AC-021.3, AC-024.1, AC-026.1, AC-026.2, AC-001.2. All of them are milestone-goal criteria. `skills/admin/uat-test-case-design` (§ One AC Scenario -> One UAT Case) asks for at least one case per criterion. `agents/build-doc-keeper/AGENT.md` Step 10 compiles cases only from the plan's manual tests, and this run adds open items that need a human check; it writes no case that no source states. Covering these criteria is a planning action, for example a manual test per goal clause on milestone M4.

## Lintable record

```yaml
project: "Northwind Enterprise sales process - build northwind-sales (design-only)"
acceptance_criteria:
  - ac_id: AC-004.1
    req_id: REQ-004
    persona: "Enterprise sales personas from the Background (P-REP, P-MGR, P-OPS): profile Sales User plus the permission sets named there"
    sandbox: "UNVERIFIED (2026-10-02) - not named in plan.json"
    artefact: "reports/MILESTONE-M1-package.xml"
    test_type: manual
    negative: false
    given: "an org where every Opportunity sits on one generic pipeline"
    when: "the M1 artefacts are deployed"
    then: "two record types exist with their own Sales Processes and stage sets"
    proof: "milestone M1 goal clause; exercised by the UAT cases listed in the coverage table"
    source: "plan.json milestones[M1].goal"
    also_serves: "REQ-005, REQ-002, REQ-003"
  - ac_id: AC-001.1
    req_id: REQ-001
    persona: "Enterprise sales personas from the Background (P-REP, P-MGR, P-OPS): profile Sales User plus the permission sets named there"
    sandbox: "UNVERIFIED (2026-10-02) - not named in plan.json"
    artefact: "reports/MILESTONE-M1-package.xml"
    test_type: manual
    negative: false
    given: "an org where every Opportunity sits on one generic pipeline"
    when: "the M1 artefacts are deployed"
    then: "the eight new stage values carry the probabilities and forecast buckets the VP signed off"
    proof: "milestone M1 goal clause; exercised by the UAT cases listed in the coverage table"
    source: "plan.json milestones[M1].goal"
  - ac_id: AC-006.1
    req_id: REQ-006
    persona: "Enterprise sales personas from the Background (P-REP, P-MGR, P-OPS): profile Sales User plus the permission sets named there"
    sandbox: "UNVERIFIED (2026-10-02) - not named in plan.json"
    artefact: "reports/MILESTONE-M1-package.xml"
    test_type: manual
    negative: false
    given: "an org where every Opportunity sits on one generic pipeline"
    when: "the M1 artefacts are deployed"
    then: "Discount__c and Approval_Status__c exist on Opportunity"
    proof: "milestone M1 goal clause; exercised by the UAT cases listed in the coverage table"
    source: "plan.json milestones[M1].goal"
    also_serves: "REQ-007"
  - ac_id: AC-008.1
    req_id: REQ-008
    persona: "Enterprise sales personas from the Background (P-REP, P-MGR, P-OPS): profile Sales User plus the permission sets named there"
    sandbox: "UNVERIFIED (2026-10-02) - not named in plan.json"
    artefact: "reports/MILESTONE-M1-package.xml"
    test_type: manual
    negative: false
    given: "an org where every Opportunity sits on one generic pipeline"
    when: "the M1 artefacts are deployed"
    then: "each record type has a layout carrying both"
    proof: "milestone M1 goal clause; exercised by the UAT cases listed in the coverage table"
    source: "plan.json milestones[M1].goal"
    also_serves: "REQ-009"
  - ac_id: AC-002.1
    req_id: REQ-002
    persona: "Enterprise sales personas from the Background (P-REP, P-MGR, P-OPS): profile Sales User plus the permission sets named there"
    sandbox: "UNVERIFIED (2026-10-02) - not named in plan.json"
    artefact: "reports/MILESTONE-M1-package.xml"
    test_type: manual
    negative: true
    given: "an org where every Opportunity sits on one generic pipeline"
    when: "the M1 artefacts are deployed"
    then: "the SMB team's record type, stages, list views and report are untouched"
    proof: "milestone M1 goal clause; exercised by the UAT cases listed in the coverage table"
    source: "plan.json milestones[M1].goal"
    also_serves: "REQ-001, REQ-014"
  - ac_id: AC-016.1
    req_id: REQ-016
    persona: "Enterprise sales personas from the Background (P-REP, P-MGR, P-OPS): profile Sales User plus the permission sets named there"
    sandbox: "UNVERIFIED (2026-10-02) - not named in plan.json"
    artefact: "reports/MILESTONE-M2-package.xml"
    test_type: manual
    negative: false
    given: "the M1 data model is accepted"
    when: "the M2 artefacts are deployed"
    then: "reps see a stage path carrying the exit criteria and key fields for each stage"
    proof: "milestone M2 goal clause; exercised by the UAT cases listed in the coverage table"
    source: "plan.json milestones[M2].goal"
    also_serves: "REQ-017"
  - ac_id: AC-015.1
    req_id: REQ-015
    persona: "Enterprise sales personas from the Background (P-REP, P-MGR, P-OPS): profile Sales User plus the permission sets named there"
    sandbox: "UNVERIFIED (2026-10-02) - not named in plan.json"
    artefact: "reports/MILESTONE-M2-package.xml"
    test_type: manual
    negative: true
    given: "the M1 data model is accepted"
    when: "the M2 artefacts are deployed"
    then: "an Enterprise or Renewal deal above a 20% discount cannot be set to Closed Won without an approved approval"
    proof: "milestone M2 goal clause; exercised by the UAT cases listed in the coverage table"
    source: "plan.json milestones[M2].goal"
  - ac_id: AC-012.1
    req_id: REQ-012
    persona: "Enterprise sales personas from the Background (P-REP, P-MGR, P-OPS): profile Sales User plus the permission sets named there"
    sandbox: "UNVERIFIED (2026-10-02) - not named in plan.json"
    artefact: "reports/MILESTONE-M2-package.xml"
    test_type: manual
    negative: true
    given: "the M1 data model is accepted"
    when: "the M2 artefacts are deployed"
    then: "the sales-ops admin is the only person who can save past that rule"
    proof: "milestone M2 goal clause; exercised by the UAT cases listed in the coverage table"
    source: "plan.json milestones[M2].goal"
    also_serves: "REQ-011, REQ-015"
  - ac_id: AC-013.1
    req_id: REQ-013
    persona: "Enterprise sales personas from the Background (P-REP, P-MGR, P-OPS): profile Sales User plus the permission sets named there"
    sandbox: "UNVERIFIED (2026-10-02) - not named in plan.json"
    artefact: "reports/MILESTONE-M2-package.xml"
    test_type: manual
    negative: false
    given: "the M1 data model is accepted"
    when: "the M2 artefacts are deployed"
    then: "the 12 reps and 2 managers can select both new record types and get the right layout"
    proof: "milestone M2 goal clause; exercised by the UAT cases listed in the coverage table"
    source: "plan.json milestones[M2].goal"
    also_serves: "REQ-014"
  - ac_id: AC-023.1
    req_id: REQ-023
    persona: "Enterprise sales personas from the Background (P-REP, P-MGR, P-OPS): profile Sales User plus the permission sets named there"
    sandbox: "UNVERIFIED (2026-10-02) - not named in plan.json"
    artefact: "reports/MILESTONE-M3-package.xml"
    test_type: manual
    negative: false
    given: "the guardrails are accepted"
    when: "the M3 artefacts are deployed"
    then: "a rep on an Enterprise or Renewal opportunity with a discount above 20% sees a panel showing the discount and the approval status with an enabled Submit button"
    proof: "milestone M3 goal clause; exercised by the UAT cases listed in the coverage table"
    source: "plan.json milestones[M3].goal"
  - ac_id: AC-021.1
    req_id: REQ-021
    persona: "Enterprise sales personas from the Background (P-REP, P-MGR, P-OPS): profile Sales User plus the permission sets named there"
    sandbox: "UNVERIFIED (2026-10-02) - not named in plan.json"
    artefact: "reports/MILESTONE-M3-package.xml"
    test_type: manual
    negative: false
    given: "the guardrails are accepted"
    when: "the M3 artefacts are deployed"
    then: "submitting routes the request to their manager and locks the record"
    proof: "milestone M3 goal clause; exercised by the UAT cases listed in the coverage table"
    source: "plan.json milestones[M3].goal"
    also_serves: "REQ-022"
  - ac_id: AC-021.2
    req_id: REQ-021
    persona: "Enterprise sales personas from the Background (P-REP, P-MGR, P-OPS): profile Sales User plus the permission sets named there"
    sandbox: "UNVERIFIED (2026-10-02) - not named in plan.json"
    artefact: "reports/MILESTONE-M3-package.xml"
    test_type: manual
    negative: false
    given: "the guardrails are accepted"
    when: "the M3 artefacts are deployed"
    then: "approving or rejecting writes the status back and emails the rep"
    proof: "milestone M3 goal clause; exercised by the UAT cases listed in the coverage table"
    source: "plan.json milestones[M3].goal"
    also_serves: "REQ-020"
  - ac_id: AC-021.3
    req_id: REQ-021
    persona: "Enterprise sales personas from the Background (P-REP, P-MGR, P-OPS): profile Sales User plus the permission sets named there"
    sandbox: "UNVERIFIED (2026-10-02) - not named in plan.json"
    artefact: "reports/MILESTONE-M3-package.xml"
    test_type: manual
    negative: false
    given: "the guardrails are accepted"
    when: "the M3 artefacts are deployed"
    then: "recalling clears it"
    proof: "milestone M3 goal clause; exercised by the UAT cases listed in the coverage table"
    source: "plan.json milestones[M3].goal"
  - ac_id: AC-024.1
    req_id: REQ-024
    persona: "Enterprise sales personas from the Background (P-REP, P-MGR, P-OPS): profile Sales User plus the permission sets named there"
    sandbox: "UNVERIFIED (2026-10-02) - not named in plan.json"
    artefact: "reports/MILESTONE-M3-package.xml"
    test_type: manual
    negative: false
    given: "the guardrails are accepted"
    when: "the M3 artefacts are deployed"
    then: "all of it renders on one record page alongside the stage path"
    proof: "milestone M3 goal clause; exercised by the UAT cases listed in the coverage table"
    source: "plan.json milestones[M3].goal"
  - ac_id: AC-026.1
    req_id: REQ-026
    persona: "Enterprise sales personas from the Background (P-REP, P-MGR, P-OPS): profile Sales User plus the permission sets named there"
    sandbox: "UNVERIFIED (2026-10-02) - not named in plan.json"
    artefact: "artefacts/M4-S04/package.xml"
    test_type: manual
    negative: false
    given: "the build works"
    when: "the M4 artefacts are deployed"
    then: "each Enterprise manager can open a report of their own reps' open pipeline by stage with amount and discount"
    proof: "milestone M4 goal clause; exercised by the UAT cases listed in the coverage table"
    source: "plan.json milestones[M4].goal"
  - ac_id: AC-026.2
    req_id: REQ-026
    persona: "Enterprise sales personas from the Background (P-REP, P-MGR, P-OPS): profile Sales User plus the permission sets named there"
    sandbox: "UNVERIFIED (2026-10-02) - not named in plan.json"
    artefact: "artefacts/M4-S04/package.xml"
    test_type: manual
    negative: false
    given: "the build works"
    when: "the M4 artefacts are deployed"
    then: "the VP's dashboard shows the whole Enterprise pipeline by close month"
    proof: "milestone M4 goal clause; exercised by the UAT cases listed in the coverage table"
    source: "plan.json milestones[M4].goal"
  - ac_id: AC-001.2
    req_id: REQ-001
    persona: "Build reviewer at the M4 milestone gate (no Salesforce profile or permission set; the oracle is the compiled document set)"
    sandbox: "UNVERIFIED (2026-10-02) - not named in plan.json"
    artefact: "artefacts/M4-S04/package.xml"
    test_type: manual
    negative: false
    given: "the build works"
    when: "the M4 artefacts are deployed"
    then: "the sales-ops admin holds one workbook, one traceability matrix, one UAT pack, one manifest and one runbook that together name every prerequisite, every assumption and every step that shipped nothing"
    proof: "milestone M4 goal clause; exercised by the UAT cases listed in the coverage table"
    source: "plan.json milestones[M4].goal"
    keyed_by: "names no requirement; keyed by the fallback rule to the lowest-numbered requirement the compiled documents cover"
  - ac_id: AC-001.3
    req_id: REQ-001
    persona: "Build reviewer at the M1 milestone gate (no Salesforce profile or permission set; the oracle is a build file)"
    sandbox: "n/a - build-record check"
    artefact: "artefacts/M1-S01/deploy-order.md"
    test_type: manual
    negative: false
    given: "D1 and assumption A24"
    when: "artefacts/M1-S01/deploy-order.md is read"
    then: "its first instruction is to run sf project retrieve start --metadata StandardValueSet:OpportunityStage against the target org and merge the retrieved active values into the shipped file, and it states in the same paragraph that a partial file deactivates every value it omits - including the SMB team's stages"
    proof: "artefacts/M1-S01/deploy-order.md read at the M1 gate, ticked against case TC-M1-S01-T6"
    source: "plan.json steps[M1-S01].acceptance_tests[5]"
  - ac_id: AC-001.4
    req_id: REQ-001
    persona: "Build reviewer at the M1 milestone gate (no Salesforce profile or permission set; the oracle is a build file)"
    sandbox: "n/a - build-record check"
    artefact: "artefacts/M1-S01/standardValueSets/OpportunityStage.standardValueSet-meta.xml"
    test_type: manual
    negative: true
    given: "Q5 and Q6"
    when: "the eight standardValue blocks are read"
    then: "Qualify/Discover/Propose/Negotiate carry 10/25/50/75 and Pipeline/Pipeline/BestCase/Forecast, Renewal Review and Renewal Proposed carry 60/85 and Pipeline/Forecast, Closed Won carries 100 with won and closed true, Closed Lost carries 0 with forecastCategory Omitted - and the word 'Commit' appears nowhere in the file"
    proof: "artefacts/M1-S01/standardValueSets/OpportunityStage.standardValueSet-meta.xml read at the M1 gate, ticked against case TC-M1-S01-T7"
    source: "plan.json steps[M1-S01].acceptance_tests[6]"
  - ac_id: AC-010.1
    req_id: REQ-010
    persona: "Build reviewer at the M1 milestone gate (no Salesforce profile or permission set; the oracle is a build file)"
    sandbox: "n/a - build-record check"
    artefact: "artefacts/M1-S02/deploy-order.md"
    test_type: manual
    negative: false
    given: "assumption A26"
    when: "artefacts/M1-S02/deploy-order.md is read"
    then: 'it names the exact sf project retrieve start --metadata "Layout:Opportunity-Opportunity Layout" command, says to copy the Opportunity Products relatedLists block verbatim from what the retrieve emits, and states that hand-authoring the related-list name is what the instruction exists to prevent'
    proof: "artefacts/M1-S02/deploy-order.md read at the M1 gate, ticked against case TC-M1-S02-T4"
    source: "plan.json steps[M1-S02].acceptance_tests[3]"
  - ac_id: AC-008.2
    req_id: REQ-008
    persona: "Build reviewer at the M1 milestone gate (no Salesforce profile or permission set; the oracle is a build file)"
    sandbox: "n/a - build-record check"
    artefact: "artefacts/M1-S02/layouts/Opportunity-Opportunity Enterprise Layout.layout-meta.xml"
    test_type: manual
    negative: true
    given: "assumption A25"
    when: "both layout files are read"
    then: "each carries Name, AccountId, StageName, CloseDate and Amount, plus Discount__c editable and Approval_Status__c read-only, and deploy-order.md records that the platform's layout-required set for Opportunity is unverified and is discovered by iterating scripts/mock_deploy.py --dry-run, one field per run"
    proof: "artefacts/M1-S02/layouts/Opportunity-Opportunity Enterprise Layout.layout-meta.xml read at the M1 gate, ticked against case TC-M1-S02-T5"
    source: "plan.json steps[M1-S02].acceptance_tests[4]"
    also_serves: "REQ-009"
  - ac_id: AC-012.2
    req_id: REQ-012
    persona: "Build reviewer at the M2 milestone gate (no Salesforce profile or permission set; the oracle is a build file)"
    sandbox: "n/a - build-record check"
    artefact: "artefacts/M2-S01/permissionsets/Sales_Ops_Validation_Bypass.permissionset-meta.xml"
    test_type: manual
    negative: true
    given: "Q13 and Q17"
    when: "artefacts/M2-S01/permissionsets/Sales_Ops_Validation_Bypass.permissionset-meta.xml is read"
    then: "it grants exactly one custom permission, carries no objectPermissions, no fieldPermissions and no userPermissions, and its description names the sales-ops admin as the only intended holder - so approving this gate is approving one bypass and nothing else"
    proof: "artefacts/M2-S01/permissionsets/Sales_Ops_Validation_Bypass.permissionset-meta.xml read at the M2 gate, ticked against case TC-M2-S01-T5"
    source: "plan.json steps[M2-S01].acceptance_tests[4]"
  - ac_id: AC-014.1
    req_id: REQ-014
    persona: "Build reviewer at the M2 milestone gate (no Salesforce profile or permission set; the oracle is a build file)"
    sandbox: "n/a - build-record check"
    artefact: "artefacts/M2-S02/profiles/Sales User.profile-meta.xml"
    test_type: manual
    negative: true
    given: "Q4 and Q9"
    when: "artefacts/M2-S02/profiles/Sales User.profile-meta.xml is read"
    then: "it contains exactly two layoutAssignments blocks, one per new record type, and no recordTypeVisibilities block at all - visibility for Enterprise and Renewal is granted by the Enterprise_Sales_Record_Types permission set, because a profile block that lists visible types must name a default and naming one would move the SMB team's default (org finding N3-F-05, MOCK-DEPLOY-M2 run 1) - and it carries no userPermissions, objectPermissions, fieldPermissions, applicationVisibilities or classAccesses, so deploying it changes nothing for the SMB team except that the two new record types have their layouts"
    proof: "artefacts/M2-S02/profiles/Sales User.profile-meta.xml read at the M2 gate, ticked against case TC-M2-S02-T5"
    source: "plan.json steps[M2-S02].acceptance_tests[4]"
  - ac_id: AC-013.2
    req_id: REQ-013
    persona: "Build reviewer at the M2 milestone gate (no Salesforce profile or permission set; the oracle is a build file)"
    sandbox: "n/a - build-record check"
    artefact: "artefacts/M2-S02/permissionsets/Enterprise_Sales_Record_Types.permissionset-meta.xml"
    test_type: manual
    negative: true
    given: "Q19"
    when: "the two files are read together"
    then: "reps and managers reach both record types through the permission set while the sales-ops admin (System Administrator) needs no row in either file, and the manager-versus-rep distinction appears nowhere in this step - it is a role-hierarchy fact, which is what decision D7 records"
    proof: "artefacts/M2-S02/permissionsets/Enterprise_Sales_Record_Types.permissionset-meta.xml read at the M2 gate, ticked against case TC-M2-S02-T6"
    source: "plan.json steps[M2-S02].acceptance_tests[5]"
  - ac_id: AC-015.2
    req_id: REQ-015
    persona: "Build reviewer at the M2 milestone gate (no Salesforce profile or permission set; the oracle is a build file)"
    sandbox: "n/a - build-record check"
    artefact: "artefacts/M2-S03/objects/Opportunity/validationRules/Opportunity_Discount_Requires_Approval.validationRule-meta.xml"
    test_type: manual
    negative: true
    given: "D8 and assumption A35"
    when: "the errorConditionFormula is read"
    then: "the discount comparison is 'Discount__c > 0.20' and not '> 20', the bypass clause NOT($Permission.Bypass_Opportunity_Sales_Validation) is the first argument of the outer AND, and the record-type gate compares RecordType.DeveloperName with = rather than ISPICKVAL"
    proof: "artefacts/M2-S03/objects/Opportunity/validationRules/Opportunity_Discount_Requires_Approval.validationRule-meta.xml read at the M2 gate, ticked against case TC-M2-S03-T4"
    source: "plan.json steps[M2-S03].acceptance_tests[3]"
  - ac_id: AC-015.3
    req_id: REQ-015
    persona: "Build reviewer at the M2 milestone gate (no Salesforce profile or permission set; the oracle is a build file)"
    sandbox: "n/a - build-record check"
    artefact: "artefacts/M2-S03/objects/Opportunity/validationRules/Opportunity_Discount_Requires_Approval.validationRule-meta.xml"
    test_type: manual
    negative: false
    given: "Q15"
    when: "errorMessage is read"
    then: "it is Q15's sentence verbatim, is 255 characters or fewer, and errorDisplayField is Discount__c so the error lands on the field the rep has to change rather than at the top of the page"
    proof: "artefacts/M2-S03/objects/Opportunity/validationRules/Opportunity_Discount_Requires_Approval.validationRule-meta.xml read at the M2 gate, ticked against case TC-M2-S03-T5"
    source: "plan.json steps[M2-S03].acceptance_tests[4]"
  - ac_id: AC-019.1
    req_id: REQ-019
    persona: "Build reviewer at the M2 milestone gate (no Salesforce profile or permission set; the oracle is a build file)"
    sandbox: "n/a - build-record check"
    artefact: "artefacts/M2-S04/deploy-order.md"
    test_type: manual
    negative: false
    given: "the two claims the step note carried as UNVERIFIED (2026-09-15) - formula-context availability of HasOpportunityLineItem, and the official-source conflict on re-firing after a line-item deletion"
    when: "artefacts/M2-S04/deploy-order.md is read at the M2 gate"
    then: "section 2.1 records the first as org-verified by MOCK-DEPLOY-M2 run 1 (2026-09-19, the formula compiled under checkOnly), and section 2.2 records the second as still unverified with 'forward gate only' stated, because a checkOnly deploy exercises no deletion"
    proof: "artefacts/M2-S04/deploy-order.md read at the M2 gate, ticked against case TC-M2-S04-T4"
    source: "plan.json steps[M2-S04].acceptance_tests[3]"
  - ac_id: AC-016.2
    req_id: REQ-016
    persona: "Build reviewer at the M2 milestone gate (no Salesforce profile or permission set; the oracle is a build file)"
    sandbox: "n/a - build-record check"
    artefact: "artefacts/M2-S05/pathAssistants/Enterprise_Opportunity_Path.pathAssistant-meta.xml"
    test_type: manual
    negative: false
    given: "Q2 and Q11"
    when: "the Enterprise path's four pathAssistantSteps are read"
    then: "the Discover step's info text names 'at least one product line added from the price book' and a booked Next Step, the Propose step's info text names a primary contact with the Decision Maker contact role, and the Negotiate step's key fields are Discount__c, Approval_Status__c and CloseDate - so every exit criterion the requester dictated is visible to a rep even though M2-S04 cannot enforce the product one"
    proof: "artefacts/M2-S05/pathAssistants/Enterprise_Opportunity_Path.pathAssistant-meta.xml read at the M2 gate, ticked against case TC-M2-S05-T5"
    source: "plan.json steps[M2-S05].acceptance_tests[4]"
  - ac_id: AC-018.1
    req_id: REQ-018
    persona: "Build reviewer at the M2 milestone gate (no Salesforce profile or permission set; the oracle is a build file)"
    sandbox: "n/a - build-record check"
    artefact: "artefacts/M2-S05/deploy-order.md"
    test_type: manual
    negative: false
    given: "admin/path-and-guidance's rule that a path is not evidence the feature is on"
    when: "artefacts/M2-S05/deploy-order.md is read"
    then: "it states that a green PathAssistant deploy proves neither that Path is enabled nor that the component is on the record page, and points at M3-S05 as the step that puts it there"
    proof: "artefacts/M2-S05/deploy-order.md read at the M2 gate, ticked against case TC-M2-S05-T6"
    source: "plan.json steps[M2-S05].acceptance_tests[5]"
    also_serves: "REQ-016, REQ-017"
  - ac_id: AC-020.1
    req_id: REQ-020
    persona: "Build reviewer at the M3 milestone gate (no Salesforce profile or permission set; the oracle is a build file)"
    sandbox: "n/a - build-record check"
    artefact: "artefacts/M3-S01/email/Sales_Approvals/Discount_Rejected.email"
    test_type: manual
    negative: true
    given: "Q33 and assumption A27"
    when: "Discount_Rejected.email is read"
    then: "it names the Approval History related list as where the manager's comments are, rather than attempting to merge them into the body, and Discount_Approved.email and Discount_Rejected.email each address the opportunity owner rather than the manager"
    proof: "artefacts/M3-S01/email/Sales_Approvals/Discount_Rejected.email read at the M3 gate, ticked against case TC-M3-S01-T4"
    source: "plan.json steps[M3-S01].acceptance_tests[3]"
  - ac_id: AC-020.2
    req_id: REQ-020
    persona: "Build reviewer at the M3 milestone gate (no Salesforce profile or permission set; the oracle is a build file)"
    sandbox: "n/a - build-record check"
    artefact: "artefacts/M3-S01/email/Sales_Approvals/Discount_Approval_Request.email-meta.xml"
    test_type: manual
    negative: false
    given: "that a Lightning email template is not packageable and the rule engine cannot reference one"
    when: "the three .email-meta.xml files are read"
    then: "each carries uiType Aloha, type text, available true and encodingKey UTF-8, and each subject is 230 characters or fewer"
    proof: "artefacts/M3-S01/email/Sales_Approvals/Discount_Approval_Request.email-meta.xml read at the M3 gate, ticked against case TC-M3-S01-T5"
    source: "plan.json steps[M3-S01].acceptance_tests[4]"
  - ac_id: AC-021.4
    req_id: REQ-021
    persona: "Build reviewer at the M3 milestone gate (no Salesforce profile or permission set; the oracle is a build file)"
    sandbox: "n/a - build-record check"
    artefact: "artefacts/M3-S02/approvalProcesses/Opportunity.Discount_Approval.approvalProcess-meta.xml"
    test_type: manual
    negative: true
    given: "Q31 and Q33"
    when: "the approval process file is read"
    then: "recordEditability is AdminOnly, allowRecall is true, finalApprovalRecordLock and finalRejectionRecordLock are both false, allowedSubmitters carries exactly one entry of type owner, and recallActions fires a field update whose operation is Null so a recalled record shows a blank Approval Status rather than Rejected"
    proof: "artefacts/M3-S02/approvalProcesses/Opportunity.Discount_Approval.approvalProcess-meta.xml read at the M3 gate, ticked against case TC-M3-S02-T4"
    source: "plan.json steps[M3-S02].acceptance_tests[3]"
  - ac_id: AC-021.5
    req_id: REQ-021
    persona: "Build reviewer at the M3 milestone gate (no Salesforce profile or permission set; the oracle is a build file)"
    sandbox: "n/a - build-record check"
    artefact: "artefacts/M3-S02/deploy-order.md"
    test_type: manual
    negative: false
    given: "D9 and assumption A34"
    when: "artefacts/M3-S02/deploy-order.md is read"
    then: "it states that the process ships active true, that approval process ORDER is not in the metadata and must be set in Setup after deploy, and that the Apex in M3-S03 names the process explicitly so order affects only the standard Submit for Approval button"
    proof: "artefacts/M3-S02/deploy-order.md read at the M3 gate, ticked against case TC-M3-S02-T5"
    source: "plan.json steps[M3-S02].acceptance_tests[4]"
  - ac_id: AC-021.6
    req_id: REQ-021
    persona: "Build reviewer at the M3 milestone gate (no Salesforce profile or permission set; the oracle is a build file)"
    sandbox: "n/a - build-record check"
    artefact: "artefacts/M3-S02/workflows/Opportunity.workflow-meta.xml"
    test_type: manual
    negative: false
    given: "admin/email-templates-and-alerts/references/gotchas.md:70 records an empty recipient set as a silent failure - 'A .workflow file whose alert carries a template, a description and a senderType but an empty recipient set deploys successfully, appears in Setup, is selectable from Flow - and delivers nothing. There is no runtime error and no entry in the debug log to look for.'"
    when: "artefacts/M3-S02/workflows/Opportunity.workflow-meta.xml is read"
    then: "each of Notify_Owner_Discount_Approved and Notify_Owner_Discount_Rejected carries a non-empty recipients block of <type>owner</type>, which is the opportunity owner and therefore the rep Q32 named"
    proof: "artefacts/M3-S02/workflows/Opportunity.workflow-meta.xml read at the M3 gate, ticked against case TC-M3-S02-T6"
    source: "plan.json steps[M3-S02].acceptance_tests[5]"
  - ac_id: AC-022.2
    req_id: REQ-022
    persona: "Build reviewer at the M3 milestone gate (no Salesforce profile or permission set; the oracle is a build file)"
    sandbox: "n/a - build-record check"
    artefact: "artefacts/M3-S03/classes/OpportunityApprovalServiceTest.cls"
    test_type: manual
    negative: true
    given: "Q35"
    when: "OpportunityApprovalServiceTest.cls is read"
    then: "one method asserts that a ProcessInstance with Status Pending exists for the opportunity after a submit, and a second asserts that a second submit while pending returns success false with a non-null failure message and creates no second pending instance"
    proof: "artefacts/M3-S03/classes/OpportunityApprovalServiceTest.cls read at the M3 gate, ticked against case TC-M3-S03-T7"
    source: "plan.json steps[M3-S03].acceptance_tests[6]"
  - ac_id: AC-023.2
    req_id: REQ-023
    persona: "Build reviewer at the M3 milestone gate (no Salesforce profile or permission set; the oracle is a build file)"
    sandbox: "n/a - build-record check"
    artefact: "artefacts/M3-S04/lwc/discountApprovalPanel/__tests__/discountApprovalPanel.test.js"
    test_type: manual
    negative: true
    given: "Q35"
    when: "__tests__/discountApprovalPanel.test.js is read"
    then: "four cases stub the getRecord wire and assert the button's disabled property: true at a discount of 20, false at 25 with no approval status, true at 25 with Approval_Status__c Pending, and true at 25 with Approved - so the rule the requester described is pinned in both directions rather than only on the happy path"
    proof: "artefacts/M3-S04/lwc/discountApprovalPanel/__tests__/discountApprovalPanel.test.js read at the M3 gate, ticked against case TC-M3-S04-T4"
    source: "plan.json steps[M3-S04].acceptance_tests[3]"
  - ac_id: AC-023.3
    req_id: REQ-023
    persona: "Build reviewer at the M3 milestone gate (no Salesforce profile or permission set; the oracle is a build file)"
    sandbox: "n/a - build-record check"
    artefact: "artefacts/M3-S04/lwc/discountApprovalPanel/discountApprovalPanel.js-meta.xml"
    test_type: manual
    negative: true
    given: "D8 and assumption A35"
    when: "discountApprovalPanel.js-meta.xml is read"
    then: "discountThreshold is a design attribute with default 20 and a description naming the Opportunity_Discount_Requires_Approval validation rule, supportedFormFactors are Large and Small only, and the component targets lightning__RecordPage scoped to the Opportunity object"
    proof: "artefacts/M3-S04/lwc/discountApprovalPanel/discountApprovalPanel.js-meta.xml read at the M3 gate, ticked against case TC-M3-S04-T5"
    source: "plan.json steps[M3-S04].acceptance_tests[4]"
  - ac_id: AC-024.2
    req_id: REQ-024
    persona: "Build reviewer at the M3 milestone gate (no Salesforce profile or permission set; the oracle is a build file)"
    sandbox: "n/a - build-record check"
    artefact: "artefacts/M3-S05/objects/Opportunity/Opportunity.object-meta.xml"
    test_type: manual
    negative: true
    given: "D10 and assumption A38"
    when: "the object file is read"
    then: "it carries exactly two actionOverrides blocks - actionName View, type Flexipage, content Opportunity_Enterprise_Record_Page, formFactor Large and Small - and nothing else, and artefacts/M3-S05/deploy-order.md states that an app with its own Opportunity record page wins over this org default and must be re-pointed in Setup if Northwind runs one"
    proof: "artefacts/M3-S05/objects/Opportunity/Opportunity.object-meta.xml read at the M3 gate, ticked against case TC-M3-S05-T4"
    source: "plan.json steps[M3-S05].acceptance_tests[3]"
  - ac_id: AC-024.3
    req_id: REQ-024
    persona: "Build reviewer at the M3 milestone gate (no Salesforce profile or permission set; the oracle is a build file)"
    sandbox: "n/a - build-record check"
    artefact: "artefacts/M3-S05/flexipages/Opportunity_Enterprise_Record_Page.flexipage-meta.xml"
    test_type: manual
    negative: false
    given: "requirement.md item 4"
    when: "the flexipage file is read"
    then: "the Path component sits in the subheader region with hideUpdateButton false, the discountApprovalPanel sits in the sidebar region with its discountThreshold property set to 20, and every componentInstance carries an identifier of 120 characters or fewer"
    proof: "artefacts/M3-S05/flexipages/Opportunity_Enterprise_Record_Page.flexipage-meta.xml read at the M3 gate, ticked against case TC-M3-S05-T5"
    source: "plan.json steps[M3-S05].acceptance_tests[4]"
  - ac_id: AC-025.1
    req_id: REQ-025
    persona: "Build reviewer at the M4 milestone gate (no Salesforce profile or permission set; the oracle is a build file)"
    sandbox: "n/a - build-record check"
    artefact: "artefacts/M4-S01/deploy-order.md"
    test_type: manual
    negative: false
    given: "Q26 and assumption A28"
    when: "artefacts/M4-S01/deploy-order.md is read"
    then: "it names the three sf commands verbatim, lists each of the six column codes M4-S02 uses (Opportunity$Name, Opportunity$StageName, Opportunity$Amount, Opportunity$Discount__c, Opportunity$CloseDate, Opportunity$Approval_Status__c) as provisional, states that RPT-COL-01 in check_report_inventory.py reports every one of them as unverifiable offline by design, and says that the retrieve is a pre-deploy prerequisite rather than a build step"
    proof: "artefacts/M4-S01/deploy-order.md read at the M4 gate, ticked against case TC-M4-S01-T1"
    source: "plan.json steps[M4-S01].acceptance_tests[0]"
  - ac_id: AC-025.2
    req_id: REQ-025
    persona: "Build reviewer at the M4 milestone gate (no Salesforce profile or permission set; the oracle is a build file)"
    sandbox: "n/a - build-record check"
    artefact: "artefacts/M4-S01/deploy-order.md"
    test_type: manual
    negative: false
    given: "Q54's default"
    when: "the same file is read"
    then: "it also states that a NEW Enterprise-scoped report type is built rather than editing whatever report type the SMB pipeline report uses, and names checking the SMB report's report type as part of the same retrieve so the decision can be confirmed rather than assumed"
    proof: "artefacts/M4-S01/deploy-order.md read at the M4 gate, ticked against case TC-M4-S01-T2"
    source: "plan.json steps[M4-S01].acceptance_tests[1]"
  - ac_id: AC-026.3
    req_id: REQ-026
    persona: "Build reviewer at the M4 milestone gate (no Salesforce profile or permission set; the oracle is a build file)"
    sandbox: "n/a - build-record check"
    artefact: "artefacts/M4-S02/reports/Enterprise_Sales.reportFolder-meta.xml"
    test_type: manual
    negative: true
    given: "Q25 and assumption A32"
    when: "the two folder files are read"
    then: "each is accessType Shared with a single folderShares entry granting View to the Enterprise_Managers group, and artefacts/M4-S02/deploy-order.md states that the group ships with no members and that the sales-ops admin adds the two managers and the VP in Setup - because Group metadata carries no membership"
    proof: "artefacts/M4-S02/reports/Enterprise_Sales.reportFolder-meta.xml read at the M4 gate, ticked against case TC-M4-S02-T4"
    source: "plan.json steps[M4-S02].acceptance_tests[3]"
  - ac_id: AC-026.4
    req_id: REQ-026
    persona: "Build reviewer at the M4 milestone gate (no Salesforce profile or permission set; the oracle is a build file)"
    sandbox: "n/a - build-record check"
    artefact: "artefacts/M4-S02/dashboards/Enterprise_Sales/Enterprise_Pipeline.dashboard-meta.xml"
    test_type: manual
    negative: true
    given: "Q24, assumption A29 and decision D7"
    when: "the dashboard file is read"
    then: "dashboardType is SpecifiedUser, no runningUser element is present, and deploy-order.md names setting runningUser to the VP's username as a mandatory pre-deploy step, stating that the platform otherwise substitutes the deploying user's and that a SpecifiedUser dashboard shows every viewer the running user's data regardless of their own security settings"
    proof: "artefacts/M4-S02/dashboards/Enterprise_Sales/Enterprise_Pipeline.dashboard-meta.xml read at the M4 gate, ticked against case TC-M4-S02-T5"
    source: "plan.json steps[M4-S02].acceptance_tests[4]"
  - ac_id: AC-026.5
    req_id: REQ-026
    persona: "Build reviewer at the M4 milestone gate (no Salesforce profile or permission set; the oracle is a build file)"
    sandbox: "n/a - build-record check"
    artefact: "artefacts/M4-S02/reports/Enterprise_Sales/Open_Enterprise_Pipeline_By_Stage.report-meta.xml"
    test_type: manual
    negative: true
    given: "Q23 and M2-S04's block"
    when: "the report file is read"
    then: "it carries no product-count column and deploy-order.md records why - the same line-item count M2-S04 is blocked on - and states that a join to Opportunity Product was rejected because it returns one row per line item and would double-count Amount"
    proof: "artefacts/M4-S02/reports/Enterprise_Sales/Open_Enterprise_Pipeline_By_Stage.report-meta.xml read at the M4 gate, ticked against case TC-M4-S02-T6"
    source: "plan.json steps[M4-S02].acceptance_tests[5]"
    amended: "corrected after G5 by the prose-only amendment plan.json steps[M4-S02].amendments[0] (2026-10-02T18:52:43Z): M2-S04 was unblocked on 2026-09-15 and shipped Opportunity.Opportunity_Products_Required_At_Propose as an org-validated rule (MOCK-DEPLOY-M2 run 3); read every clause that assumes a blocked or empty M2-S04 as satisfied by that rule's presence - the exclusion it describes does not apply."
  - ac_id: AC-001.5
    req_id: REQ-001
    persona: "Build reviewer at the M4 milestone gate (no Salesforce profile or permission set; the oracle is a build file)"
    sandbox: "n/a - build-record check"
    artefact: "artefacts/M4-S03/configuration-workbook.md"
    test_type: manual
    negative: false
    given: "30 informational clarifications were left unanswered at G1 and eleven org facts nobody supplied"
    when: "the workbook's assumptions section is read"
    then: "all 43 assumption rows appear with a named owner who can close each one and the step ids each constrains, and the three rows carrying risk high - which are exactly the three pre-deploy prerequisites: A24 the OpportunityStage union, A28 the report column codes and A29 the dashboard runningUser - are called out rather than buried in the list"
    proof: "artefacts/M4-S03/configuration-workbook.md read at the M4 gate, ticked against case TC-M4-S03-T5"
    source: "plan.json steps[M4-S03].acceptance_tests[4]"
    keyed_by: "names no single requirement; keyed to the requirement of the first prerequisite its own text names (A24, the OpportunityStage union, constrains M1-S01 / REQ-001)"
  - ac_id: AC-019.2
    req_id: REQ-019
    persona: "Build reviewer at the M4 milestone gate (no Salesforce profile or permission set; the oracle is a build file)"
    sandbox: "n/a - build-record check"
    artefact: "artefacts/M4-S03/traceability.md"
    test_type: manual
    negative: false
    given: "M2-S04 ships nothing in this release"
    when: "traceability.md is read"
    then: "its row for the product-before-Propose requirement names M2-S04 with its blocked_reason verbatim rather than being silently absent, and the workbook's Validation Rules section carries the same row rather than only the rule that did ship"
    proof: "artefacts/M4-S03/traceability.md read at the M4 gate, ticked against case TC-M4-S03-T6"
    source: "plan.json steps[M4-S03].acceptance_tests[5]"
    amended: "corrected after G5 by the prose-only amendment plan.json steps[M4-S03].amendments[1] (2026-10-02T18:52:43Z): M2-S04 was unblocked on 2026-09-15 and shipped Opportunity.Opportunity_Products_Required_At_Propose as an org-validated rule (MOCK-DEPLOY-M2 run 3); read every clause that assumes a blocked or empty M2-S04 as satisfied by that rule's presence - the exclusion it describes does not apply."
  - ac_id: AC-001.6
    req_id: REQ-001
    persona: "Build reviewer at the M4 milestone gate (no Salesforce profile or permission set; the oracle is a build file)"
    sandbox: "n/a - build-record check"
    artefact: "artefacts/M4-S04/deploy-order.md"
    test_type: manual
    negative: true
    given: "section 5's deploy deny-list and this layer's rule that it never deploys"
    when: "artefacts/M4-S04/deploy-order.md is read"
    then: "it contains no sf project deploy start without --dry-run anywhere, and the only org-facing command it offers is scripts/mock_deploy.py <plan.json> --org-alias <alias> --milestone <id>, which a release owner may choose to run"
    proof: "artefacts/M4-S04/deploy-order.md read at the M4 gate, ticked against case TC-M4-S04-T4"
    source: "plan.json steps[M4-S04].acceptance_tests[3]"
    keyed_by: "names no requirement at all; keyed by the fallback rule to the lowest-numbered requirement in the build-level manifest the runbook governs"
  - ac_id: AC-019.3
    req_id: REQ-019
    persona: "Build reviewer at the M4 milestone gate (no Salesforce profile or permission set; the oracle is a build file)"
    sandbox: "n/a - build-record check"
    artefact: "artefacts/M4-S04/package.xml"
    test_type: manual
    negative: false
    given: "M2-S04 was unblocked on 2026-09-15 and shipped Opportunity.Opportunity_Products_Required_At_Propose as an org-validated rule (MOCK-DEPLOY-M2 run 3)"
    when: "package.xml and deploy-order.md are read together"
    then: "that rule appears exactly once as a ValidationRule member with its file behind it, and deploy-order.md lists it in the validation-rule position after M2-S01's custom permission"
    proof: "artefacts/M4-S04/package.xml read at the M4 gate, ticked against case TC-M4-S04-T5"
    source: "plan.json steps[M4-S04].acceptance_tests[4]"
    amended: "reworded after G5 by plan.json steps[M4-S04].amendments[0] (2026-10-02T18:52:18Z): the original text assumed a blocked step and would have dropped a shipped rule from the manifest"
  - ac_id: AC-001.7
    req_id: REQ-001
    persona: "Build reviewer at the M4 milestone gate (no Salesforce profile or permission set; the oracle is a build file)"
    sandbox: "n/a - build-record check"
    artefact: "artefacts/M4-S04/deploy-order.md"
    test_type: manual
    negative: false
    given: "Q8, Q17, Q25, Q26 and the eight assumptions this step carries"
    when: "the cutover runbook section is read"
    then: "each of the nine post-deploy or pre-deploy prerequisites has a named owner and an ordered position - retrieve and merge OpportunityStage, discover the layout-required fields, retrieve the products related-list name, confirm the report column codes, set the dashboard runningUser, populate the Enterprise Managers group, set approval process order, reassign the 140 open Enterprise deals, and record every bypass use in Chatter"
    proof: "artefacts/M4-S04/deploy-order.md read at the M4 gate, ticked against case TC-M4-S04-T6"
    source: "plan.json steps[M4-S04].acceptance_tests[5]"
    keyed_by: "spans nine prerequisites; keyed to the requirement of the first one its text names (retrieve and merge OpportunityStage, REQ-001)"
  - ac_id: AC-010.3
    req_id: REQ-010
    persona: "Build reviewer at the M4 milestone gate (no Salesforce profile or permission set; the oracle is a build file)"
    sandbox: "n/a - build-record check"
    artefact: "artefacts/M4-S04/deploy-order.md"
    test_type: manual
    negative: false
    given: "assumption A26 (REQ-010: the Opportunity Products related list is retrieved from the org's current Opportunity layout and copied into both Enterprise and Renewal layouts, never hand-authored)"
    when: "deploy-order.md's cutover runbook is read"
    then: "it carries that retrieve-and-copy as a pre-deploy step with a named owner before the Layout deploy, and the M4 gate records REQ-010 as covered by this runbook step rather than by metadata - the related list has had no artefact and no test since M1"
    proof: "artefacts/M4-S04/deploy-order.md and the milestone:M4 gate record, read at the M4 gate and ticked against case TC-M4-S04-T7"
    source: "plan.json steps[M4-S04].acceptance_tests[6]"
    added_by: "plan.json steps[M4-S04].amendments[0] (2026-10-02T18:52:18Z)"
  - ac_id: AC-004.3
    req_id: REQ-004
    persona: "Sales User profile with the org's Sales Cloud permission set (Q19), without the Enterprise_Sales_Record_Types permission set; the Sales User overlay carries no recordTypeVisibilities block (CWB-PERM-004)"
    sandbox: "UNVERIFIED (2026-10-02) - not named in plan.json"
    artefact: "artefacts/M2-S02/permissionsets/Enterprise_Sales_Record_Types.permissionset-meta.xml"
    test_type: manual
    negative: true
    given: "a user holding neither Enterprise_Sales_Record_Types nor a profile grant for the new types"
    when: "they create an Opportunity after deploy"
    then: "neither Enterprise nor Renewal is offered on the New dialog and the SMB default is unchanged - a UAT step, recorded in the runbook's post-deploy checks"
    proof: "the New Opportunity dialog the persona sees after deploy, and the persona's default Opportunity record type recorded before and after deploy, ticked against case TC-M4-S04-T8"
    source: "plan.json steps[M4-S04].acceptance_tests[7]"
    added_by: "plan.json steps[M4-S04].amendments[0] (2026-10-02T18:52:18Z)"
    amended: "moved to UAT after the first deploy, not the M4 gate, by plan.json steps[M4-S04].amendments[2] (2026-10-02T19:17:05Z)"
  - ac_id: AC-016.3
    req_id: REQ-016
    persona: "P-REP - Enterprise rep: profile Sales User with the org's Sales Cloud permission set (Q19) plus the Enterprise_Sales_Record_Types permission set (M2-S02); role Enterprise Rep; does not hold Sales_Ops_Validation_Bypass"
    sandbox: "UNVERIFIED (2026-10-02) - not named in plan.json"
    artefact: "artefacts/M2-S05/pathAssistants/Enterprise_Opportunity_Path.pathAssistant-meta.xml"
    test_type: manual
    negative: true
    given: "an Opportunity of the SMB record type"
    when: "its record page is opened after deploy"
    then: "the Enterprise Path's stages and key fields do not render for it - the Path is bound to the Enterprise record type only"
    proof: "the SMB Opportunity's record page after deploy, ticked against case TC-M4-S04-T9"
    source: "plan.json steps[M4-S04].acceptance_tests[8]"
    added_by: "plan.json steps[M4-S04].amendments[0] (2026-10-02T18:52:18Z)"
    amended: "moved to UAT after the first deploy, not the M4 gate, by plan.json steps[M4-S04].amendments[2] (2026-10-02T19:17:05Z)"
  - ac_id: AC-017.2
    req_id: REQ-017
    persona: "P-REP - Enterprise rep: profile Sales User with the org's Sales Cloud permission set (Q19) plus the Enterprise_Sales_Record_Types permission set (M2-S02); role Enterprise Rep; does not hold Sales_Ops_Validation_Bypass"
    sandbox: "UNVERIFIED (2026-10-02) - not named in plan.json"
    artefact: "artefacts/M2-S05/pathAssistants/Renewal_Opportunity_Path.pathAssistant-meta.xml"
    test_type: manual
    negative: true
    given: "an Opportunity of the Enterprise record type"
    when: "its record page is opened after deploy"
    then: "the Renewal Path's two stages do not render for it - the Renewal Path is bound to the Renewal record type only"
    proof: "the Enterprise Opportunity's record page after deploy, ticked against case TC-M4-S04-T10"
    source: "plan.json steps[M4-S04].acceptance_tests[9]"
    added_by: "plan.json steps[M4-S04].amendments[0] (2026-10-02T18:52:18Z)"
    amended: "split, and moved to UAT after the first deploy, by plan.json steps[M4-S04].amendments[2] (2026-10-02T19:17:05Z); the former second clause is AC-017.3"
  - ac_id: AC-017.3
    req_id: REQ-017
    persona: "Build reviewer at the M4 milestone gate (no Salesforce profile or permission set; the oracle is a build file)"
    sandbox: "n/a - build-record check"
    artefact: "artefacts/M4-S04/deploy-order.md"
    test_type: manual
    negative: false
    given: "the Renewal record type falls through to the org's existing Opportunity record page (O-M2S05-04)"
    when: "the cutover runbook is read"
    then: "it carries the retrieve-and-grep of that page for runtime_sales_pathassistant:pathAssistant as a pre-deploy step with a named owner, and names the decision if the component is absent (add it to that page, or accept that the Renewal Path does not render)"
    proof: "artefacts/M4-S04/deploy-order.md read at the M4 gate, ticked against case TC-M4-S04-T11"
    source: "plan.json steps[M4-S04].acceptance_tests[10]"
    added_by: "plan.json steps[M4-S04].amendments[2] (2026-10-02T19:17:05Z), split out of the former compound test 10"
  - ac_id: AC-018.2
    req_id: REQ-018
    persona: "P-REP - Enterprise rep: profile Sales User with the org's Sales Cloud permission set (Q19) plus the Enterprise_Sales_Record_Types permission set (M2-S02); role Enterprise Rep; does not hold Sales_Ops_Validation_Bypass; a second user, P-MGR, stands for the test's 'others'"
    sandbox: "UNVERIFIED (2026-10-02) - not named in plan.json"
    artefact: "artefacts/M2-S05/settings/PathAssistant.settings-meta.xml"
    test_type: manual
    negative: true
    given: "the PathAssistant org setting is deployed with the user-preference override enabled (artefacts/M2-S05/settings/PathAssistant.settings-meta.xml, canOverrideAutoPathCollapseWithUserPref true)"
    when: "a user collapses the Path and reopens the record"
    then: "it stays collapsed for that user and expanded for others"
    proof: "the reopened record as the collapsing user, and the same record as a second user, ticked against case TC-M4-S04-T12"
    source: "plan.json steps[M4-S04].acceptance_tests[11]"
    added_by: "plan.json steps[M4-S04].amendments[0] (2026-10-02T18:52:18Z)"
    amended: "split, and moved to UAT after the first deploy, by plan.json steps[M4-S04].amendments[2] (2026-10-02T19:17:05Z), which states the override value; the former rehearsal clause is AC-018.3"
  - ac_id: AC-018.3
    req_id: REQ-018
    persona: "Build reviewer at the M4 milestone gate (no Salesforce profile or permission set; the oracle is a build file)"
    sandbox: "n/a - build-record check"
    artefact: "artefacts/M4-S04/deploy-order.md"
    test_type: manual
    negative: false
    given: "a scratch-org or sandbox rehearsal is part of the cutover runbook"
    when: "the runbook is read"
    then: "it states that the PathAssistant setting member deploys with M2-S05 and that a rehearsal without it shows neither Path - the setting is load-bearing, not a default"
    proof: "artefacts/M4-S04/deploy-order.md read at the M4 gate, ticked against case TC-M4-S04-T13"
    source: "plan.json steps[M4-S04].acceptance_tests[12]"
    added_by: "plan.json steps[M4-S04].amendments[2] (2026-10-02T19:17:05Z), split out of the former compound test 11"
  - ac_id: AC-001.8
    req_id: REQ-001
    persona: "Named owner of the OpportunityStage merge - the Sales-ops admin role in CWB-OBJ-001's owner cell (no individual is named in any source); retrieves with their own org login, no permission set exercised"
    sandbox: "n/a - build-record check"
    artefact: "artefacts/M1-S01/standardValueSets/OpportunityStage.standardValueSet-meta.xml"
    test_type: manual
    negative: false
    given: "assumption A24 at risk high"
    when: "the M1 gate is reached"
    then: "a named owner confirms the OpportunityStage file about to be deployed is the union of the org's currently active stage values and the eight new ones - because a partial file deactivates every value it omits, which is the single way this milestone could break the SMB pipeline it is designed to leave alone"
    proof: "artefacts/M1-S01/standardValueSets/OpportunityStage.standardValueSet-meta.xml read at the M1 gate, ticked against case TC-M1-T3"
    source: "plan.json milestones[M1].acceptance_tests[2]"
  - ac_id: AC-002.2
    req_id: REQ-002
    persona: "Build reviewer at the M1 milestone gate (no Salesforce profile or permission set; the oracle is a build file)"
    sandbox: "n/a - build-record check"
    artefact: "artefacts/M1-S01/package.xml"
    test_type: manual
    negative: true
    given: "requirement.md item 6 and Q9"
    when: "the whole M1 artefact tree is listed"
    then: "no file anywhere names the SMB record type, either SMB list view, or the SMB pipeline report - the milestone is additive by construction rather than by promise"
    proof: "artefacts/M1-S01/package.xml read at the M1 gate, ticked against case TC-M1-T4"
    source: "plan.json milestones[M1].acceptance_tests[3]"
    also_serves: "REQ-001, REQ-014"
  - ac_id: AC-019.4
    req_id: REQ-019
    persona: "Build reviewer at the M2 milestone gate (no Salesforce profile or permission set; the oracle is a build file)"
    sandbox: "n/a - build-record check"
    artefact: "artefacts/M2-S04/deploy-order.md"
    test_type: manual
    negative: false
    given: "M2-S04 was unblocked on 2026-09-15 and shipped the product-before-Propose gate as a validation rule (not as Path guidance)"
    when: "the M2 gate is reached"
    then: "the approver has read artefacts/M2-S04/deploy-order.md sections 2.1 (org-verified: HasOpportunityLineItem compiles in formula context) and 2.2 (still unverified: re-firing after a line-item deletion is a forward gate only) and has recorded that no deferred owner for a library gap is needed"
    proof: "artefacts/M2-S04/deploy-order.md read at the M2 gate, ticked against case TC-M2-T5"
    source: "plan.json milestones[M2].acceptance_tests[4]"
  - ac_id: AC-012.3
    req_id: REQ-012
    persona: "Approver of milestone:M2 - VP Sales Operations (Pranav, per the G4 record); no Salesforce permission set is exercised"
    sandbox: "n/a - build-record check"
    artefact: "artefacts/M2-S01/permissionsets/Sales_Ops_Validation_Bypass.permissionset-meta.xml"
    test_type: manual
    negative: false
    given: "both M2 access steps carry their own step gate"
    when: "the M2 gate is reached"
    then: "the person approving it can name every person who gains the bypass permission (the sales-ops admin, and nobody else) and every person who gains the two record types (the 12 reps, the 2 managers and the sales-ops admin)"
    proof: "artefacts/M2-S01/permissionsets/Sales_Ops_Validation_Bypass.permissionset-meta.xml read at the M2 gate, ticked against case TC-M2-T6"
    source: "plan.json milestones[M2].acceptance_tests[5]"
    also_serves: "REQ-013"
  - ac_id: AC-021.7
    req_id: REQ-021
    persona: "Build reviewer at the M3 milestone gate (no Salesforce profile or permission set; the oracle is a build file)"
    sandbox: "n/a - build-record check"
    artefact: "artefacts/M3-S02/workflows/Opportunity.workflow-meta.xml"
    test_type: manual
    negative: true
    given: "Q33's four outcomes"
    when: "the M3 artefacts are read end to end"
    then: "submit writes Pending and locks, approve writes Approved and unlocks and emails the rep, reject writes Rejected and unlocks and emails the rep, recall clears the field and sends nothing - and the one clause that is not delivered as asked, the manager's comments inside the rejection email, is visible as assumption A27 rather than as a silent substitution"
    proof: "artefacts/M3-S02/workflows/Opportunity.workflow-meta.xml read at the M3 gate, ticked against case TC-M3-T4"
    source: "plan.json milestones[M3].acceptance_tests[3]"
    also_serves: "REQ-020"
  - ac_id: AC-022.3
    req_id: REQ-022
    persona: "Build reviewer at the M3 milestone gate (no Salesforce profile or permission set; the oracle is a build file)"
    sandbox: "n/a - build-record check"
    artefact: "reports/MOCK-DEPLOY-M3.md"
    test_type: manual
    negative: false
    given: "no offline Apex compiler and no Jest runner exist in this layer"
    when: "the M3 gate is reached"
    then: "a reviewer confirms that scripts/mock_deploy.py has been run for M3 and that its summary.md is attached to the gate - because three green checkers over Apex, an LWC and an approval process prove shape and not compilation"
    proof: "reports/MOCK-DEPLOY-M3.md read at the M3 gate, ticked against case TC-M3-T5"
    source: "plan.json milestones[M3].acceptance_tests[4]"
    also_serves: "REQ-023, REQ-021"
    keyed_by: "names no single requirement; keyed to the requirement of the first artefact its text names (the Apex, M3-S03 / REQ-022)"
  - ac_id: AC-001.9
    req_id: REQ-001
    persona: "Build reviewer at the M4 milestone gate (no Salesforce profile or permission set; the oracle is a build file)"
    sandbox: "n/a - build-record check"
    artefact: "artefacts/M4-S04/deploy-order.md"
    test_type: manual
    negative: false
    given: "the nine pre-deploy and post-deploy prerequisites this plan discovered"
    when: "the M4 gate is reached"
    then: "each has a named owner in the cutover runbook and the three that would silently produce a wrong result if skipped - the OpportunityStage union, the report column codes and the dashboard runningUser - are marked as blocking the deploy rather than as follow-ups"
    proof: "artefacts/M4-S04/deploy-order.md read at the M4 gate, ticked against case TC-M4-T4"
    source: "plan.json milestones[M4].acceptance_tests[3]"
    also_serves: "REQ-025, REQ-026"
    keyed_by: "spans nine prerequisites; keyed to the requirement of the first of the three blocking ones its text names (the OpportunityStage union, REQ-001)"
  - ac_id: AC-004.2
    req_id: REQ-004
    persona: "Build reviewer at the M4 milestone gate (no Salesforce profile or permission set; the oracle is a build file)"
    sandbox: "n/a - build-record check"
    artefact: "artefacts/M4-S04/deploy-order.md"
    test_type: manual
    negative: false
    given: "Q8"
    when: "the cutover runbook is read"
    then: "the reassignment of about 140 open Enterprise deals to the Enterprise record type is an ordered step with an owner and a stated position relative to the deploy, and it is described as a one-time data update rather than as a migration - which is what requirement.md item 6 rules out"
    proof: "artefacts/M4-S04/deploy-order.md read at the M4 gate, ticked against case TC-M4-T5"
    source: "plan.json milestones[M4].acceptance_tests[4]"
  - ac_id: AC-001.10
    req_id: REQ-001
    persona: "Sales Operations lead (Q39 owner_role) reading the target org's Opportunity settings through a metadata retrieve - no profile or permission set is exercised"
    sandbox: "UNVERIFIED (2026-10-02) - not named in plan.json"
    artefact: "settings/Opportunity.settings-meta.xml (target-org retrieve; no such file ships in this build)"
    test_type: manual
    negative: false
    given: "Q39 is still open and assumption A4 relies on OpportunitySettings.enableOpportunityFieldHistoryTracking defaulting to true, with no OpportunitySettings file shipped anywhere in this build"
    when: "the target org's Opportunity settings are read before go-live"
    then: "Opportunity field history tracking is on, so stage movement can be measured from day one - Opportunity field history cannot be backfilled"
    proof: "the retrieved enableOpportunityFieldHistoryTracking value, or the setting read in Setup, recorded with its date - UNVERIFIED (2026-10-02): the settings file name is inferred from the Settings member convention CWB-PATH-003 records, not stated by a cited skill"
    source: "decisions.md O-M1S01-02"
    keyed_by: "assumption A4 constrains M1-S01; keyed to its first requirement (REQ-001, the stage values whose movement Q39 asks to measure)"
  - ac_id: AC-002.3
    req_id: REQ-002
    persona: "P-REP - Enterprise rep: profile Sales User with the org's Sales Cloud permission set (Q19) plus the Enterprise_Sales_Record_Types permission set (M2-S02); role Enterprise Rep; does not hold Sales_Ops_Validation_Bypass"
    sandbox: "UNVERIFIED (2026-10-02) - not named in plan.json"
    artefact: "artefacts/M1-S01/deploy-order.md"
    test_type: manual
    negative: false
    given: "neither BusinessProcess carries a default stage after the N3-F-01 repair (D-M1S01-05), and no cited skill documents a per-process default-stage mechanism for Opportunity"
    when: "a new Enterprise and a new Renewal Opportunity are created after deploy and the post-deploy SOQL in artefacts/M1-S01/deploy-order.md section 4 is run"
    then: "the stage each record opens on is read from the query and is a member of its own process's stage set (Enterprise: Qualify, Discover, Propose, Negotiate, Closed Won, Closed Lost; Renewal: Renewal Review, Renewal Proposed, Closed Won, Closed Lost)"
    proof: "the section 4 SOQL result for both records, cross-checked against each process's stage list - never what the UI shows as selected"
    source: "decisions.md O-M1S01-04"
    also_serves: "REQ-003"
  - ac_id: AC-010.2
    req_id: REQ-010
    persona: "P-REP - Enterprise rep: profile Sales User with the org's Sales Cloud permission set (Q19) plus the Enterprise_Sales_Record_Types permission set (M2-S02); role Enterprise Rep; does not hold Sales_Ops_Validation_Bypass"
    sandbox: "UNVERIFIED (2026-10-02) - not named in plan.json"
    artefact: "artefacts/M1-S02/layouts/Opportunity-Opportunity Enterprise Layout.layout-meta.xml"
    test_type: manual
    negative: true
    given: "the Opportunity Products relatedLists element has been retrieved from the target org's Opportunity Layout and pasted verbatim into both layouts before deploy (O-M1S02-01, assumption A26)"
    when: "a rep opens an Enterprise opportunity and adds a product line from the Standard Price Book"
    then: "the Opportunity Products related list is on the page and the product line saves, and the relatedLists element in each shipped layout diffs empty against the retrieved file - no hand-typed related-list name"
    proof: "the diff of each shipped layout's relatedLists element against the retrieved layout, plus a screenshot of the related list with the added line"
    source: "decisions.md O-M1S02-01"
  - ac_id: AC-014.2
    req_id: REQ-014
    persona: "Release owner preparing the target-org deploy (no Salesforce permission set exercised; reads build files and the target org's metadata)"
    sandbox: "UNVERIFIED (2026-10-02) - not named in plan.json"
    artefact: "artefacts/M2-S02/profiles/Sales User.profile-meta.xml"
    test_type: manual
    negative: false
    given: "the Profile member and file stem are written Sales User, with its space, on Q19's phrase alone (UNVERIFIED (2026-09-19) in artefacts/M2-S02/deploy-order.md)"
    when: "the target org's profiles are listed before deploy"
    then: "a profile whose Name is exactly Sales User exists, or the file stem and package member are corrected before deploy - a mismatch is an INVALID_CROSS_REFERENCE_KEY on the profile half only"
    proof: "the target org's profile list, with the matching Name recorded"
    source: "decisions.md O-M2S02-03"
  - ac_id: AC-015.4
    req_id: REQ-015
    persona: "Release owner preparing the target-org deploy (no Salesforce permission set exercised; reads build files and the target org's metadata)"
    sandbox: "UNVERIFIED (2026-10-02) - not named in plan.json"
    artefact: "artefacts/M2-S03/deploy-order.md"
    test_type: manual
    negative: true
    given: "assumption A8 assumes no legacy automation writes StageName, Amount, Discount__c or Approval_Status__c after save, and a custom validation rule does not re-run after a workflow field update re-saves the record"
    when: "the target org's workflow rules and other automation on Opportunity are listed before go-live"
    then: "no pre-existing automation on Opportunity writes StageName, Amount, Discount__c or Approval_Status__c after save; any that does is recorded as a gap against the discount cap before go-live"
    proof: "the list of Opportunity workflow rules and field updates in the target org, with each one's target fields"
    source: "decisions.md O-M2S03-02"
  - ac_id: AC-015.5
    req_id: REQ-015
    persona: "Release owner preparing the target-org deploy (no Salesforce permission set exercised; reads build files and the target org's metadata)"
    sandbox: "n/a - no org"
    artefact: "artefacts/M4-S04/deploy-order.md"
    test_type: manual
    negative: true
    given: "the discount cap ships active, the approval process is the only non-bypass path to satisfy it, and G4 decided that M3-S02 deploys in the same release as M2-S03"
    when: "the release's deploy order and manifest are read before go-live"
    then: "Opportunity_Discount_Requires_Approval is not deployed to the target org ahead of Opportunity.Discount_Approval - both are in the same release"
    proof: "the build-level package.xml and the cutover runbook's deploy order"
    source: "decisions.md O-M2S03-03"
    also_serves: "REQ-021"
  - ac_id: AC-019.5
    req_id: REQ-019
    persona: "P-REP - Enterprise rep: profile Sales User with the org's Sales Cloud permission set (Q19) plus the Enterprise_Sales_Record_Types permission set (M2-S02); role Enterprise Rep; does not hold Sales_Ops_Validation_Bypass"
    sandbox: "UNVERIFIED (2026-10-02) - not named in plan.json"
    artefact: "artefacts/M2-S04/objects/Opportunity/validationRules/Opportunity_Products_Required_At_Propose.validationRule-meta.xml"
    test_type: apex
    negative: true
    given: "an Enterprise opportunity at Discover with no product lines, owned by a rep who does not hold Sales_Ops_Validation_Bypass"
    when: "the rep changes the stage to Propose and saves"
    then: "the save is rejected with “Add at least one product before moving this opportunity to Propose.” on the Stage field, and the stage stays Discover"
    proof: "the error shown against StageName, and SELECT StageName, HasOpportunityLineItem FROM Opportunity WHERE Id = :oppId"
    source: "decisions.md O-M2S04-05"
  - ac_id: AC-019.6
    req_id: REQ-019
    persona: "P-OPS - the sales-ops admin seat holding the Sales_Ops_Validation_Bypass permission set (the one person Q13 allows past the rules); its profile is recorded in permission_setup"
    sandbox: "UNVERIFIED (2026-10-02) - not named in plan.json"
    artefact: "artefacts/M2-S04/objects/Opportunity/validationRules/Opportunity_Products_Required_At_Propose.validationRule-meta.xml"
    test_type: apex
    negative: false
    given: "the same Enterprise opportunity with no product lines, and a user holding Sales_Ops_Validation_Bypass"
    when: "that user changes the stage to Propose and saves"
    then: "the save succeeds and the stage reads Propose"
    proof: "SELECT StageName FROM Opportunity WHERE Id = :oppId after the save"
    source: "decisions.md O-M2S04-05"
    also_serves: "REQ-012"
  - ac_id: AC-017.1
    req_id: REQ-017
    persona: "P-REP - Enterprise rep: profile Sales User with the org's Sales Cloud permission set (Q19) plus the Enterprise_Sales_Record_Types permission set (M2-S02); role Enterprise Rep; does not hold Sales_Ops_Validation_Bypass"
    sandbox: "UNVERIFIED (2026-10-02) - not named in plan.json"
    artefact: "artefacts/M2-S05/pathAssistants/Renewal_Opportunity_Path.pathAssistant-meta.xml"
    test_type: manual
    negative: false
    given: "M3-S05 builds the Enterprise record page only, and the org default it writes is not record-type-scoped (ActionOverride on CustomObject has no recordType field)"
    when: "the org's existing FlexiPages are retrieved and searched for the Path component before deploy, and a rep opens a Renewal opportunity after deploy"
    then: "the page the Renewal opportunity resolves to carries runtime_sales_pathassistant:pathAssistant and shows the Renewal path (Renewal Review, Renewal Proposed)"
    proof: "the grep result over the retrieved flexipages folder, and a screenshot of the Renewal record page"
    source: "decisions.md O-M2S05-04, O-M3S05-03 (operator entry, line 1375), O-M3S05-04 (renderer entry, line 1408)"
  - ac_id: AC-020.3
    req_id: REQ-020
    persona: "P-REP - Enterprise rep: profile Sales User with the org's Sales Cloud permission set (Q19) plus the Enterprise_Sales_Record_Types permission set (M2-S02); role Enterprise Rep; does not hold Sales_Ops_Validation_Bypass (submitter); P-MGR approves or rejects"
    sandbox: "UNVERIFIED (2026-10-02) - not named in plan.json"
    artefact: "artefacts/M3-S01/email/Sales_Approvals/Discount_Approved.email"
    test_type: manual
    negative: false
    given: "Q33 puts the field update and the alert in the same approval action block, no cited skill fixes their order, and the bodies carry no % sign after Discount__c (UNVERIFIED (2026-09-19))"
    when: "each of the three templates is sent once in UAT - one submit, one approval and one rejection"
    then: "the approved and rejected bodies show Approval_Status__c as Approved and Rejected respectively, or the line is deleted from the template, and the rendered Discount__c value is recorded as it appears in each body"
    proof: "the three received messages, attached whole"
    source: "decisions.md O-M3S01-03"
    also_serves: "REQ-021"
  - ac_id: AC-021.8
    req_id: REQ-021
    persona: "Release owner preparing the target-org deploy (no Salesforce permission set exercised; reads build files and the target org's metadata)"
    sandbox: "UNVERIFIED (2026-10-02) - not named in plan.json"
    artefact: "artefacts/M3-S02/approvalProcesses/Opportunity.Discount_Approval.approvalProcess-meta.xml"
    test_type: manual
    negative: true
    given: "the approval step reads the Manager field on the record owner (useApproverFieldOfRecordOwner true), and a blank Manager is a run-time submission failure no deploy catches"
    when: "the Manager of every Enterprise and Renewal opportunity owner is listed before go-live"
    then: "no Enterprise or Renewal opportunity owner has a blank Manager; each owner who does is fixed before go-live or recorded against a fallback-approver decision"
    proof: "a list of every Enterprise and Renewal opportunity owner with their Manager, dated"
    source: "decisions.md O-M3S02-01"
  - ac_id: AC-023.4
    req_id: REQ-023
    persona: "Developer running the Jest harness locally - no Salesforce profile or permission set; the oracle is the test runner"
    sandbox: "n/a - no org"
    artefact: "artefacts/M3-S04/lwc/discountApprovalPanel/__tests__/discountApprovalPanel.test.js"
    test_type: manual
    negative: false
    given: "the 16 Jest cases in __tests__/discountApprovalPanel.test.js have been reviewed but never run, because no Node harness exists in this build (G5 accepted the suite as reviewed; a Jest harness is a release item)"
    when: "sfdx-lwc-jest is run against the bundle in a project that has the harness"
    then: "all 16 cases pass, including the four button-state cases Q35 asked for"
    proof: "the sfdx-lwc-jest run output, attached"
    source: "decisions.md O-M3S04-01"
  - ac_id: AC-023.5
    req_id: REQ-023
    persona: "P-REP - Enterprise rep: profile Sales User with the org's Sales Cloud permission set (Q19) plus the Enterprise_Sales_Record_Types permission set (M2-S02); role Enterprise Rep; does not hold Sales_Ops_Validation_Bypass"
    sandbox: "UNVERIFIED (2026-10-02) - not named in plan.json"
    artefact: "artefacts/M3-S04/lwc/discountApprovalPanel/discountApprovalPanel.js"
    test_type: manual
    negative: false
    given: "the panel compares Discount__c against 20 through the UI API while the validation rule and the approval entry criteria compare 0.20 in formula context (assumption A35, UNVERIFIED (2026-09-19))"
    when: "one Enterprise opportunity with Discount__c entered as 20% is opened on the record page in UAT"
    then: "the panel receives the value 20, not 0.20, and the Submit button is disabled at exactly 20%"
    proof: "a screenshot of the panel at 20% with the disabled button, and the record read through the UI API"
    source: "decisions.md O-M3S04-02"
  - ac_id: AC-024.4
    req_id: REQ-024
    persona: "Release owner preparing the target-org deploy (no Salesforce permission set exercised; reads build files and the target org's metadata)"
    sandbox: "UNVERIFIED (2026-10-02) - not named in plan.json"
    artefact: "artefacts/M3-S05/deploy-order.md"
    test_type: manual
    negative: true
    given: "an app with its own Opportunity record page outranks the org default this build writes, and nobody has enumerated which Lightning apps expose Opportunity at Northwind (assumption A38)"
    when: "the org's CustomApplication metadata is retrieved and read before the M4 deploy, per artefacts/M3-S05/deploy-order.md section 3.1"
    then: "no app the reps use carries its own Opportunity record page assignment, or each one that does is re-pointed to Opportunity_Enterprise_Record_Page in Setup before go-live"
    proof: "the retrieved CustomApplication files and the list of apps carrying an Opportunity page assignment"
    source: "decisions.md O-M3S05-02 (operator entry, line 1368), O-M3S05-03 (renderer entry, line 1402)"
  - ac_id: AC-025.3
    req_id: REQ-025
    persona: "Release owner preparing the target-org deploy (no Salesforce permission set exercised; reads build files and the target org's metadata)"
    sandbox: "UNVERIFIED (2026-10-02) - not named in plan.json"
    artefact: "artefacts/M4-S01/deploy-order.md"
    test_type: manual
    negative: false
    given: "M4-S02's report type and column codes are provisional until the org confirms them (assumption A28, Q26)"
    when: "Phase A in artefacts/M4-S01/deploy-order.md section 2 is run against the target org before M4-S02 deploys"
    then: "the org's report folders and the SMB pipeline report's report type are recorded in the runbook, closing U2 (and U3 if the SMB type is standard)"
    proof: "the Phase A retrieve output and the recorded report type"
    source: "decisions.md O-M4S01-02"
  - ac_id: AC-025.4
    req_id: REQ-025
    persona: "Release owner preparing the target-org deploy (no Salesforce permission set exercised; reads build files and the target org's metadata)"
    sandbox: "UNVERIFIED (2026-10-02) - not named in plan.json"
    artefact: "artefacts/M4-S01/deploy-order.md"
    test_type: manual
    negative: true
    given: "a report on a custom report type created in the same deployment cannot be validated by checkOnly (N4-F-06), and the six column codes stay provisional until the org confirms them"
    when: "the M4 deploy is split - Group, ReportType, folders and the M1-S01 fields first - and a throwaway report is retrieved and compared before the Report and Dashboard deploy"
    then: "section 4's confirmed-code column in artefacts/M4-S01/deploy-order.md is filled for every code, any replaced code reaches M4-S02 through a rebuild rather than a hand edit, and the record-type criterion code is present in the report - it never ships absent"
    proof: "the filled confirmed-code column, the retrieved throwaway report, and the deployed report's filter"
    source: "decisions.md O-M4S01-01, O-M4S01-03, O-M4S02-03, O-M4S02-05"
    also_serves: "REQ-026"
  - ac_id: AC-026.6
    req_id: REQ-026
    persona: "P-MGR - Enterprise manager: profile Sales User with the org's Sales Cloud permission set plus Enterprise_Sales_Record_Types; role Enterprise Manager (above Enterprise Rep, Q19); member of the Enterprise_Managers public group"
    sandbox: "UNVERIFIED (2026-10-02) - not named in plan.json"
    artefact: "artefacts/M4-S02/reports/Enterprise_Sales/Open_Enterprise_Pipeline_By_Stage.report-meta.xml"
    test_type: manual
    negative: false
    given: "Q4 implies a public Opportunity org-wide default and forbids tightening it, Q24 asks that each manager sees only their own reps' pipeline on the report, and the report carries no scope element (D7)"
    when: "the target org's Opportunity org-wide default is read and a manager runs the open-pipeline report"
    then: "the org-wide default is recorded; if it is public, the report shows each manager the whole Enterprise pipeline and a human ranks Q4 against Q24 before go-live (artefacts/M4-S02/deploy-order.md section 8); if it is private, the manager sees only their own reps' open deals"
    proof: "the Opportunity org-wide default as read, and the report's row owners for P-MGR"
    source: "decisions.md O-M4S02-01, O-M4S02-06"
  - ac_id: AC-026.7
    req_id: REQ-026
    persona: "Release owner preparing the target-org deploy (no Salesforce permission set exercised; reads build files and the target org's metadata)"
    sandbox: "UNVERIFIED (2026-10-02) - not named in plan.json"
    artefact: "artefacts/M4-S02/dashboards/Enterprise_Sales/Enterprise_Pipeline.dashboard-meta.xml"
    test_type: manual
    negative: true
    given: "the dashboard ships as SpecifiedUser with no runningUser element, and the VP's username is not on file in any source (assumption A29)"
    when: "the deploy copy of the dashboard is prepared for a target org"
    then: "runningUser carries the VP's username for that org, or the gate records the decision to use a service user - never the deploying user's, which the platform substitutes when the element is absent"
    proof: "the deploy copy's runningUser element and the username it names"
    source: "decisions.md O-M4S02-02, O-M4S02-07"
  - ac_id: AC-026.8
    req_id: REQ-026
    persona: "P-OPS - the sales-ops admin seat holding the Sales_Ops_Validation_Bypass permission set (the one person Q13 allows past the rules); its profile is recorded in permission_setup; then P-MGR checks folder access"
    sandbox: "UNVERIFIED (2026-10-02) - not named in plan.json"
    artefact: "artefacts/M4-S02/groups/Enterprise_Managers.group-meta.xml"
    test_type: manual
    negative: false
    given: "the Enterprise_Managers public group ships with no members because Group metadata carries no membership (assumption A32)"
    when: "the sales-ops admin adds the members after deploy"
    then: "the group holds the two Enterprise managers and the VP, and P-MGR can open the Enterprise_Sales report and dashboard folders"
    proof: "the group's member list, and P-MGR's view of both folders"
    source: "decisions.md O-M4S02-11"
  - ac_id: AC-024.5
    req_id: REQ-024
    persona: "Sales-ops admin preparing the deploy copy, the owner O-M4S04-01 records (no Salesforce permission set exercised; retrieves the target org's metadata)"
    sandbox: "UNVERIFIED (2026-10-02) - not named in plan.json"
    artefact: "artefacts/M3-S05/objects/Opportunity/Opportunity.object-meta.xml"
    test_type: manual
    negative: true
    given: "M3-S05 ships a two-element Opportunity object file (the two View actionOverrides), and admin/object-creation-and-design Gotcha 10 says a partial object file replaces the whole object definition on deploy - UNVERIFIED (2026-10-02): no validate-only run can settle it"
    when: "the deploy copy for request 1 is prepared"
    then: "CustomObject:Opportunity has been retrieved alone from the target org and the two actionOverrides merged into it in the deploy copy before request 1 starts, the artefact file itself is unchanged, and no request carries the two-element file unmerged"
    proof: "the retrieved Opportunity object file and the merged deploy copy, recorded before request 1"
    source: "decisions.md O-M4S04-01, O-M4S04-05"
  - ac_id: AC-004.4
    req_id: REQ-004
    persona: "The VP and the Sales Operations lead, who settle the stage mapping (O-M4S04-02); the update runs from the seat holding the Sales_Ops_Validation_Bypass permission set where it moves a product-less deal into a gated stage"
    sandbox: "UNVERIFIED (2026-10-02) - not named in plan.json"
    artefact: "artefacts/M4-S04/deploy-order.md"
    test_type: manual
    negative: true
    given: "none of the generic pipeline's open stages exists in Enterprise_Sales_Process, values missing from the new record type are cleared on a record-type change (admin/record-types-and-page-layouts Gotcha 1), and mapping them fires M2-S04's product gate on about twenty product-less deals (Q16)"
    when: "the VP and the Sales Operations lead settle the stage mapping before P-8 and the one-time update reassigns the roughly 140 open deals Q8 names to the Enterprise record type"
    then: "every reassigned deal carries a mapped Enterprise stage rather than a cleared one, the count the runbook's SOQL returned is recorded beside the mapping, and every save that passed the product gate through the bypass carries a Chatter post on the record (Q17)"
    proof: "the recorded mapping and SOQL count, the reassigned deals' Stage values after the update, and the Chatter posts on bypassed saves"
    source: "decisions.md O-M4S04-02, O-M4S04-06"
    also_serves: "REQ-019"
  - ac_id: AC-024.6
    req_id: REQ-024
    persona: "An SMB-team user without the Enterprise_Sales_Record_Types permission set (profile not on file; recorded at the run)"
    sandbox: "UNVERIFIED (2026-10-02) - not named in plan.json"
    artefact: "artefacts/M3-S05/objects/Opportunity/Opportunity.object-meta.xml"
    test_type: manual
    negative: true
    given: "the org-default record page M3-S05 activates has no record-type dimension (D-M3S05-01), the discount approval panel carries no record-type check, and requirement.md item 6 asks that the SMB team be left alone"
    when: "an SMB-team user opens an Opportunity of the SMB record type after deploy"
    then: "the record opens on a page other than Opportunity_Enterprise_Record_Page, through an app-level assignment scoped to the Enterprise record type, unless the VP's acceptance that SMB records open the Enterprise page is on record from A-8"
    proof: "the A-8 decision record, and the SMB record's page as the SMB-team user sees it after deploy"
    source: "decisions.md O-M4S04-03, O-M4S04-07"
```

