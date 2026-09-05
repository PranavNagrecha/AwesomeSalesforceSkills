# Well-Architected Notes — DevOps Process Documentation

## Relevant Pillars

### Operational Excellence — Primary Pillar

Process documentation is where Operational Excellence stops being a slogan: every deployment event should be reconstructible from written records, which is what a runbook with numbered steps, owners, pass criteria and recorded deploy ids gives you. UNVERIFIED (2026-09-05): the framing above is attributed in this package to the Well-Architected Automated pillar at architect.salesforce.com/well-architected/easy/automated; that page cannot be fetched from this environment and is not among the extracted PDFs, so treat the attribution as unconfirmed and the argument as this skill's own.

What *is* grounded is why the reconstruction matters mechanically. A deployment reports one of a documented set of statuses including `SucceededPartial` (api_meta.txt L3338–3352); a partial landing is a normal outcome, not an anomaly, and the only durable record of which components made it is the deploy id plus the manifest the runbook recorded. Without both, the post-incident question "what state is production in" has no cheap answer.

### Reliability — Supporting Pillar

Recovery procedures belong in writing before the deployment, not after the incident. A rollback decision gate — threshold, named owner, ordered procedure, time estimate — is the reliability artefact. UNVERIFIED (2026-09-05): as above, the attribution to the Resilient pillar at architect.salesforce.com/well-architected/adaptable/resilient is unconfirmed from this environment.

Three grounded facts shape what a rollback path can actually say. `rollbackOnError` decides whether a failure unwinds or leaves a partial landing, defaults to `false`, and must be `true` for production (api_meta.txt L3126–3130). `purgeOnDelete` does not work in production orgs (api_meta.txt L3119–3123), so deleted components normally remain recoverable from the Recycle Bin — except roll-up summary fields, which are purged regardless (api_meta.txt L4638–4640). And in API version 65.0 and later a deployment in `Finalizing Deploy` cannot be cancelled (api_meta.txt L4124–4127), so "cancel it" is not always available as the first move. A rollback section that does not distinguish these is a sentence, not a plan.

### Security — Applicable

Credential re-entry steps carry a security dimension, and the platform pushes teams toward the right answer whether they notice or not. Because a defined consumer secret is exported as a placeholder rather than an encrypted value (api_meta.txt L24855–24856), the secret cannot ride the pipeline unless someone deliberately puts the plaintext into the XML — which since November 2022 is the supported form (api_meta.txt L25120–25122) and which commits a secret to source control. The runbook's job is to name the *source* (a vault entry, a named handoff) and never the value, and to carry a verification callout with an expected status code so "I entered it" and "it works" are different pass criteria.

## Architectural Tradeoffs

**Documentation granularity vs. maintenance cost:** Highly granular runbooks (field-level steps, expected durations, verification commands) reduce execution error but require more maintenance effort as the process evolves. The tradeoff is resolved by separating stable standing content (deployment guide) from event-specific content (runbook). The deployment guide handles slow-changing process detail; the runbook inherits it and adds release-specific steps.

**Centralized vs. embedded documentation:** Some teams embed runbook content inside their CI/CD tool (GitHub Actions job descriptions, DevOps Center notes) rather than maintaining a separate document. This reduces context-switching during execution but creates retrieval problems during post-incident review when the team needs to reconstruct the sequence of events across tools. The Well-Architected recommendation is to maintain a canonical runbook document that survives tool migration.

## Anti-Patterns

1. **No runbook, just a release plan** — Teams that maintain release plans but not deployment runbooks have documented the "what" but not the "how at execution time." Release plans are useful for stakeholder governance; they are not usable by the person performing the deployment. Well-Architected Operational Excellence requires both.

2. **Runbook stored in the deploying admin's notes** — A runbook that only one person can access is a single point of failure. If that person is unavailable during or after the deployment, the org's state cannot be reconstructed and rollback cannot be validated. Runbooks must be stored in a shared, version-controlled location before the deployment window opens.

3. **Environment matrix treated as a one-time artifact** — Authoring an environment matrix once and never reviewing it leads to decision-making based on stale environmental assumptions. Well-Architected Resilient guidance requires that environment documentation is reviewed and updated as a standard step in the release cycle, not on an ad hoc basis.

## Official Sources Used

- **Metadata API Developer Guide**, deployOptions Parameters — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (api_meta.txt L3088–3168) — the deploy contract the runbook records: `checkOnly`, `testLevel` and its five-value enumeration, `runTests`, `rollbackOnError` and its production requirement, `ignoreWarnings`, `purgeOnDelete`, `singlePackage`.
- **Metadata API Developer Guide**, Deleting Components in a Deployment / Adding and Deleting Components in a Single Deployment (api_meta.txt L4610–4682) — `destructiveChanges.xml`, the companion `package.xml` with no components, `destructiveChangesPre.xml` / `destructiveChangesPost.xml` ordering, and the roll-up-summary purge exception that shapes the rollback path.
- **Metadata API Developer Guide**, Deployment Status, Cancel a Deployment, and deploy status enumeration (api_meta.txt L3338–3352, L4117–4127) — `SucceededPartial` as a documented outcome; one deployment at a time; the queue is not FIFO; `Finalizing Deploy` cannot be cancelled from API 65.0.
- **Metadata API Developer Guide**, deployRecentValidation() (api_meta.txt L4855–4875) — the ten-day, target-specific quick-deploy window that the release calendar's validate-only date has to sit inside.
- **Metadata API Developer Guide**, Running Tests in a Deployment / Run the Same Tests in Sandbox and Production Deployments (api_meta.txt L2656–2679) — no tests by default in non-production; production runs tests by default only when the package contains Apex; `RunLocalTests` is enforced regardless of package contents. This is why the rehearsal and the production run each record a test level.
- **Metadata API Developer Guide**, Maintaining User References (api_meta.txt L2705–2718) and Flow / FlowDefinition metadata types (api_meta.txt L68416–68423, L73921–73931) — the two post-deploy verification steps the runbook cannot skip: user references halt a deployment outright, and a `FlowDefinition` overrides a `Flow`'s `status`.
- **Metadata API Developer Guide**, AuthProvider `consumerSecret` field and Declarative Metadata Sample Definition (api_meta.txt L24839–24857, L25120–25122) — the placeholder-on-export rule and the plaintext-since-November-2022 rule that together define the credential manual step.
- **Metadata API Developer Guide**, deploy/retrieve size limits (api_meta.txt L2038–2045, L3654–3669) — 10,000 files and approximately 39 MB compressed, the pre-deploy gate item nobody checks until a release fails on it.
- **Repo standard — `agents/_shared/AGENT_CONTRACT.md`**, Mandatory Reads and Citations sections — why the process document lists its consumers by agent path, so a run-time agent citing this artefact resolves to something real.
- **Sibling skill — `skills/admin/sandbox-strategy/SKILL.md`** § "Type Capacities and Refresh Windows" — the tier capacities and platform refresh intervals this skill deliberately does not restate in the environment ladder.
- **Sibling skill — `skills/admin/change-management-and-deployment/SKILL.md`** § "Questions to Ask Before Configuring" — the deploy-option *choice* this skill records rather than makes.
