# Well-Architected Notes — Scratch Org Management

## Relevant Pillars

- **Reliability** — Scratch org allocation limits are hard platform constraints. CI pipelines that do not explicitly delete orgs after each run will exhaust the pool and cause test failures unrelated to the code under test. Designing reliable lifecycle management (unconditional delete steps, short `--duration-days` for CI) directly supports pipeline reliability.

- **Operational Excellence** — The definition file is the operational specification for the development environment. Keeping it accurate and version-controlled ensures every developer and CI job gets the same environment. Drifting definition files (e.g., using deprecated `orgPreferences`, missing production features) are an operational risk that causes inconsistent test results.

- **Adaptable** — Org Shape allows scratch orgs to automatically adapt to changes in the production org's feature configuration without requiring manual definition file maintenance. This is the more adaptable pattern for mature teams where production features change regularly.

## Architectural Tradeoffs

**Definition File vs. Org Shape:**
A hand-maintained definition file gives precise, portable, version-controlled control over the org shape. It is the right choice for packaging workflows where a minimal, predictable environment is required. However, it requires ongoing maintenance as production features evolve. Org Shape trades that control for automatic alignment with production — valuable for application development teams but requires the source org to remain stable and accessible.

**Short vs. Long Scratch Org Lifetime:**
Short-lived orgs (1–2 days for CI, 7 days for feature work) minimize allocation pressure and enforce a clean-state discipline. Long-lived orgs (up to 30 days) reduce setup friction for extended feature work but accumulate drift and consume allocation slots. The right default is the shortest duration that covers the expected work unit.

**Shared Dev Hub vs. Dedicated Dev Hub:**
Using a Developer Edition as a shared Dev Hub caps the team at 3 active orgs and 6 daily creates — a hard bottleneck for teams with more than 2 developers plus CI. The architectural recommendation is to use an Enterprise or higher Dev Hub for any multi-developer team or automated CI pipeline.

## Anti-Patterns

1. **Shared mutable scratch org** — Multiple developers pushing to a single scratch org destroys source tracking integrity and creates a shared-mutable-environment anti-pattern that scratch orgs are specifically designed to avoid. Each developer and CI run should have its own isolated org.

2. **Definition file not committed to source control** — If the definition file is local-only or generated ad-hoc, there is no reproducible org shape. When a developer's org expires or a new team member joins, the org shape cannot be recreated deterministically. The definition file must live in `config/` and be committed alongside the source code it describes.

3. **CI pipeline without unconditional org deletion** — A pipeline that only deletes the scratch org on success will leak active orgs on every failed run. Over time this exhausts the daily active allocation. All CI pipelines must include a deletion step with an `if: always()` or equivalent unconditional guard.

## Official Sources Used

- Salesforce DX Developer Guide (Scratch Orgs) — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_scratch_orgs.htm
- Salesforce DX Developer Guide (Scratch Org Definition File) — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_scratch_orgs_def_file.htm
- Salesforce DX Developer Guide (Editions and Allocations) — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_scratch_orgs_editions_and_allocations.htm
- Salesforce DX Developer Guide (Manage Scratch Orgs from Dev Hub) — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_scratch_orgs_view_lex.htm
- Salesforce CLI Command Reference — https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
