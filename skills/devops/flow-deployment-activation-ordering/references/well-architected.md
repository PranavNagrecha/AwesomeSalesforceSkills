# Well-Architected Notes — Flow Deployment & Activation

## Relevant Pillars

- **Reliability** — the platform gives flows a rollback property most metadata
  does not have: the previous version is still in the org, and activating it is
  one click. That is only usable by a team that recorded which version was active
  before deploying, which makes the pre-deploy capture the load-bearing practice
  in this whole domain.
- **Operational Excellence** — deploy success means metadata was saved. The
  pre-state/post-state diff of `FlowDefinitionView` is what converts that into
  "the intended version is active and nothing else moved," including changes
  nobody in the release caused.
- **Security and Compliance** — version retention interacts with audit
  obligations in regulated industries, and with the paused-interview population,
  which since Spring '24 has no platform cap. Retention is a policy decision, not
  a housekeeping one.

## Architectural Tradeoffs

- **Deploy active vs deploy Draft then activate:** deploying active is one step
  and leaves no verification window. Draft-then-activate costs a second
  deployment and gives you a version in the org you can smoke-test before it
  takes traffic. Use the second for anything with paused interviews, subflow
  callers, or a scheduled run in the next few hours.
- **`Flow.status` vs `FlowDefinition.activeVersionNumber`:** `status` is the
  recommended mechanism and expresses "this new version should be active."
  `FlowDefinition` is the only one that can point at an *existing* version, which
  is precisely what rollback needs. Using both in one package is the documented
  failure case.
- **Retention depth vs deletion risk:** retaining versions protects paused
  interviews and rollback depth, and brings the per-flow version ceiling closer.
  Three inactive versions plus a policy cap keeps both risks bounded.
- **Deactivation vs caller gating as a kill switch:** deactivation is one action
  and does not stop subflow callers or, reliably, Apex callers. A feature flag in
  the caller is more to build and actually works. For anything with callers,
  build the flag.
- **Fast rollback vs data remediation:** activating the previous version is
  seconds and repairs nothing already written. Stamping a version or run id on
  records the flow touches costs a field and turns remediation from forensics
  into a query.

## Hygiene

- Pre-deploy capture of active version per flow per environment, stored with the
  release artifact.
- Pre-deploy snapshot of `FlowInterview` for the flows in scope.
- New versions deploy as `Draft` when there is anything to verify; `Obsolete` is
  never chosen deliberately.
- `FlowDefinition` is absent from routine packages.
- Activation order is child-then-parent for subflows, as a separate step from
  the deploy.
- Post-deploy diff of `FlowDefinitionView`, with unexplained rows treated as
  findings.
- One real interview run per changed flow, through its actual entry point.
- Version deletion gated on zero interview references, not on age.
- The production-only "Deploy processes and flows as active" preference and its
  coverage percentage are checked during release readiness, not at deploy time.

## Related

- `flow/flow-versioning-strategy` — whether a change is a new version or a new
  flow, and the retention rule this skill enforces at deploy time.
- `flow/flow-deployment-and-packaging` — change sets vs SFDX vs packages.
- `devops/devops-center-advanced` — promoting flows through a work-item pipeline.
- `devops/deployment-error-diagnosis` — reading a failed deploy.
- `devops/metadata-api-retrieve-deploy` — what the API does per metadata type.
- `flow/flow-interview-debugging` — why the version in an error email is usually
  not the active one.

## Official Sources Used

- FlowDefinition (Metadata API) — fields `activeVersionNumber` ("The version number of the active flow"), `apiVersion` (reserved for internal use), `description`, `masterLabel`; API 34.0 and later; "In API version 44.0, we recommend upgrading your flows to flow metadata file names without version numbers and discontinue using the FlowDefinition object to activate or deactivate a flow"; "the active version numbers in the flow definitions override the status fields in the flows" — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_flowdefinition.htm
- Flow (Metadata API) — the five-value `status` enumeration `Active`, `Draft`, `Obsolete`, `InvalidDraft`, `UnderReview`, with UI labels that differ from the API values — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_visual_workflow.htm
- Flow (Tooling API) — flow versions are Tooling API objects — https://developer.salesforce.com/docs/atlas.en-us.api_tooling.meta/api_tooling/tooling_api_objects_flow.htm
- FlowDefinitionView (Object Reference) — read-only standard-API view exposing `ActiveVersionId` and `LatestVersionId` — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_flowdefinitionview.htm
- FlowVersionView (Object Reference) — API version 46.0 and later — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_flowversionview.htm
- Deploy Processes and Flows as Active — Setup → Process Automation Settings; applies to processes and autolaunched flows deployed via change sets and the Metadata API; not available in developer, sandbox, or other non-production orgs; at least one Apex test must cover the configured percentage; the requirement does not apply to flows that have screens — https://help.salesforce.com/s/articleView?id=platform.flow_distribute_deploy_active.htm&type=5
- Flow Builder: Run a Flow Within a Flow (Trailhead) — the parent runs the child's active version, or the latest version if none is active — https://trailhead.salesforce.com/content/learn/modules/flow-build-logic/run-flow-within-flow
- Monitoring and Managing Paused and Failed Flow Interviews — deleting a FlowInterview requires the Manage Flow permission — https://help.salesforce.com/s/articleView?id=platform.automate_ala_monitor.htm&type=5
- Have Unlimited Paused and Waiting Flows (Spring '24) — https://help.salesforce.com/s/articleView?id=release-notes.rn_automate_flow_mgmt_remove_paused_interview_limit.htm&release=248&type=5
- Salesforce CLI Command Reference, `sf project deploy` — `--tests` supplies the "Apex tests to run when --test-level is RunSpecifiedTests" — https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference_project_commands_unified.htm
- deploy() (Metadata API) — `RunSpecifiedTests`: "Only the tests that you specify in the runTests option are run… Each class and trigger in the deployment package must be covered by the executed tests for a minimum of 75% code coverage." — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_deploy.htm
- Salesforce Well-Architected — Resilient — https://architect.salesforce.com/docs/architect/well-architected/resilient/resilient
