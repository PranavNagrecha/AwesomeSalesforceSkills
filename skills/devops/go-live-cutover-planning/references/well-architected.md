# Well-Architected Notes — Go Live Cutover Planning

## Relevant Pillars

- **Operational Excellence** — Go-live cutover planning is fundamentally an operational discipline. A well-designed cutover runbook embodies repeatable, documented processes with clear ownership, measurable success criteria, and defined escalation paths. The mock deployment rehearsal pattern directly supports the Well-Architected principle of validating operational procedures before they are needed in production.
- **Reliability** — The cutover plan determines whether the production org transitions smoothly or suffers downtime. Validation deploys, quick deploy windows, and go/no-go gates are all reliability controls that reduce the probability of failed deployments. Rollback triggers defined in advance prevent the team from improvising under pressure, which is the primary cause of extended outages during go-live events.
- **Security** — Code freeze enforcement prevents unauthorized or untested changes from entering the deployment package. The go/no-go checklist should include a security review confirmation (permission sets, sharing rules, field-level security) to ensure the deployment does not inadvertently widen data access. Named Credential authentication must be verified post-deployment to prevent integration authentication failures.

## Architectural Tradeoffs

**Speed vs. safety in cutover window sizing.** A narrow cutover window (4-6 hours) minimizes user disruption but leaves little room for troubleshooting. A wide window (12-24 hours) provides buffer but requires longer downtime communication and may affect business operations. The validation deploy + quick deploy pattern resolves this tradeoff by reducing the actual deployment time to minutes while keeping the window available for smoke testing and issue resolution.

**Monolithic vs. phased deployment.** A single deployment package is simpler to manage and has fewer coordination requirements, but creates a binary pass/fail outcome where one failing component forces a complete rollback. Phased deployment isolates blast radius but requires multiple validation deploys, hold-point coordination, and more complex rollback procedures. Choose phased deployment when the deployment includes more than 200 components or spans multiple functional areas with independent teams.

**Mock deployment cost vs. risk reduction.** A full mock deployment in a Full sandbox consumes team time (typically 4-8 hours including setup and review) and requires a recently refreshed Full sandbox. For routine releases with well-understood deployment patterns, this cost may not be justified. For first-time production deployments, destructive changes, or data migrations, the mock deployment consistently catches issues that would otherwise surface during the live cutover.

## Anti-Patterns

1. **No formal go/no-go gate** — Teams that skip the go/no-go meeting and proceed directly from validation deploy to cutover execution lose the opportunity to catch issues that the automated validation cannot detect: business readiness, support staffing, communication gaps, and UAT defects accepted as known issues. The go/no-go meeting is the last checkpoint where human judgment evaluates overall readiness.
2. **Hypercare treated as optional** — Teams that declare go-live complete on cutover day and return to normal support levels miss the critical stabilization period. Production issues surface gradually as users exercise different features over the first 1-2 weeks. Without dedicated hypercare, these issues queue behind normal support tickets and erode user confidence in the new system.
3. **Code freeze violated for last-minute fixes** — Allowing commits after the validation deploy invalidates the validated deploy ID and introduces untested changes. Every post-freeze change requires a new validation deploy, which may not complete before the cutover window. The emergency change process exists for genuine P1 issues, not for feature additions that missed the deadline.

## Official Sources Used

- Salesforce Help — Deploy to Production: https://help.salesforce.com/s/articleView?id=sf.deploy_to_production.htm
- Salesforce Metadata API Developer Guide — Deploy: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_deploy.htm
- Salesforce CLI Reference — sf project deploy: https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference_project_commands_unified.htm
- Salesforce Architects — Well-Architected Operational Excellence: https://architect.salesforce.com/well-architected/operational-excellence
- Trailhead — Prepare Your Org for a Successful Go-Live: https://trailhead.salesforce.com/content/learn/modules/go-live-readiness
