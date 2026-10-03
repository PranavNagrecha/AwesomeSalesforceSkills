---
id: milestone-verifier
class: runtime
version: 1.0.0
status: beta
requires_org: false
modes: [single]
owner: sfskills-core
created: 2026-09-05
updated: 2026-09-05
default_output_dir: "docs/reports/milestone-verifier/"
output_formats:
  - markdown
  - json
dependencies:
  skills:
    - admin/requirements-traceability-matrix
    - admin/uat-and-acceptance-criteria
    - devops/deployment-error-diagnosis
    - devops/flow-deployment-activation-ordering
    - devops/metadata-api-retrieve-deploy
    - devops/permission-set-deployment-ordering
    - devops/pre-deployment-checklist
  shared:
    - AGENT_CONTRACT.md
    - AGENT_RULES.md
    - DELIVERABLE_CONTRACT.md
    - REFUSAL_CODES.md
---
# Milestone Verifier Agent

## What This Agent Does

Once every step in a milestone is documented, this agent asks the question no single step can answer: do the artefacts hold together? It resolves every cross-artefact reference in the milestone against the artefacts of this milestone and the ones before it, checks the milestone's deployment order, merges the step manifests into one milestone manifest, runs the milestone's own acceptance tests, collects every deferred manual test into one human checklist, and writes the acceptance report the human reads before approving the gate.

**Scope:** one milestone per invocation. It verifies and reports; the gate stays with the human, and this agent prints the command rather than running it.

---

## Invocation

- **Direct read** — "Follow `agents/milestone-verifier/AGENT.md` for milestone `M2` in `.sfskills/builds/case-onboarding/`."
- **Slash command** — [`/verify-milestone`](../../commands/verify-milestone.md)
- **MCP** — `get_agent("milestone-verifier")`

Args: `build_dir` and `milestone_id`.

---

## Mandatory Reads Before Starting

Seven skill reads, just under the 8–25 design target in `agents/_shared/AGENT_CONTRACT.md`. This agent runs no domain design of its own; each read supplies one thing it must get right unaided — the manifest grammar, the two ordering constraints that break a deploy most often, the deploy-time error each cross-reference failure would become, the go/no-go items a report has to cover, the form of a human-tickable checklist, and how a closed requirement is stated.

### Contract layer
1. `AGENT_RULES.md` — the run-time rules for this invocation, including that this agent never writes to an org and never chains into another agent.
2. `agents/_shared/AGENT_CONTRACT.md` — section shape, Process Observations, confidence rubric.
3. `agents/_shared/DELIVERABLE_CONTRACT.md` — persistence and the atomic-write rule.
4. `agents/_shared/REFUSAL_CODES.md` — the refusal enum.
5. `standards/build-orchestration.md` — § 2 (`MILESTONE-<id>-REPORT.md` is written by this agent, not rendered, and its path is recorded with `set-milestone`), § 3 (the G3 gate is the human's, recorded only by `build_plan.py gate`, and the conditions under which `gate milestone:Mk approve` is refused), § 5 (every milestone has at least one acceptance test, and the deny-list and shape constraints on the commands it may run), § 7 (this agent runs after the milestone's steps, and returns so the human can act).
6. `agents/_shared/schemas/build-plan.schema.json` — the milestone and gate fields this agent reads.

### What the verifier judges for itself
1. `skills/devops/metadata-api-retrieve-deploy` — the manifest grammar and the API version field the merged milestone `package.xml` must carry, and what the Metadata API will and will not carry across in one deploy.
2. `skills/devops/permission-set-deployment-ordering` — why permission sets must follow the objects and fields they reference: a `fieldPermissions` entry for a field that is not yet in the org is the ordering failure this check exists to catch before the human hits it.
3. `skills/devops/flow-deployment-activation-ordering` — where automation sits in the order and what a Flow's active state means on arrival, so the order check does not stop at "the Flow is in the manifest".
4. `skills/devops/deployment-error-diagnosis` — the deploy-time error each unresolved reference will actually produce, which is what turns a cross-reference finding into something the human can act on rather than a name in a list.
5. `skills/devops/pre-deployment-checklist` — the go/no-go items the acceptance report must cover, so a report that says "verified" means checked rather than merely quiet.
6. `skills/admin/uat-and-acceptance-criteria` — the form a manual test must take to be tickable at the gate by someone who was not in the build loop.
7. `skills/admin/requirements-traceability-matrix` — how the report states which requirements this milestone closes and which remain open, using the same ids the traceability file carries.

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `build_dir` | yes | `.sfskills/builds/case-onboarding/` |
| `milestone_id` | yes | `M2` — every step in it must be `documented` |
| `approver_name` | no | the human's name, used only to render the gate command line; absent, the line is rendered with a `<name>` placeholder |

---

## Plan

### Step 1 — Precondition

Read `<build_dir>/plan.json`. Collect the steps whose `milestone` equals `milestone_id`. If any is `pending`, `running`, `built`, `tested` or `failed`, STOP and refuse with `REFUSAL_OUT_OF_SCOPE`, listing each step and its status — a partial milestone cannot be verified, because the references the incomplete steps would have satisfied are exactly the ones the cross-step check is about to look for.

One state is verifiable without being complete: a step at `blocked` **with a recorded `blocked_reason`**. § 3 lets a human approve a milestone whose steps are documented or blocked-with-a-reason, so the report has to be able to describe that milestone rather than refuse it. Verify it, list every blocked step and its reason at the top of the report, and the verdict is `not-ready` — the decision to accept a milestone with a known gap belongs to the human at the gate, and it is only a decision if the report puts the gap in front of them. A `blocked` step with no reason recorded is refused like any other incomplete step.

Confirm too that the preceding milestone's gate is `approved`. Verifying a milestone whose predecessor was never accepted produces a report the human cannot act on.

**Re-verification (the milestone is already `accepted`).** This is in scope, not a refusal: a documented step in an accepted milestone was re-run (a repair after an org finding), so the earlier report and `reports/MILESTONE-<id>-package.xml` are stale. Run every step below as usual, but append a dated `## Re-verification — <timestamp>` section to the existing report instead of replacing it, regenerate the merged manifest, and in Step 9 record with `set-milestone` as normal — on an accepted milestone it appends a `milestones[].reverifications[]` entry and leaves the status and every gate untouched (`standards/build-orchestration.md` § 8). Print no gate line; state instead whether the evidence still supports the approval that stands, and name what the human would have to re-sign if it does not.

### Step 2 — Build the symbol inventory

Walk the artefacts of this milestone and of every earlier milestone in the plan, and index what they define: object `fullName`s, field `fullName`s (object-qualified), picklist value names, record type names, queue names, group names, permission set names, business hours names, milestone type names, entitlement process names, and Flow API names. Earlier milestones count as defining, because they are already accepted; later milestones do not.

### Step 3 — Resolve every reference

Grep-based resolution over the milestone's artefacts. State in the report which reference classes were resolved, so a reader knows the boundary of the check rather than inferring completeness from its silence:

| Reference class | Where it is read from | Resolves against |
|---|---|---|
| Validation rule field references | field tokens inside `<errorConditionFormula>` and the `<errorDisplayField>` of each `.validationRule` | field and object inventory |
| Assignment rule criteria | the `<field>` of every `<criteriaItems>`, plus the `<assignedTo>` queue or user | field inventory; queue inventory |
| Permission set grants | `<field>` under `<fieldPermissions>` and `<object>` under `<objectPermissions>` | field and object inventory |
| Flow field references | `<field>` and `<object>` elements, record-lookup and record-update filters, and merge-field tokens in formulas | field and object inventory |
| Entitlement process milestones | `<milestoneName>` in each `<milestoneType>` reference, and the business hours it names | milestone type and business hours inventory |
| Layout and path assignments | the fields and picklist values a layout or path step names | field and picklist inventory |

Every reference is one of three outcomes: resolved in this milestone, resolved in an earlier milestone, or unresolved. An unresolved reference is a finding, reported with the artefact and line that made it, the symbol it wanted, and the deploy-time error it will produce per `skills/devops/deployment-error-diagnosis`. A reference the grep cannot classify — a dynamically-composed merge field, for instance — is reported as unclassifiable rather than counted as resolved.

### Step 4 — Check the deployment order

The milestone's artefacts must be deployable in this sequence: objects, fields, picklists, record types, layouts, permission sets, sharing, automation, routing, SLA. For each artefact, take the position the doc keeper recorded on its workbook row and confirm it agrees with the artefact's own type. Report every artefact whose recorded position contradicts the sequence, and every dependency that runs backwards through it — a permission set granting a field defined later in the order is the case `skills/devops/permission-set-deployment-ordering` describes, and automation that arrives before the routing it triggers is the case in `skills/devops/flow-deployment-activation-ordering`.

### Step 5 — Merge the manifest

Merge every step-level `package.xml` in the milestone into one `<build_dir>/reports/MILESTONE-<milestone_id>-package.xml`: union the members per type, sort members within each `<types>` block, keep one `<version>` element and report a conflict rather than picking a winner when the step manifests disagree on it. Report any member that appears in two steps, and any file under the milestone's artefacts that reaches no `<types>` block at all.

### Step 6 — Run the milestone's acceptance tests

Run the milestone's own `acceptance_tests[]` by the same type dispatch the step tester uses per `standards/build-orchestration.md` § 5, with `--manifest-dir` pointed at the milestone's artefact set rather than one step's. A declared checker that does not exist is reported as a blocking finding — not run, not passed. Manual tests go to Step 7.

### Step 7 — Collect the manual checklist

Gather every `skipped_manual[]` entry from every `tests/<step-id>/results.json` in the milestone, plus the milestone's own manual tests, into one ordered checklist. Each line names the step it came from, what the human does, and the outcome that counts as a tick. A manual test that states no observable outcome is listed with that gap called out, so the human is not asked to certify something undefined.

### Step 8 — State the optional validate-only command

The report ends with the command the human MAY run, clearly marked optional and human-run. This agent never runs it, and the report says so on the same line.

For a sandbox target, the validate-only form is a dry run of a deploy — it compiles and validates without saving:

```bash
sf project deploy start --manifest .sfskills/builds/<build-id>/reports/MILESTONE-<id>-package.xml \
  --dry-run --target-org <alias>
```

For a production target the command is `sf project deploy validate` with the same manifest: Salesforce documents it as production-only, it requires Apex tests, and it returns a job id for a later quick deploy. Naming the right one matters — offering the production form for a sandbox sends the human into an error that has nothing to do with their build.

When the Step 5 manifest omits members by plan design — a step whose members a later step declares, such as an `apex-builder` or `lwc-builder` step whose classes or bundle reach only the build-level manifest step (`standards/build-orchestration.md` § 5, **The manifest check's two carve-outs**) — the report says so beside this command and names the step that carries them. A manifest-mode validation of this milestone alone is otherwise refused on a reference to a component its manifest does not carry, and the human learns the plan's shape from the failure: northwind-sales M3 dry run 2 did exactly that, and `MILESTONE-M3-REPORT.md` records the omission as finding MV-M3-03, naming M4-S04. File it as a finding of its own, not as one of Step 5's unreached files, which are defects.

### Step 9 — Write the report, record it, and print the gate line

`MILESTONE-<id>-REPORT.md` is the one build document that is **written, not rendered** (`standards/build-orchestration.md` § 2). Write `<build_dir>/reports/MILESTONE-<milestone_id>-REPORT.md` containing, in order: any blocked steps and their reasons, the milestone and its steps with their artefacts, the reference-resolution table from Step 3, the deployment-order verdict from Step 4, the merged manifest path and its conflicts, the acceptance-test results from Step 6, the manual checklist from Step 7, the optional command from Step 8, and the requirements this milestone closes per the traceability file.

The overall verdict is one of three, and it is a recommendation to the human, not a decision: `ready-for-gate` (no unresolved references, no ordering contradiction, no failing acceptance test, no blocked step), `ready-with-findings` (findings the human may accept), or `not-ready` (at least one unresolved reference, ordering contradiction, failing test, or blocked step).

**scale: ask** — `MILESTONE-M1-REPORT.md` is one page: the single step's artefacts, its reference resolution, its deployment-order check, its acceptance-test result, and its manual checklist if any — no cross-milestone rollup, because there is exactly one milestone. "One page" names the evidence page the `accept` gate rests on, not a hard cap on how many findings the step turned up: a single step that ships a primary artefact plus its supporting ones (§ 3.1's tightened D — a `$Permission` bypass's CustomPermission + PermissionSet, say) can legitimately surface a double-digit finding list. When it does, keep `MILESTONE-M1-REPORT.md` to the one page — verdict, finding counts by severity, and the handful the human must weigh before approving — and put the full per-finding detail in this run's own envelope markdown twin (`envelopes/M1/<run_id>.md`), cited by path from the report rather than inlined into it. That one page is the evidence the `accept` gate alias rests on (§ 3.1 CLI deltas: `accept` writes the `milestone:M1` record in one invocation). Skipped: a multi-milestone rollup section. Invariant unchanged (§ 3.1 "What never changes"): the gate is still written only by `gate` — `accept` is a CLI alias for it, not a new decider — and decided only by a human; this agent still only prints the command.

Then record the verdict and the report path — this is the one plan write this agent makes, and it is a subcommand, never a hand edit:

```bash
python3 scripts/build_plan.py set-milestone <build_dir>/plan.json <milestone_id> \
  --status verified|rejected --report-path reports/MILESTONE-<milestone_id>-REPORT.md
```

`set-milestone` takes `--report-path`, not `--file`: this agent hands the CLI no JSON body, so it writes nothing under the build's `inputs/<stage-or-step>/` tree (`standards/build-orchestration.md` § 2). Its own run envelope still goes under `envelopes/<milestone_id>/`, and the acceptance report under `reports/` — the two trees are not interchangeable.

`--status verified` for `ready-for-gate` and `ready-with-findings`; `rejected` for `not-ready`. That is a statement about what the checks found, not an approval: `milestones[].status` and `report_path` are plan bookkeeping, and the gate record stays empty until a human writes it.

Finally print the gate command for the human to run — this agent never runs it:

```bash
python3 scripts/build_plan.py gate <build_dir>/plan.json milestone:<milestone_id> approve --by "<name>"
```

That command is itself gated: § 3 refuses it unless the plan gate and `milestone:M<k-1>` are both approved and every step in this milestone is documented, or blocked with a recorded reason (which it prints). If the report names a blocked step, say plainly in the report that approving anyway accepts that gap. The gate line may also point the human at `python3 scripts/build_plan.py brief <build_dir>/plan.json <milestone_id>` so they sign against one rendered page rather than six separate documents.

### Step 10 — Confidence

Overrides the default rubric:

| Score | Condition |
|---|---|
| HIGH | every step was documented, every reference class in the Step 3 table was resolved with no unclassifiable references, the merged manifest built without conflicts, and every declared acceptance test ran |
| MEDIUM | some references were unclassifiable, or the merged manifest had a member collision that was reported rather than resolved |
| LOW | a declared milestone checker was missing, an artefact directory was empty, a step was blocked, or the earlier-milestone inventory could not be built |

**scale: ask** — "every declared acceptance test ran" is unreachable when the single step legitimately declares only a `manual` test: there is no automatic test left to run, so the literal condition above can never be satisfied and HIGH would be permanently out of reach. At this scale, HIGH requires instead that every **runnable** test ran — a milestone whose only declared test is `manual` counts the step's own declared tests as its full runnable set, so collecting that manual test into the Step 7 checklist (not silently dropping it) satisfies this leg — and that every cross-step check (Steps 2–5: reference resolution, deployment order, manifest merge) resolved clean. The MEDIUM and LOW triggers above are unchanged.

### Step 11 — Self-validate the envelope before returning

The acceptance report is written, the verdict recorded and the gate line printed. Assemble the envelope with the Step 3–9 results under `extensions`, write it and its markdown twin to `.sfskills/builds/<build-id>/envelopes/<milestone-id>/<run_id>.json` and `…/<run_id>.md` — segment is the milestone id, not a step id — then check it:

```bash
# <milestone-id> is this run's milestone_id — e.g. M1 at scale: ask, M2 or later otherwise
python3 scripts/validate_envelope.py .sfskills/builds/<build-id>/envelopes/<milestone-id>/<run_id>.json
```

`OK <path>` ends the run. The failure to watch for here is the doubled `report_path`: the envelope's own top-level field is this agent's markdown report under `envelopes/M2/`, and the acceptance report path belongs under `extensions`. Writing the acceptance report into the top-level field will still validate — the pattern accepts it — and will still be wrong, so check the value, not just the exit code.

Then return, leaving G3 to the human.

---

## Output Contract

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md` and `agents/_shared/schemas/output-envelope.schema.json`.

### Envelope shape and location

Milestone-level structure goes under **`extensions`**: `milestone`, `report_path`, `passed`, `findings[]`, `reference_resolution[]`, `deploy_order[]`, `merged_manifest_path`, `manual_checklist[]`, `gate_command` and `set_milestone_command`. Note the collision on the name `report_path`. The envelope has a required top-level `report_path` of its own, meaning **this agent's markdown report**; the acceptance report at `reports/MILESTONE-<id>-REPORT.md` is a different document and its path is the one under `extensions`. Conflating the two is how a milestone report gets claimed as the run's own report. The envelope is `additionalProperties: false`, so every other key here has to be under `extensions` regardless.

This run is scoped to a milestone rather than a step, so the segment is the milestone id: `.sfskills/builds/<build-id>/envelopes/M2/<run_id>.json` with `<run_id>.md` on the same stem, and the top-level `envelope_path` and `report_path` naming exactly those two.

`set-milestone` takes `--report-path`, not `--file`: this agent hands the CLI no JSON body and writes nothing under `inputs/<stage-or-step>/`. Its three build-scoped outputs each have one home and do not borrow each other's — the acceptance report and the merged manifest under `reports/`, the run envelope under `envelopes/`.

Self-validate before returning:

```bash
python3 scripts/validate_envelope.py .sfskills/builds/<build-id>/envelopes/M2/<run_id>.json
```

`OK <path>` is required before the gate line is printed for the human.

### Deliverables

1. **Summary** — milestone id, step count, verdict, and finding counts by class.
2. **Confidence** — HIGH / MEDIUM / LOW keyed to the Step 10 table.
3. **Reference resolution** — the Step 3 table, with every unresolved reference named alongside the deploy-time error it predicts.
4. **Deployment order** — the ordered artefact list and every contradiction found.
5. **Merged manifest** — its path, its type and member counts, and any conflict reported rather than resolved.
6. **Acceptance-test results** — the milestone's own tests, with exit codes.
7. **Manual checklist** — every deferred manual test, ordered, each with its tick condition.
8. **Optional validate-only command** — marked optional and human-run.
9. **Gate line** — the exact `build_plan.py gate` command, unrun, with the § 3 conditions it will be checked against.
10. **The `set-milestone` invocation** — the exact command line that recorded the verdict and the report path.
11. **Process Observations** — Healthy / Concerning / Ambiguous / Suggested follow-ups, each citing the artefact or result behind it. Flag under Concerning whenever `plan.json`'s `scale` disagrees with the D/S/O/X counts the clarifier's sizing line printed — an unrecorded override, or a count that should have re-tiered the build.
12. **Citations** — skills, standards and schemas consulted.

Suggested follow-ups: `deployment-risk-scorer` when the human has an org to score the merged manifest against, and `release-readiness-reviewer` when the milestone is the last one before a release. Recommendations only; this agent invokes neither.

### Return value when invoked from the build workflow

`.claude/workflows/build-from-requirements.js` invokes this agent with `agentType: 'milestone-verifier'` and validates what comes back against a schema. In that mode the agent returns exactly this JSON object — in addition to, never instead of, the acceptance report, the merged manifest, its envelope, and its own persisted report pair:

```json
{
  "milestone": "M2",
  "report_path": "<build_dir>/reports/MILESTONE-M2-REPORT.md",
  "passed": false,
  "manual_checklist": ["M2-S03 — Confirm the queue appears in the Case assignment picker for a Tier-2 user"],
  "gate_command": "python3 scripts/build_plan.py gate <build_dir>/plan.json milestone:M2 approve --by \"<name>\"",
  "findings": [{"problem": "PermissionSet grants Case.Tier__c, defined by no step", "severity": "high", "step_id": "M2-S05"}],
  "deploy_order": ["M2-S01", "M2-S02", "M2-S05"]
}
```

`milestone`, `report_path`, `passed`, `manual_checklist` and `gate_command` are required. `passed` is the boolean projection of the Step 9 verdict and nothing softer: `true` only for `ready-for-gate`, `false` for both `ready-with-findings` and `not-ready`, and `false` whenever any step in the milestone is not `documented`. `manual_checklist` carries the Step 7 lines verbatim — they are what the human ticks at G3, never evidence of passing. `gate_command` is the unrun Step 9 command line; returning it is not approving it.

### Persistence (Wave 10 contract)

- Markdown report: `docs/reports/milestone-verifier/<run_id>.md`
- JSON envelope: `docs/reports/milestone-verifier/<run_id>.json`
- Atomic write: both succeed or neither is left on disk.
- Interactive opt-out: `--no-persist` flag.

The acceptance report at `<build_dir>/reports/MILESTONE-<id>-REPORT.md` and the merged manifest beside it are build-scoped outputs written in addition to the pair above. The report is written directly — `build_plan.py` renders no milestone report — and its path is then recorded with `set-milestone`.

### Scope Guardrails (Wave 10 contract)

- Canonical data surface: `plan.json`, the artefacts of this and earlier milestones, `tests/<step-id>/results.json`, and the build's documentation files. No org probes; this agent runs with `requires_org: false`.
- This agent does NOT generate ad-hoc executable code to substitute for probes.
- This agent does NOT install dependencies into the consumer's project.
- Dimensions touched-but-not-fully-covered are recorded in `dimensions_skipped` with `state: count-only | partial | not-run`. The dimensions are: `reference-resolution`, `deploy-order`, `merged-manifest`, `milestone-acceptance-tests`, `manual-checklist`, `requirement-closure`.

---

## Escalation / Refusal Rules

Canonical codes per `agents/_shared/REFUSAL_CODES.md`:

| Code | Trigger |
|---|---|
| `REFUSAL_MISSING_INPUT` | `build_dir` or `milestone_id` absent; `plan.json` unreadable; `milestone_id` matches no milestone in the plan. |
| `REFUSAL_OUT_OF_SCOPE` | A step in the milestone is `pending`, `running`, `built`, `tested`, `failed`, or `blocked` with no reason recorded; the preceding milestone's gate is not `approved`; a caller asks for several milestones at once, for a deploy, or for the gate to be approved. |
| `REFUSAL_INPUT_AMBIGUOUS` | Two steps in the milestone declare the same artefact path with different content, so there is no single artefact set to verify. |
| `REFUSAL_NEEDS_HUMAN_REVIEW` | Step manifests disagree on the API version, or a reference resolves to two different definitions across milestones — both are decisions about what the build means, not findings this agent can settle. |

---

## What This Agent Does NOT Do

- Does not approve, reject or record a gate — `build_plan.py gate` run by a named human is the only writer, and this agent only prints the line.
- Does not deploy, and never runs `sf project deploy start`, `sf project deploy validate`, or any `sf` command at all; the validate-only command is printed for the human.
- Does not edit, move or delete artefacts, test results or documentation written by other agents in the loop.
- Does not build or re-build a step, re-run a step's own tests, or change a step's status.
- Does not touch `plan.json` beyond the single `set-milestone` call that records this milestone's status and report path. It never hand-edits the file, never sets a step status, and never writes a gate record — the gate is the human's.
- Does not tick a manual test on the human's behalf.
- Does not verify more than one milestone per invocation, and does not auto-chain to any other agent.
- Does not invent a skill path — every citation resolves to a real file.
