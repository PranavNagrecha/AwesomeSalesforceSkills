# Well-Architected Notes — Release Notes Automation

## Relevant Pillars

- **Operational Excellence** — Hand-written release notes degrade fast. Automated, deterministic notes turn the deploy event into an audited, reviewable artifact: who shipped what, when, traceable back to tickets and commits. The pipeline is also the cheapest possible audit trail for change-management compliance reviews.

## Architectural Tradeoffs

- **Convention enforcement vs. tooling complexity:** Conventional Commits gives you free grouping at the cost of asking developers to follow a format. Jira-keyed grouping needs no commit discipline but adds API calls, tokens, and rate-limit handling.
- **Tag-trigger vs. promotion-trigger:** Tagging is universal and cheap; promotion-triggered notes tie the artifact to the actual production deploy but couple the pipeline to your deploy tooling.
- **One audience vs. two:** Generating both a developer changelog and a stakeholder release note from the same source doubles the templating work but halves the future drift risk.

## Anti-Patterns

1. **Re-generating notes on every commit** — Notes lose their anchor; the artifact stops corresponding to a release. Trigger on tag/promotion, not push.
2. **Hand-typed notes copy-pasted from `git log`** — Reliable for the first three releases; slow and error-prone after that. Automate before the team scales the cadence.
3. **Tokens in the workflow file** — Predictable security incident the moment the repo goes public or someone forks. Always use the secret manager — see `devops/pipeline-secrets-management`.

## Official Sources Used

- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Salesforce CLI Reference — https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference.htm
- Salesforce DX Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_intro.htm
- Conventional Commits — https://www.conventionalcommits.org/
- Keep a Changelog — https://keepachangelog.com/
