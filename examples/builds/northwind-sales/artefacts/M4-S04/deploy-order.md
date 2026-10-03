# Deploy order and go-live cutover runbook: northwind-sales, M1–M4

Build: `northwind-sales` · Step: `M4-S04` (`docs`, owner `metadata-builder`) · Manifest: `artefacts/M4-S04/package.xml`
(23 types, 38 members, API 62.0, no wildcards) · Written 2026-10-02

`agents/metadata-builder` wrote this note under Step 7 of its playbook. **It is text for a human.** No agent and no
acceptance test runs any command in it. This agent ran no `sf` command and no `scripts/mock_deploy.py`.

**Commands in this file.** Exactly one command validates anything: `scripts/mock_deploy.py`, in § 10. It hard-codes
`--dry-run` (`checkOnly: true`), and a human passes no such flag to it because there is none to pass. Its `--help` says:
"There is no flag to disable --dry-run and no --deploy option; that is by design." The `sf project retrieve start` and
`sf org list metadata` lines and the SOQL in §§ 5–6 read the org and write nothing to it. They are the
retrieve-and-grep checks this step's acceptance tests 7 and 11 ask for. **This file writes no deploy command.** The
real deploy is the release owner's, done with the team's own tool (`admin/change-management-and-deployment`,
Deployment Method Decision Matrix), and § 9 lists what they must decide first.

---

## 0. How to read this runbook

| Phase | When | What | Section |
|---|---|---|---|
| A: pre-deploy checks | Before the rehearsal, and again before the window | Seventeen read-only checks and decisions, each with an owner | § 5 |
| E: deploy-copy edits | Before the rehearsal | Four files change in the copy that is deployed. The build's artefacts do not change. | § 2 |
| R: rehearsal | In a sandbox, before the window | Validate the build, then the deploy copy, with `scripts/mock_deploy.py` | § 10 |
| D1: request 1 | The window | 36 members: all of M1–M3, plus M4's group, report type and two folders | §§ 3–4 |
| B: between the halves | Straight after request 1 | Confirm the report column codes; insert the dashboard's running user | § 5, items B-1 and B-2 |
| D2: request 2 | After phase B | 2 members: the report, then the dashboard | §§ 3–4 |
| P: post-deploy | After request 2 | Permission-set assignments, group membership, process order, the 140-deal reassignment | § 6 |
| U: UAT | After the first deploy | The four negative cases this step carries, plus the positive checks | § 7 |

**Owners.** The plan names roles, not people, except the requester. Put a person against each role before the window.

| Role | Who, per the plan | Owns |
|---|---|---|
| VP Sales Operations | Pranav, the requester (`requirement.md`) | Every decision this file leaves open |
| Sales Operations lead | `owner_role` on Q8, Q13, Q16, Q19 and Q26 | User data, the report codes, the reassignment's stage mapping |
| Sales-ops admin | The one admin `requirement.md` names. Holds System Administrator (Q19) and is the only bypass holder (Q13). | Setup clicks, assignments, group membership, the reassignment run |
| Release owner | Named in acceptance test 4; "the person deploying" in `artefacts/M4-S02/deploy-order.md` B4 | The retrieves, the deploy copy, the rehearsal, both requests |

`UNVERIFIED (2026-10-02):` no person is on file for the release owner. At Northwind it may well be the sales-ops admin,
the only admin the requirement names. One person may hold two roles. Each row still needs a name.

---

## 1. What the manifest contains

The build-level `package.xml` is the union of the eleven step manifests. It also carries the members of the two
steps that declare no manifest:

| Type | Members | From |
|---|---|---|
| `StandardValueSet` | `OpportunityStage` | M1-S01 |
| `CustomField` | `Opportunity.Approval_Status__c`, `Opportunity.Discount__c` | M1-S01 |
| `BusinessProcess` | `Opportunity.Enterprise_Sales_Process`, `Opportunity.Renewal_Sales_Process` | M1-S01 |
| `RecordType` | `Opportunity.Enterprise`, `Opportunity.Renewal` | M1-S01 |
| `Layout` | `Opportunity-Opportunity Enterprise Layout`, `Opportunity-Opportunity Renewal Layout` | M1-S02 |
| `CustomPermission` | `Bypass_Opportunity_Sales_Validation` | M2-S01 |
| `PermissionSet` | `Sales_Ops_Validation_Bypass` (M2-S01), `Enterprise_Sales_Record_Types` (M2-S02) | M2-S01, M2-S02 |
| `Profile` | `Sales User` (an overlay) | M2-S02 |
| `ValidationRule` | `Opportunity.Opportunity_Discount_Requires_Approval` (M2-S03), `Opportunity.Opportunity_Products_Required_At_Propose` (M2-S04) | M2-S03, M2-S04 |
| `PathAssistant` | `Enterprise_Opportunity_Path`, `Renewal_Opportunity_Path` | M2-S05 |
| `Settings` | `PathAssistant` | M2-S05 |
| `EmailFolder` | `Sales_Approvals` | M3-S01 |
| `EmailTemplate` | `Sales_Approvals/Discount_Approval_Request`, `…/Discount_Approved`, `…/Discount_Rejected` | M3-S01 |
| `Workflow` | `Opportunity` (2 alerts, 4 field updates) | M3-S02 |
| `ApprovalProcess` | `Opportunity.Discount_Approval` (active, D9) | M3-S02 |
| `ApexClass` | `OpportunityApprovalController`, `OpportunityApprovalService`, `OpportunityApprovalServiceTest`, `OpportunityApprovalSubmitAction`, `TestDataFactory` | **M3-S03, which declares no manifest** (§ 5, "The Apex exception") |
| `LightningComponentBundle` | `discountApprovalPanel` | **M3-S04, which declares no manifest** (§ 4, borrowed-agent condition 2) |
| `FlexiPage` | `Opportunity_Enterprise_Record_Page` | M3-S05 |
| `CustomObject` | `Opportunity` (the two `actionOverrides` only) | M3-S05 |
| `Group` | `Enterprise_Managers` | M4-S02 |
| `ReportType` | `Enterprise_Opportunity_Pipeline` | M4-S02 |
| `Report` | `Enterprise_Sales` (folder), `Enterprise_Sales/Open_Enterprise_Pipeline_By_Stage` | M4-S02 |
| `Dashboard` | `Enterprise_Sales` (folder), `Enterprise_Sales/Enterprise_Pipeline` | M4-S02 |

**This is the set the org has already validated.** `reports/mock-deploy/2026-10-02T18-04-04Z/summary.md` (MOCK-DEPLOY-M4
run 3, source mode, M1–M4) reports 44 components. These 38 members account for all 44: `Workflow:Opportunity` adds
two `WorkflowAlert` and four `WorkflowFieldUpdate`. 43 were accepted, and the Report and the Dashboard failed for the
reason in § 4 (N4-F-06). `reports/MILESTONE-M3-package.xml` lacks the six Apex and LWC members, because no step
manifest declared them. That gap is why MOCK-DEPLOY-M3 run 2, in manifest mode, failed with "We couldn't retrieve the
design time component information for component c:discountApprovalPanel". This file closes that gap. The first
manifest-mode run that reads a manifest carrying the bundle and the Apex is the § 10 rehearsal.

**M2-S04's rule is a member, exactly once, at the validation-rule position (§ 3 row 9), after M2-S01's custom
permission (row 5).** `plan.json` `steps[M4-S04].inputs` still lists "M2-S04 (excluded, blocked)", and its note says
M2-S04 "is listed as excluded with its blocked reason verbatim". That prose is stale. M2-S04 was unblocked on
2026-09-15 and is `documented`. MOCK-DEPLOY-M2 run 3 validated the rule (18/18). This step's acceptance test 5,
amended at 2026-10-02T18:52:18Z, requires the rule to appear once, with its file behind it. The amended test and the
step's real status win over the stale input note. **Nothing is excluded from this build.**

**Steps that produce documents, not components.** M4-S01 (the report-code probe runbook) and M4-S03 (the workbook,
traceability, acceptance criteria and UAT pack) contribute no members.

**No deletions.** No `destructiveChangesPre.xml` or `destructiveChangesPost.xml` exists. Nothing in this build retires
a component.

**Member forms**, each copied from the step manifests the org accepted. Object-qualified: `CustomField`,
`BusinessProcess`, `RecordType`, `ValidationRule`, `ApprovalProcess`. `Layout` is the object, a hyphen, then the layout
name, with literal spaces. `EmailTemplate` is `Folder/Name`, and its folder is its own `EmailFolder` member. Report and
dashboard folders are bare members of `Report` and `Dashboard`, because `describeMetadata()` has no `ReportFolder` type
(`admin/reports-and-dashboards` `references/metadata-examples.md` § 5). `Settings` is `PathAssistant`, because feature
settings take no wildcard (`admin/opportunity-management` `references/metadata-examples.md` § 5).

`UNVERIFIED (2026-10-02):` the `Dashboard` folder-as-bare-member form has not been validated in manifest mode. MOCK-DEPLOY-M4
ran in source mode only, where the org named it `DashboardFolder Enterprise_Sales` and accepted it. The form is
grounded in the skill reference above. The § 10 rehearsal is its first manifest-mode test.

**A deploy manifest, never a retrieve manifest.** It names `Profile` and `PermissionSet` beside `CustomObject`.
Retrieved together, the object rewrites the profile files (`admin/object-creation-and-design` `references/gotchas.md`
Gotcha 10; `artefacts/M2-S02/deploy-order.md` § 4).

---

## 2. Four files differ between this build and what is deployed

This build ships four files that cannot be deployed as they stand. The edits are made in the **deploy copy**: the
release owner's own Salesforce DX project, outside `.sfskills/builds/northwind-sales/`. They are never made in
`artefacts/`. A tested artefact changes only through a rebuild of its step.

| # | File in the deploy copy | Edit | Why | Owner | Phase |
|---|---|---|---|---|---|
| E1 | `standardValueSets/OpportunityStage.standardValueSet-meta.xml` (M1-S01) | Retrieve the org's file. Write back the **union** of its active values and the 8 shipped ones. | The shipped file holds only the 8 new stages. For a value set, an omitted value is deactivated, which would strip the SMB pipeline of its stages. D1, A24 (risk high), O-M1S01-01; `artefacts/M1-S01/deploy-order.md` § 0. | Release owner | A-3 |
| E2 | Both `layouts/Opportunity-Opportunity … Layout.layout-meta.xml` files (M1-S02) | Paste the Opportunity Products `<relatedLists>` element verbatim, from a retrieve of the org's current Opportunity layout. | Neither layout carries a related list. The API name is a retrieval alias that no skill documents. A26, REQ-010, O-M1S02-01; `artefacts/M1-S02/deploy-order.md` § 0. | Release owner | A-4 |
| E3 | `objects/Opportunity/Opportunity.object-meta.xml` (M3-S05) | Retrieve the org's object file. Add the two `View` `actionOverrides` (Large and Small) to it, and deploy that merged file. | **New in this step.** `admin/object-creation-and-design` `references/gotchas.md` Gotcha 10: "a partial object file overwrites rather than merges … A file trimmed down to the two elements someone wanted to change is a full replacement of the object definition with those two elements" (api_meta L41900–41901). M3-S05's own header says the file "changes no other Opportunity configuration". That contradicts the gotcha, and a validate-only run cannot settle it (§ 8). | Release owner | A-5 |
| E4 | `dashboards/Enterprise_Sales/Enterprise_Pipeline.dashboard-meta.xml` (M4-S02) | Insert `<runningUser>` with the VP's username **in the target org**, between `</rightSection>` and `<textColor>`. | Without it the platform fills in whoever runs the deploy. There is no error and no warning. A29, O-M4S02-02, O-M4S02-07; `artefacts/M4-S02/deploy-order.md` § 6. Do not commit a username to the build. | Sales-ops admin, with the VP's username from the VP | B-2 |

Four merge rules. Each is easy to get wrong:

- **E1, the default.** Keep the org's existing `<default>true</default>` exactly where it is. All 8 shipped values
  carry `false` on purpose (D-M1S01-01). Exactly one value in the merged file may be `true`. Retire a value with
  `<isActive>false</isActive>`; never delete the element (`admin/picklist-and-value-sets` Gotcha 10, cited in M1-S01 § 0).
- **E1, the two shared values.** `Closed Won` (Closed, 100, won) and `Closed Lost` (Omitted, 0) exist in the org
  already, and SMB uses them. Each must appear once. If the org's attributes differ from the shipped ones, the merged
  file decides SMB's forecast too. Keep the org's attributes unless the VP decides otherwise (`requirement.md` item 6).
- **E3, overrides already in the org.** If the retrieved object already has a `View` override for `Large` or `Small`,
  this build replaces it. Record the replaced page under "Overrides being deleted"
  (`admin/lightning-record-page-configuration` template § 2), and have the VP confirm.
- **E3, the retrieve itself.** Retrieve `CustomObject:Opportunity` on its own, never in the same request as `Profile`
  or `PermissionSet`. Otherwise the retrieve rewrites the profile files (Gotcha 10, second half).

**The deploying project also needs a `.forceignore` that excludes `**/__tests__/**`.** Without it, the org compiles
the bundle's Jest file as a module and rejects it with thirteen `LWC1503` errors (N3-F-07, MOCK-DEPLOY-M3 run 3).
`scripts/mock_deploy.py` writes that file for its own runs, but a release owner's project does not get it for free.
Owner: the release owner, at A-16.

**Two more edits may follow, but neither is a deploy-copy edit.** A report column code that phase B replaces goes
into M4-S02 through a rebuild (`documented → running`), never by hand (`artefacts/M4-S01/deploy-order.md` § 3 step 4).
The same applies to any change the VP decides at A-7 or A-8 (a FlexiPage or an app assignment).

---

## 3. Deploy order across the four milestones

Inside one request the platform resolves references by itself
(`admin/opportunity-management` `references/metadata-examples.md` § 7). The order below matters in three cases: when
a request is split, when a failure is triaged, and when the release owner deploys milestone by milestone.

| # | Component(s) | Step | Must come after | Why |
|---|---|---|---|---|
| 1 | `StandardValueSet:OpportunityStage` (**merged, E1**) | M1-S01 | E1 | A stage must exist globally before a sales process can list it (`admin/opportunity-management` Gotcha 6, `metadata-examples.md` § 7). |
| 2 | `CustomField` `Discount__c`, `Approval_Status__c` | M1-S01 | — | The data model goes first, and everything that references it after (`admin/change-management-and-deployment` `llm-anti-patterns.md` Anti-Pattern 4). Every later row names these fields. |
| 3 | `BusinessProcess` ×2 | M1-S01 | 1 | Each value is a stage from row 1. Neither process carries `<default>` (N3-F-01; `admin/opportunity-management` Gotcha 17). |
| 4 | `RecordType` ×2 | M1-S01 | 3 | `<businessProcess>` must resolve (`artefacts/M1-S01/deploy-order.md` § 1). |
| 5 | `CustomPermission:Bypass_Opportunity_Sales_Validation` | M2-S01 | — | It must precede the permission set that grants it and both rules that read it. A `$Permission` token with no permission behind it evaluates to false silently, so nobody can bypass (`artefacts/M2-S01/deploy-order.md` §§ 1–2; `admin/custom-permissions` Gotcha 4). |
| 6 | `PermissionSet` `Sales_Ops_Validation_Bypass`, `Enterprise_Sales_Record_Types` | M2-S01, M2-S02 | 5; 2 and 4 | The bypass set grants row 5. The record-types set grants rows 4 and 2 (record-type visibility, plus FLS on both fields, D-M2S02-03). |
| 7 | `Layout` ×2 (**with the related list, E2**) | M1-S02 | 2, E2 | Layout items name both fields (`artefacts/M1-S02/deploy-order.md` § 1). The related list goes in first (A26, REQ-010). |
| 8 | `Profile:Sales User` | M2-S02 | 4, 7 | `layoutAssignments` names the layouts in file-name form and the record types (`artefacts/M2-S02/deploy-order.md` § 2). It is an overlay: it carries layout assignments only (D-M2S02-02). |
| 9 | `ValidationRule` `Opportunity_Discount_Requires_Approval`, then `Opportunity_Products_Required_At_Propose` | M2-S03, **M2-S04** | 1, 2, 4, 5 | Every formula token must resolve at deploy (`artefacts/M2-S03/deploy-order.md` § 2; `artefacts/M2-S04/deploy-order.md` § 3). Both rules come after M2-S01's custom permission (row 5). That is acceptance test 5's position. |
| 10 | `PathAssistant` ×2, then `Settings:PathAssistant` | M2-S05 | 1, 2, 3, 4 | `recordTypeName` and `picklistValueName` match by exact string. The setting goes last, so nobody sees a half-built path (`artefacts/M2-S05/deploy-order.md` §§ 1–2). |
| 11 | `EmailFolder:Sales_Approvals`, then `EmailTemplate` ×3 | M3-S01 | — | A template is addressed through its folder (`artefacts/M3-S01/deploy-order.md` § 2). |
| 12 | `Workflow:Opportunity` (2 alerts, 4 field updates) | M3-S02 | 2, 11 | An alert's template must already exist in the org (`artefacts/M3-S02/deploy-order.md` § 2; `admin/approval-processes`, "Approval Actions Are Workflow Actions"). |
| 13 | `ApprovalProcess:Opportunity.Discount_Approval` (active) | M3-S02 | 2, 4, 11, 12 | It names six workflow actions and one template. It ships `active` true (D9, A36), and activation freezes its step structure (`admin/approval-processes` gotchas). |
| 14 | `ApexClass` ×5 | M3-S03 | 2, 13 | The service queries both fields. The test submits to `Discount_Approval` by name. MOCK-DEPLOY-M3 run 5 validated rows 1–17 together: 6/6 tests, 95.6% coverage. |
| 15 | `LightningComponentBundle:discountApprovalPanel` | M3-S04 | 14, A-16 | It imports `OpportunityApprovalController.submitForApproval`. The deploying project needs the `.forceignore` (N3-F-07). |
| 16 | `FlexiPage:Opportunity_Enterprise_Record_Page` | M3-S05 | 10, 15 | `c:discountApprovalPanel` must resolve (MOCK-DEPLOY-M3 runs 2 and 4). |
| 17 | `CustomObject:Opportunity` (**merged, E3**) | M3-S05 | 16, E3 | The override's `<content>` names the page. This row is the activation (`artefacts/M3-S05/deploy-order.md` § 1). |
| 18 | `Group:Enterprise_Managers` | M4-S02 | — | Both folder shares name it (`artefacts/M4-S02/deploy-order.md` § 1). |
| 19 | `ReportType:Enterprise_Opportunity_Pipeline` | M4-S02 | 2, 4 | Its section names both fields and the `RecordType` column, which was org-verified in MOCK-DEPLOY-M4 run 3. |
| 20 | `Report:Enterprise_Sales` (folder), `Dashboard:Enterprise_Sales` (folder) | M4-S02 | 18 | A folder names only the group. |
| | **End of request 1. Phase B (§ 5, B-1 and B-2) runs here.** | | | |
| 21 | `Report:Enterprise_Sales/Open_Enterprise_Pipeline_By_Stage` | M4-S02 | 19 **deployed for real**, 20, B-1 | **N4-F-06:** a report cannot be validated in the same deployment as its new report type (MOCK-DEPLOY-M4 run 3). |
| 22 | `Dashboard:Enterprise_Sales/Enterprise_Pipeline` (**with runningUser, E4**) | M4-S02 | 21, B-2 | Its `<report>` names row 21 (`artefacts/M4-S02/deploy-order.md` § 1). |

**Deploying milestone by milestone instead of in two requests?** Then submit each request only after the previous
one has succeeded. Queued deploys do not run in submission order (`admin/change-management-and-deployment`, "Deployment
Locks the Metadata It Is Touching"). **Keep M2 and M3 in the same window.** M2-S03's rule ships active. Without M3's
approval process, a deal above the cap has no way to Closed Won except the bypass (O-M2S03-03). Request 1 as defined
in § 4 closes that window, because both milestones land together.

---

## 4. The two requests, member by member

The M4 deploy is split, as O-M4S01-01, O-M4S02-03 and O-M4S02-05 asked the M4 gate to decide, and N4-F-06 now
requires. The report and its new report type cannot share a deployment, and the column codes are confirmed between
the halves (`artefacts/M4-S01/deploy-order.md` § 3; D-M4S01-01, D-M4S02-03).

**Request 1: 36 members.** This is `package.xml` without the two members below. It covers rows 1–20.

```text
StandardValueSet  OpportunityStage                       (merged, E1)
CustomField       Opportunity.Approval_Status__c, Opportunity.Discount__c
BusinessProcess   Opportunity.Enterprise_Sales_Process, Opportunity.Renewal_Sales_Process
RecordType        Opportunity.Enterprise, Opportunity.Renewal
CustomPermission  Bypass_Opportunity_Sales_Validation
PermissionSet     Enterprise_Sales_Record_Types, Sales_Ops_Validation_Bypass
Layout            Opportunity-Opportunity Enterprise Layout, Opportunity-Opportunity Renewal Layout   (E2)
Profile           Sales User
ValidationRule    Opportunity.Opportunity_Discount_Requires_Approval, Opportunity.Opportunity_Products_Required_At_Propose
PathAssistant     Enterprise_Opportunity_Path, Renewal_Opportunity_Path
Settings          PathAssistant
EmailFolder       Sales_Approvals
EmailTemplate     Sales_Approvals/Discount_Approval_Request, Sales_Approvals/Discount_Approved, Sales_Approvals/Discount_Rejected
Workflow          Opportunity
ApprovalProcess   Opportunity.Discount_Approval
ApexClass         OpportunityApprovalController, OpportunityApprovalService, OpportunityApprovalServiceTest,
                  OpportunityApprovalSubmitAction, TestDataFactory
LightningComponentBundle  discountApprovalPanel
FlexiPage         Opportunity_Enterprise_Record_Page
CustomObject      Opportunity                            (merged, E3)
Group             Enterprise_Managers
ReportType        Enterprise_Opportunity_Pipeline
Report            Enterprise_Sales                       (the folder only)
Dashboard         Enterprise_Sales                       (the folder only)
```

**Request 2: 2 members,** after B-1 and B-2:

```text
Report            Enterprise_Sales/Open_Enterprise_Pipeline_By_Stage
Dashboard         Enterprise_Sales/Enterprise_Pipeline   (runningUser inserted, E4)
```

The record-type filter in the report (`Opportunity$RecordType`, value `Enterprise`) must not ship without its
criterion. Without it, the "Enterprise" report and the VP's tile total every record type, SMB and Renewal included.
If B-1 cannot confirm it, request 2 waits (`artefacts/M4-S02/deploy-order.md` § 2).

---

## 5. Pre-deploy checks and decisions, in order, each with an owner

Run every retrieve in a scratch DX project outside `.sfskills/builds/northwind-sales/`, so that org files never land
in `artefacts/` (M4-S01 U5). Every command below reads the org and writes nothing to it.

| Pos. | Check or decision | Owner | Close condition | Source |
|---|---|---|---|---|
| A-1 | **Confirm the Opportunity org-wide default.** If it is public, Q4 ("no sharing change") and Q24 ("each manager sees only their own reps") conflict for the managers' report. | Sales-ops admin reads it; the VP decides if it is public | The OWD is Private, or the VP ranks Q4 against Q24 | O-M4S02-06, U12, B3; `artefacts/M4-S02/deploy-order.md` § 8 |
| A-2 | **Confirm the profile's exact `Name` is `Sales User`**, with the space | Sales-ops admin | The name matches, or M2-S02 is rebuilt with the real name | O-M2S02-03 |
| A-3 | **Retrieve and merge `OpportunityStage` (E1).** `sf project retrieve start --metadata "StandardValueSet:OpportunityStage" --target-org <alias>` | Release owner; the VP signs off any difference on `Closed Won` / `Closed Lost` | The merged file holds every active org value plus the 8 new ones, with the org's default unchanged | D1, A24, O-M1S01-01; `artefacts/M1-S01/deploy-order.md` § 0 |
| A-4 | **Retrieve the Opportunity Products related list and copy it into both layouts (E2).** `sf project retrieve start --metadata "Layout:Opportunity-Opportunity Layout" --target-org <alias>`. Copy the whole `<relatedLists>` element verbatim. `UNVERIFIED (2026-10-02):` `Opportunity Layout` is the platform's default layout name. If the SMB layout has another name, list layouts first (`sf org list metadata --metadata-type Layout --target-org <alias>`). | Release owner | Both deploy-copy layouts carry the block. The M4 gate records **REQ-010 as covered by this runbook step, not by metadata.** | A26, REQ-010, O-M1S02-01; acceptance test 7 |
| A-5 | **Retrieve `CustomObject:Opportunity` alone and merge the two `actionOverrides` (E3).** `sf project retrieve start --metadata "CustomObject:Opportunity" --target-org <alias>`. Never in the same request as `Profile`. | Release owner; the VP confirms any replaced override | The deploy copy's `Opportunity.object-meta.xml` is the retrieved file plus the two `View` overrides | `admin/object-creation-and-design` Gotcha 10 |
| A-6 | **Find app-level Opportunity record-page assignments.** `sf project retrieve start --metadata "CustomApplication" --target-org <alias>`, then `grep -l -E "actionOverrides|profileActionOverrides" force-app/main/default/applications/*.app-meta.xml` and `grep -B 2 -A 8 "Opportunity" force-app/main/default/applications/*.app-meta.xml`. For each hit, delete the entry or re-point it at `Opportunity_Enterprise_Record_Page`. Either way it is a `CustomApplication` deploy this build does not contain. | Sales-ops admin; the VP decides delete or re-point | Every app over Opportunity is listed, with a decision against each | A38, O-M3S05-02; `artefacts/M3-S05/deploy-order.md` § 3.1 |
| A-7 | **Grep the page a Renewal record lands on for the Path component.** The org default written by M3-S05 has no record-type dimension (D-M3S05-01). So a Renewal record opens `Opportunity_Enterprise_Record_Page`, unless an A-6 hit outranks it. That page carries `runtime_sales_pathassistant:pathAssistant` (its `subheader` region, in the build's file). For any page A-6 found: `sf project retrieve start --metadata "FlexiPage" --target-org <alias>`, then `grep -rl "runtime_sales_pathassistant:pathAssistant" force-app/main/default/flexipages/`. **If the component is absent,** the VP decides between two options: add it to that page (a FlexiPage change this build does not contain), or accept that the Renewal Path does not render there. | Sales-ops admin runs it; the VP decides | Each page a Renewal record can land on either carries the component, or the decision not to render is recorded | O-M2S05-04, O-M3S05-03; acceptance test 11 |
| A-8 | **Decide what SMB users should see.** For the same reason as A-7, an SMB Opportunity opens the Enterprise page unless an A-6 hit outranks it. On that page it renders the Path component (no SMB path exists, so no stages show: UAT 9) and the discount panel. The panel has no record-type gate (`artefacts/M3-S04/lwc/discountApprovalPanel/`). `UNVERIFIED (2026-10-02):` what the panel shows an SMB user. The 14 Enterprise users get FLS on its two fields through `Enterprise_Sales_Record_Types`; SMB users get none from this build. | The VP | The VP accepts the Enterprise page for SMB records, or asks for an app-level assignment (a plan change) | `requirement.md` item 6; D-M3S05-01; `artefacts/M3-S05/deploy-order.md` § 3.2 |
| A-9 | **Every Enterprise and Renewal opportunity owner has a `Manager`.** A blank Manager makes a submission fail at run time, and no deploy catches it. Check the 12 reps, and the 2 managers if they own deals: `SELECT Id, Name, UserRole.Name, ManagerId FROM User WHERE IsActive = true AND UserRole.Name IN ('Enterprise Rep', 'Enterprise Manager')`. `UNVERIFIED (2026-10-02):` the role names come from Q19's wording, not from the org. | Sales Operations lead | Every row has a `ManagerId`, or a fallback is added as a step | O-M3S02-01; `artefacts/M3-S02/deploy-order.md` § 5; `admin/approval-processes`, "Blank Approver Fields Fail at Runtime" |
| A-10 | **No legacy automation writes `StageName`, `Amount`, `Discount__c` or `Approval_Status__c` after save.** Setup → Workflow Rules, filtered to Opportunity. | Sales-ops admin | None found, or each one is listed and accepted | A8, O-M2S03-02, Q43 (open) |
| A-11 | **Opportunity field history tracking is on.** History cannot be backfilled. | Sales Operations lead | Confirmed on in the target org | A4, O-M1S01-02, Q39 (open) |
| A-12 | **List any approval processes that already exist on Opportunity in production**, so that P-5 can set the order | Sales-ops admin | The ordered list is written down | A34, Q58 (open); `admin/approval-processes`, "A Record Enters Exactly One Process" |
| A-13 | **Report-type phase A probes:** M4-S01 § 2, A1–A4 (which report type the SMB pipeline report uses, and what shares it) | Sales Operations lead | U2 and U3 closed in M4-S01 § 7 | O-M4S01-02; `artefacts/M4-S01/deploy-order.md` § 2 |
| A-14 | **Get the VP's username for each target org,** or decide that a service user runs the dashboard | The VP; the sales-ops admin records it | A username is on hand for B-2 | A29, O-M4S02-07, U14 |
| A-15 | **Pre-release retrieve for backout.** Retrieve every component this deploy overwrites, before the window: `OpportunityStage`, `Profile:Sales User`, `CustomObject:Opportunity`, `Settings:PathAssistant`, and any existing Opportunity approval process | Release owner | The retrieve is stored at a named path | `admin/change-management-and-deployment` `references/metadata-examples.md` § 6; `templates/release-plan-template.md` |
| A-16 | **`.forceignore` in the deploying project excludes `**/__tests__/**`** | Release owner | The file is present | N3-F-07, MOCK-DEPLOY-M3 run 3 |
| A-17 | **The rehearsal keeps the Path setting.** `Settings:PathAssistant` deploys with M2-S05, here in request 1 (row 10), and sets `pathAssistantEnabled` true and `canOverrideAutoPathCollapseWithUserPref` true. Outside Enterprise Edition, `pathAssistantEnabled` defaults to false. So a scratch-org or Developer Edition rehearsal without this member **shows neither Path, and the deploy is still green.** The setting is load-bearing, not a default. Do not drop it from a rehearsal. | Release owner | The rehearsal run includes `Settings:PathAssistant` | `artefacts/M2-S05/deploy-order.md` § 3 item 1 (A12); acceptance test 13 |
| R-1 | **Rehearse: validate the build** (§ 10, command 1). This also re-runs A25's discovery of the layout-required fields against this org. Expect no "Layout must contain an item for required layout field" and no "Field:… must be Required" message. MOCK-DEPLOY-M1 runs 1–4 settled Probability present and Name, StageName and CloseDate Required, on `sfskills-dev`. | Release owner | Exactly the two expected errors in § 10, and 6/6 tests | A25; MOCK-DEPLOY-M1 runs 1–4; O-M1S02-04 |
| R-2 | **Rehearse: validate the deploy copy** (§ 10, command 2). It patches E1–E3 into a probe copy. | Release owner | The same two expected errors and nothing new | § 2 |
| B-1 | **Between the halves: confirm the report column codes.** Build one scratch report on `Enterprise_Opportunity_Pipeline`, retrieve it, and diff each code against M4-S02's report, as M4-S01 § 3 steps 2–7 set out. A code that changes goes into M4-S02 through a rebuild. Never guess one, and never hand-edit one. | Sales Operations lead (Q26's owner), with the release owner | Every code in M4-S01 § 4 has a confirmed value, including the record-type criterion | A28, Q26, D-M4S01-01, O-M4S01-03 |
| B-2 | **Between the halves: insert the dashboard's running user (E4)** | Sales-ops admin, with A-14's username | The deploy copy carries `<runningUser>` | A29, O-M4S02-02 |

### The nine prerequisites acceptance test 6 names, and where each sits

| Prerequisite | Position | Owner |
|---|---|---|
| Retrieve and merge `OpportunityStage` (A24) | A-3, then E1, before request 1 (row 1) | Release owner |
| Discover the layout-required fields (A25) | Settled on `sfskills-dev` by MOCK-DEPLOY-M1 runs 1–4; re-checked at R-1 | Release owner |
| Retrieve the products related-list name (A26) | A-4, then E2, before row 7 | Release owner |
| Confirm the report column codes (A28) | A-13, then B-1, between request 1 and request 2 | Sales Operations lead |
| Set the dashboard's `runningUser` (A29) | A-14, then B-2, before row 22 | Sales-ops admin |
| Populate the Enterprise Managers group (A32) | P-4, after request 2 | Sales-ops admin |
| Set approval process order (A34) | A-12, then P-5, after request 1 | Sales-ops admin |
| Reassign the ~140 open Enterprise deals (A37, Q8) | P-8, after P-1 to P-6 | Sales-ops admin; mapping decided by the Sales Operations lead and the VP |
| Record every bypass use in Chatter (Q17) | P-9, a standing control from go-live | Sales-ops admin |

---

## 6. Post-deploy steps, in order

None of these ships in any manifest. Assignment, membership, process order and record updates are data or Setup
state (`admin/change-management-and-deployment`, Questions to Ask, row 5).

| Pos. | Step | Owner | Source |
|---|---|---|---|
| P-1 | **Assign `Sales_Ops_Validation_Bypass` to the sales-ops admin, and to nobody else** (Q13). Expiry is not applied; the grant is a standing capability (O-M2S01-03). | Sales-ops admin | O-M2S01-01; `artefacts/M2-S01/deploy-order.md` § 4 |
| P-2 | **Assign `Enterprise_Sales_Record_Types` to the 12 reps and 2 managers.** The assignment-count query in `artefacts/M2-S02/deploy-order.md` § 8 should then show 14. The sales-ops admin needs neither this set nor a row for it (A39). | Sales-ops admin | Q19; `artefacts/M2-S02/deploy-order.md` § 8 |
| P-3 | **Prove who holds the bypass**, then read `PermissionSet.IsOwnedByProfile` on each row. `true` means the grant came through a profile (O-M2S01-04). The query below is copied from `admin/custom-permissions` `references/metadata-examples.md`, "Verification", with the permission's name substituted. Expect exactly one assignee. | Sales-ops admin | O-M2S01-01, O-M2S01-04 |
| P-4 | **Add the two Enterprise managers and the VP to the `Enterprise Managers` public group.** Until then, only the folder owner and administrators can open either folder. | Sales-ops admin | A32, O-M4S02-11; `artefacts/M4-S02/deploy-order.md` § 5 |
| P-5 | **Set the approval process order** in Setup → Process Automation → Approval Processes, filtered to Opportunity, using A-12's list. Order decides which process the standard Submit for Approval button enters. The Apex names `Discount_Approval` explicitly and is unaffected. | Sales-ops admin | A34; `artefacts/M3-S02/deploy-order.md` § 4 |
| P-6 | **Verify the stage ladder and the record types.** Run the two SOQL queries in `artefacts/M1-S01/deploy-order.md` § 4. Open one Enterprise and one Renewal record **as a rep**, and confirm the new stages appear in each record type's picklist (M1-S01 § 3 item 1). Record which stage a new record opens on (O-M1S01-04). | Sales-ops admin | O-M1S01-04; `artefacts/M1-S01/deploy-order.md` §§ 3–4 |
| P-7 | **Verify the dashboard and the rules.** `SELECT DeveloperName, Title, Type, RunningUserId, FolderName FROM Dashboard WHERE FolderName = 'Enterprise Sales'` should return `Type` = `SpecifiedUser` and the VP's Id, not the deployer's. Both validation rules should read `Active` (the Tooling query in `admin/validation-rules` `references/metadata-examples.md`, "Verification after deploy"). | Sales-ops admin | `artefacts/M4-S02/deploy-order.md` § 6; `artefacts/M2-S03/deploy-order.md` § 8 |
| P-8 | **Reassign the ~140 open Enterprise deals to the `Enterprise` record type** (a one-time data update, Q8). See the box below before running it. | Sales-ops admin runs it; the Sales Operations lead and the VP decide the mapping | A37, Q8; `admin/record-types-and-page-layouts` Gotcha 1 |
| P-9 | **Standing control from go-live: every use of the bypass gets a Chatter post on the record, saying why** (Q17). No metadata can enforce this; it is a human control. `UNVERIFIED (2026-10-02):` that Chatter and Opportunity feeds are enabled in Northwind's org. No step in this build configures them. | Sales-ops admin | Q17; `artefacts/M2-S01/deploy-order.md` § 4 |
| P-10 | **Optional: Path celebration on Closed Won.** It is a Setup click in production and in every later sandbox, because no metadata element carries it. | The VP decides; the sales-ops admin configures it | O-M2S05-05, A14 |

**P-3 query:**

```sql
SELECT Assignee.Name, Assignee.Username, PermissionSet.Label,
       PermissionSet.Profile.Name, PermissionSet.IsOwnedByProfile
FROM PermissionSetAssignment
WHERE PermissionSetId IN (
    SELECT ParentId FROM SetupEntityAccess
    WHERE SetupEntityType = 'CustomPermission'
      AND SetupEntityId IN (
          SELECT Id FROM CustomPermission WHERE DeveloperName = 'Bypass_Opportunity_Sales_Validation'
      )
)
```

**P-8 needs a decision before it runs. Q8's "no field mapping changes" probably cannot hold.** The Enterprise process
carries only `Qualify`, `Discover`, `Propose`, `Negotiate`, `Closed Won` and `Closed Lost`
(`artefacts/M1-S01/objects/Opportunity/businessProcesses/Enterprise_Sales_Process.businessProcess-meta.xml`). The four
open stages are new in this build. So every open deal on the generic record type carries a stage the Enterprise record
type does not offer. `admin/record-types-and-page-layouts` Gotcha 1 says such a value is cleared when the record type
changes. Its remedy: find the at-risk records, map the source values, update the picklist values before changing the
record type, and rehearse in a sandbox. In this order:

1. Export the 140 deals' `Id`, `RecordTypeId`, `StageName`, `Probability` and `ForecastCategoryName`. The export is
   the data backout, which no metadata rollback covers (`admin/change-management-and-deployment` § 6).
2. Count them by stage. This follows the shape of `admin/opportunity-management` query 8b:
   `SELECT StageName, COUNT(Id) Deals FROM Opportunity WHERE IsClosed = FALSE AND RecordType.DeveloperName = '<the generic record type>' GROUP BY StageName`.
   Then pick the 140 Enterprise deals by the criterion the Sales Operations lead uses today.
   `UNVERIFIED (2026-10-02):` the generic record type's developer name and the selection criterion are not on file.
3. The Sales Operations lead and the VP map each stage to an Enterprise stage. **This contradicts Q8's answer as
   written, and the VP must confirm it.**
4. A stage change does three things here. It recomputes `Probability` and `ForecastCategoryName`
   (`admin/opportunity-management` Gotcha 9). It makes `ISCHANGED(StageName)` true, so M2-S04's product rule blocks
   any deal moved into `Propose`, `Negotiate` or `Closed Won` without products: Q16 counts about 20 deals with none.
   And the sales-ops admin passes that rule only by holding the bypass (P-1), which brings in Q17's Chatter post. The
   VP decides whether a bulk cleanup counts as a bypass use that needs one post per record.
5. `UNVERIFIED (2026-10-02):` whether `StageName` can be set to an Enterprise-only value while the record is still on
   the generic record type, or must change in the same update as `RecordTypeId`. Gotcha 1 says to update values
   before the record type, and no cited skill tests that for `StageName`. Rehearse on a sample in a full sandbox
   first (Gotcha 1, step 4).

---

## 7. UAT after the first deploy

Plan.json puts four of this step's tests in UAT, after the first deploy (`expected: "ticked in UAT after the first
deploy, not at the M4 gate"`). **Tests 11 and 13 are pre-deploy runbook checks,** ticked at the M4 gate, and they sit
at A-7 and A-17 above. They are not post-deploy UAT. Run every case as the named persona, never as System
Administrator.

| Test | Requirement | Given / when / then | Persona |
|---|---|---|---|
| 8 | REQ-004 | A user who holds neither `Enterprise_Sales_Record_Types` nor a profile grant for the new types creates an Opportunity. Neither `Enterprise` nor `Renewal` is offered on New, and the SMB default is unchanged. | An SMB user on `Sales User` |
| 9 | REQ-016 | An SMB-record-type Opportunity's page is opened. The Enterprise Path's stages and key fields do not render. | Any rep |
| 10 | REQ-017 (a) | An Enterprise-record-type Opportunity's page is opened. The Renewal Path's two stages do not render. | An Enterprise rep |
| 12 | REQ-018 (a) | With the setting deployed (`canOverrideAutoPathCollapseWithUserPref` true), a user collapses the Path and reopens the record. It stays collapsed for that user, and expanded for others. | Two reps |

The positive checks the step notes carry for the same UAT pass are below. Each is something no validate-only run
proved (§ 8).

- **The bypass bypasses.** As the sales-ops admin, save a Closed Won Enterprise deal at 25% discount with no approval
  (O-M2S03-04). Then move an Enterprise deal with no products from `Discover` to `Propose` (O-M2S04-05). As a rep,
  both saves are refused.
- **The approval runs.** As a real rep, submit a deal above 20% from the panel. Then run the `ProcessInstance` and
  `ProcessInstanceWorkitem` queries in `admin/approval-processes` `references/metadata-examples.md`, "Verification".
  Expect one email on submit and one on the outcome. Recall clears `Approval_Status__c` to blank. A manager can
  approve but not edit (`artefacts/M3-S02/deploy-order.md` § 10).
- **The rendering facts.** The Percent field reads 20, not 0.20, in the panel (O-M3S04-02, A35). The merge fields and
  the Percent value render as intended in each of the three emails (O-M3S01-03). The rejection email's Approval
  History list is on the page a rep sees (O-M3S01-01).
- **The page, as a rep and on mobile.** The Enterprise page shows the Path, the detail panel and the discount panel on
  desktop and in the mobile app (`artefacts/M3-S05/deploy-order.md` § 7). A Renewal record and an SMB record render
  what A-7 and A-8 decided.

---

## 8. What the validate-only loop could not prove

Every org run in this build was `checkOnly`. These are what those runs did not, or could not, establish. Each line
names its evidence.

1. **The Jest suite never ran.** No Node harness exists for this build. The 16 cases are reviewed evidence, not
   passing evidence (O-M3S04-01; MOCK-DEPLOY-M3 run 5, "Still not proven"). The org compiled the bundle in M3 run 4.
2. **The product gate does not re-fire after a line-item deletion.** Two official sources conflict. The rule is a
   forward gate only: a deal already at `Propose` can reach zero products and nothing catches it (`artefacts/M2-S04/deploy-order.md`
   § 2.2; `admin/validation-rules` Gotcha 15).
3. **Manager routing at run time.** The approval process validated, but a blank `Manager` on an owner fails the
   submission at run time (O-M3S02-01; A-9).
4. **The report and the dashboard were never validated green.** They can be validated only after their report type
   exists in the org (N4-F-06, MOCK-DEPLOY-M4 run 3). Their column codes are confirmed only at B-1 (A28). The report
   type validated with the `RecordType` column; a wrong record-type *value* would filter to zero rows rather than
   fail.
5. **Who holds what.** Permission-set assignments are data. No run can show that the bypass is assigned, or that it
   bypasses (O-M2S01-01, O-M2S03-04, O-M2S04-05).
6. **Which page Renewal and SMB records land on.** That depends on app-level assignments outside the build (A38,
   O-M2S05-04; A-6 to A-8).
7. **The deploy-copy edits.** Every run validated the build's files, not E1–E3. R-2's probe validates them, but a
   probe is never gate evidence (`standards/build-orchestration.md` § 5).
8. **What a partial `CustomObject` file resets.** MOCK-DEPLOY-M3 run 4 showed that the activation "deploys". A
   `checkOnly` run cannot show what a real deploy of a two-element object file would replace (Gotcha 10; E3).
9. **What the value set deactivates.** "checkOnly never deactivates anything" (MOCK-DEPLOY-M1 run 1). The merged E1
   file has never been validated.
10. **`CloseDate` as `Required`.** The org showed the four-item layout set is *sufficient*, not that `CloseDate` is
    *necessary* (O-M1S02-04).
11. **The opening stage of a new Enterprise or Renewal record** (O-M1S01-04), **the approval process order** (A34, not
    in the metadata) and **the history-tracking state** (A4).

---

## 9. Release decisions before the window

`admin/change-management-and-deployment`, "The Deploy Contract": each value below is decided on paper, not defaulted.
The release owner records the choices in `templates/release-plan-template.md` from that skill.

| Option | This release | Note |
|---|---|---|
| `checkOnly` | A validation pass against the **actual target** first, then the deploy | A validation against a sandbox licenses nothing in production (`metadata-examples.md` § 3). |
| `rollbackOnError` | `true`, set explicitly | Required in production, and set it explicitly in the sandbox rehearsal too. Otherwise a partial failure reads as `SucceededPartial`. |
| `testLevel` | `RunSpecifiedTests` with `OpportunityApprovalServiceTest`, **or** `RunLocalTests` | `RunSpecifiedTests` needs 75% per class. MOCK-DEPLOY-M3 run 5 measured 94.2% (service), 100% (controller) and 100% (invocable) on `sfskills-dev`. `RunLocalTests` is the production default when Apex is present, and runs Northwind's own tests too, with a run time not on file. **The release owner decides and times it.** |
| `purgeOnDelete` | `false` | No deletions in this release |
| Destructive manifests | None | § 1 |

**Backout**, one path per scenario, chosen before go-live (`metadata-examples.md` § 6):

- **Wrong behaviour.** Deactivate first: the two validation rules, or the approval process.
- **Full reversal.** Redeploy A-15's pre-release retrieve. New components stay unless a destructive manifest removes
  them, and none is prepared.
- **Bad data.** Restore the P-8 reassignment from step 1's export. That is a separate job with a separate owner.

---

## 10. The validate-only command a human may choose to run

Text to copy. **This agent does not run it, and no acceptance test invokes it.** `scripts/mock_deploy.py` assembles the
selected steps' artefacts and runs `sf project deploy start --dry-run` (`checkOnly: true`). The `--dry-run` is
hard-coded and the script has no deploy option. Results land under `reports/mock-deploy/<UTC timestamp>/`.

**Command 1: validate the build** (R-1, and the gate evidence for M4):

```bash
python3 scripts/mock_deploy.py .sfskills/builds/northwind-sales/plan.json \
  --org-alias <alias> \
  --milestone M1 --milestone M2 --milestone M3 --milestone M4 \
  --mode manifest \
  --test-level RunSpecifiedTests --tests OpportunityApprovalServiceTest
```

**Expected:** every component ok except two. The Report fails with "invalid report type", and the Dashboard with "no
Report named Enterprise_Sales/Open_Enterprise_Pipeline_By_Stage found" (N4-F-06). The tests should be 6 run, 6 passed.
Any other error is a finding. `--mode manifest` merges the selected steps' `package.xml` files by type. Once M4-S04 is
built, that merge includes this step's manifest, which makes it the first manifest-mode run carrying the Apex and the
bundle (§ 1).

`UNVERIFIED (2026-10-02):` `--milestone M4` also selects M4-S03. The script copies every non-`.md` file it finds, so
M4-S03's `uat-test-cases.yaml` lands in the assembled tree. No run has yet included it. If the run fails on that file,
select the same metadata without M4-S03:
`--milestone M1 --milestone M2 --milestone M3 --step M4-S02 --step M4-S04`.

**Command 2: validate the deploy copy** (R-2). This is a probe, so it is **never gate evidence**, and it writes nothing
into the build:

```bash
python3 scripts/mock_deploy.py .sfskills/builds/northwind-sales/plan.json \
  --org-alias <alias> \
  --milestone M1 --milestone M2 --milestone M3 --milestone M4 \
  --mode manifest --probe \
  --patch "artefacts/M1-S01/standardValueSets/OpportunityStage.standardValueSet-meta.xml=<merged E1 file>" \
  --patch "artefacts/M1-S02/layouts/Opportunity-Opportunity Enterprise Layout.layout-meta.xml=<E2 Enterprise layout>" \
  --patch "artefacts/M1-S02/layouts/Opportunity-Opportunity Renewal Layout.layout-meta.xml=<E2 Renewal layout>" \
  --patch "artefacts/M3-S05/objects/Opportunity/Opportunity.object-meta.xml=<merged E3 file>"
```

Patch paths are relative to the build directory (the probe copies the whole build). The expected result is the same
two errors.

Command 2 cannot model the split. `--without` maps `Report` but refuses `Dashboard` ("unmappable metadata type",
friction 64, MOCK-DEPLOY-M4 run 3). So `artefacts/M4-S02/deploy-order.md` § 10's
`--without "Dashboard:Enterprise_Sales/Enterprise_Pipeline"` is refused. A request-1-only rehearsal through the script
therefore still shows the Dashboard error.

---

## 11. Open clarifications the cutover still depends on

These are open in `plan.json`. Each has a default applied, and none blocks the deploy, but the people who own them
should know that go-live rests on them.

| Q | Question, in short | Where it bites |
|---|---|---|
| Q39 | How stage movement will be measured | A-11: history cannot be backfilled |
| Q42 | Whether the product rule is enforced everywhere (A7 applied) | UAT; O-M2S04-02 |
| Q43 | Whether legacy automation writes the gated fields (A8 applied) | A-10 |
| Q47 | The target org's edition | A-17: the Path setting's default depends on it |
| Q58 | Whether there will ever be a second approval process | A-12, P-5 |
| Q64 | Whether any portal or partner user touches these opportunities | `allowedSubmitters` and folder access assume internal users only |

---

## 12. Sources

- `admin/change-management-and-deployment`: SKILL.md (Questions to Ask, The Deploy Contract, Recommended Workflow);
  `references/metadata-examples.md` §§ 1, 3, 5, 6; `references/gotchas.md`; `references/llm-anti-patterns.md`
  Anti-Pattern 4; `templates/release-plan-template.md`; `scripts/check_deployment_manifest.py`.
- `admin/opportunity-management`: SKILL.md; `references/metadata-examples.md` §§ 5, 7, 8; `references/gotchas.md`
  Gotchas 6, 9, 17.
- `admin/approval-processes`: SKILL.md (Questions to Ask row 1, Deployable Metadata Shape, Recommended Workflow step 6);
  `references/metadata-examples.md` ("package.xml", "Retrieve, lint, deploy", "Verification"); `references/gotchas.md`.
- Also used: `admin/object-creation-and-design` Gotcha 10; `admin/reports-and-dashboards` `references/metadata-examples.md` § 5;
  `admin/custom-permissions` `references/metadata-examples.md` ("Verification");
  `admin/record-types-and-page-layouts` Gotcha 1; `admin/email-templates-and-alerts`
  `references/metadata-and-sender-identity.md`; `admin/validation-rules` SKILL.md.
- The build: every step's `deploy-order.md` (M1-S01, M1-S02, M2-S01 to M2-S05, M3-S01, M3-S02, M3-S05, M4-S01, M4-S02);
  `reports/MOCK-DEPLOY-M1.md` to `MOCK-DEPLOY-M4.md`; `reports/mock-deploy/2026-10-02T17-10-46Z/` and
  `2026-10-02T18-04-04Z/`; `reports/MILESTONE-M1-package.xml` to `MILESTONE-M3-package.xml`; `decisions.md` (open
  items cited inline); `plan.json` Q4, Q8, Q13, Q16, Q17, Q19, Q24 to Q26 and A4, A8, A24 to A29, A32, A34, A37, A38, D1, D9.
- Precedent: `examples/builds/case-onboarding/artefacts/M5-S05/` (the build-level manifest step of the committed
  example) and its `reports/MOCK-DEPLOY-M5.md` run 3.
