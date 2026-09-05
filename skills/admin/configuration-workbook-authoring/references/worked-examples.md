# Worked Examples — Configuration Workbook Authoring

`references/examples.md` shows *excerpts* of the row schema. This file shows
the **format rules applied end to end** to one small feature, so an assistant
can copy the shape rather than re-derive it: the RTM linkage block, the
per-row schema, a row that cites a decision-tree branch, sections that are
deliberately empty, the descope ledger, the deployment manifest the committed
rows produce, and the checker run that gates sprint commit.

**A full ten-section workbook for a larger solution already exists in this
library** — `skills/admin/case-management-setup/references/worked-example-case-intake.md`
carries all ten sections for a case-intake build, with the skill file that
supplied each row. Read that one for *breadth*. Read this one for the
*format rules*. Neither file repeats the other's rows.

---

## The feature

Acme wants inbound Leads scored and tiered so SDRs work the hot ones first.
Three approved fit-gap rows and three stories:

| RTM `req_id` | Story | What it asks for |
|---|---|---|
| `REQ-088` | `US-3140` | A qualification score and tier on Lead, set automatically |
| `REQ-089` | `US-3141` | Stop a tier being set without a score |
| `REQ-090` | `US-3142` | SDRs must be able to see tiered Leads they do not own |
| `REQ-091` | `US-3143` | Hot Leads route to the fast-lane queue |

`source_req_id` is the RTM's `req_id`, not a locally invented id.
`admin/requirements-traceability-matrix` § ID Conventions fixes the shape as
`REQ-XXX` (project-prefixed as `ACME-REQ-001` when several programs share an
agile tool), immutable for the life of the project.

---

## Rule 1 — the per-row schema, on every row of every section

| Column | Required | What makes it valid |
|---|---|---|
| `row_id` | yes | Unique across the **whole** workbook, not just its section. Survives reordering. |
| `section` | yes | Exactly one of the ten canonical names. Carried by the table's section heading in markdown; an explicit column in `cwb.json` / `cwb.csv`. |
| `target_value` | yes | The metadata component and its value. Not a Setup click-path — see Rule 5. |
| `owner` | yes | A named human. Not "the admin team". |
| `source_req_id` | yes | The RTM `req_id`. Blank = orphan = reject. |
| `source_story_id` | yes | The story id. Blank = orphan = reject. |
| `recommended_agent` | yes | Exactly one runtime agent id, optionally followed by `--flag` arguments. |
| `recommended_skills` | yes (≥ 1) | `;`-delimited. Every entry must resolve on disk — see Rule 2. |
| `status` | yes | From the closed enum. Never a placeholder. |
| `notes` | optional | Dependencies, decision-tree branch, org-probe evidence. |

---

## Rule 2 — one row, one agent, and both the agent and the skills must resolve

`agents/_shared/SKILL_MAP.md` is the authoring reference for the runtime
roster: its own opening paragraph states that every skill id it lists has
been verified to exist at `skills/<domain>/<slug>/SKILL.md`, and that a new
citation must be verified before it is committed. A workbook row inherits
that obligation.

Three resolution steps, in this order (they mirror
`agents/config-workbook-author/AGENT.md` Step 6, which the agent runs against
the workbook you hand it):

1. **Strip the arguments.** `audit-router --domain=validation_rule` is the
   agent id `audit-router`; everything after the first space is invocation
   argument.
2. **Confirm `agents/<id>/AGENT.md` exists.** Presence in `SKILL_MAP.md` is
   not enough on its own.
3. **Read that file's frontmatter and confirm `status` is not
   `deprecated`.** This is the step people skip. The fourteen Wave-3b
   auditors still have `AGENT.md` files on disk, so a presence-only check
   passes them and routes the row to a stub. Each carries
   `deprecated_in_favor_of: audit-router`;
   `agents/_shared/AGENT_DISAMBIGUATION.md` gives the `--domain=` argument to
   rewrite the row with.

`recommended_skills` entries resolve the same way, and three shapes are
accepted:

| Shape | Resolves to |
|---|---|
| `admin/validation-rules` | `skills/admin/validation-rules/SKILL.md` |
| `admin/assignment-rules -> references/routing-selector.md` | that reference file inside the skill package |
| `templates/admin/naming-conventions.md`, `standards/decision-trees/sharing-selection.md` | the repo-relative file itself |

Anything else — a plausible-sounding slug the author never opened — is the
failure `scripts/check_workbook.py` exists to catch.

---

## Rule 3 — the RTM linkage block sits at the top of `cwb.md`

It is the reviewer's index: it answers "which gap drove this?" without
reading ten section tables, and "did anything get dropped?" by being diffable
against the RTM.

```markdown
## RTM Linkage Block

| row_id | source_req_id | source_story_id | recommended_agent | status |
|---|---|---|---|---|
| CWB-OBJ-101 | REQ-088 | US-3140 | object-designer | committed |
| CWB-OBJ-102 | REQ-088 | US-3140 | object-designer | committed |
| CWB-OBJ-103 | REQ-090 | US-3142 | object-designer | committed |
| CWB-PSG-101 | REQ-088 | US-3140 | permission-set-architect | committed |
| CWB-SHR-101 | REQ-090 | US-3142 | audit-router --domain=sharing | committed |
| CWB-VR-101 | REQ-089 | US-3141 | audit-router --domain=validation_rule | committed |
| CWB-VR-102 | REQ-089 | US-3141 | audit-router --domain=validation_rule | committed |
| CWB-AUT-101 | REQ-088 | US-3140 | flow-builder | committed |
| CWB-AUT-102 | REQ-091 | US-3143 | assignment-and-auto-response-rules-designer | committed |
| CWB-DAT-101 | REQ-088 | US-3140 | data-loader-pre-flight | committed |
```

Every `row_id` here appears exactly once in exactly one section table, and
every `req_id` in the table above appears here at least once. Those two
statements are the whole point of the block.

---

## Rule 4 — populated sections

### Section 1 — Objects + Fields

```markdown
| row_id | target_value | owner | source_req_id | source_story_id | recommended_agent | recommended_skills | status | notes |
|---|---|---|---|---|---|---|---|---|
| CWB-OBJ-101 | New field `Lead.Qualification_Score__c`, Number(3,0), not required, default blank | R. Okafor | REQ-088 | US-3140 | object-designer | admin/custom-field-creation; templates/admin/naming-conventions.md | committed | New field; org probe on 2026-09-08 confirmed no existing `Score__c` on Lead. |
| CWB-OBJ-102 | New field `Lead.Qualification_Tier__c`, Picklist, restricted, values from Global Value Set `Lead_Qualification_Tier` (Hot, Warm, Cold) | R. Okafor | REQ-088 | US-3140 | object-designer | admin/custom-field-creation; admin/picklist-field-integrity-issues | committed | Depends on CWB-OBJ-101 — the Flow in CWB-AUT-101 writes this from the score. |
| CWB-OBJ-103 | `Lead.sharingModel` stays `ReadWrite`; no change to the Lead object file this release | R. Okafor | REQ-090 | US-3142 | object-designer | admin/sharing-and-visibility | committed | Recorded here, not in Section 4: OWD is the `sharingModel` element on the Lead object file, not a `sharingRules/` component. See CWB-SHR-101. |
```

`CWB-OBJ-103` is the row most authors get wrong. The org-wide default is the
`sharingModel` field on `CustomObject`, so it deploys inside the object file
that Section 1 owns — the Metadata API Developer Guide lists `sharingModel`
in the `CustomObject` field table and notes it is settable through the API
for internal users in version 30.0 and later. Section 4 owns the `SharingRules`
container, which is a different file with a different suffix. Writing "OWD =
Public Read/Write" as a Section 4 row hands `audit-router --domain=sharing` a
row whose artefact is not in its scope.

### Section 5 — Validation Rules

```markdown
| row_id | target_value | owner | source_req_id | source_story_id | recommended_agent | recommended_skills | status | notes |
|---|---|---|---|---|---|---|---|---|
| CWB-VR-101 | New VR `Lead_Tier_Requires_Score` on Lead: `AND(NOT(ISBLANK(TEXT(Qualification_Tier__c))), ISBLANK(Qualification_Score__c), NOT($Permission.Bypass_Lead_Validation))`, error on field `Qualification_Score__c` | D. Mensah | REQ-089 | US-3141 | audit-router --domain=validation_rule | admin/validation-rules; templates/admin/validation-rule-patterns.md | committed | Bypass clause depends on CWB-VR-102 deploying first. |
| CWB-VR-102 | New Custom Permission `Bypass_Lead_Validation`, granted through PS `Feat_DataLoadBypass` only | D. Mensah | REQ-089 | US-3141 | audit-router --domain=validation_rule | admin/validation-rules; admin/custom-permissions | committed | Bypass infrastructure. Must deploy before CWB-VR-101. |
```

The bypass is its own row because it is its own metadata component with its
own deploy position, and because `CWB-DAT-101` in Section 10 needs it to
exist before the backfill runs.

### Section 6 — Automation

```markdown
| row_id | target_value | owner | source_req_id | source_story_id | recommended_agent | recommended_skills | status | notes |
|---|---|---|---|---|---|---|---|---|
| CWB-AUT-101 | Before-save record-triggered Flow `Lead_Set_Qualification_Tier_v1` on Lead (create and update), sets `Qualification_Tier__c` from `Qualification_Score__c` | J. Park | REQ-088 | US-3140 | flow-builder | flow/record-triggered-flow-patterns; flow/flow-record-save-order-interaction | committed | `automation-selection.md` Q2 — same-record fields only, so before-save Flow, not Apex. |
| CWB-AUT-102 | Add entry 1 to the existing Lead assignment rule `Lead_Routing_v2`: `Qualification_Tier__c = Hot` routes to queue `SDR_Fast_Lane` | J. Park | REQ-091 | US-3143 | assignment-and-auto-response-rules-designer | admin/assignment-rules -> references/routing-selector.md; admin/assignment-rules -> references/metadata-examples.md | committed | `automation-selection.md` Q1 is a record change, but ownership routing is outside that tree's scope; resolved by `admin/assignment-rules` routing-selector row 1 (Lead has a rule engine). Reorders existing entries — whole rule file redeploys. |
```

---

## Rule 5 — how a row cites a decision-tree step

A tree name alone is decoration. The citation must name **the branch that
resolved the choice**, because that is what a reviewer disagrees with and
what the executing agent re-checks. The trees under
`standards/decision-trees/` label their branches `Q1`…`Q12`, so the citation
is `<tree>.md Q<n>` plus the one-clause reason:

| Row | Citation in `notes` | Why that branch |
|---|---|---|
| `CWB-AUT-101` | `automation-selection.md` Q2 — same-record fields only | Q2 asks whether the logic runs under ~10s and touches only fields on the triggering record; yes routes to before-save Flow |
| `CWB-AUT-102` | `automation-selection.md` Q1 is a record change, but ownership routing is outside that tree's scope; resolved by `admin/assignment-rules` → `references/routing-selector.md` row 1 | The routing selector states in its own opening that `automation-selection.md` decides Flow vs Apex and does not cover ownership routing |
| `CWB-SHR-101` | `sharing-selection.md` Q1 — Lead OWD is Public Read/Write, so no grant layer is needed | Q1 is "what is T's current OWD?", and a permissive OWD ends the walk |

`CWB-AUT-102` is the honest case worth copying: when the tree does **not**
cover the decision, say which branch you reached, say the tree stops there,
and name the skill reference that did resolve it. Silently omitting the
citation and silently inventing one are both worse.

---

## Rule 6 — a section with no work still gets a row

```markdown
## Section 9 — Integrations

| row_id | target_value | owner | source_req_id | source_story_id | recommended_agent | recommended_skills | status | notes |
|---|---|---|---|---|---|---|---|---|
| CWB-INT-101 | not-in-scope-this-release | D. Mensah |  |  |  |  | committed | No new Named Credential, Connected App, or event channel. |
```

`not-in-scope-this-release` is the only `target_value` that exempts a row
from `source_req_id`, `source_story_id`, `recommended_agent` and
`recommended_skills` — it has no upstream requirement and no downstream agent
by construction. It still needs a `row_id`, a named `owner` who asserted the
emptiness, and a `status`. An empty section is a statement someone signed;
a missing section is a hole nobody noticed.

---

## Rule 7 — descoped, deferred and escalated rows

These are **not** workbook rows, and the distinction is not cosmetic —
`agents/config-workbook-author/AGENT.md` Step 3 refuses with
`REFUSAL_DESCOPE_BREACH` if a story the steering committee marked `descope`
turns up in any row. Record them in a ledger that sits after Section 10:

```markdown
## Descope / Defer Ledger

| source_req_id | source_story_id | fit-gap decision | Recorded as | Rationale | Decided by | Date |
|---|---|---|---|---|---|---|
| REQ-093 | US-3145 | descope | No workbook row. Process Observations only. | Tier trend dashboards need a CRM Analytics licence the org has not bought. | Steering, 2026-09-05 | 2026-09-05 |
| REQ-094 | US-3146 | defer | No workbook row this release; carried to R4-2026. | Lead-to-Opportunity tier attribution depends on the R4 opportunity model. | Steering, 2026-09-05 | 2026-09-05 |
| REQ-095 | US-3147 | escalate | ADR required before any row is written. | Third-party routing product would become a second writer of `Lead.OwnerId`. | Architecture, 2026-09-05 | 2026-09-05 |
```

The ledger keeps a workbook honest in the direction reviewers never check:
it is easy to see that a row exists, and hard to see that a requirement
deliberately produced none. `REQ-095` is the one to watch — an escalated
requirement gets an ADR (`architect/architecture-decision-records`), not a
row, and any workbook that quietly grows one before the ADR lands has
skipped the decision.

---

## Rule 8 — the committed workbook produces the deployment manifest

The rows are not the deliverable on their own; they name the components a
deploy has to carry. Section by section, the committed rows above become one
manifest. The Metadata API Developer Guide's own framework applies: a
`<types>` element holds `<members>` (the component `fullName`) and `<name>`
(the metadata type), and `<version>` closes the `Package`.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <!-- CWB-VR-102 — deploys first; CWB-VR-101 references it -->
    <types>
        <members>Bypass_Lead_Validation</members>
        <name>CustomPermission</name>
    </types>
    <!-- CWB-OBJ-101, CWB-OBJ-102 -->
    <types>
        <members>Lead.Qualification_Score__c</members>
        <members>Lead.Qualification_Tier__c</members>
        <name>CustomField</name>
    </types>
    <!-- CWB-OBJ-102 — the restricted picklist's value set -->
    <types>
        <members>Lead_Qualification_Tier</members>
        <name>GlobalValueSet</name>
    </types>
    <!-- CWB-PSG-101 -->
    <types>
        <members>Feat_LeadQualification</members>
        <members>Feat_DataLoadBypass</members>
        <name>PermissionSet</name>
    </types>
    <!-- CWB-VR-101 -->
    <types>
        <members>Lead.Lead_Tier_Requires_Score</members>
        <name>ValidationRule</name>
    </types>
    <!-- CWB-AUT-101 -->
    <types>
        <members>Lead_Set_Qualification_Tier_v1</members>
        <name>Flow</name>
    </types>
    <!-- CWB-AUT-102 — the whole rule file redeploys, entries and all -->
    <types>
        <members>Lead</members>
        <name>AssignmentRules</name>
    </types>
    <version>62.0</version>
</Package>
```

How to read it:

- **One `<types>` block per metadata type, one `<members>` per component.**
  The `<members>` value is the component's `fullName`, which is why a row
  whose `target_value` is a Setup click-path cannot be turned into a
  manifest line at all.
- **The comments are the traceability.** Each `<types>` block names the
  `row_id` that produced it, so the manifest diffs against the RTM linkage
  block.
- **`AssignmentRules` takes the object name, not the rule name.** The guide
  gives both syntaxes: `<name>AssignmentRules</name>` with `<members>Case</members>`
  for every rule on an object, and the singular `<name>AssignmentRule</name>`
  with `<members>Case.samplerule</members>` for one named rule. Either way all
  of an object's assignment rules live in one `Lead.assignmentRules` file and a
  rule carries all of its entries, so `CWB-AUT-102`'s single new entry
  redeploys the ordered entry list — which is why its `notes` say so.
- **`<version>` is the API version you are deploying against.** The guide's
  own quick-start sample uses `66.0`; set it to the version your project
  targets rather than copying either number blindly.
- **Ordering inside `package.xml` does not control deploy order.** The
  cutover order lives in `CWB-DAT-101`'s `notes` and in the hand-off block,
  not here.

Retrieve, validate and deploy with the CLI commands the guide documents:

```bash
# Confirm the components named by the rows actually exist in the source org
sf project retrieve start --manifest manifest/package.xml --target-org acme-uat

# Validate-only against the target before the release window
sf project deploy start --dry-run -d "force-app/main/default" --target-org acme-prod
```

Verification step after the deploy, in the target org. A query that names
both Section 1 fields fails to compile if either did not land, which is the
point — a compiling query is the proof:

```sql
SELECT Id, Qualification_Score__c, Qualification_Tier__c
FROM   Lead
LIMIT  1
```

Then the negative test for Section 5: create one Lead with
`Qualification_Tier__c = Hot` and `Qualification_Score__c` blank and confirm
`Lead_Tier_Requires_Score` blocks the save with the error on the score field.
`admin/change-management-and-deployment` owns the release-window mechanics
this hands off to; the workbook stops at naming what must be verified.

---

## Rule 9 — the checker is the gate, not the review

Run it before setting any row to `committed`:

```bash
python3 skills/admin/configuration-workbook-authoring/scripts/check_workbook.py \
    --workbook docs/workbooks/R3-2026/cwb.md
```

A clean workbook:

```text
OK: workbook /path/to/docs/workbooks/R3-2026/cwb.md passes all checks.
```

The same feature written the way an assistant writes it on the first pass —
a Setup path for a `target_value`, two agents in one cell, a reused `row_id`,
a placeholder status, a skill slug nobody opened, a deprecated agent, and
Sections 4 and 6 with no tree branch — produces this:

```text
ERROR: [Objects + Fields] row CWB-OBJ-011: target_value reads as a Setup navigation path, not a metadata component — a row is executed and deployed by component fullName, and a click-path has none
ERROR: [Objects + Fields] row CWB-OBJ-011: status `TBD` is a placeholder — must be one of ['change-requested', 'committed', 'executed', 'in-progress', 'proposed', 'verified']
ERROR: [Objects + Fields] row CWB-OBJ-011: recommended_agent names more than one agent ('object-designer, flow-builder') — one row, one agent, one section. Split the row.
ERROR: [Sharing Settings] row CWB-SHR-004: recommended_agent `sharing-audit-agent` is deprecated — route to `audit-router` instead (see agents/_shared/AGENT_DISAMBIGUATION.md for the `--domain=` argument)
ERROR: [Sharing Settings] row CWB-SHR-004: recommended_skills entry `admin/lead-sharing-rules` does not resolve — skills/admin/lead-sharing-rules/SKILL.md does not exist
ERROR: [Sharing Settings] row CWB-SHR-004: no `sharing-selection.md` citation — every Sharing Settings row must name the decision-tree branch that resolved the choice (standards/decision-trees/sharing-selection.md)
ERROR: [Automation] row CWB-AUT-018: no `automation-selection.md` citation — every Automation row must name the decision-tree branch that resolved the choice (standards/decision-trees/automation-selection.md)
ERROR: [Objects + Fields] row CWB-OBJ-011: duplicate row_id — already used in section `Objects + Fields`. row_id must be unique across the whole workbook.

8 issue(s) found.
```

Exit code is `1`, so it fails a pre-commit hook or a CI step without further
wiring. `--allow-empty-section` suppresses the "section has no rows" finding
for a workbook that is still being drafted; do not pass it at sprint commit,
because Rule 6 is exactly what it turns off.

---

## What this file deliberately does not carry

- **A second full ten-section workbook.** Read
  `skills/admin/case-management-setup/references/worked-example-case-intake.md`.
- **The blank skeleton.** That is `templates/config-workbook.md`.
- **The content rules for each section's artefact.** A Section 5 row's
  formula is `admin/validation-rules`' subject; a Section 6 row's Flow shape
  is `flow/record-triggered-flow-patterns`'. The workbook says *which*
  component and *who* builds it, never *how* to build it.
