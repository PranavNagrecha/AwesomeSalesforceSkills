# Well-Architected Notes — Metadata Diff Between Sandboxes

## Relevant Pillars

- **Operational Excellence** — Drift between sandboxes is the most common cause of mid-deploy failures. A diff pipeline that runs before promotion and surfaces source-only items turns surprise failures into a routine pre-flight check.
- **Reliability** — When a hotfix lands in Prod, the question "is everything else still aligned?" only has a fast answer if the diff is automated. Manual diffs degrade fast and miss types.

## Architectural Tradeoffs

- **Full-retrieve vs. scoped-retrieve:** Full retrieve catches everything but is slow and noisy. Scoped retrieve is fast and signal-rich but can miss drift in untouched types. Default to scoped + periodic full-retrieve audits.
- **CLI + git diff vs. specialized tooling:** Free, transparent, and infinite-flexibility on one side; pre-built profile-aware comparisons, audit history, and stakeholder-friendly UIs on the other. Most teams should start with CLI and adopt tooling when team size or audit needs justify it.
- **Treat target-only as candidate-for-delete vs. candidate-for-back-port:** The right choice depends on which org is the source of truth. Always state the source-of-truth assumption explicitly in the diff report header.

## Anti-Patterns

1. **Single flat unsorted diff list** — Without categorization (source-only / target-only / changed) the report is unreviewable. Always categorize.
2. **Treating retrieve coverage as universal** — Some metadata types are not retrievable. Absence of diff in those types is not evidence of equivalence. Document the gap.
3. **Auto-deploying destructiveChanges from a diff** — Destructive metadata operations against custom fields lose data irreversibly. Human review is the cheapest insurance.

## Official Sources Used

- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Salesforce CLI Reference — https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference.htm
- Salesforce DX Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_intro.htm
- Metadata Coverage Report — https://developer.salesforce.com/docs/metadata-coverage
- sfdx-hardis — https://sfdx-hardis.cloudity.com/
