# Well-Architected Notes — Salesforce CLI Automation

## Relevant Pillars

- **Operational Excellence** — Repeatable scripts, pinned CLI versions, structured logs, and explicit org targeting reduce operational toil and speed incident response when a pipeline misbehaves.
- **Reliability** — Correct use of `--wait`, async polling, and timeouts prevents false-green deployments and race conditions between sequential automation steps.
- **Security** — Automation must never embed long-lived secrets in repository scripts; JWT keys and consumer keys belong in secret stores, and commands should use least-privilege org users dedicated to CI.

## Architectural Tradeoffs

- **JSON everywhere vs selective JSON:** Parsing `--json` for every informational command adds noise; restrict structured parsing to commands whose results drive branching (deploy, test, data job status).
- **Fat shell scripts vs thin wrappers:** Large bash files are fast to write but hard to test; extracting JSON validation into a small Python stdlib script improves readability without adding package managers to the repo.
- **Global CLI vs project-local npm:** Global images are simpler for CI vendors; local `@salesforce/cli` pins help developer parity but require a consistent `npx`/`npm exec` invocation pattern.

## Anti-Patterns

1. **Implicit default org** — Relying on whichever alias is currently default on a shared runner breaks Reliability and Security expectations; always pass `--target-org`.
2. **Human-output parsing** — Scraping table output couples automation to cosmetic CLI changes; prefer documented JSON fields.
3. **Unbounded waits** — Setting infinite waits can stall queues; pair generous `--wait` values with monitoring and retry policies appropriate to the org.

## Official Sources Used

- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm — clarifies what the CLI ultimately deploys or validates against the Metadata API contract.
- Salesforce CLI Reference — https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference.htm — authoritative list of `sf` topics, flags, `--json`, and data/project command behavior.
- Salesforce DX Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_intro.htm — project layout, scratch org model, and CI authentication patterns such as JWT.
