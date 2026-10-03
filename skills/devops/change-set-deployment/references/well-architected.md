# Well-Architected Notes: Change Set Deployment

## Relevant Pillars

### Operational Excellence

Change set deployment is primarily an Operational Excellence concern. The mechanism itself is simple; the discipline around it determines whether releases are predictable and repeatable.

Key operational excellence practices for change sets:
- **Validate before every production deploy.** The 10-day Quick Deploy window exists precisely so validation and deployment can be separated. Skipping validation to save time converts a repeatable process into a gambling exercise.
- **Named owners for each step.** Who uploads, who validates, who deploys, who runs smoke tests, and who owns rollback must be documented in the release plan, not assumed.
- **Post-deploy tasks in the plan.** Flow activation, permission set assignment, and named credential updates are out-of-band from the change set and must be captured as explicit steps.
- **Release communication.** Users and downstream integrations should be notified of the window and any expected behavior changes.

### Reliability

Reliability in change set deployments centers on: atomic rollback behavior, dependency completeness, and avoiding partial state.

Key reliability practices:
- Change set deploys are atomic in Salesforce: if any component fails, the entire deployment rolls back. This is a reliability guarantee, but it also means a single missing dependency or a single failing test halts the entire release.
- The rollback plan must be defined before the deploy begins, not after. For metadata-only deployments, the rollback is straightforward: re-deploy the prior version. For releases that include data changes or Flow activations, rollback is more complex and must be rehearsed.
- Validate in a staging sandbox before production. The target environment must mirror production as closely as possible for validation results to be meaningful.

---

## Architectural Tradeoffs

**Change sets vs. Salesforce CLI deploy:**
Change sets are UI-driven and require no tooling setup, which makes them accessible for admin teams with no development infrastructure. However, they offer no branching, no diff visibility, no repeatable automation, and no history beyond the Deployment Status log. For teams doing more than 1-2 releases per sprint, the manual overhead of change sets compounds quickly. The Salesforce Well-Architected framework favors automation and source-of-truth-driven delivery (Operational Excellence pillar) over manual processes.

**Change sets vs. DevOps Center:**
The DevOps Center guide positions DevOps Center as an alternative to change sets that captures every change in a source control system. It keeps a click-based experience for admins, so it is a better next step for teams growing beyond change sets but not yet ready for a full CI/CD pipeline.

**Validate-then-Quick-Deploy vs. direct Deploy:**
Quick Deploy reduces production window time by separating test execution from metadata promotion. The tradeoff is planning: validation must happen before the release window, which requires the change set to be finalized earlier. Teams that treat change sets as last-minute activities cannot benefit from Quick Deploy.

---

## Anti-Patterns

1. **Deploying broad profile metadata repeatedly**: each profile deploy changes the settings for the components in the same deployment and always replaces user permissions, login IP ranges, and login hours. Repeated deploys from sandboxes accumulate silent drift in those sections. Use permission sets for new access grants. Deploy profiles only when unavoidable, and always with a before/after diff of those sections.

2. **Using a single change set for the entire release**: Monolithic change sets with 50+ components have large dependency surfaces, long deployment windows, and catastrophic rollback if any component fails. Sequenced, smaller change sets (data model first, then logic, then permissions) reduce blast radius and make the deployment window more predictable.

3. **Treating sandbox validation as a substitute for staging-org validation**: A developer sandbox does not mirror production data volume, connected integrations, or full permission model. Validating only in a developer sandbox before uploading to production means the first real test of the change set against a production-like environment is production itself. A full-copy or partial-copy sandbox should be the penultimate validation step before production.

---

## Official Sources Used

- Metadata API Developer Guide, Summer '26 (release 262): `deployRecentValidation()` (quick deploy from Deployment Status, 10-day window), DeployOptions `testLevel` and `rollbackOnError`, "Running Tests in a Deployment", Profile > Usage (scoped profile settings and the three always-included sections), FlowSettings `enableFlowDeployAsActiveEnabled`, Layout member naming, "Slow Deployments" - https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Apex Developer Guide, Summer '26: "Deploy Components to Production" (deployment connection, Create and Upload Change Sets permission, View/Add Dependencies, edition availability), "Deploy Apex Using Change Sets", Apex Scheduler (classes with active scheduled jobs), code coverage considerations (tests don't run in parallel in change set deployments) - https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- DevOps Center guide, Summer '26: positioning as an alternative to change sets - https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/devops_center.pdf
- Salesforce DX Developer Guide, Summer '26: org development model ("the deployment artifact as the inbound change set") - https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/sfdx_dev.pdf
- Salesforce CLI 2.151.7 local `--help` output for `project retrieve start` (`--manifest`, `--metadata`, `--output-dir`)
- Local corpus: knowledge/imports/salesforce-apex-developer-guide.md (change set procedure, same text as the Apex Developer Guide)
