# Well-Architected Notes — Flow Versioning

## Relevant Pillars

- **Reliability** — the whole discipline exists to prevent one class of bug: a
  paused interview resuming into a version that no longer supports it, or a
  caller invoking a contract that quietly changed. Both fail long after the
  change, which is what makes the prevention worth the process.
- **Operational Excellence** — rollback on this platform is one click on an
  existing version. That is a genuinely excellent property, and it is only
  available to a team that recorded which version was active before deploying.
  The changelog and the pre-deploy capture are what convert the platform's
  capability into a usable runbook.
- **Adaptable** — subflow version resolution is late, so a shared subflow is a
  published interface whose consumers cannot pin it. Treating it as one is the
  difference between reuse that scales and reuse that couples everything to one
  team's release cadence.

## Architectural Tradeoffs

- **New version vs new flow:** a version is cheap and keeps callers untouched; a
  new flow is the only safe path when the contract changes, and it buys an
  incremental cutover in exchange for a period where two flows exist. The test is
  mechanical: if anything outside the flow must change at the same moment, it is
  a new flow.
- **Retention depth vs version ceiling:** three inactive versions is enough
  rollback depth for almost every incident, and a per-flow cap well below the
  platform ceiling keeps the pruning decision away from a failed save. More
  retention is not free — it makes the version list harder to reason about and
  brings the ceiling closer.
- **Automated cleanup vs manual:** automation is the only thing that scales, and
  an automated rule keyed on age is actively dangerous. The safe automation
  checks interview references and refuses to delete when any exist; the unsafe
  automation checks a date. If you cannot build the first, do the cleanup
  manually on a cadence.
- **Shared subflow vs duplicated logic:** sharing removes duplication and makes
  every activation a multi-caller production change. Duplication is cheaper to
  change safely and drifts. Prefer sharing for stable, well-tested logic and
  duplication for logic still finding its shape.
- **`Flow.status` vs `FlowDefinition`:** `status` is the recommended mechanism;
  `FlowDefinition.activeVersionNumber` is the only one that points at a specific
  *existing* version, which is exactly what a rollback needs. Using both in one
  package is the failure case, because flow definitions override statuses. Note
  the asymmetry in what each can express: `status` can take a version off,
  `activeVersionNumber` is documented only as naming the active one.

## Hygiene

- Every activation records the previously active version number, per
  environment.
- Every flow change states breaking or non-breaking, with the reason.
- Caller inventory is part of any change to the contract surface, not
  verification afterwards.
- Version deletion is gated on zero interview references, never on age alone.
- At least three inactive versions retained; total capped by policy below the
  platform ceiling.
- Subflow activations are preceded by a `<flowName>` reference search.
- API version is noted before and after any edit to a legacy flow.
- `FlowDefinition` is kept out of routine deployment packages.

## Related

- `devops/flow-deployment-activation-ordering` — the deploy-time mechanics of
  activation, ordering, and rollback across environments.
- `flow/flow-deployment-and-packaging` — change sets vs SFDX vs packages.
- `flow/flow-interview-debugging` — reading the version number out of an error
  email, and why it is usually not the active one.
- `flow/flow-runtime-context-and-sharing` — the run-mode default that changed at
  API 52.0, which an API version bump silently picks up.
- `flow/pause-elements-and-wait-events` — what creates the paused interviews this
  skill spends its time draining.
- `flow/subflows-and-reusability` — designing subflows as interfaces.

## Official Sources Used

- FlowDefinition (Metadata API) — `activeVersionNumber`, documented in full as "The version number of the active flow"; available in API 34.0 and later; "In API version 44.0, we recommend upgrading your flows to flow metadata file names without version numbers and discontinue using the FlowDefinition object to activate or deactivate a flow"; "the active version numbers in the flow definitions override the status fields in the flows" — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_flowdefinition.htm
- Flow (Metadata API) — the five-value `status` enumeration `Active`, `Draft`, `Obsolete`, `InvalidDraft`, `UnderReview`, whose API values differ from their UI labels — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_visual_workflow.htm
- Flow (Tooling API) — flow versions are Tooling API objects — https://developer.salesforce.com/docs/atlas.en-us.api_tooling.meta/api_tooling/tooling_api_objects_flow.htm
- FlowDefinitionView (Object Reference) — read-only standard-API view of a flow definition — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_flowdefinitionview.htm
- FlowVersionView (Object Reference) — available in API version 46.0 and later — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_flowversionview.htm
- FlowInterview (Object Reference) — a running instance of a flow — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_flowinterview.htm
- Flow Builder: Run a Flow Within a Flow (Trailhead) — "the parent flow runs the child flow's active version"; the latest version if none is active — https://trailhead.salesforce.com/content/learn/modules/flow-build-logic/run-flow-within-flow
- Flow Element: Subflow — https://help.salesforce.com/s/articleView?id=platform.flow_ref_elements_subflow.htm&type=5
- Monitoring and Managing Paused and Failed Flow Interviews — deleting a FlowInterview requires the Manage Flow permission — https://help.salesforce.com/s/articleView?id=platform.automate_ala_monitor.htm&type=5
- Have Unlimited Paused and Waiting Flows (Spring '24) — the paused/waiting interview cap was removed — https://help.salesforce.com/s/articleView?id=release-notes.rn_automate_flow_mgmt_remove_paused_interview_limit.htm&release=248&type=5
- Flow Limits (Visual Workflow Implementation Guide, legacy) — "Maximum number of versions per flow: 50", independently corroborated by Salesforce's own save error, "Maximum number of Versions per flow is 50". Use the page for that one figure only: it still states the 2,000 executed-elements limit removed at API 57.0 — https://developer.salesforce.com/docs/atlas.en-us.salesforce_vpm_implementation_guide.meta/salesforce_vpm_implementation_guide/vpm_admin_flow_limits.htm
- General Flow Limits (current, authoritative) — https://help.salesforce.com/s/articleView?id=platform.flow_considerations_limit.htm&type=5
