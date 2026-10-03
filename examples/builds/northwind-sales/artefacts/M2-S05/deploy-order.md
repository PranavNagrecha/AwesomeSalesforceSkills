# Deploy order — M2-S05

Build: `northwind-sales` · Milestone: M2 (Guidance, guardrails and who may bypass them) · Step type: `ui` · API version 62.0

This note is written by `agents/metadata-builder` Step 7 and is text for a human. Nothing in it is
executed by this agent or by any acceptance test.

Sourced from `skills/admin/path-and-guidance/references/metadata-examples.md` ("The five artifacts and
what each one owns", § 2 the path, § 3 the org preference, § 5 package.xml, § 6 retrieve and deploy,
§ 7 verification after deploy), `skills/admin/path-and-guidance/references/gotchas.md` #1, #5, #7, #8,
#9, #10, #11, #12 and #13, `skills/admin/path-and-guidance/SKILL.md` ("Questions to Ask Before
Configuring", "Key Fields Per Stage", "Path and Sales Process", "Review Checklist"),
`skills/admin/opportunity-management/SKILL.md` ("Questions to Ask Before Configuring"),
`skills/admin/sales-process-mapping/SKILL.md` ("Questions to Ask Before Configuring", "Stage as a Gate,
Not a Label") and `skills/admin/change-management-and-deployment/references/metadata-examples.md` §§ 1
and 3.

## 0. Why API version 62.0

`plan.json` carries no `api_version` key, so `agents/metadata-builder/AGENT.md` ("Inputs") falls back
to `62.0`. Every step already built in this build carries the same number — `artefacts/M1-S01/package.xml`,
`artefacts/M1-S02/package.xml` and `artefacts/M2-S01/package.xml` all declare `<version>62.0</version>` —
so `scripts/mock_deploy.py`'s highest-version scan across the selected steps sees one version for the
whole build rather than a step that silently raises it.

One element in this step has a version floor worth knowing: `canOverrideAutoPathCollapseWithUserPref`
is API 47.0 and later (`path-and-guidance/references/metadata-examples.md` § 3, quoting api_meta.txt
L124216–124221). 62.0 clears it.

## 1. Order inside this step

This step produces two `PathAssistant` components and one `PathAssistantSettings` file. All three are
in the single `package.xml` below, so one manifest deploy satisfies the ordering by itself.

| # | Component | Because |
|---|---|---|
| 1 | `PathAssistant:Enterprise_Opportunity_Path` | Order between the two paths is free — neither references the other. The pair `(entityName, recordTypeName)` is the unique key, and the two files claim `(Opportunity, Enterprise)` and `(Opportunity, Renewal)` respectively, so they cannot collide (api_meta.txt L94496, quoted in `metadata-examples.md` § 2 and `gotchas.md` #9). |
| 2 | `PathAssistant:Renewal_Opportunity_Path` | Same. |
| 3 | `Settings:PathAssistant` | Last on purpose. `metadata-examples.md` § 6 puts `Settings:PathAssistant` and the `FlexiPage` at the end of a split deploy — "make it visible last, so nobody sees a half-built path". The preference does not gate the deploy either way: "The preference does not need to be on to retrieve or deploy PathAssistant" (api_meta.txt L94498). |

A split-source deploy runs `pathAssistants/` then `settings/`.

## 2. Dependencies on components outside this step

**Everything in M1-S01 must exist in the target org first, and the dependency is by exact string.**
`recordTypeName` is the bare record type developer name (`metadata-examples.md` § 2, matching the
guide's own sample at api_meta.txt L94573) and it is **not updateable** (api_meta.txt L94529) — a path
deployed against the wrong record type is a delete-and-recreate, not an edit (`gotchas.md` #7).

| This step names | Which must already exist as | Built by |
|---|---|---|
| `recordTypeName` `Enterprise` | `RecordType` `Opportunity.Enterprise`, bound to `BusinessProcess` `Enterprise_Sales_Process` | M1-S01 (`objects/Opportunity/recordTypes/Enterprise.recordType-meta.xml`) |
| `recordTypeName` `Renewal` | `RecordType` `Opportunity.Renewal`, bound to `BusinessProcess` `Renewal_Sales_Process` | M1-S01 (`objects/Opportunity/recordTypes/Renewal.recordType-meta.xml`) |
| `picklistValueName` `Qualify`, `Discover`, `Propose`, `Negotiate` | values of `Enterprise_Sales_Process`, and active values of the `OpportunityStage` standard value set | M1-S01 |
| `picklistValueName` `Renewal Review`, `Renewal Proposed` | values of `Renewal_Sales_Process`, and active values of `OpportunityStage` | M1-S01 |
| `fieldNames` `Discount__c`, `Approval_Status__c` | `CustomField` on Opportunity | M1-S01 (`objects/Opportunity/fields/`) |
| `fieldNames` `Amount`, `CloseDate`, `NextStep` | standard Opportunity fields | the platform |

Two consequences the deploy will not spell out:

- **A `picklistValueName` that does not match, character for character, a value the record type exposes
  fails silently.** It is not a deploy error; the step simply does not render (`gotchas.md` #12, quoting
  api_meta.txt L94525–94526: "a missing step in the .xml file means it has not been configured, not
  that it doesn't exist"). `Renewal Review` and `Renewal Proposed` carry a space and no underscore,
  exactly as M1-S01's business process writes them.
- **A stage that reached the org through `StandardValueSet` alone is not selected on the record type.**
  New values loaded through the Metadata API "don't display in the picklist UI by default" until they
  are added to the record type's Selected Values (api_meta.txt L130774–130779, `gotchas.md` #13). M1-S01
  ships the business processes that make the selection, which is why this step depends on that step and
  not merely on the value set.

**Nothing in M2 has to precede this step.** The paths reference no custom permission, no validation
rule, no permission set and no layout, so M2-S01, M2-S02, M2-S03 and M2-S04 may deploy before or after
in any order. The guidance text *describes* the discount rule that M2-S03 enforces, but describing it
creates no metadata reference: if M2-S03 never deploys, the words on the Negotiate step are still there
and nothing blocks the save.

**Field-level security is not granted here and is not this step's to grant.** A key field a user cannot
read does not appear in the Path panel; `Discount__c` and `Approval_Status__c` reach the 12 reps and 2
managers through their profile and permission sets (M2-S01, M2-S02), not through this file.

## 3. What a green deploy of this step does *not* prove

This is the section `skills/admin/path-and-guidance` exists to force, and it is the step's second
manual acceptance test.

**A green `PathAssistant` deploy proves neither that Path is enabled in the org, nor that the Path
component is on the record page.** Three things must all be true simultaneously before a rep sees a
chevron (`SKILL.md`, "Path Settings and Setup Location"), and this step's deploy establishes at most
two of them:

1. **The org preference is on.** `settings/PathAssistant.settings-meta.xml` in this step asserts
   `pathAssistantEnabled` `true` rather than inheriting it. It defaults `true` for Enterprise Edition
   and `false` for every other edition (api_meta.txt L124222–124224, `gotchas.md` #11) — the reason the
   file ships at all is assumption **A12**: Northwind's production org is Sales Cloud Enterprise, where
   it is already true, but a scratch org or Developer Edition used to rehearse this build starts with
   Path off and the deploy would still be green.
2. **The path record is active.** Both files carry `<active>true</active>`.
3. **The Path component is on the Lightning record page.** *This step does nothing about that at all.*
   The component is `runtime_sales_pathassistant:pathAssistant` in the `subheader` region
   (api_meta.txt L67766–67779, L67993–67996) and it lives in a `FlexiPage`, which no step in M2 writes.
   **M3-S05** — "Opportunity Enterprise Lightning record page carrying the Path and the discount panel"
   — is the step that puts it there, and it is `pending`. Until M3-S05 is built and deployed, a green
   M2-S05 deploy plus a green M2 milestone gate is entirely compatible with a rep seeing nothing:
   "The preference does not need to be on to retrieve or deploy PathAssistant" (api_meta.txt L94498),
   and `gotchas.md` #5 is the same failure from the page side.

**And M3-S05 covers only the Enterprise record type.** Its own step note records the decision: "Only
the Enterprise page is built: Q50's default allowed one page, the Renewal record type falls through to
the org's existing Opportunity page". So `Renewal_Opportunity_Path` renders only if Northwind's current
Opportunity record page already carries `runtime_sales_pathassistant:pathAssistant`. Nothing in this
build asserts that it does. Check it before the M2 gate rather than after a renewal rep reports a
missing chevron:

```bash
sf project retrieve start --metadata "FlexiPage" --target-org <alias>
grep -rl "runtime_sales_pathassistant:pathAssistant" force-app/main/default/flexipages/
```

`check_path_and_guidance.py` cannot raise this for you: its FlexiPage check only fires when *some*
FlexiPage for Opportunity is present in the manifest and lacks the component. With no FlexiPage in the
tree at all — which is this step, and the whole of M2 — it stays silent by construction
(`scripts/check_path_and_guidance.py`, "Check 6c").

## 4. Manifest member forms used

| Type | Member form | Source |
|---|---|---|
| `PathAssistant` | `Enterprise_Opportunity_Path`, `Renewal_Opportunity_Path` — the file-name stem, unqualified by the object | `metadata-examples.md` § 5, modelled on the guide's own PathAssistant manifest (api_meta.txt L94576–94611) |
| `Settings` | `PathAssistant` — the **type name without the `Settings` suffix**, so `PathAssistant`, not `PathAssistantSettings` and not `Settings` | `metadata-examples.md` § 3 (api_meta.txt L108368–108369) and § 5 |

`PathAssistant` does support the `*` wildcard (api_meta.txt L94614–94615), and it is the right tool for
*inventorying* an org before an audit. Both members are named explicitly here anyway so that the
manifest and the files on disk agree in both directions — every file covered by a member, every member
backed by a file — which is what the step's `manifest` acceptance test asserts. Settings wildcards
apply "only when retrieving all settings, not for an individual setting" (api_meta.txt L124194–124197),
so `Settings` could not have been wildcarded here in any case.

## 5. Elements deliberately not written, and why

- **No `Closed Won` or `Closed Lost` step on either path.** Both values exist on both business
  processes and both chevrons will render; they simply carry no key fields and no guidance. This is the
  documented meaning of an omitted step, not an oversight: "a missing step in the .xml file means it has
  not been configured, not that it doesn't exist" (api_meta.txt L94525–94526, `gotchas.md` #12), and the
  skill's own worked example omits Closed Lost for exactly this reason (`metadata-examples.md` § 2).
  The plan's own step note asked for this explicitly.
- **No celebration or confetti element anywhere.** There is none to write. The `PathAssistant` and
  `PathAssistantStep` field tables are exactly `active`, `entityName`, `fieldName`, `masterLabel`,
  `pathAssistantSteps`, `recordTypeName` and `fieldNames`, `info`, `picklistValueName`
  (api_meta.txt L94510–94529, L94545–94549). Celebration is configured per stage in Setup and does not
  travel with a deploy (`gotchas.md` #8). See § 6 — assumption **A14** says the rep advances the stage
  in the UI, which is the one condition under which confetti would fire at all, so the choice is
  Northwind's to make by hand rather than one this build can make for them.
- **No `pathAssistantForOpportunityEnabled` in the settings file.** It is API 34.0 **and earlier**
  (api_meta.txt L124226–124228). `metadata-examples.md` § 3 and `gotchas.md` #11 both say not to put it
  in a modern package.
- **No `FlexiPage`.** Not this step's declared output; M3-S05 owns it (§ 3 above).
- **No `BusinessProcess`, `RecordType` or `StandardValueSet` block.** They are M1-S01's, already built
  and accepted at the M1 gate. This matters beyond tidiness: `path-and-guidance/references/metadata-examples.md`
  § 1 shows an Opportunity `BusinessProcess` whose opening value carries `<default>true</default>`, and
  the org refused exactly that shape in this build — *"Cannot specify a default on: Opportunity"*,
  finding **N3-F-01** in `reports/MOCK-DEPLOY-M1.md` run 1, closed in run 2 and recorded as
  D-M1S01-05. No businessProcess block was copied from that example into this step, and none should be
  copied from it into any later one until the skill is corrected.
- **`LeadSource` and `Type` are not key fields on any step.** Q11's answer names them as "shown for
  context only". The step's `inputs.key_fields_by_stage` — which is the planner's explicit binding and
  outranks the clarification text under `agents/metadata-builder/AGENT.md` Step 4 — lists neither, on
  any stage. Written as declared. If the VP wants them visible, they belong on the layout (M1-S02),
  not in `fieldNames`.
- **The Decision Maker contact role is guidance text, not a key field.** Assumption **A16**:
  `fieldNames` "names fields on `entityName` only — no cross-object dotted references"
  (`SKILL.md`, "Before Starting", quoting api_meta.txt L94545), and an `OpportunityContactRole` is a
  related record. The Propose step's `info` names the requirement in words and says where to set it.
- **No step carries more than three key fields.** The commonly cited cap is five, and the skill marks
  it `UNVERIFIED (2026-09-05)` — it appears in neither the Metadata API guide's `fieldNames`
  description nor the limits cheat sheet, so `check_path_and_guidance.py` reports counts above five as
  a NOTE rather than an ISSUE. Nothing here comes close to the line either way.

## 6. Post-deploy steps the deploy does not perform

- **Celebration must be re-enabled by hand in every org, if it is wanted at all.** It has no metadata
  element (§ 5), so it does not travel. Assumption **A14** (Q49 left unanswered at G1, default applied)
  records that the rep advances the stage in the UI and no automation writes `StageName` — which is the
  only way confetti ever fires: not on a picklist edit on the detail page, not from a Flow, not from an
  API call (`SKILL.md`, "Celebration Confetti"; `gotchas.md` #4). **No celebration is configured by this
  build.** If Northwind wants it on Closed Won, it is a Setup click in production and in every sandbox
  refreshed afterwards, and it belongs on the M4-S04 cutover runbook as a manual line.
- **Run the three verification queries, not just the Setup page** (`metadata-examples.md` § 7). They
  separate three failures that look identical from a record page:

  ```sql
  SELECT ApiName, MasterLabel, IsActive, IsClosed, IsWon, SortOrder
  FROM OpportunityStage ORDER BY SortOrder

  SELECT Id, DeveloperName, SobjectType, BusinessProcessId, IsActive
  FROM RecordType WHERE SobjectType = 'Opportunity'

  SELECT Id, Username, UserPreferencesPathAssistantCollapsed
  FROM User WHERE Username = '<a real Enterprise rep>'
  ```

  The first proves every `picklistValueName` is a live value; a step pointed at an inactive value is
  dead configuration. The second proves the record type is bound to the business process — a null
  `BusinessProcessId` on an Opportunity record type means the stage set is undefined. The third is the
  one that stops a second debugging session: "the path is collapsed for one user" is a per-user
  preference, not a config bug (`gotchas.md` #10; object_reference.txt L296509–296515).
- **Verify as a non-admin.** `SKILL.md` Recommended Workflow step 7. An admin sees everything; the
  question is whether a rep does.

## 7. How to read this step's three checkers

All three exited 0 on the first pass with zero repair passes. They did not all assert the same amount.

| Declared test | Command | What its exit code stands for |
|---|---|---|
| build scope | `check_path_and_guidance.py --manifest-dir artefacts` | The real one. `Checked 2 path(s): no issues found.` with zero NOTE lines — it resolved both `recordTypeName` values against M1-S01's record types and matched all six `picklistValueName` values against the business processes and the value set. At `--manifest-dir artefacts/M2-S05` the same checker prints NOTE lines saying it could not resolve any of that, and still exits 0. |
| step scope | `check_opportunity_management.py --manifest-dir artefacts/M2-S05` | `No issues found.` Path-internal shape only: one path per `(entity, recordType)` pair, `fieldName` is `StageName`, `recordTypeName` present. It reads `<manifest-dir>/pathAssistants/` without recursing, so build scope would find nothing. |
| step scope | `check_sales_process_mapping.py --manifest-dir artefacts/M2-S05` | **`Scanned 0 file(s) — nothing asserted; check --manifest-dir`, exit 0.** Read it as it is written: the exit code stands for nothing. That checker lints `*.yaml`/`*.yml`/`*.csv` sales-process maps and a retrieved `OpportunityStage` value set; this step ships none of those. Its subject matter — the stage ladder — is M1-S01's artefact, and at `--manifest-dir artefacts` the same command prints `No issues found.` having actually read it. |

The third row is a plan defect, not an artefact defect, and it is not this agent's to fix: `amend-step`
refuses a step whose status is `running`. The remedy for a human, before the M2 gate, is one of —
re-declare that test at `scope: "build"` with `--manifest-dir artefacts` (which is what
`standards/build-orchestration.md` § 5 "Checker scope" prescribes when a checker's assertions are not
satisfiable inside one step's output), or carry it as an M2 milestone acceptance test, or accept that
the skill is cited for its Questions-to-Ask table (Q2 came from it) and not for its checker. Whichever
is chosen, the test's `description` should say so, because today a green tick on that row means only
that a checker ran.

## 8. Validate-only command for a human

`agents/metadata-builder` never runs this. It is text to copy.

`scripts/mock_deploy.py` assembles the selected steps' artefacts and hands them to
`sf project deploy start --dry-run` (`checkOnly: true`). The `--dry-run` is hard-coded inside the
script — there is no flag that turns it off and no deploy option — so nothing about the dry run is the
operator's to pass or to forget.

**Validate this step together with M1, not alone:**

```bash
python3 scripts/mock_deploy.py .sfskills/builds/northwind-sales/plan.json \
  --org-alias <your-sandbox-alias> \
  --milestone M1 \
  --step M2-S05 \
  --mode manifest
```

Alone, against an org that has never received M1, both paths fail on `recordTypeName` — the record
types do not exist there, and a `--dry-run` never saved M1's earlier runs (§ 2). Against an org where
M1 is genuinely deployed, `--step M2-S05` on its own is the narrower and faster check. `--mode manifest`
matches how M1 was validated (`reports/MOCK-DEPLOY-M1.md`). Results land under
`reports/mock-deploy/<UTC timestamp>/`.

What that run can and cannot tell you: it can catch a `recordTypeName` the org does not have, a
malformed settings file, or a member form the platform rejects. It cannot catch a `picklistValueName`
that does not match — an unmatched step is valid metadata that renders nothing (§ 2) — and it cannot
tell you whether any of this will be visible, which is § 3.

For a production target the sequence is different: `sf project deploy validate` returning a job id,
then `sf project deploy quick`, per `change-management-and-deployment/references/metadata-examples.md`
§ 3, which carries its own `UNVERIFIED (2026-09-04)` caveat on `sf` CLI flag spellings — if a flag is
rejected, run `sf project deploy validate --help` rather than guessing a synonym.
