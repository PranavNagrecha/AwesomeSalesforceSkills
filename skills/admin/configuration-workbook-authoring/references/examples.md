# Examples — Configuration Workbook Authoring

These are workbook *excerpts* — never the whole 10-section file. Each excerpt
shows the row schema in action so authors can see how `source_req_id`,
`recommended_agent`, and `recommended_skills[]` get populated.

---

## Example 1: Sales Cloud Greenfield — Objects + Fields Section

**Context:** Greenfield Sales Cloud rollout for a manufacturing distributor.
Fit-gap analysis surfaced a need for a custom `Account_Plan__c` object plus
two new fields on Opportunity for ATV (Annual Target Volume) and Renewal
Probability. Three user stories drive these (US-2031 plan tracking, US-2032
pipeline target, US-2033 renewal forecast).

**Problem:** Without a structured workbook, the BA hands the admin a Notion
page with bullet points. The admin builds Account_Plan__c with the wrong
parent relationship, picks an inconsistent suffix on the Opportunity fields,
and skips the External ID required by the integration team.

**Solution (workbook excerpt):**

```markdown
## Section 1 — Objects + Fields

| row_id | target_value | owner | source_req_id | source_story_id | recommended_agent | recommended_skills | status | notes |
|---|---|---|---|---|---|---|---|---|
| CWB-OBJ-001 | New custom object `Account_Plan__c`. Master-detail to Account. Auto Number name `AP-{YYYY}-{0000}`. | A. Singh | FG-014 | US-2031 | object-designer | admin/object-creation-and-design; admin/custom-field-creation; data/external-id-strategy | proposed | Cite `templates/admin/naming-conventions.md` for label set. |
| CWB-OBJ-002 | New field `Account_Plan__c.External_Id__c` Text(40), unique, case-insensitive, External ID. | A. Singh | FG-014 | US-2031 | object-designer | data/external-id-strategy; admin/custom-field-creation | proposed | Required for upsert from CRMA pipeline. |
| CWB-OBJ-003 | New field `Opportunity.Annual_Target_Volume__c` Currency(16,2). | A. Singh | FG-015 | US-2032 | object-designer | admin/custom-field-creation; admin/standard-object-quirks | proposed | Confirm no existing `ATV__c` first via probe. |
| CWB-OBJ-004 | New field `Opportunity.Renewal_Probability__c` Percent(3,0), 0–100. | A. Singh | FG-016 | US-2033 | object-designer | admin/custom-field-creation; admin/formula-fields | proposed | Validation rule lives in CWB-VR-007. |
```

**Why it works:** Every row has both `source_req_id` and `source_story_id`,
exactly one `recommended_agent`, at least one entry in
`recommended_skills[]`, and a non-placeholder `status`. The
`object-designer` agent can pick up rows CWB-OBJ-001 through CWB-OBJ-004 in a
single batch — every cell it needs is on the row.

---

## Example 2: Service Cloud Expansion — Profiles + Permission Sets + PSGs Section

**Context:** Service Cloud expansion adding a Tier-2 Support persona. The
existing org has `Feat_KnowledgeReader` and `Obj_CaseEditor` Permission Sets;
fit-gap calls for adding a `Feat_OmniSupervisor` Feature PS, composing a new
PSG `Tier2Support_Bundle`, and muting `View All Cases` from the bundle for
NA-region T2 reps only.

**Problem:** The previous workbook attempt collapsed PSG composition and
muting into one row, addressed it to "the admin team" with no agent, and
didn't reference the muting decision. The permission-set-architect agent
couldn't pick it up cleanly.

**Solution (workbook excerpt):**

```markdown
## Section 3 — Profiles + Permission Sets + PSGs

| row_id | target_value | owner | source_req_id | source_story_id | recommended_agent | recommended_skills | status | notes |
|---|---|---|---|---|---|---|---|---|
| CWB-PSG-021 | New Feature PS `Feat_OmniSupervisor` granting Omni-Channel supervisor System Permissions per `templates/admin/permission-set-patterns.md`. | M. Vidal | FG-031 | US-2104 | permission-set-architect | admin/permission-set-architecture; security/permission-set-groups-and-muting | proposed | |
| CWB-PSG-022 | New PSG `Tier2Support_Bundle` composing `Obj_CaseEditor`, `Feat_KnowledgeReader`, `Feat_OmniSupervisor`. | M. Vidal | FG-031 | US-2104 | permission-set-architect | admin/permission-set-architecture; security/permission-set-groups-and-muting | proposed | Deployment order per `devops/permission-set-deployment-ordering`. |
| CWB-PSG-023 | New Muting PS `Mute_NARegion_In_Tier2Support_Bundle` muting `ViewAllCases` from the PSG. | M. Vidal | FG-032 | US-2104 | permission-set-architect | security/permission-set-groups-and-muting | proposed | Apply only when `User.RegionCode__c = NA`. |
```

**Why it works:** Each row is one configurable artifact (one PS, one PSG, one
muting PS). The permission-set-architect agent can execute them in deployment
order. None of the rows accidentally do object or sharing work — those would
be split into Objects+Fields and Sharing Settings rows.

---

## Example 3: Multi-Flow Feature — Automation Section

**Context:** A renewal-forecast feature requires two record-triggered Flows on
Opportunity (one before-save normalization, one after-save notification) plus
a scheduled Flow to roll up renewal probability into a custom report rollup
field on Account. Decision tree resolves to Flow over Apex per
`automation-selection.md` Q3.

**Problem:** A single row "Build the renewal automation" hides the three
distinct triggers, gives the flow-builder agent no decision-tree citation, and
makes it impossible to test or roll back independently.

**Solution (workbook excerpt):**

```markdown
## Section 6 — Automation (Flow / Apex / Approvals)

| row_id | target_value | owner | source_req_id | source_story_id | recommended_agent | recommended_skills | status | notes |
|---|---|---|---|---|---|---|---|---|
| CWB-AUT-041 | Record-triggered Flow `Opportunity_Renewal_BeforeSave_v1` on Opportunity, before-save, normalize Renewal_Probability__c into bucket field. | J. Park | FG-051 | US-2033 | flow-builder | flow/record-triggered-flow-patterns; flow/flow-record-save-order-interaction | proposed | Per `automation-selection.md` Q3 → Flow (no callout, no DML beyond same-record). |
| CWB-AUT-042 | Record-triggered Flow `Opportunity_Renewal_AfterSave_Notify_v1` on Opportunity, after-save, send custom notification to Owner when Renewal_Probability__c crosses 60%. | J. Park | FG-052 | US-2033 | flow-builder | flow/record-triggered-flow-patterns; flow/fault-handling | proposed | Fault path required; cite `templates/flow/FaultPath_Template.md`. |
| CWB-AUT-043 | Scheduled Flow `Account_Renewal_Rollup_Daily_v1`, runs nightly, rolls up max(Renewal_Probability__c) of open Opportunities into Account.Best_Renewal_Probability__c. | J. Park | FG-053 | US-2033 | flow-builder | flow/scheduled-flows; flow/flow-bulkification | proposed | Confirm RSF alternative not viable in CWB-OBJ note; rollup field requires Number(3,0). |
```

**Why it works:** Each Flow is its own row. Each row cites the
`automation-selection.md` decision tree branch (or links to the alternative
considered). The flow-builder agent picks up one row at a time, builds one
Flow at a time, and reports back independently per row.

---

## Anti-Pattern: The "Build Sheet" Wiki

**What practitioners do:** Author a free-text Notion or Google Doc titled
"Q2 Build Sheet" with bullet points like "add Account Plan object", "PSGs
for tier 2", "renewal flow stuff". No row IDs, no `source_req_id`, no agent
field.

**What goes wrong:** The doc is untestable. The admin reads it, builds what
they think it means, and the QA team approves what they think *that* means.
Six months later nobody can answer "which fit-gap row drove this field?". The
RTM is fiction.

**Correct approach:** Use the row schema. If a change is too vague to write
as a single row with all canonical fields populated, it is not yet ready for
the workbook — it goes back to the BA as a fit-gap clarification.
