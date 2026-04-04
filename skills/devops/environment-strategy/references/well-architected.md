# Well-Architected Notes — Environment Strategy

## Relevant Pillars

- **Adaptable** — Environment topology is the foundational enabler of adaptability. A well-designed topology allows teams to iterate quickly, test confidently at each stage, and release on a predictable cadence. The Salesforce Well-Architected Adaptable pillar explicitly covers environment parity, source-driven development, and pipeline design as core adaptability practices. Reference: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html

- **Operational Excellence** — Every environment must have a defined purpose, a refresh or expiry governance process, and a post-refresh runbook. Ad hoc environment management — creating sandboxes with no owner, no refresh plan, and no masking policy — is an operational risk that escalates as teams grow. Operational Excellence requires that environment operations are repeatable, documented, and owned.

- **Reliability** — Reliability testing requires environments with sufficient data parity and stability to detect regressions before they reach production. Using the wrong environment type (for example, using a scratch org for load testing) produces misleading results. Mapping test types to appropriate environments is a reliability practice.

## Architectural Tradeoffs

**Scratch orgs vs. persistent sandboxes for CI:** Scratch orgs give clean, parallel, disposable environments at the cost of requiring full source-driven development maturity. Teams that cannot deploy their full org configuration into a scratch org (due to managed packages, complex data, or unsupported metadata types) must use persistent sandboxes instead. The tradeoff is isolation and parallelism (scratch orgs) vs. configuration completeness and familiarity (sandboxes).

**Environment count vs. governance overhead:** More environments increase pipeline confidence but also increase operational overhead — more refresh schedules, more masking plans, more post-refresh automation, more cost. The minimum viable topology matches environment count to the number of meaningfully distinct pipeline stages. Adding environments that duplicate an existing stage's purpose without adding testing value is an anti-pattern.

**Trunk-based vs. feature-branch topology alignment:** Trunk-based development allows a simpler, smaller environment set. Feature-branch models require one environment per active long-lived branch, which multiplies environment count with team size. Choosing a branching strategy and a topology simultaneously — rather than evolving one to fit a pre-existing other — produces a more coherent design.

## Anti-Patterns

1. **Using a Full Sandbox as the primary development environment** — Full sandboxes have a 29-day refresh minimum and are expensive. Using one for individual developer work wastes a scarce resource, exposes production data to routine dev activity, and blocks the pre-production regression use case the Full sandbox is designed for. Use Developer or Developer Pro sandboxes for development work.

2. **No environment for integration testing between individual dev and UAT** — Without a dedicated integration environment (Developer Pro or Partial Copy), individual developer changes go directly to UAT without a merge gate. This means UAT constantly encounters unfinished, partially-integrated features. An integration sandbox functions as the shared merge target — equivalent to the `main` or `integration` branch in Git — where code is verified to work together before advancing.

3. **Scratch org topology with no Dev Hub capacity management** — Using scratch orgs for CI without tracking active org counts and enforcing deletion leads to Dev Hub capacity exhaustion. When the limit is hit, all scratch org creation fails silently or with cryptic errors. Capacity management (deletion on pipeline completion, scheduled cleanup jobs) is not optional in a scratch-org-based topology.

## Official Sources Used

- Salesforce Well-Architected Overview — Adaptable pillar, environment strategy and pipeline design framing
  URL: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html

- Salesforce DX Developer Guide — Scratch org creation, expiry, limits, Dev Hub capacity, source tracking behavior
  URL: https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_intro.htm

- Metadata API Developer Guide — Deployment mechanics, sandbox vs. scratch org deployment differences, manifest-based deployment
  URL: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm

- Salesforce CLI Reference — `sf org create scratch`, `sf org delete scratch`, `sf project deploy start` command behavior
  URL: https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference.htm
