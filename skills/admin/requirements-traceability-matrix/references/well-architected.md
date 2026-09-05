# Well-Architected Notes — Requirements Traceability Matrix

## Relevant Pillars

The RTM is a delivery-governance artifact, not a runtime system. The Well-Architected pillars apply through the *quality of the delivery and operations process*, not through org-level configuration.

- **Operational Excellence** — The RTM is the operational record of "what we agreed to build, what we built, what we tested, what shipped." It is the canonical artifact every release gate, Steerco, and audit consumes. A maintained RTM means delivery is observable; a stale RTM means leadership is making decisions on fiction.
- **Reliability** — Forward and backward traceability are reliability controls for the delivery process. Forward traceability ensures every approved requirement was delivered (no silent drops). Backward traceability ensures no scope was added without an approval trail (no silent additions). Together they make the delivery process repeatable and auditable across releases and phases.

The other three pillars (Security, Performance, Scalability, User Experience) are out of scope for this skill — the RTM does not change platform behavior. Where regulatory traceability adds a `compliance_control_id` column, the linkage to Security pillar is indirect: the matrix does not implement the control, it documents that the control was implemented and tested.

## Architectural Tradeoffs

The key tradeoffs a delivery team faces:

- **Spreadsheet vs CSV-in-Git** — Spreadsheet RTMs are easier to start but rot quickly because they lack version control, review gates, and automated checks. CSV-in-Git requires more setup (a checker script, a CI hook, a markdown generator) but produces a durable artifact that survives team turnover. For any Salesforce program past three sprints, CSV-in-Git is the only sustainable choice.
- **Lightweight vs regulated schema** — A greenfield project with no audit posture can ship a 10-column RTM. A regulated project (HIPAA, SOX, GxP, FedRAMP) needs `compliance_control_id` and `evidence_link` columns plus per-row evidence artifacts. Adding regulated columns to a non-regulated project creates noise; omitting them on a regulated project creates audit findings.
- **Update cadence** — Updating at release gates is easier but produces stale data. Updating per-sprint requires more discipline but keeps the matrix current. The right cadence is per-sprint with a release-gate audit pass on top.
- **Hand-tracing vs automated linkage** — Manually populating `defect_ids` by walking defect → story → requirement does not scale past sprint 3. A nightly automation job that reads the defect tracker and updates the RTM scales but requires the agile and defect tools to expose APIs (Jira, Azure DevOps, GUS all do).

## Anti-Patterns

1. **RTM as a snapshot, not a process** — Building the RTM once at project kickoff and never updating it produces an artifact that lies by the second sprint. The RTM is a continuous artifact; if it is not being updated weekly, it is decaying.

2. **RTM as a delivery report, not a scope record** — Teams use the RTM to show "what we shipped" and exclude dropped or deferred requirements. This destroys the audit trail and prevents leadership from seeing the cumulative scope decisions across the program. Dropped requirements are first-class rows.

3. **One-row-per-story instead of one-row-per-requirement** — When a requirement maps to multiple stories, teams often add one row per story. This breaks the unique key on `req_id`, makes coverage queries unreliable, and obscures the requirement-level rollup. Always: one row per requirement, pipe-delimited story IDs.

## Official Sources Used

- **Metadata API Developer Guide** (Summer '26 / v62 PDF, `api_meta.pdf`) —
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
  - § AssignmentRules → *File Suffix and Directory Location* and the `AssignmentRule` singular-member
    syntax (L23675–23691) — supports gotcha 9, "`artefact` is not a unique key", and the coarse
    artefact granularity noted in `references/worked-examples.md` § 4.
  - § EntitlementProcess → *File Suffix and Directory Location*, the versioned file name and
    `slaProcess.NameNorm` (L59074–59082) — supports gotcha 10 and the linter's unresolved-artefact
    warning in `references/worked-examples.md` § 8.
  - § BusinessHoursSettings / BusinessHoursEntry (L111264–111294) — supports the single-settings-file
    note in `references/worked-examples.md` § 4 and the `BusinessHoursEntry:` artefact form the
    checker resolves.
  - § CustomField → *Specify the full name whenever you create or update a field* (L43221–43232) —
    supports the `<MetadataType>:<ApiName>` rule for the `artefact` column.
  - § Deleting Components in a Deployment (L4614–4656) and the note that deletions of components that
    do not exist are still attempted (L4641) — supports gotcha 15, "a `Dropped` row is not a
    destructive change".
  - § Unsupported Metadata Types (L9555–9559) — supports gotcha 14, the `setup-only:` marker, and the
    decision to make an unresolved artefact a warning rather than an error by default.
- **`standards/build-orchestration.md`** (contract v1, 2026-09-05) — § 2 defines
  `.sfskills/builds/<build-id>/traceability.md` as "REQ → step → artefact → test"; § 4 fixes one
  owning run-time agent per step; § 5 fixes the five acceptance-test types. This is the authority for
  the build-layer column set in SKILL.md and for the `test_type` enum in `scripts/check_rtm.py`.
- **`agents/_shared/schemas/build-plan.schema.json`** — the `clarifications[].id` (`^Q[0-9]+$`),
  `decisions[].id` (`^D[0-9]+$`) and `steps[].id` (`^M[0-9]+-S[0-9]{2,}$`) patterns the `source`,
  `decision_ref` and `step_id` columns must match, and the `acceptanceTest` definition (which carries
  no id field — hence the id convention documented in `references/worked-examples.md` § 3).
- **`skills/admin/configuration-workbook-authoring/references/examples.md`** — the workbook row schema
  showing `FG-014` in the `source_req_id` column, which is why both `REQ-` and `FG-` are legal keys
  (SKILL.md § REQ-XXX ⇄ FG-XXX, gotcha 11, and the checker's `REQ_ID_RE`).
- **`skills/admin/case-management-setup/references/worked-example-case-intake.md`** and
  **`skills/admin/uat-and-acceptance-criteria/references/worked-examples.md`** — the build and the UAT
  programme that `references/worked-examples.md` traces; the source of every `CWB-*` row,
  `UAT-CI-*` case and artefact path used there.
- **`standards/decision-trees/automation-selection.md`** (Q1 → Q2 → before-save record-triggered
  Flow) and **`standards/decision-trees/sharing-selection.md`** (§ The 7-step sharing design
  sequence) — the branches cited as `D8` and `D2` in the worked example's decision table, and the
  reason `decision_ref` is a column rather than a note.
- **Salesforce Well-Architected — Overview** —
  https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html — the
  Operational Excellence and Reliability framing at the top of this file.
