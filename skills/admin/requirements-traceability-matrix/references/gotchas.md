# Gotchas — Requirements Traceability Matrix

Non-obvious delivery realities that turn an RTM from a governance artifact into a fiction.

---

## Gotcha 1: Bidirectional Drift Between Requirement and Story

**What happens:** A requirement is updated mid-flight (often via a verbal change in a refinement workshop). The story that implements it is updated to match the new behavior, but the RTM row still cites the original requirement text. Now the matrix says story `US-101` implements requirement `REQ-007 — original`, while `US-101` actually delivers `REQ-007 — refined`. At audit, the trace is wrong.

**When it occurs:** Mid-sprint scope refinements where the BA updates the agile tool but treats the RTM as a release-gate artifact, not a living document.

**How to avoid:** Treat the requirement description as a versioned field. If the requirement is materially refined, either (a) bump the description and add a `last_updated` column, or (b) close the original `REQ-007` as `Dropped` and add a new `REQ-007a` with `source: change-request`. Never silently overwrite a requirement description without an entry in the change log.

---

## Gotcha 2: Test Cases Not Tied Back to Requirements

**What happens:** UAT test cases get authored against user stories (because the QA team works from the agile tool, not the requirements doc). Tests are linked to stories, stories are linked to requirements, but the RTM only captures `req_id ↔ story_ids`, not `req_id ↔ test_case_ids`. At audit, the auditor asks "show me the test that proves REQ-007 was validated" and the team has to walk through stories to find it.

**When it occurs:** When the test management tool and the requirements tool are different systems and nobody owns the cross-reference.

**How to avoid:** Make the `test_case_ids` column mandatory before status moves to `In UAT`. The BA or QA lead populates it as cases are authored. A test case that does not trace to a requirement is either a regression test (separate column) or scope creep (escalate).

---

## Gotcha 3: IDs Reused Across Project Phases

**What happens:** Phase 1 ships REQ-001 through REQ-050. The Phase 2 BA starts a new RTM file and reuses REQ-001 for a totally different requirement. Six months later, a defect log says "regression in REQ-001" and nobody knows which one.

**When it occurs:** Multi-phase programs where each phase has a different BA or different agile tool project, and IDs are not namespaced.

**How to avoid:** Either (a) continue numbering across phases (Phase 2 starts at REQ-051), or (b) use a phase prefix (`P1-REQ-001`, `P2-REQ-001`). Never reuse a bare `REQ-XXX` ID across phases of the same program.

---

## Gotcha 4: RTM Lives in a Spreadsheet That Nobody Maintains

**What happens:** RTM is created at project kickoff in SharePoint or Google Sheets. It is populated for the first sprint, then not updated. By release, half the rows have stale story IDs, missing test references, and wrong statuses. The Steerco deck is built off the spreadsheet anyway and contains incorrect coverage numbers.

**When it occurs:** Always — this is the default failure mode for any RTM that is not in version control with a per-PR check.

**How to avoid:** Move the RTM to CSV-in-Git with a CI job that runs `check_rtm.py` on every PR. The matrix becomes a code artifact: changes are reviewed, history is auditable, drift is detectable. The markdown rendering for Steerco is generated from the CSV, never hand-edited.

---

## Gotcha 5: Missing the Deferred / Dropped Column (or Hiding Those Rows)

**What happens:** Stakeholders drop a requirement. The team deletes the row "to keep the matrix clean." Six months later, the auditor asks "you scoped 200 requirements, you delivered 150 — where are the other 50?" There is no answer.

**When it occurs:** When the team treats the RTM as a "delivered scope" artifact instead of a "scope decision" artifact.

**How to avoid:** Dropped and deferred requirements are first-class rows. Status enum includes `Deferred` and `Dropped`. Each dropped row has a documented decision (owner + date + rationale) in a sibling decision log. The Steerco rollup explicitly counts dropped rows so leadership sees the cumulative scope decisions.

---

## Gotcha 6: Backlog Churn Outpaces RTM Updates

**What happens:** Aggressive sprint teams split, merge, and rename stories weekly. The story IDs in the RTM go stale within sprints. By release, the `story_ids` column is full of dead links to tickets that were closed without delivering, while the actual delivering tickets are not in the matrix.

**When it occurs:** Programs with high backlog churn — typically Agile-mature teams that refactor stories frequently.

**How to avoid:** Update the RTM at the end of every sprint, not at release gates. Better: write a CI job that diffs the agile tool's "completed in this sprint" list against the RTM and flags any story IDs in the matrix that do not exist in the tool. Best: treat the RTM update as part of the sprint Definition of Done.

---

## Gotcha 7: Multi-Valued Cells Use the Wrong Delimiter

**What happens:** Team uses commas to separate multiple story IDs in `story_ids`. The CSV parser treats them as separate columns. The matrix loads with shifted columns and silent data corruption.

**When it occurs:** When the RTM author uses a delimiter that conflicts with the CSV format.

**How to avoid:** Standardize on the pipe `|` delimiter for multi-valued cells. Document the convention in the file header or a `README.md` next to the CSV. The `check_rtm.py` script enforces it.

---

## Gotcha 8: Defects Raised Against Stories, Not Requirements

**What happens:** QA logs defects against user stories in Jira. The defect tracker links defect to story, but never to requirement. The RTM `defect_ids` column gets populated by hand-tracing defect → story → requirement, which is error-prone and frequently skipped.

**When it occurs:** When the defect tool is configured at the story level (the agile tool default) rather than the requirement level.

**How to avoid:** Configure the defect tracker so a defect can carry both a story link and a requirement link. Where that is not possible, run a nightly job that reads the defect tracker, follows defect → story → requirement, and writes the result to the RTM `defect_ids` column. Hand-tracing does not scale past sprint 3.

---

## Gotcha 9: `artefact` Is Not a Unique Key — the Rule Files Are One Per Object

**What happens:** The matrix gets a column for the Salesforce artefact each requirement produced, and
tooling built on top of it assumes one row ↔ one file. Three requirements — "billing mail goes to the
Billing queue", "Severity 1 goes to Tier 2", "everything else goes to Tier 1 General" — all resolve
to the same artefact, so a de-duplicating join collapses them to one row and the coverage count drops
by two without anything being wrong.

**When it occurs:** With the rule types, which are stored per object rather than per rule. The
Metadata API guide is explicit: "Assignment rules for an object have the suffix `.assignmentRules`
and are stored in the `assignmentRules` folder. For example, all Case assignment rules are stored in
the `Case.assignmentRules` file" (`api_meta.txt` L23689–23691). Auto-response and escalation rules
follow the same shape.

**How to avoid:** Treat `req_id` as the only key and `artefact` as a many-to-one reference. Where the
requirement needs to name one rule rather than the file, use the *singular* type in the manifest:
`AssignmentRule` with members `Case.samplerule`, `Case.newrule` — the guide flags the difference
itself ("Notice that for this example the type name syntax is `AssignmentRule` and not
`AssignmentRules`", `api_meta.txt` L23675–23682). Then the row's artefact is
`AssignmentRule:Case.Support_Case_Routing` and it resolves to a rule, not a file.

---

## Gotcha 10: The Artefact Name Is the `fullName`, Not the Setup Label

**What happens:** The BA fills the artefact column from the Setup screen, because that is what is on
screen during the walkthrough. `EntitlementProcess:Premier Support` goes into the row. The artefact
cross-check never resolves it, the release manager cannot find it in the manifest, and the row is
quietly excluded from the deploy.

**When it occurs:** Any time the UI label and the API name differ — but entitlement processes are the
sharp edge, because the file name is not even the API name of the current version. Per the guide, the
file name "is the name of the entitlement process with the version appended to the end, if
applicable (for example, an entitlement process named 'gold_support' can have the file name
'gold_support_v2.entitlementProcess')", it "corresponds to the `slaProcess.NameNorm` field", it is
lowercase, and it "is distinct from the `name` field, which represents what displays in the user
interface and, if versioning is enabled, can be shared among multiple versions"
(`api_meta.txt` L59074–59082). So one label can map to several files, and none of them is spelled
like the label.

**How to avoid:** Write `<MetadataType>:<fullName>` and take the `fullName` from the retrieved source,
not from Setup. For a custom field that is `Object.Field__c` — the guide's own examples are
`MyCustomObject__c.MyCustomField__c` and `Account.MyAcctCustomField__c` (`api_meta.txt`
L43221–43226). For a versioned entitlement process it is the versioned lowercase file name. When the
retrieve has not happened yet, `listMetadata()` returns the `fullName` for components of a type
(`api_meta.txt` L2095–2097) — that is the lookup, not the Setup list view.

---

## Gotcha 11: Two Id Families Produce Two Rows for One Need

**What happens:** Discovery mints `REQ-042`. The fit-gap pass against the existing org independently
raises `FG-017` for the same behaviour. Both land in the matrix. Coverage now counts the need twice,
the workbook row cites `FG-017` while the UAT case cites `REQ-042`, and at the gate nobody can say
which of the two is authoritative — so both stay, and the "requirements delivered" number is wrong in
the direction that looks good.

**When it occurs:** On re-platform and org-consolidation projects, where elicitation and fit-gap run
in parallel by different people. It is also invisible: two rows with different ids and different
wording do not look like duplicates to any checker.

**How to avoid:** Decide the key before row 1 (SKILL.md § REQ-XXX ⇄ FG-XXX). The non-key prefix moves
to a `fit_gap_ref` column and never appears in the key column. Where a project is genuinely fit-gap
led, `FG-XXX` *is* the key — `admin/configuration-workbook-authoring` → `references/examples.md`
shows `FG-014` sitting in the workbook's `source_req_id` column, so a matrix that rejects `FG-` ids
cannot join to that workbook at all.

---

## Gotcha 12: The Audit RTM and the Build's `traceability.md` Drift Into Two Truths

**What happens:** The programme keeps `governance/rtm.csv` for Steerco and the build layer writes
`.sfskills/builds/<id>/traceability.md` per `standards/build-orchestration.md` § 2. Both are correct
on the day the build starts. Three steps later the build has re-scoped a requirement and updated its
own file; the governance CSV has not moved. Steerco is reading the stale one, because that is the one
with the release column.

**When it occurs:** As soon as a build layer exists alongside a pre-existing governance process — so,
on every project that adopts the build layer mid-programme rather than at kickoff.

**How to avoid:** One file is authored, the other is generated, and the direction is written down.
The build-layer schema is a superset of the audit schema minus the multi-release columns, so
generating the audit RTM from `traceability.md` at each release gate is the cheaper direction. What
does not work is maintaining both by hand and diffing them at the gate — by then the disagreement is
a Steerco conversation rather than a merge.

---

## Gotcha 13: A Row With No Owning Agent Is a Requirement Nobody Can Fail

**What happens:** The matrix has a requirement, an artefact and a test, but the `agent` cell is empty
or holds something like "the admin team". At the milestone gate the test fails and there is no owner
to route it to, so it becomes a standing action item and the milestone is accepted with it open.

**When it occurs:** On requirements that sit between roster agents — reporting sets, console layouts,
anything where the honest answer is that no agent covers the topic. The empty cell reads as an
oversight, so nobody treats it as the signal it is.

**How to avoid:** `standards/build-orchestration.md` § 4 gives each step exactly one owning run-time
agent from the roster, and § 8 says the planner may only assign agents that exist with
`class: runtime` and a status other than deprecated. Enforce the same on the row: one id, resolving
to `agents/<id>/AGENT.md`. When no agent owns the topic, the correct move is the one § 8 names —
mark the step blocked with `reason: skill-gap` and record it in `decisions.md`, which is the signal
to deepen a skill. An empty cell records nothing.

---

## Gotcha 14: Setup-Only Components Make the Artefact Cross-Check Cry Wolf

**What happens:** The checker cross-references every row's artefact against the metadata in the
manifest. A handful of rows never resolve, run after run, because the component they name has no file
to resolve to. Within two sprints the team stops reading the unresolved list — and the day a genuinely
misspelled API name joins it, nobody notices.

**When it occurs:** Wherever the requirement lands in a feature the Metadata API does not carry. The
guide states it plainly: "Some Salesforce features have metadata types that aren't available in
Metadata API. These metadata types can't be retrieved or deployed with Metadata API. To make changes
to these types, you must do it manually in each of your organizations" — and adds that some types are
also unsupported in source tracking, packaging and change sets (`api_meta.txt` L9555–9559). It is
also true of a component that simply has not been built yet at the time the check runs.

**How to avoid:** Make it a declared state rather than a permanent warning. Mark the row
`setup-only:<component>` so the checker skips resolution and instead demands a `manual` test type and
a named owner for the Setup step — the check becomes "is there a human procedure and a human tester",
which is the real control. Check the type against Metadata Coverage before marking it, because
"it did not resolve" and "the API cannot carry it" are different diagnoses with different fixes.

---

## Gotcha 15: A `Dropped` Row Is Not a Destructive Change — and a Green Delete Is Not Proof

**What happens:** A requirement is dropped after it was partly built. The row's status moves to
`Dropped`, the team adds the component to `destructiveChanges.xml`, the deploy comes back green, and
the row is closed. The component is still in the org — the deploy deleted nothing, because that
particular component had never been deployed to *this* org under that name.

**When it occurs:** Whenever the drop is recorded against an artefact whose name is wrong (see gotcha
10) or whose earlier build never reached the target org. The delete does not fail loudly: "If you try
to delete some components that don't exist in the organization, the rest of the deletions are still
attempted" (`api_meta.txt` L4641). A partially-wrong delete manifest therefore reports success.

**How to avoid:** Split the status from the change. `Dropped` records the scope decision; the removal
is its own row with its own artefact and its own test, and the test is a *post-deploy* check that the
component is absent, not the deploy's exit code. Get the delete manifest right while you are there:
it is named `destructiveChanges.xml`, wildcards are not supported in it, and it needs a companion
`package.xml` that lists no components and carries the API version (`api_meta.txt` L4614–4632); use
`destructiveChangesPre.xml` / `destructiveChangesPost.xml` when order against the additions matters
(`api_meta.txt` L4645–4656). And never bundle the removal into the feature deploy — that makes the
feature's rollback also a restore.

---

## Gotcha 16: The Member Form Is Not the File Stem for Every Type

**What happens:** `check_rtm.py --manifest-dir` reports a real component as an orphan, or a row's
artefact as unresolved, even though the file is right there. The row wrote the member the way most
types actually work — `Type:BareName`, matching the file's own stem — but a handful of types name
their member differently from their file: an `EmailTemplate` member is `Folder/Name` (the file is
`email/Folder/Name.email`), an `EmailFolder` member is the folder's own bare name (`email/
Folder.emailFolder-meta.xml`), and a `BusinessProcess` member is `Object.Process_Name` (the file is
`objects/Object/businessProcesses/Process_Name.businessProcess-meta.xml`) — the same object-qualified
shape `CustomField`, `ValidationRule`, `RecordType` and `CompactLayout` already use, but easy to miss
for a type introduced later.

**When it occurs:** Whenever a row is written against the Setup label or the file name alone instead
of the Metadata API's actual `fullName` for that member shape. It is the same class of mistake as
Gotcha 10 (label vs. `fullName`), but one level up: even a row that already writes a real `fullName`
still needs the *folder* or *object* qualifier some types require and others don't.

**How to avoid:** Before writing an `artefact` cell for a type you have not used in this matrix
before, check the member-form table in `check_rtm.py`'s module docstring — it lists the file path
next to the exact member shape for every type this skill's rows commonly name (`CustomField`,
`ValidationRule`, `RecordType`, `CompactLayout`, `BusinessProcess`, `EmailTemplate`, `EmailFolder`,
`SharingRules`, `Layout`, `Settings`, `StandardValueSet`, `Queue`/`Group`,
`PermissionSet`/`PermissionSetGroup`/`Profile`). A type not in that table still resolves through the
checker's same-name, any-type fallback, so a wrong type spelling recovers — a wrong *shape*
(folder or object qualifier missing entirely) does not, because the fallback matches on the full name
string, not just the file stem.

---

## Gotcha 17: Naming the Rule Container Doesn't Look Like It Covers Its Own Rules

**What happens:** A row correctly names the deployable member `check_rtm.py`'s manifest reads and
`package.xml` and `deploy-order.md` both declare — `AssignmentRules:Case`, the whole container, not
one rule inside it. The linter still reports every individual rule read out of that same file
(`AssignmentRule:Case.Case_Intake_Routing`, `AutoResponseRule:Case.Case_Acknowledgement`, ...) as an
orphan, even though the container row is the *only* correct way to cite a component that has no
per-rule file to point to (Gotcha 9). The team either files a false coverage-gap ticket or starts
adding a second, finer-grained row per rule just to quiet the linter — which makes the traceability
row wrong (`AssignmentRule:Case.Case_Intake_Routing` is not what `package.xml` declares) to make the
orphan report clean.

**When it occurs:** Any `AssignmentRules` / `AutoResponseRules` / `EscalationRules` component with
more than one named rule inside its one shared file, once a row exists that correctly names the
container. Below `check_rtm.py` v1.1.3 the checker's manifest indexer registers two different kinds
of key from that one file — the container key (`AssignmentRules:Case`) and one singular key per rule
(`AssignmentRule:Case.<rule fullName>`) — and treated a row's coverage as resolved only against the
one key it named, so the container row never propagated to the rules the checker itself had derived.

**How to avoid:** Nothing to do in the row — `check_rtm.py` v1.1.3+ resolves container ↔ rule
coverage by key, not by the file path each key happens to carry: a row naming the container marks
every rule inside it covered, and a row naming one rule marks that rule and the container covered
(not its sibling rules — Gotcha 9's per-rule granularity still traces one row to one rule). Naming
the container remains correct and sufficient whenever no requirement calls out an individual rule.
If this still surfaces on a repo pinned to an older `check_rtm.py`, that is the signal to update the
script, not to rewrite the row.
