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

- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Architects: Center of Excellence playbook (workbook-driven implementation handoff) — https://architect.salesforce.com/decision-guides/center-of-excellence
- Salesforce Help: Track changes to your org with Setup Audit Trail (rationale for source-grounded change records) — https://help.salesforce.com/s/articleView?id=sf.setup_audit_trail.htm
