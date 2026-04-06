# Well-Architected Notes — Post Deployment Validation

## Relevant Pillars

- **Reliability** — Post-deployment validation is fundamentally a reliability practice. Validation deploys confirm that metadata will land successfully before committing to production. Quick deploy minimizes the commit window, reducing the probability of partial deployment states affecting users. Rollback planning ensures the system can recover from deployment-induced regressions.

- **Operational Excellence** — Structured post-deployment verification (test result review, functional smoke tests, component landing checks) moves deployments from "hope it worked" to "confirmed it worked." Documenting validation IDs, quick deploy IDs, test baselines, and rollback steps creates an auditable deployment history that improves operational maturity over time.

## Architectural Tradeoffs

**Validation deploy + quick deploy vs. direct deploy:** The validate-then-quick-deploy pattern adds an extra step and requires tracking a validation ID with a 10-day expiry window. In exchange, it separates the risky test-execution phase from the commit phase, reducing the production exposure window from tens of minutes to seconds. For organizations with large test suites (30+ minutes of test execution), this tradeoff is almost always worthwhile. For small orgs with fast test suites, direct deploy may be acceptable.

**RunSpecifiedTests vs. RunLocalTests:** RunSpecifiedTests is faster because it runs only the tests you name, but it enforces 75% coverage per class in the package — meaning you must know exactly which tests cover which classes. RunLocalTests runs all non-managed-package tests and checks org-wide coverage, which is slower but catches cross-cutting regressions. The tradeoff is deploy speed vs. regression detection breadth.

**Pre-deployment retrieve for rollback vs. source-control-based rollback:** Retrieving the current org state before every deployment creates a reliable rollback snapshot but adds time and storage overhead. Source-control-based rollback (reverting to the prior commit) is faster and more natural for source-tracked projects but assumes the org was in sync with source control before the deployment — which is not always true in orgs with manual admin changes.

## Anti-Patterns

1. **Deploy-and-pray** — Deploying to production without a prior validation deploy, then assuming success because the CLI did not throw an error. This skips test result review, functional verification, and rollback planning entirely. The correct pattern is validate first, review results, quick deploy, then run the post-deployment checklist.

2. **Monitoring the wrong deployment ID after quick deploy** — Checking the validation ID for status after the quick deploy executes. The validation ID shows the validation result, not the commit result. The quick deploy returns a new ID that must be tracked separately.

3. **Treating deployment success as functional success** — The Metadata API confirms that metadata compiled and landed. It does not confirm that the deployed logic is correct, that permissions are set up, or that end users can access the new features. Post-deployment validation must include functional smoke tests beyond the deployment status check.

## Official Sources Used

- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Salesforce CLI Reference — https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference.htm
- Salesforce DX Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_intro.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
