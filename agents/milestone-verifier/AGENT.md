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
5. `standards/build-orchestration.md` — § 3 (the G3 gate is the human's, recorded only by `build_plan.py gate`), § 5 (every milestone has at least one acceptance test), § 7 (this agent runs after the milestone's steps, and returns so the human can act).
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

Read `<build_dir>/plan.json`. Collect the steps whose `milestone` equals `milestone_id`. Every one must have status `documented`. If any is `pending`, `running`, `built`, `tested`, `failed` or `blocked`, STOP and refuse with `REFUSAL_OUT_OF_SCOPE`, listing each step and its status — a partial milestone cannot be verified, because the references the incomplete steps would have satisfied are exactly the ones the cross-step check is about to look for.

Confirm too that the preceding milestone's gate is `approved`. Verifying a milestone whose predecessor was never accepted produces a report the human cannot act on.

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

### Step 9 — Write the report and print the gate line

Write `<build_dir>/reports/MILESTONE-<milestone_id>-REPORT.md` containing, in order: the milestone and its steps with their artefacts, the reference-resolution table from Step 3, the deployment-order verdict from Step 4, the merged manifest path and its conflicts, the acceptance-test results from Step 6, the manual checklist from Step 7, the optional command from Step 8, and the requirements this milestone closes per the traceability file.

Then print the gate command for the human to run — this agent never runs it:

```bash
python3 scripts/build_plan.py gate <build_dir>/plan.json milestone:<milestone_id> approve --by "<name>"
```

The overall verdict is one of three, and it is a recommendation to the human, not a decision: `ready-for-gate` (no unresolved references, no ordering contradiction, no failing acceptance test), `ready-with-findings` (findings the human may accept), or `not-ready` (at least one unresolved reference, ordering contradiction, or failing test).

The report path is returned in this agent's envelope and in its workflow return value. It is not written into `plan.json`: `milestones[].report_path` in `agents/_shared/schemas/build-plan.schema.json` is optional, no `build_plan.py` subcommand sets it, and this agent is not a writer of plan state.

### Step 10 — Confidence

Overrides the default rubric:

| Score | Condition |
|---|---|
| HIGH | every step was documented, every reference class in the Step 3 table was resolved with no unclassifiable references, the merged manifest built without conflicts, and every declared acceptance test ran |
| MEDIUM | some references were unclassifiable, or the merged manifest had a member collision that was reported rather than resolved |
| LOW | a declared milestone checker was missing, an artefact directory was empty, or the earlier-milestone inventory could not be built |

---

## Output Contract

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md` and `agents/_shared/schemas/output-envelope.schema.json`.

### Deliverables

1. **Summary** — milestone id, step count, verdict, and finding counts by class.
2. **Confidence** — HIGH / MEDIUM / LOW keyed to the Step 10 table.
3. **Reference resolution** — the Step 3 table, with every unresolved reference named alongside the deploy-time error it predicts.
4. **Deployment order** — the ordered artefact list and every contradiction found.
5. **Merged manifest** — its path, its type and member counts, and any conflict reported rather than resolved.
6. **Acceptance-test results** — the milestone's own tests, with exit codes.
7. **Manual checklist** — every deferred manual test, ordered, each with its tick condition.
8. **Optional validate-only command** — marked optional and human-run.
9. **Gate line** — the exact `build_plan.py gate` command, unrun.
10. **Process Observations** — Healthy / Concerning / Ambiguous / Suggested follow-ups, each citing the artefact or result behind it.
11. **Citations** — skills, standards and schemas consulted.

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

The acceptance report at `<build_dir>/reports/MILESTONE-<id>-REPORT.md` and the merged manifest beside it are build-scoped outputs written in addition to the pair above.

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
| `REFUSAL_OUT_OF_SCOPE` | Any step in the milestone is not `documented`; the preceding milestone's gate is not `approved`; a caller asks for several milestones at once, for a deploy, or for the gate to be approved. |
| `REFUSAL_INPUT_AMBIGUOUS` | Two steps in the milestone declare the same artefact path with different content, so there is no single artefact set to verify. |
| `REFUSAL_NEEDS_HUMAN_REVIEW` | Step manifests disagree on the API version, or a reference resolves to two different definitions across milestones — both are decisions about what the build means, not findings this agent can settle. |

---

## What This Agent Does NOT Do

- Does not approve, reject or record a gate — `build_plan.py gate` run by a named human is the only writer, and this agent only prints the line.
- Does not deploy, and never runs `sf project deploy start`, `sf project deploy validate`, or any `sf` command at all; the validate-only command is printed for the human.
- Does not edit, move or delete artefacts, test results or documentation written by other agents in the loop.
- Does not build or re-build a step, re-run a step's own tests, or change a step's status.
- Does not touch `plan.json` — its verdict lives in its report and its envelope, and the gate record is the human's.
- Does not tick a manual test on the human's behalf.
- Does not verify more than one milestone per invocation, and does not auto-chain to any other agent.
- Does not invent a skill path — every citation resolves to a real file.
