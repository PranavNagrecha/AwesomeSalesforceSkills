# Well-Architected Notes — Change Advisory Board Process

## Relevant Pillars

- **Security** — The primary pillar. CAB governance directly enforces Intentional Governance and least-privilege access control principles. Changes to Profiles, Permission Sets, Sharing Rules, and integrations must pass through an approval gate precisely because these changes alter the security posture of the org. The Well-Architected framework principle of "know who can do what and why" depends on controlled, audited change processes.
- **Operational Excellence** — The CAB process is a core Operational Excellence mechanism. The Salesforce Well-Architected framework emphasizes that mature operations require defined change control, deployment runbooks, and post-implementation reviews. A poorly governed change process directly causes unplanned outages and data integrity incidents.
- **Reliability** — Change is the leading cause of production incidents in Salesforce orgs. A structured CAB process with mandatory rollback planning reduces the blast radius of failed deployments and provides the documented procedures necessary for rapid recovery.
- **Performance** — Less directly applicable, but large Flow deployments and sharing rule recalculations triggered by changes can cause performance degradation. The CAB review step is an appropriate place to flag any planned changes that could trigger org-wide sharing recalculations or Apex bulk processing spikes.
- **Scalability** — The CAB process itself must scale with org complexity. A process designed for 10 deployments per month may create a governance bottleneck when the org matures to 50 deployments. The Well-Architected principle of designing for the expected scale applies to governance processes, not just technical architecture.

## Architectural Tradeoffs

**Speed of delivery vs. rigor of review:** A heavier CAB process (weekly board meeting, multi-week advance notice) provides thorough review but slows delivery. A lighter process (async approvals, 24-hour turnaround for Normal changes) maintains speed but requires more discipline from individual approvers. The right balance depends on regulatory context and org change volume. Start with async approvals for Normal changes and synchronous CAB meetings only for changes affecting the security model or external integrations.

**Automated gate vs. procedural enforcement:** An automated pipeline gate (the deployment tool calls the ITSM API) provides hard enforcement but requires ITSM integration effort. A procedural gate (approvers are responsible for verifying tickets before clicking Deploy) is faster to implement but relies on human compliance and will degrade under pressure. For regulated industries, automated gates are non-negotiable. For smaller organizations, procedural enforcement with compensating controls (deployment logs, ITSM audit) is a reasonable starting point.

**Broad CAB scope vs. tiered exemptions:** Including every change type in the CAB process creates overhead that drives teams to either route around the process or classify everything as Standard to avoid it. Tiering (Standard / Normal / Emergency) with clear criteria per tier maintains governance rigor for high-risk changes while keeping the process frictionless for low-risk routine changes.

## Anti-Patterns

1. **Single-Tier CAB (Everything Needs Approval)** — Treating every Salesforce change — including dashboard edits, report updates, and trivial configuration — as requiring full CAB approval. This creates a governance bottleneck that either slows delivery to a crawl or causes teams to route around the process informally. Instead, maintain explicit Standard change pre-authorization for low-risk, repeatable changes so the CAB review budget is reserved for high-risk changes that genuinely need it.

2. **Platform-Internal Approval Process as CAB Gate** — Using a Salesforce Approval Process or a custom `Deployment_Request__c` object as the enforcement mechanism for CAB approvals. This creates a false sense of governance: the Salesforce org cannot gate its own deployment pipeline. A developer with CLI access can deploy to production regardless of any object state inside the org. CAB gates must live in the deployment toolchain and check an external ITSM system.

3. **No Rollback Requirement** — Approving changes through CAB without requiring a documented and tested rollback procedure. When a deployment fails in production, the absence of a rollback plan converts a recoverable incident into an extended outage. The CAB change ticket must require a rollback procedure, and the Normal change review must explicitly confirm that the rollback has been validated in sandbox.

## Official Sources Used

**Official Salesforce documentation** (v62 / Summer '26 PDF extractions; line numbers are into
the extracted text, so the section titles are given alongside):

- Metadata API Developer Guide — `deploy()` **DeployOptions** table, §"deploy()"
  (`checkOnly`, `ignoreWarnings`, `rollbackOnError`, `runTests`, `singlePackage`, `testLevel`
  and its five-value enum; `NoTestRun` restricted to development environments; `RunLocalTests`
  the production default when Apex is present; the Master-Detail ↔ Lookup `checkOnly`
  restriction). Supports the deploy-options table in `worked-examples.md` §5, Gotcha 7, and the
  `check_deploy_options` check. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Metadata API Developer Guide — §"Deploy a Recently Validated Component Set Without Tests" and
  §"deployRecentValidation()" ("validated successfully for the target environment within the
  last 10 days"). Supports Gotcha 6 and the `check_quick_deploy` check. Same PDF.
- Metadata API Developer Guide — §"Slow Deployments" ("avoid running deployments during the
  service upgrade"; a deploy interrupted by downtime has "both component deployment and
  validation… retried from the beginning"; "Salesforce performs major service upgrades three
  times per year"). Supports the freeze-window rule and the deploy-window-vs-freeze check.
  Same PDF.
- Metadata API Developer Guide — §"cancelDeploy()" (a deployment with status `Finalizing
  Deploy` can't be cancelled in API 65.0+; below that, cancellation may succeed while data is
  still committed) and the `DeployResult` field table (`createdBy` / `canceledBy`,
  API 30.0+; the `DeployStatus` enum including `SucceededPartial`). Supports Gotcha 9 and the
  deploy-evidence step in the workflow. Same PDF.
- Metadata API Developer Guide — §"Metadata API Edit Access" (Modify Metadata Through Metadata
  API Functions is enabled automatically by **Deploy Change Sets** or **Author Apex**; it does
  not govern Setup-UI edits) and §"Deleting Components in a Deployment"
  (`destructiveChangesPre`/`Post`, no wildcards). Supports Gotcha 10 and the manifests in
  `worked-examples.md` §4. Same PDF.
- Object Reference for the Salesforce Platform — **SetupAuditTrail** (Setup-area changes for at
  least 180 days; `Action` / `Section` / `Display` / `DelegateUser` / `CreatedByContext`;
  `query()` and `retrieve()` only; aggregate queries unsupported). Supports Gotcha 8 and the
  post-window verification SOQL. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- Best Practices for Deployments with Large Data Volumes — §"Defer Sharing Calculation"
  (suspending sharing-rule and group-membership calculation during large configuration changes
  that "might lead to very long sharing rule evaluations or timeouts"). Supports the risk signal
  that separates sharing changes from list views in the classification matrix. (Cited by guide
  title and section; the PDF filename for this guide was not verified from this environment, so
  no URL is given rather than a guessed one.)

**Salesforce Architects / Trust:**

- Salesforce Well-Architected — Intentional Governance (the Security and Operational Excellence
  framing at the top of this file): https://architect.salesforce.com/well-architected/easy/intentional
- Salesforce Well-Architected Overview (pillar definitions used in "Relevant Pillars"):
  https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Trust (the instance upgrade schedule the freeze register is built from — the
  Metadata API guide points here explicitly for "whether your Salesforce instance is due for an
  upgrade"): https://trust.salesforce.com

**Repo standards and sibling artefacts this skill defers to rather than restates:**

- `skills/admin/devops-process-documentation/references/worked-examples.md` §1b — the
  `change_request` record and its state machine. The CAB decision record here attaches to the
  `Approved` transition of that machine and joins on `Change_Request__c.Name`.
- `skills/admin/salesforce-release-preparation/SKILL.md` — Release Updates posture, the release
  run sheet, and the Sandbox Preview opt-in rules the freeze register consumes as an input.
- `skills/admin/sandbox-strategy/SKILL.md` — sandbox types and refresh floors (the Full sandbox
  refresh interval is the constraint the rehearsal window has to fit inside).
- `skills/admin/uat-and-acceptance-criteria/` and
  `skills/admin/stakeholder-raci-for-sf-projects/` — the UAT pack and RACI cited as
  `test_evidence` entries on the decision record.
- `agents/field-impact-analyzer/AGENT.md` (`/analyze-field-impact`) — produces the blast-radius
  report the decision record imports rather than estimating in the meeting.
