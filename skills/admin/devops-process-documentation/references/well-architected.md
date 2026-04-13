# Well-Architected Notes — DevOps Process Documentation

## Relevant Pillars

### Operational Excellence — Primary Pillar

The Well-Architected Automated pillar (architect.salesforce.com/well-architected/easy/automated) treats process documentation as a first-class Operational Excellence requirement. Specifically, teams should maintain an environment matrix and deployment guides as living documents, not one-time artifacts. The automated pillar's guidance on repeatable delivery requires that every deployment event can be reconstructed from written records — which is the purpose of a deployment runbook. Without documentation, delivery relies on tribal knowledge that does not survive team rotation or incident review.

### Reliability — Supporting Pillar

The Well-Architected Resilient pillar (architect.salesforce.com/well-architected/adaptable/resilient) requires that teams document recovery procedures before a deployment, not after an incident. A runbook's rollback decision gate — who owns the call, what the procedure is, and how long it takes — is a reliability artifact. An org that deploys without a documented rollback path is non-resilient by Well-Architected definition, regardless of deployment method.

### Security — Applicable

Named Credential and External Credential re-entry steps in a runbook carry a security dimension: secret values must be sourced from an approved secrets management system (password manager, secrets vault), not from email, chat, or plain-text documents. The runbook must specify the secret source but must not contain the secret value itself. This is an operational security control.

## Architectural Tradeoffs

**Documentation granularity vs. maintenance cost:** Highly granular runbooks (field-level steps, expected durations, verification commands) reduce execution error but require more maintenance effort as the process evolves. The tradeoff is resolved by separating stable standing content (deployment guide) from event-specific content (runbook). The deployment guide handles slow-changing process detail; the runbook inherits it and adds release-specific steps.

**Centralized vs. embedded documentation:** Some teams embed runbook content inside their CI/CD tool (GitHub Actions job descriptions, DevOps Center notes) rather than maintaining a separate document. This reduces context-switching during execution but creates retrieval problems during post-incident review when the team needs to reconstruct the sequence of events across tools. The Well-Architected recommendation is to maintain a canonical runbook document that survives tool migration.

## Anti-Patterns

1. **No runbook, just a release plan** — Teams that maintain release plans but not deployment runbooks have documented the "what" but not the "how at execution time." Release plans are useful for stakeholder governance; they are not usable by the person performing the deployment. Well-Architected Operational Excellence requires both.

2. **Runbook stored in the deploying admin's notes** — A runbook that only one person can access is a single point of failure. If that person is unavailable during or after the deployment, the org's state cannot be reconstructed and rollback cannot be validated. Runbooks must be stored in a shared, version-controlled location before the deployment window opens.

3. **Environment matrix treated as a one-time artifact** — Authoring an environment matrix once and never reviewing it leads to decision-making based on stale environmental assumptions. Well-Architected Resilient guidance requires that environment documentation is reviewed and updated as a standard step in the release cycle, not on an ad hoc basis.

## Official Sources Used

- Salesforce Well-Architected Automated — https://architect.salesforce.com/well-architected/easy/automated
- Salesforce Well-Architected Resilient — https://architect.salesforce.com/well-architected/adaptable/resilient
- Salesforce DevOps Center Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.salesforce_vcs_developer_guide.meta/salesforce_vcs_developer_guide/devops_center_dev_overview.htm
- Metadata API Developer Guide (NamedCredential) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_named_cred.htm
