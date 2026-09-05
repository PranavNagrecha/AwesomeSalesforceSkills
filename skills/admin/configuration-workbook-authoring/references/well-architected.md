# Well-Architected Notes — Configuration Workbook Authoring

## Relevant Pillars

- **Operational Excellence** — the workbook is the central artifact between
  requirements (RTM) and metadata (deployment manifest). A schema-bound,
  version-locked workbook is the operational instrument that makes admin
  delivery reviewable, auditable, and routable to downstream agents.
- **Reliability** — by enforcing one row per addressable change with a
  required `source_req_id` and `source_story_id`, the workbook makes every
  deployed change traceable. Rollback is rollback of one row, not "the whole
  release."
- **Security** — workbook rows reference credentials and secrets by Named
  Credential alias only. Inline secrets are flagged at review time and by
  the stdlib checker, removing the most common path by which secrets land in
  version control.

## Architectural Tradeoffs

- **Schema rigor vs. authoring speed.** The 10-section structure with
  per-row mandatory fields adds upfront authoring overhead compared to
  free-text "build sheets." The tradeoff is fully repaid the first time a
  reviewer needs to know which fit-gap row drove a deployed field, or the
  first time the team needs to roll back a single change without unwinding
  the whole release.
- **Granularity vs. overhead.** "One row, one agent, one section" produces
  more rows than a feature-level row would. The tradeoff is essential: a
  multi-section row cannot be routed to a single agent and degrades the
  workbook into a wiki.
- **Version-lock vs. live edit.** Treating the committed workbook as
  immutable feels heavyweight, but in-place edits destroy the audit trail.
  Mid-sprint change requests open new rows that reference the superseded
  row(s) in `notes`.

## Anti-Patterns

1. **Workbook-as-wiki** — free-text bullet points without `row_id`,
   `source_req_id`, or `recommended_agent`. Looks fast on day one;
   untestable by week two.
2. **Multi-section rows** — a row that says "add object, grant PSG, build
   Flow" cannot be addressed by a single agent. Split or reject.
3. **Orphan rows** — rows missing `source_req_id` cannot be traced to the
   RTM and become permanent technical debt the moment they're deployed.
4. **In-place edits after sprint commit** — destroys the audit trail and
   lets reviewers approve a workbook that no longer matches what was
   deployed.
5. **Inline secrets** — workbook rows that paste API keys, tokens, or
   passwords directly into `target_value`. Use Named Credential aliases.

## Official Sources Used

This section is canonical for the whole package; `SKILL.md` points here.

### Salesforce platform documentation

- Metadata API Developer Guide — *Quick Start → Package.xml Manifest Structure* (the `<types>` / `<members>` / `<name>` / `<version>` framework, and that `<members>` holds a component `fullName` — the reason a `target_value` must name a component, not a Setup path; `references/worked-examples.md` Rule 8, `references/gotchas.md` Gotcha 9) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Metadata API Developer Guide — *Metadata Types → Profile* (the profile field table listing `layoutAssignments`, `loginHours`, `loginIpRanges`, `categoryGroupVisibilities` and `loginFlows`; that a returned profile's content depends on what else was in the `RetrieveRequest`; that profile deployment overlays rather than replaces and does not export disabled permissions; that editing standard objects on standard profiles is disabled in API version 50.0 and later — `references/gotchas.md` Gotcha 15) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Metadata API Developer Guide — *Metadata Types → SharingRules and CustomObject* (`sharingModel` is a `CustomObject` field, settable through the API for internal users in version 30.0 and later; sharing rules live in one `<Object>.sharingRules` file; manual sharing rules cannot be retrieved, deleted or deployed — `references/gotchas.md` Gotcha 13, `references/worked-examples.md` row `CWB-OBJ-103`) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Metadata API Developer Guide — *Metadata Types → AssignmentRules* (both manifest syntaxes: `AssignmentRules` with the object name for every rule on an object, `AssignmentRule` with `Object.rulename` for one; all of an object's rules live in one `.assignmentRules` file — `references/worked-examples.md` Rule 8, row `CWB-AUT-102`) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Metadata API Developer Guide — *Deploy and retrieve with Salesforce CLI* (`sf project retrieve start --manifest`, `sf project deploy start --dry-run` — the commands in `references/worked-examples.md` Rule 8) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Object Reference for the Salesforce Platform — *SetupAuditTrail* (rationale for source-grounded change records: the org records who changed what, and the workbook is the artefact that says why) — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_setupaudittrail.htm
- Salesforce Architects — *Center of Excellence decision guide* (the premise this skill rests on: a structured, reviewable handoff artefact between requirements and build) — https://architect.salesforce.com/decision-guides/center-of-excellence
- Salesforce Well-Architected — *Overview* (the Operational Excellence / Reliability / Security framing at the top of this file) — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html

### Repo standards this skill's artefact is bound to

- `agents/config-workbook-author/AGENT.md` — Step 3 (descope / defer / escalate handling and `REFUSAL_DESCOPE_BREACH`) and Step 6 (the three-step `recommended_agent` resolution: strip arguments, confirm `AGENT.md` exists, assert `status` is not `deprecated`). Both are implemented in `scripts/check_workbook.py` and documented in `references/worked-examples.md` Rules 2 and 7.
- `agents/_shared/SKILL_MAP.md` — the authoring reference for the runtime roster; its opening paragraph is the source of the rule that every cited skill id must be verified to exist before it is committed.
- `agents/_shared/AGENT_DISAMBIGUATION.md` — the deprecated-agent → `audit-router --domain=<x>` mapping the checker points at when a row names a Wave-3b auditor.
- `standards/decision-trees/automation-selection.md` — branch labels `Q1`…`Q12`; every Section 6 row cites one (`references/gotchas.md` Gotcha 12).
- `standards/decision-trees/sharing-selection.md` — branch labels `Q1`…`Q9`; every Section 4 row cites one (`references/gotchas.md` Gotcha 13).
- `skills/admin/requirements-traceability-matrix` § ID Conventions — fixes `source_req_id` as the RTM `REQ-XXX`, immutable and never reused.
- `skills/admin/permission-sets-vs-profiles` § What Only a Profile Can Hold — the profile-only residue list the Section 3 check exempts.
